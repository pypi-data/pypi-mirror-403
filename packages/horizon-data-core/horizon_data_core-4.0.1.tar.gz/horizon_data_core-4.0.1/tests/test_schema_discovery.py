"""Tests for Iceberg schema discovery module."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from horizon_data_core.schema_discovery import (
    FieldIdMap,
    PartitionFieldInfo,
    PartitionSpec,
    _collect_field_ids,
    _collect_nested_type_ids,
    _get_transform_name,
    discover_field_ids,
    discover_partition_spec,
)


class TestFieldIdMap:
    """Tests for FieldIdMap class."""

    def test_init_creates_defensive_copy(self):
        """Test that __init__ creates a defensive copy of the mapping."""
        original = {"col1": 1, "col2": 2}
        field_map = FieldIdMap("test.table", original)

        # Modify original - should not affect field_map
        original["col1"] = 999

        assert field_map.get_field_id("col1") == 1

    def test_table_name_property(self):
        """Test table_name property returns correct value."""
        field_map = FieldIdMap("horizon.data_row", {"col1": 1})
        assert field_map.table_name == "horizon.data_row"

    def test_get_field_id_returns_correct_id(self):
        """Test get_field_id returns correct field ID."""
        mapping = {
            "data_stream_id": 1,
            "datetime": 2,
            "vector": 3,
            "vector.element": 8,
        }
        field_map = FieldIdMap("test.table", mapping)

        assert field_map.get_field_id("data_stream_id") == 1
        assert field_map.get_field_id("datetime") == 2
        assert field_map.get_field_id("vector") == 3
        assert field_map.get_field_id("vector.element") == 8

    def test_get_field_id_raises_for_missing_column(self):
        """Test get_field_id raises ValueError for unknown column."""
        field_map = FieldIdMap("test.table", {"col1": 1})

        with pytest.raises(ValueError, match="Column 'unknown' not found in table 'test.table'"):
            field_map.get_field_id("unknown")

    def test_validate_columns_passes_for_valid_columns(self):
        """Test validate_columns passes when all required columns exist."""
        mapping = {"col1": 1, "col2": 2, "col3": 3, "nested.field": 4}
        field_map = FieldIdMap("test.table", mapping)

        # Should not raise
        field_map.validate_columns({"col1", "col2"})

    def test_validate_columns_raises_for_missing_columns(self):
        """Test validate_columns raises ValueError for missing columns."""
        mapping = {"col1": 1, "col2": 2}
        field_map = FieldIdMap("test.table", mapping)

        with pytest.raises(ValueError, match="Columns .* required by SDK but not found"):
            field_map.validate_columns({"col1", "col2", "col3", "col4"})

    def test_validate_columns_ignores_nested_paths(self):
        """Test validate_columns only checks top-level columns."""
        mapping = {"col1": 1, "col1.nested": 2}
        field_map = FieldIdMap("test.table", mapping)

        # Should pass - only "col1" is a top-level column
        field_map.validate_columns({"col1"})

        # Should fail - "nested" is not a top-level column
        with pytest.raises(ValueError, match="Columns .* required by SDK but not found"):
            field_map.validate_columns({"col1", "nested"})

    def test_repr(self):
        """Test __repr__ returns useful string."""
        field_map = FieldIdMap("horizon.data_row", {"col1": 1, "col2": 2})
        repr_str = repr(field_map)

        assert "FieldIdMap" in repr_str
        assert "horizon.data_row" in repr_str
        assert "2" in repr_str  # Number of fields


class TestCollectFieldIds:
    """Tests for _collect_field_ids helper function."""

    def test_collect_simple_field(self):
        """Test collecting field ID for simple field."""
        from pyiceberg.types import IntegerType, NestedField

        field = NestedField(field_id=1, name="col1", field_type=IntegerType(), required=True)
        mapping: dict[str, int] = {}

        _collect_field_ids(field, mapping)

        assert mapping == {"col1": 1}

    def test_collect_field_with_path(self):
        """Test collecting field ID with existing path prefix."""
        from pyiceberg.types import StringType, NestedField

        field = NestedField(field_id=5, name="nested", field_type=StringType(), required=True)
        mapping: dict[str, int] = {}

        _collect_field_ids(field, mapping, path="parent")

        assert mapping == {"parent.nested": 5}


class TestCollectNestedTypeIds:
    """Tests for _collect_nested_type_ids helper function."""

    def test_collect_list_type(self):
        """Test collecting field IDs for list type."""
        from pyiceberg.types import FloatType, ListType, NestedField

        element_field = NestedField(field_id=8, name="element", field_type=FloatType(), required=True)
        list_type = ListType(element_id=8, element=element_field.field_type, element_required=True)
        mapping: dict[str, int] = {}

        _collect_nested_type_ids(list_type, mapping, "vector")

        assert "vector.element" in mapping
        assert mapping["vector.element"] == 8

    def test_collect_struct_type(self):
        """Test collecting field IDs for struct type."""
        from pyiceberg.types import IntegerType, NestedField, StringType, StructType

        struct_type = StructType(
            NestedField(field_id=10, name="name", field_type=StringType(), required=True),
            NestedField(field_id=11, name="age", field_type=IntegerType(), required=False),
        )
        mapping: dict[str, int] = {}

        _collect_nested_type_ids(struct_type, mapping, "person")

        assert mapping == {"person.name": 10, "person.age": 11}

    def test_collect_map_type(self):
        """Test collecting field IDs for map type."""
        from pyiceberg.types import MapType, StringType

        map_type = MapType(
            key_id=20,
            key_type=StringType(),
            value_id=21,
            value_type=StringType(),
            value_required=False,
        )
        mapping: dict[str, int] = {}

        _collect_nested_type_ids(map_type, mapping, "properties")

        assert mapping["properties.key"] == 20
        assert mapping["properties.value"] == 21

    def test_collect_nested_list_in_struct(self):
        """Test collecting field IDs for nested list inside struct."""
        from pyiceberg.types import FloatType, ListType, NestedField, StructType

        # Struct with a list field
        list_type = ListType(element_id=15, element=FloatType(), element_required=True)
        struct_type = StructType(
            NestedField(field_id=12, name="values", field_type=list_type, required=True),
        )
        mapping: dict[str, int] = {}

        _collect_nested_type_ids(struct_type, mapping, "data")

        assert mapping["data.values"] == 12
        assert mapping["data.values.element"] == 15


class TestAddFieldIds:
    """Tests for add_field_ids helper function."""

    def test_add_field_ids_simple_schema(self):
        """Test adding field IDs to a simple schema."""
        import pyarrow as pa

        from horizon_data_core.schema_discovery import add_field_ids

        schema = pa.schema([
            pa.field("id", pa.int64()),
            pa.field("name", pa.string()),
        ])
        field_map = FieldIdMap("test.table", {"id": 1, "name": 2})

        result = add_field_ids(schema, field_map)

        assert result.field("id").metadata[b"PARQUET:field_id"] == b"1"
        assert result.field("name").metadata[b"PARQUET:field_id"] == b"2"

    def test_add_field_ids_list_type(self):
        """Test adding field IDs to schema with list column."""
        import pyarrow as pa

        from horizon_data_core.schema_discovery import add_field_ids

        schema = pa.schema([
            pa.field("vector", pa.list_(pa.field("element", pa.float32()))),
        ])
        field_map = FieldIdMap("test.table", {"vector": 3, "vector.element": 10})

        result = add_field_ids(schema, field_map)

        assert result.field("vector").metadata[b"PARQUET:field_id"] == b"3"
        # Check list element field
        list_type = result.field("vector").type
        assert list_type.value_field.metadata[b"PARQUET:field_id"] == b"10"

    def test_add_field_ids_struct_type(self):
        """Test adding field IDs to schema with struct column."""
        import pyarrow as pa

        from horizon_data_core.schema_discovery import add_field_ids

        schema = pa.schema([
            pa.field("person", pa.struct([
                pa.field("name", pa.string()),
                pa.field("age", pa.int32()),
            ])),
        ])
        field_map = FieldIdMap("test.table", {
            "person": 5,
            "person.name": 6,
            "person.age": 7,
        })

        result = add_field_ids(schema, field_map)

        assert result.field("person").metadata[b"PARQUET:field_id"] == b"5"
        struct_type = result.field("person").type
        assert struct_type.field("name").metadata[b"PARQUET:field_id"] == b"6"
        assert struct_type.field("age").metadata[b"PARQUET:field_id"] == b"7"

    def test_add_field_ids_raises_for_missing_field(self):
        """Test that add_field_ids raises ValueError for missing field."""
        import pyarrow as pa

        from horizon_data_core.schema_discovery import add_field_ids

        schema = pa.schema([pa.field("unknown", pa.string())])
        field_map = FieldIdMap("test.table", {"id": 1})

        with pytest.raises(ValueError, match="Column 'unknown' not found"):
            add_field_ids(schema, field_map)


class TestDiscoverFieldIds:
    """Tests for discover_field_ids function."""

    @patch("horizon_data_core.schema_discovery.load_catalog")
    def test_discover_field_ids_simple_schema(self, mock_load_catalog):
        """Test discovering field IDs from a simple schema."""
        from pyiceberg.types import IntegerType, NestedField, StringType

        # Create mock schema
        mock_schema = MagicMock()
        mock_schema.fields = [
            NestedField(field_id=1, name="id", field_type=IntegerType(), required=True),
            NestedField(field_id=2, name="name", field_type=StringType(), required=False),
        ]

        # Create mock table
        mock_table = MagicMock()
        mock_table.schema.return_value = mock_schema

        # Create mock catalog
        mock_catalog = MagicMock()
        mock_catalog.load_table.return_value = mock_table
        mock_load_catalog.return_value = mock_catalog

        result = discover_field_ids("http://localhost:8181", "test.table")

        assert result.get_field_id("id") == 1
        assert result.get_field_id("name") == 2
        mock_load_catalog.assert_called_once_with("rest", uri="http://localhost:8181")
        mock_catalog.load_table.assert_called_once_with("test.table")

    @patch("horizon_data_core.schema_discovery.load_catalog")
    def test_discover_field_ids_with_warehouse(self, mock_load_catalog):
        """Test discovering field IDs with warehouse configuration."""
        from pyiceberg.types import IntegerType, NestedField

        mock_schema = MagicMock()
        mock_schema.fields = [
            NestedField(field_id=1, name="col", field_type=IntegerType(), required=True),
        ]

        mock_table = MagicMock()
        mock_table.schema.return_value = mock_schema
        mock_catalog = MagicMock()
        mock_catalog.load_table.return_value = mock_table
        mock_load_catalog.return_value = mock_catalog

        discover_field_ids(
            "http://localhost:8181",
            "test.table",
            warehouse="s3://my-bucket/warehouse",
        )

        mock_load_catalog.assert_called_once_with(
            "rest",
            uri="http://localhost:8181",
            warehouse="s3://my-bucket/warehouse",
        )

    @patch("horizon_data_core.schema_discovery.load_catalog")
    def test_discover_field_ids_with_list_column(self, mock_load_catalog):
        """Test discovering field IDs from schema with list column."""
        from pyiceberg.types import FloatType, ListType, NestedField, StringType

        list_type = ListType(element_id=10, element=FloatType(), element_required=True)

        mock_schema = MagicMock()
        mock_schema.fields = [
            NestedField(field_id=1, name="id", field_type=StringType(), required=True),
            NestedField(field_id=2, name="vector", field_type=list_type, required=True),
        ]

        mock_table = MagicMock()
        mock_table.schema.return_value = mock_schema
        mock_catalog = MagicMock()
        mock_catalog.load_table.return_value = mock_table
        mock_load_catalog.return_value = mock_catalog

        result = discover_field_ids("http://localhost:8181", "test.table")

        assert result.get_field_id("id") == 1
        assert result.get_field_id("vector") == 2
        assert result.get_field_id("vector.element") == 10

    @patch("horizon_data_core.schema_discovery.load_catalog")
    def test_discover_field_ids_additional_props(self, mock_load_catalog):
        """Test discovering field IDs with additional catalog properties."""
        from pyiceberg.types import IntegerType, NestedField

        mock_schema = MagicMock()
        mock_schema.fields = [
            NestedField(field_id=1, name="col", field_type=IntegerType(), required=True),
        ]

        mock_table = MagicMock()
        mock_table.schema.return_value = mock_schema
        mock_catalog = MagicMock()
        mock_catalog.load_table.return_value = mock_table
        mock_load_catalog.return_value = mock_catalog

        discover_field_ids(
            "http://localhost:8181",
            "test.table",
            token="my-auth-token",
            custom_prop="value",
        )

        mock_load_catalog.assert_called_once_with(
            "rest",
            uri="http://localhost:8181",
            token="my-auth-token",
            custom_prop="value",
        )


class TestPartitionFieldInfo:
    """Tests for PartitionFieldInfo dataclass."""

    def test_partition_field_info_is_frozen(self):
        """Test that PartitionFieldInfo is immutable."""
        field = PartitionFieldInfo(
            source_field_name="data_stream_id",
            partition_name="data_stream_id",
            transform="identity",
        )

        with pytest.raises(AttributeError):
            field.transform = "day"


class TestPartitionSpec:
    """Tests for PartitionSpec class."""

    def test_init_stores_fields_as_tuple(self):
        """Test that fields are stored as immutable tuple."""
        fields = [
            PartitionFieldInfo("col1", "col1", "identity"),
            PartitionFieldInfo("col2", "col2_day", "day"),
        ]
        spec = PartitionSpec("test.table", fields)

        assert isinstance(spec.fields, tuple)
        assert len(spec.fields) == 2

    def test_table_name_property(self):
        """Test table_name property returns correct value."""
        spec = PartitionSpec("horizon.data_row", [])
        assert spec.table_name == "horizon.data_row"

    def test_compute_key_identity_transform(self):
        """Test compute_key with identity transform."""
        fields = [PartitionFieldInfo("id", "id", "identity")]
        spec = PartitionSpec("test.table", fields)

        data = {"id": "abc123"}
        key = spec.compute_key(data)

        assert key == b"abc123"

    def test_compute_key_uuid_identity(self):
        """Test compute_key converts UUID to string with identity transform."""
        fields = [PartitionFieldInfo("stream_id", "stream_id", "identity")]
        spec = PartitionSpec("test.table", fields)

        test_uuid = uuid4()
        data = {"stream_id": test_uuid}
        key = spec.compute_key(data)

        assert key == str(test_uuid).encode("utf-8")

    def test_compute_key_day_transform(self):
        """Test compute_key with day transform."""
        fields = [PartitionFieldInfo("datetime", "datetime_day", "day")]
        spec = PartitionSpec("test.table", fields)

        dt = datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC)
        data = {"datetime": dt}
        key = spec.compute_key(data)

        assert key == b"2025-01-15"

    def test_compute_key_multiple_fields(self):
        """Test compute_key combines multiple fields with pipe separator."""
        fields = [
            PartitionFieldInfo("stream_id", "stream_id", "identity"),
            PartitionFieldInfo("datetime", "datetime_day", "day"),
            PartitionFieldInfo("data_type", "data_type", "identity"),
        ]
        spec = PartitionSpec("test.table", fields)

        stream_id = uuid4()
        dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
        data = {"stream_id": stream_id, "datetime": dt, "data_type": "audio"}

        key = spec.compute_key(data)
        expected = f"{stream_id}|2025-01-15|audio".encode("utf-8")

        assert key == expected

    def test_compute_key_none_value(self):
        """Test compute_key handles None values."""
        fields = [PartitionFieldInfo("optional", "optional", "identity")]
        spec = PartitionSpec("test.table", fields)

        data = {"optional": None}
        key = spec.compute_key(data)

        assert key == b""

    def test_compute_key_day_transform_invalid_type(self):
        """Test compute_key raises for day transform on non-datetime."""
        fields = [PartitionFieldInfo("value", "value_day", "day")]
        spec = PartitionSpec("test.table", fields)

        data = {"value": "not-a-datetime"}

        with pytest.raises(ValueError, match="Day transform requires datetime"):
            spec.compute_key(data)

    def test_compute_key_unsupported_transform(self):
        """Test compute_key raises for unsupported transform."""
        fields = [PartitionFieldInfo("value", "value_bucket", "bucket")]
        spec = PartitionSpec("test.table", fields)

        data = {"value": 123}

        with pytest.raises(ValueError, match="Unsupported transform: bucket"):
            spec.compute_key(data)

    def test_repr(self):
        """Test __repr__ returns useful string."""
        fields = [
            PartitionFieldInfo("col1", "col1", "identity"),
            PartitionFieldInfo("col2", "col2_day", "day"),
        ]
        spec = PartitionSpec("horizon.data_row", fields)
        repr_str = repr(spec)

        assert "PartitionSpec" in repr_str
        assert "horizon.data_row" in repr_str
        assert "col1" in repr_str
        assert "col2_day" in repr_str


class TestGetTransformName:
    """Tests for _get_transform_name helper function."""

    def test_identity_transform(self):
        """Test identity transform is detected."""
        from pyiceberg.transforms import IdentityTransform

        mock_field = MagicMock()
        mock_field.transform = IdentityTransform()

        assert _get_transform_name(mock_field) == "identity"

    def test_day_transform(self):
        """Test day transform is detected."""
        from pyiceberg.transforms import DayTransform

        mock_field = MagicMock()
        mock_field.transform = DayTransform()

        assert _get_transform_name(mock_field) == "day"


class TestDiscoverPartitionSpec:
    """Tests for discover_partition_spec function."""

    @patch("horizon_data_core.schema_discovery.load_catalog")
    def test_discover_partition_spec_simple(self, mock_load_catalog):
        """Test discovering partition spec from catalog."""
        from pyiceberg.partitioning import PartitionField
        from pyiceberg.transforms import IdentityTransform
        from pyiceberg.types import IntegerType, NestedField, StringType

        # Create mock schema
        mock_schema = MagicMock()
        mock_schema.find_field.side_effect = lambda id: {
            1: NestedField(field_id=1, name="id", field_type=IntegerType(), required=True),
            2: NestedField(field_id=2, name="name", field_type=StringType(), required=False),
        }[id]

        # Create mock partition spec
        mock_spec = MagicMock()
        mock_spec.fields = [
            PartitionField(source_id=1, field_id=1000, transform=IdentityTransform(), name="id"),
        ]

        # Create mock table
        mock_table = MagicMock()
        mock_table.schema.return_value = mock_schema
        mock_table.spec.return_value = mock_spec

        # Create mock catalog
        mock_catalog = MagicMock()
        mock_catalog.load_table.return_value = mock_table
        mock_load_catalog.return_value = mock_catalog

        result = discover_partition_spec("http://localhost:8181", "test.table")

        assert result.table_name == "test.table"
        assert len(result.fields) == 1
        assert result.fields[0].source_field_name == "id"
        assert result.fields[0].partition_name == "id"
        assert result.fields[0].transform == "identity"

    @patch("horizon_data_core.schema_discovery.load_catalog")
    def test_discover_partition_spec_multiple_fields(self, mock_load_catalog):
        """Test discovering partition spec with multiple fields."""
        from pyiceberg.partitioning import PartitionField
        from pyiceberg.transforms import DayTransform, IdentityTransform
        from pyiceberg.types import IntegerType, NestedField, StringType, TimestampType

        # Create mock schema
        mock_schema = MagicMock()
        mock_schema.find_field.side_effect = lambda id: {
            1: NestedField(field_id=1, name="stream_id", field_type=StringType(), required=True),
            2: NestedField(field_id=2, name="datetime", field_type=TimestampType(), required=True),
            3: NestedField(field_id=3, name="data_type", field_type=StringType(), required=True),
        }[id]

        # Create mock partition spec
        mock_spec = MagicMock()
        mock_spec.fields = [
            PartitionField(source_id=1, field_id=1000, transform=IdentityTransform(), name="stream_id"),
            PartitionField(source_id=2, field_id=1001, transform=DayTransform(), name="datetime_day"),
            PartitionField(source_id=3, field_id=1002, transform=IdentityTransform(), name="data_type"),
        ]

        # Create mock table
        mock_table = MagicMock()
        mock_table.schema.return_value = mock_schema
        mock_table.spec.return_value = mock_spec

        # Create mock catalog
        mock_catalog = MagicMock()
        mock_catalog.load_table.return_value = mock_table
        mock_load_catalog.return_value = mock_catalog

        result = discover_partition_spec("http://localhost:8181", "test.table")

        assert len(result.fields) == 3
        assert result.fields[0] == PartitionFieldInfo("stream_id", "stream_id", "identity")
        assert result.fields[1] == PartitionFieldInfo("datetime", "datetime_day", "day")
        assert result.fields[2] == PartitionFieldInfo("data_type", "data_type", "identity")
