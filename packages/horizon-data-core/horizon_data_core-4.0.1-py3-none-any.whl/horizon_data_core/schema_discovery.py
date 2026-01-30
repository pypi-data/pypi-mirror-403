"""Iceberg schema discovery for dynamic field ID and partition spec mapping.

This module discovers field IDs and partition specs from Iceberg catalog at runtime,
enabling the SDK to write Parquet files with correct field IDs and partition keys
regardless of schema evolution history.

Field IDs are immutable once assigned in Iceberg - schema evolution only adds new fields.
This means field ID mappings can be cached forever at SDK initialization time.

Partition specs define how data is organized in the Iceberg table. The SDK uses these
specs to generate Kafka partition keys that align with Iceberg file layout.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

import pyarrow as pa
from pyiceberg.catalog import load_catalog
from pyiceberg.transforms import DayTransform, IdentityTransform
from pyiceberg.types import ListType, MapType, StructType

if TYPE_CHECKING:
    from pyiceberg.partitioning import PartitionField as IcebergPartitionField
    from pyiceberg.table import Table
    from pyiceberg.types import (
        IcebergType,
        NestedField,
    )

logger = logging.getLogger(__name__)


class FieldIdMap:
    """Immutable mapping of column names to Iceberg field IDs.

    Field IDs are discovered from the Iceberg catalog and cached for the lifetime
    of the SDK. This mapping is used when constructing PyArrow schemas to ensure
    Parquet files have correct field IDs for Iceberg compatibility.

    The mapping uses dot-notation for nested fields:
    - "vector" -> field ID for the list column
    - "vector.element" -> field ID for the list element
    - "struct_field.nested_field" -> field ID for nested struct field

    Example:
        >>> field_ids = discover_field_ids("http://localhost:8181", "horizon.data_row")
        >>> field_ids.get_field_id("data_stream_id")
        1
        >>> field_ids.get_field_id("vector")
        3
        >>> field_ids.get_field_id("vector.element")
        8
    """

    def __init__(self, table_name: str, mapping: dict[str, int]) -> None:
        """Initialize the field ID map.

        Args:
            table_name: Full Iceberg table name (e.g., "horizon.data_row")
            mapping: Dictionary mapping column paths to field IDs
        """
        self._table_name = table_name
        self._mapping = mapping.copy()  # Defensive copy for immutability

    @property
    def table_name(self) -> str:
        """Return the table name this mapping was created for."""
        return self._table_name

    def get_field_id(self, column_path: str) -> int:
        """Get field ID for a column path.

        Args:
            column_path: Dot-separated path to the field (e.g., "vector.element")

        Returns:
            The Iceberg field ID for the column

        Raises:
            ValueError: If the column path is not found in the table schema
        """
        if column_path not in self._mapping:
            msg = f"Column '{column_path}' not found in table '{self._table_name}'"
            raise ValueError(msg)
        return self._mapping[column_path]

    def validate_columns(self, required_columns: set[str]) -> None:
        """Validate that all required columns exist in the table schema.

        This should be called at SDK initialization to fail fast if the SDK's
        model fields don't match the Iceberg table schema.

        Args:
            required_columns: Set of column names required by the SDK model

        Raises:
            ValueError: If any required columns are missing from the table schema
        """
        available_columns = {k for k in self._mapping if "." not in k}
        missing = required_columns - available_columns
        if missing:
            msg = f"Columns {missing} required by SDK but not found in table '{self._table_name}'"
            raise ValueError(msg)

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return f"FieldIdMap(table={self._table_name!r}, fields={len(self._mapping)})"


def _add_field_ids_to_field(field: pa.Field, field_id_map: FieldIdMap, path: str = "") -> pa.Field:
    """Recursively add Iceberg field IDs to a PyArrow field.

    Args:
        field: PyArrow field to annotate
        field_id_map: Mapping of column paths to field IDs
        path: Current dot-separated path prefix

    Returns:
        New field with PARQUET:field_id metadata added
    """
    full_path = f"{path}.{field.name}" if path else field.name
    field_id = field_id_map.get_field_id(full_path)

    # Handle nested types
    if pa.types.is_list(field.type):
        # List types have an element field that needs its own field_id
        list_value_field = field.type.value_field
        annotated_element = _add_field_ids_to_field(list_value_field, field_id_map, full_path)
        list_type = pa.list_(annotated_element)
        return pa.field(field.name, list_type, nullable=field.nullable).with_metadata(
            {"PARQUET:field_id": str(field_id)}
        )

    if pa.types.is_struct(field.type):
        # Struct types have nested fields
        annotated_fields = [_add_field_ids_to_field(f, field_id_map, full_path) for f in field.type]
        struct_type = pa.struct(annotated_fields)
        return pa.field(field.name, struct_type, nullable=field.nullable).with_metadata(
            {"PARQUET:field_id": str(field_id)}
        )

    if pa.types.is_map(field.type):
        # Map types have key and value fields
        # Note: pa.map_() doesn't support field-level metadata, so we annotate key/value
        # fields but only their types are used in the final map type
        key_field = pa.field("key", field.type.key_type, nullable=False)
        map_value_field = pa.field("value", field.type.item_type, nullable=True)
        annotated_key = _add_field_ids_to_field(key_field, field_id_map, full_path)
        annotated_value = _add_field_ids_to_field(map_value_field, field_id_map, full_path)
        map_type = pa.map_(annotated_key.type, annotated_value.type)
        return pa.field(field.name, map_type, nullable=field.nullable).with_metadata(
            {"PARQUET:field_id": str(field_id)}
        )

    # Simple type - just add metadata
    return field.with_metadata({"PARQUET:field_id": str(field_id)})


def add_field_ids(schema: pa.Schema, field_id_map: FieldIdMap) -> pa.Schema:
    """Add Iceberg field IDs to a PyArrow schema.

    Annotates each field in the schema with PARQUET:field_id metadata,
    enabling Parquet files to be written with correct Iceberg field IDs.

    Handles nested types (lists, structs, maps) by recursively annotating
    child fields using dot-notation paths (e.g., "vector.element").

    Args:
        schema: PyArrow schema to annotate
        field_id_map: Mapping of column paths to Iceberg field IDs

    Returns:
        New schema with field ID metadata on all fields

    Example:
        >>> schema = pa.schema([
        ...     pa.field("id", pa.string()),
        ...     pa.field("vector", pa.list_(pa.field("element", pa.float32()))),
        ... ])
        >>> annotated = add_field_ids(schema, field_id_map)
    """
    annotated_fields = [_add_field_ids_to_field(f, field_id_map, "") for f in schema]
    return pa.schema(annotated_fields)


@dataclass(frozen=True)
class PartitionFieldInfo:
    """Information about a single partition field.

    Attributes:
        source_field_name: Name of the source column in the schema
        partition_name: Name of the partition field (e.g., "datetime_day")
        transform: Type of transform applied ("identity", "day", "bucket", etc.)
    """

    source_field_name: str
    partition_name: str
    transform: str


class PartitionSpec:
    """Immutable partition specification discovered from Iceberg catalog.

    Contains the list of partition fields and their transforms, used to generate
    partition keys for Kafka that align with Iceberg table partitioning.

    Example:
        >>> spec = discover_partition_spec("http://localhost:8181", "horizon.data_row")
        >>> # For a DataRow with data_stream_id, datetime, data_type, track_id
        >>> key = spec.compute_key(model_data)
        >>> # Returns bytes like: b"uuid-str|2025-01-15|audio|track-uuid"
    """

    def __init__(self, table_name: str, fields: list[PartitionFieldInfo]) -> None:
        """Initialize the partition spec.

        Args:
            table_name: Full Iceberg table name (e.g., "horizon.data_row")
            fields: List of partition fields in order
        """
        self._table_name = table_name
        self._fields = tuple(fields)  # Make immutable

    @property
    def table_name(self) -> str:
        """Return the table name this spec was created for."""
        return self._table_name

    @property
    def fields(self) -> tuple[PartitionFieldInfo, ...]:
        """Return the partition fields."""
        return self._fields

    def compute_key(self, data: dict[str, Any]) -> bytes:
        """Compute Kafka partition key from model data.

        Applies the partition transforms to extract values from the data
        and combines them into a pipe-separated key.

        Args:
            data: Dictionary of model field values (field_name -> value)

        Returns:
            UTF-8 encoded partition key as bytes

        Raises:
            KeyError: If a required partition field is missing from data
            ValueError: If a value cannot be transformed
        """
        key_parts: list[str] = []

        for field in self._fields:
            value = data.get(field.source_field_name)

            # Apply transform to get partition value
            transformed = self._apply_transform(value, field.transform)
            key_parts.append(transformed)

        return "|".join(key_parts).encode("utf-8")

    def _apply_transform(self, value: Any, transform: str) -> str:  # noqa: ANN401
        """Apply a partition transform to a value.

        Args:
            value: The source field value
            transform: Transform type ("identity", "day", etc.)

        Returns:
            String representation of the transformed value
        """
        if value is None:
            return ""

        if transform == "identity":
            # Identity transform - just convert to string
            if isinstance(value, UUID):
                return str(value)
            return str(value)

        if transform == "day":
            # Day transform - extract YYYY-MM-DD from datetime
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d")
            msg = f"Day transform requires datetime, got {type(value)}"
            raise ValueError(msg)

        # Add more transforms as needed (bucket, truncate, hour, month, year)
        msg = f"Unsupported transform: {transform}"
        raise ValueError(msg)

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        field_names = [f.partition_name for f in self._fields]
        return f"PartitionSpec(table={self._table_name!r}, fields={field_names})"


def _collect_field_ids(
    field: NestedField,
    mapping: dict[str, int],
    path: str = "",
) -> None:
    """Recursively collect field IDs for nested types.

    Args:
        field: Iceberg NestedField to process
        mapping: Dictionary to populate with path -> field_id mappings
        path: Current dot-separated path prefix
    """
    full_path = f"{path}.{field.name}" if path else field.name
    mapping[full_path] = field.field_id

    _collect_nested_type_ids(field.field_type, mapping, full_path)


def _collect_nested_type_ids(
    field_type: IcebergType,
    mapping: dict[str, int],
    path: str,
) -> None:
    """Collect field IDs from nested Iceberg types.

    Args:
        field_type: Iceberg type to inspect for nested fields
        mapping: Dictionary to populate with path -> field_id mappings
        path: Current dot-separated path prefix
    """
    if isinstance(field_type, ListType):
        # List element field
        element_field = field_type.element_field
        element_path = f"{path}.element"
        mapping[element_path] = element_field.field_id
        # Recurse if element is a complex type
        _collect_nested_type_ids(element_field.field_type, mapping, element_path)

    elif isinstance(field_type, StructType):
        # Struct fields
        for nested_field in field_type.fields:
            _collect_field_ids(nested_field, mapping, path)

    elif isinstance(field_type, MapType):
        # Map key and value fields
        key_path = f"{path}.key"
        value_path = f"{path}.value"
        mapping[key_path] = field_type.key_field.field_id
        mapping[value_path] = field_type.value_field.field_id
        # Recurse if key/value are complex types
        _collect_nested_type_ids(field_type.key_field.field_type, mapping, key_path)
        _collect_nested_type_ids(field_type.value_field.field_type, mapping, value_path)


def discover_field_ids(
    catalog_uri: str,
    table_name: str,
    warehouse: str | None = None,
    **catalog_props: str,
) -> FieldIdMap:
    """Query Iceberg catalog and build column name to field ID mapping.

    Connects to the Iceberg REST catalog, loads the table schema, and extracts
    all field IDs including those for nested types (lists, structs, maps).

    Args:
        catalog_uri: REST catalog URI (e.g., "http://localhost:8181")
        table_name: Full table name (e.g., "horizon.data_row")
        warehouse: Optional warehouse location
        **catalog_props: Additional catalog properties

    Returns:
        FieldIdMap containing all discovered field ID mappings

    Raises:
        Exception: If catalog connection fails or table doesn't exist

    Example:
        >>> field_ids = discover_field_ids(
        ...     "http://localhost:8181",
        ...     "horizon.data_row",
        ... )
        >>> field_ids.get_field_id("vector")
        3
    """
    # Build catalog properties
    properties: dict[str, str] = {"uri": catalog_uri}
    if warehouse is not None:
        properties["warehouse"] = warehouse
    properties.update(catalog_props)

    logger.info("Discovering field IDs from catalog %s for table %s", catalog_uri, table_name)

    catalog = load_catalog("rest", **properties)
    table = catalog.load_table(table_name)

    mapping: dict[str, int] = {}

    for field in table.schema().fields:
        _collect_field_ids(field, mapping)

    logger.debug("Discovered %d field mappings for %s: %s", len(mapping), table_name, mapping)

    return FieldIdMap(table_name, mapping)


def _get_transform_name(partition_field: IcebergPartitionField) -> str:
    """Extract transform name from a pyiceberg PartitionField.

    Args:
        partition_field: pyiceberg PartitionField object

    Returns:
        Transform name as string (e.g., "identity", "day", "bucket")
    """
    transform = partition_field.transform
    if isinstance(transform, IdentityTransform):
        return "identity"
    if isinstance(transform, DayTransform):
        return "day"
    # Add more as needed: HourTransform, MonthTransform, YearTransform, BucketTransform, TruncateTransform
    return type(transform).__name__.lower().replace("transform", "")


def _extract_partition_fields(table: Table) -> list[PartitionFieldInfo]:
    """Extract partition field info from an Iceberg table.

    Args:
        table: pyiceberg Table object

    Returns:
        List of PartitionFieldInfo in partition spec order
    """
    schema = table.schema()
    spec = table.spec()
    fields: list[PartitionFieldInfo] = []

    for partition_field in spec.fields:
        # Get source field name from schema using source_id
        source_field = schema.find_field(partition_field.source_id)
        source_name = source_field.name

        # Get transform type
        transform_name = _get_transform_name(partition_field)

        fields.append(
            PartitionFieldInfo(
                source_field_name=source_name,
                partition_name=partition_field.name,
                transform=transform_name,
            )
        )

    return fields


def discover_partition_spec(
    catalog_uri: str,
    table_name: str,
    warehouse: str | None = None,
    **catalog_props: str,
) -> PartitionSpec:
    """Query Iceberg catalog and build partition specification.

    Connects to the Iceberg REST catalog, loads the table partition spec,
    and builds a PartitionSpec that can compute partition keys from model data.

    Args:
        catalog_uri: REST catalog URI (e.g., "http://localhost:8181")
        table_name: Full table name (e.g., "horizon.data_row")
        warehouse: Optional warehouse location
        **catalog_props: Additional catalog properties

    Returns:
        PartitionSpec containing partition fields and transforms

    Raises:
        Exception: If catalog connection fails or table doesn't exist

    Example:
        >>> spec = discover_partition_spec(
        ...     "http://localhost:8181",
        ...     "horizon.data_row",
        ... )
        >>> # Compute key from model data
        >>> data = {"data_stream_id": uuid, "datetime": dt, "data_type": "audio", "track_id": track_uuid}
        >>> key = spec.compute_key(data)
    """
    # Build catalog properties
    properties: dict[str, str] = {"uri": catalog_uri}
    if warehouse is not None:
        properties["warehouse"] = warehouse
    properties.update(catalog_props)

    logger.info("Discovering partition spec from catalog %s for table %s", catalog_uri, table_name)

    catalog = load_catalog("rest", **properties)
    table = catalog.load_table(table_name)

    fields = _extract_partition_fields(table)

    logger.debug(
        "Discovered partition spec for %s: %s",
        table_name,
        [(f.source_field_name, f.transform) for f in fields],
    )

    return PartitionSpec(table_name, fields)
