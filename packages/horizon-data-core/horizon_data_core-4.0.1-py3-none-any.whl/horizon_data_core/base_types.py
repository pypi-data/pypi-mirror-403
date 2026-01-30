"""Definitions for dataclasses."""

# Do not lint for exception strings being assigned to variables first
# ruff: noqa: EM101
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol, Self
from uuid import UUID

import pyarrow as pa
from dagster_pandera import pandera_schema_to_dagster_type
from pandera import DataFrameModel
from pandera.api.pandas.model_config import BaseConfig
from pandera.engines.pandas_engine import PydanticModel
from pydantic import BaseModel, Field

from horizon_data_core.helpers import name_to_uuid
from horizon_data_core.schema_discovery import FieldIdMap, add_field_ids


class PyarrowSerializable(Protocol):
    """Protocol for types that can be serialized to PyArrow tables.

    For Iceberg writes, field_id_map is required to ensure Parquet files
    have correct field IDs matching the Iceberg table schema.

    Partition keys are computed dynamically from the Iceberg table's partition
    spec, discovered at SDK initialization time.
    """

    def to_pyarrow(self, field_id_map: FieldIdMap) -> pa.Table:
        """Convert the model to a PyArrow table with Iceberg field IDs."""

    def model_dump(self, *, mode: str) -> dict:
        """Dump model to dictionary (provided by Pydantic BaseModel)."""
        ...


class BasePyarrowModel(BaseModel):
    """A base model for PyArrow models.

    Subclasses must implement pyarrow_schema() and to_pyarrow().
    The IcebergSerializable protocol enforces this at type-check time,
    while these methods enforce it at runtime.

    For Iceberg writes, field_id_map is required to ensure Parquet files
    have correct field IDs matching the Iceberg table schema.
    """

    @classmethod
    def pyarrow_schema(cls, field_id_map: FieldIdMap) -> pa.Schema:
        """Get the PyArrow schema for the model with Iceberg field IDs."""
        raise NotImplementedError("Subclasses must implement pyarrow_schema().")

    def to_pyarrow(self, field_id_map: FieldIdMap) -> pa.Table:
        """Convert the model to a PyArrow table with Iceberg field IDs."""
        raise NotImplementedError("Subclasses must implement to_pyarrow().")


class BasePostgresModel(BaseModel):
    """A base model for Postgres models.

    This simply ensures that all Postgres models have an id.
    """

    id: UUID | None
    created_datetime: None | datetime = None
    modified_datetime: None | datetime = None


class Mission(BasePostgresModel):
    """A group that can group entities around some bounded time or purpose."""

    name: None | str = None
    start_datetime: None | datetime = None
    end_datetime: None | datetime = None
    position: None | str = None
    free_text: None | str = None
    organization_id: UUID | None = None


class MissionEntity(BasePostgresModel):
    """A relationship table that specifies entity association with a mission."""

    mission_id: UUID
    entity_id: UUID
    organization_id: UUID | None = None


class EntityKind(BasePostgresModel):
    """A kind of entity."""

    name: None | str = None
    image_url: None | str = None
    short_description: None | str = None
    long_description: None | str = None
    organization_id: UUID | None = None


class Entity(BasePostgresModel):
    """An instance of an entity."""

    name: None | str = None
    kind_id: UUID
    free_text: None | str = None
    position: None | tuple[float, float] = None
    organization_id: UUID | None = None
    start_datetime: None | datetime = None
    end_datetime: None | datetime = None


class DataStream(BasePostgresModel):
    """A data stream of an entity."""

    entity_id: UUID
    organization_id: UUID | None = None
    name: None | str = None

    @classmethod
    def from_platform_and_name(cls, platform: Entity, data_stream_name: str) -> Self:
        """Create a DataStream from an entity and a name."""
        entity_id = platform.id
        assert entity_id is not None, "Entity ID should not be None when creating a datastream"
        name = data_stream_name.capitalize()
        id = name_to_uuid(f"{entity_id}:{name}")
        return cls(id=id, entity_id=entity_id, name=name)


class Ontology(BasePostgresModel):
    """An ontology for organizing entities."""

    name: None | str = None
    description: None | str = None
    organization_id: UUID | None = None


class OntologyClass(BasePostgresModel):
    """A class within an ontology."""

    ontology_id: UUID
    parent_id: UUID | None = None
    name: None | str = None
    description: None | str = None
    order: None | int = None
    organization_id: UUID | None = None
    relationship_type: None | str = None


class BeamgramSpecification(BasePostgresModel):
    """A specification for beamgram data processing."""

    center_bearing: None | float = None
    center_bin_width: None | float = None
    min_frequency: None | float = None
    max_frequency: None | float = None
    nfft: None | int = None
    organization_id: UUID | None = None
    elevation: None | float = None
    update_rate: None | timedelta = None
    normalizer: None | str = None


class BearingTimeRecordSpecification(BasePostgresModel):
    """A specification for bearing-time record data processing."""

    min_frequency: None | float = None
    max_frequency: None | float = None
    nfft: None | int = None
    frequency_spacing: None | float = None
    organization_id: UUID | None = None
    elevation: None | float = None
    update_rate: None | timedelta = None
    normalizer: None | str = None


class DataRow(BasePostgresModel, BasePyarrowModel):
    """A row of data in the Iceberg data_row table."""

    id: UUID | None = Field(default=None, exclude=True)
    data_stream_id: UUID
    datetime: datetime
    vector: list[float]
    data_type: str
    track_id: UUID
    vector_start_bound: float
    vector_end_bound: float

    @classmethod
    def pyarrow_schema(cls, field_id_map: FieldIdMap) -> pa.Schema:
        """Get the PyArrow schema for the model.

        Column names and field IDs are discovered from the Iceberg catalog at SDK init.
        Field IDs must match exactly for iceberg-rust to write data correctly.

        Args:
            field_id_map: Mapping of column names to Iceberg field IDs
        """
        schema = pa.schema(
            (
                pa.field("data_stream_id", pa.string(), nullable=False),
                pa.field("datetime", pa.timestamp("us", tz="UTC"), nullable=False),
                pa.field("vector", pa.list_(pa.field("element", pa.float32(), nullable=False)), nullable=False),
                pa.field("data_type", pa.string(), nullable=False),
                pa.field("track_id", pa.string(), nullable=True),
                pa.field("vector_start_bound", pa.float32(), nullable=False),
                pa.field("vector_end_bound", pa.float32(), nullable=False),
                pa.field("created_datetime", pa.timestamp("us", tz="UTC"), nullable=True),
            )
        )
        return add_field_ids(schema, field_id_map)

    def to_pyarrow(self, field_id_map: FieldIdMap) -> pa.Table:
        """Convert the model to a PyArrow table.

        Sets created_datetime to the current time if not already set,
        ensuring each row has an insert timestamp for duplicate resolution.

        Args:
            field_id_map: Mapping of column names to Iceberg field IDs
        """
        data = self.model_dump(mode="python", exclude_none=False)
        schema = self.pyarrow_schema(field_id_map)

        # Set created_datetime to now if not present
        if "created_datetime" not in data or data.get("created_datetime") is None:
            data["created_datetime"] = datetime.now(UTC)

        # Convert each field according to the schema
        arrays = []
        for field in schema:
            value = data.get(field.name)

            # Convert UUIDs to strings
            if isinstance(value, UUID):
                value = str(value)

            # Wrap single value in list for array creation
            arrays.append(pa.array([value], type=field.type))

        return pa.Table.from_arrays(arrays, schema=schema)


class MetadataRow(BasePostgresModel, BasePyarrowModel):
    """A row of metadata in the Iceberg metadata_row table."""

    id: UUID | None = Field(default=None, exclude=True)
    data_stream_id: UUID
    datetime: datetime
    latitude: None | float = None
    longitude: None | float = None
    altitude: None | float = None
    speed: None | float = None
    heading: None | float = None
    pitch: None | float = None
    roll: None | float = None
    speed_over_ground: None | float = None

    @classmethod
    def pyarrow_schema(cls, field_id_map: FieldIdMap) -> pa.Schema:
        """Get the PyArrow schema for the model.

        Column names and field IDs are discovered from the Iceberg catalog at SDK init.
        Field IDs must match exactly for iceberg-rust to write data correctly.

        Args:
            field_id_map: Mapping of column names to Iceberg field IDs
        """
        schema = pa.schema(
            (
                pa.field("data_stream_id", pa.string(), nullable=False),
                pa.field("datetime", pa.timestamp("us", tz="UTC"), nullable=False),
                pa.field("latitude", pa.float32(), nullable=True),
                pa.field("longitude", pa.float32(), nullable=True),
                pa.field("altitude", pa.float32(), nullable=True),
                pa.field("speed", pa.float32(), nullable=True),
                pa.field("heading", pa.float32(), nullable=True),
                pa.field("pitch", pa.float32(), nullable=True),
                pa.field("roll", pa.float32(), nullable=True),
                pa.field("speed_over_ground", pa.float32(), nullable=True),
                pa.field("created_datetime", pa.timestamp("us", tz="UTC"), nullable=True),
            )
        )
        return add_field_ids(schema, field_id_map)

    def to_pyarrow(self, field_id_map: FieldIdMap) -> pa.Table:
        """Convert the model to a PyArrow table.

        Sets created_datetime to the current time if not already set,
        ensuring each row has an insert timestamp for duplicate resolution.

        Args:
            field_id_map: Mapping of column names to Iceberg field IDs
        """
        data = self.model_dump(mode="python", exclude_none=False)
        schema = self.pyarrow_schema(field_id_map)

        # Set created_datetime to now if not present
        if "created_datetime" not in data or data.get("created_datetime") is None:
            data["created_datetime"] = datetime.now(UTC)

        # Convert each field according to the schema
        arrays = []
        for field in schema:
            value = data.get(field.name)

            # Convert UUIDs to strings
            if isinstance(value, UUID):
                value = str(value)

            # Wrap single value in list for array creation
            arrays.append(pa.array([value], type=field.type))

        return pa.Table.from_arrays(arrays, schema=schema)


class EntityBearingTimeRecordSpecification(BasePostgresModel):
    """A relationship table that specifies entity association with a btr specification."""

    entity_id: UUID
    bearing_time_record_specification_id: UUID
    organization_id: UUID | None = None


class EntityBeamgramSpecification(BasePostgresModel):
    """A relationship table that specifies entity association with a beamgram specification."""

    entity_id: UUID
    beamgram_specification_id: UUID
    organization_id: UUID | None = None


class EntityKindSchema(DataFrameModel):
    """Pandera schema using the Pydantic model."""

    class Config(BaseConfig):
        """Config with dataframe-level data type."""

        dtype = PydanticModel(EntityKind)
        title = "EntityKindSchema"
        coerce = True  # This is required, otherwise a SchemaInitError is raised


class EntitySchema(DataFrameModel):
    """Pandera schema using the Pydantic model."""

    class Config(BaseConfig):
        """Config with dataframe-level data type."""

        dtype = PydanticModel(Entity)
        title = "EntitySchema"
        coerce = True  # This is required, otherwise a SchemaInitError is raised


class DataStreamSchema(DataFrameModel):
    """Pandera schema using the Pydantic model."""

    class Config(BaseConfig):
        """Config with dataframe-level data type."""

        dtype = PydanticModel(DataStream)
        title = "DataStreamSchema"
        coerce = True  # This is required, otherwise a SchemaInitError is raised


class MissionSchema(DataFrameModel):
    """Pandera schema using the Pydantic model."""

    class Config(BaseConfig):
        """Config with dataframe-level data type."""

        dtype = PydanticModel(Mission)
        title = "MissionSchema"
        coerce = True  # This is required, otherwise a SchemaInitError is raised


class MissionEntitySchema(DataFrameModel):
    """Pandera schema using the Pydantic model."""

    class Config(BaseConfig):
        """Config with dataframe-level data type."""

        dtype = PydanticModel(MissionEntity)
        title = "MissionEntitySchema"
        coerce = True  # This is required, otherwise a SchemaInitError is raised


class OntologySchema(DataFrameModel):
    """Pandera schema using the Pydantic model."""

    class Config(BaseConfig):
        """Config with dataframe-level data type."""

        dtype = PydanticModel(Ontology)
        title = "OntologySchema"
        coerce = True  # This is required, otherwise a SchemaInitError is raised


class OntologyClassSchema(DataFrameModel):
    """Pandera schema using the Pydantic model."""

    class Config(BaseConfig):
        """Config with dataframe-level data type."""

        dtype = PydanticModel(OntologyClass)
        title = "OntologyClassSchema"
        coerce = True  # This is required, otherwise a SchemaInitError is raised


class BeamgramSpecificationSchema(DataFrameModel):
    """Pandera schema using the Pydantic model."""

    class Config(BaseConfig):
        """Config with dataframe-level data type."""

        dtype = PydanticModel(BeamgramSpecification)
        title = "BeamgramSpecificationSchema"
        coerce = True  # This is required, otherwise a SchemaInitError is raised


class BearingTimeRecordSpecificationSchema(DataFrameModel):
    """Pandera schema using the Pydantic model."""

    class Config(BaseConfig):
        """Config with dataframe-level data type."""

        dtype = PydanticModel(BearingTimeRecordSpecification)
        title = "BearingTimeRecordSpecificationSchema"
        coerce = True  # This is required, otherwise a SchemaInitError is raised


class DataRowSchema(DataFrameModel):
    """Pandera schema using the Pydantic model."""

    class Config(BaseConfig):
        """Config with dataframe-level data type."""

        dtype = PydanticModel(DataRow)
        title = "DataRowSchema"
        coerce = True  # This is required, otherwise a SchemaInitError is raised


class MetadataRowSchema(DataFrameModel):
    """Pandera schema using the Pydantic model."""

    class Config(BaseConfig):
        """Config with dataframe-level data type."""

        dtype = PydanticModel(MetadataRow)
        title = "MetadataRowSchema"
        coerce = True  # This is required, otherwise a SchemaInitError is raised


EntityKindSchemaType = pandera_schema_to_dagster_type(EntityKindSchema)
EntitySchemaType = pandera_schema_to_dagster_type(EntitySchema)
DataStreamSchemaType = pandera_schema_to_dagster_type(DataStreamSchema)
MissionSchemaType = pandera_schema_to_dagster_type(MissionSchema)
MissionEntitySchemaType = pandera_schema_to_dagster_type(MissionEntitySchema)
OntologySchemaType = pandera_schema_to_dagster_type(OntologySchema)
OntologyClassSchemaType = pandera_schema_to_dagster_type(OntologyClassSchema)
BeamgramSpecificationSchemaType = pandera_schema_to_dagster_type(BeamgramSpecificationSchema)
BearingTimeRecordSpecificationSchemaType = pandera_schema_to_dagster_type(BearingTimeRecordSpecificationSchema)
DataRowSchemaType = pandera_schema_to_dagster_type(DataRowSchema)
MetadataRowSchemaType = pandera_schema_to_dagster_type(MetadataRowSchema)
