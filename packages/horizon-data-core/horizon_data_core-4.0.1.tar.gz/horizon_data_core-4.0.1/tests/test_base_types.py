"""Tests for base types and PyArrow serialization."""

from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest

from horizon_data_core.base_types import BasePyarrowModel, DataRow, MetadataRow
from horizon_data_core.schema_discovery import FieldIdMap, PartitionFieldInfo, PartitionSpec


@pytest.fixture
def data_row_field_id_map():
    """Create a mock FieldIdMap for DataRow.

    Field IDs match the actual Iceberg schema in horizon-database.
    See: packages/horizon-database/src/iceberg/tables/data_row.py
    """
    mapping = {
        "data_stream_id": 1,
        "datetime": 2,
        "vector": 3,
        "data_type": 4,
        "track_id": 5,
        "vector_start_bound": 6,
        "vector_end_bound": 7,
        "created_datetime": 8,
        "vector.element": 10,  # List element field ID from ListType(10, ...)
    }
    return FieldIdMap("horizon_public.data_row", mapping)


@pytest.fixture
def metadata_row_field_id_map():
    """Create a mock FieldIdMap for MetadataRow.

    Field IDs match the actual Iceberg schema in horizon-database.
    See: packages/horizon-database/src/iceberg/tables/metadata_row.py
    """
    mapping = {
        "data_stream_id": 1,
        "datetime": 2,
        "latitude": 3,
        "longitude": 4,
        "altitude": 5,
        "speed": 6,
        "heading": 7,
        "pitch": 8,
        "roll": 9,
        "speed_over_ground": 10,
        "created_datetime": 11,
    }
    return FieldIdMap("horizon_public.metadata_row", mapping)


@pytest.fixture
def data_row_partition_spec():
    """Create a mock PartitionSpec for DataRow.

    Partition fields match the actual Iceberg schema in horizon-database.
    See: packages/horizon-database/src/iceberg/tables/data_row.py
    """
    fields = [
        PartitionFieldInfo(source_field_name="data_stream_id", partition_name="data_stream_id", transform="identity"),
        PartitionFieldInfo(source_field_name="datetime", partition_name="datetime_day", transform="day"),
        PartitionFieldInfo(source_field_name="data_type", partition_name="data_type", transform="identity"),
        PartitionFieldInfo(source_field_name="track_id", partition_name="track_id", transform="identity"),
    ]
    return PartitionSpec("horizon_public.data_row", fields)


@pytest.fixture
def metadata_row_partition_spec():
    """Create a mock PartitionSpec for MetadataRow.

    Partition fields match the actual Iceberg schema in horizon-database.
    See: packages/horizon-database/src/iceberg/tables/metadata_row.py
    """
    fields = [
        PartitionFieldInfo(source_field_name="data_stream_id", partition_name="data_stream_id", transform="identity"),
        PartitionFieldInfo(source_field_name="datetime", partition_name="datetime_day", transform="day"),
    ]
    return PartitionSpec("horizon_public.metadata_row", fields)


# =============================================================================
# Tests for PartitionSpec.compute_key() behavior
# =============================================================================


def test_partition_spec_compute_key_data_row_format(data_row_partition_spec):
    """Test PartitionSpec.compute_key() returns correct format for DataRow data."""
    stream_id = uuid4()
    track_id = uuid4()
    dt = datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC)

    data = {
        "data_stream_id": stream_id,
        "datetime": dt,
        "vector": [1.0, 2.0, 3.0],
        "data_type": "audio",
        "track_id": track_id,
        "vector_start_bound": 0.0,
        "vector_end_bound": 100.0,
    }

    key = data_row_partition_spec.compute_key(data)

    # Should be bytes
    assert isinstance(key, bytes)

    # Decode to verify format
    key_str = key.decode("utf-8")

    # Should contain all partition fields separated by |
    assert str(stream_id) in key_str
    assert "2025-01-15" in key_str  # Day format
    assert "audio" in key_str
    assert str(track_id) in key_str

    # Verify format is exactly: stream_id|day|data_type|track_id
    parts = key_str.split("|")
    assert len(parts) == 4
    assert parts[0] == str(stream_id)
    assert parts[1] == "2025-01-15"
    assert parts[2] == "audio"
    assert parts[3] == str(track_id)


def test_partition_spec_compute_key_same_partition(data_row_partition_spec):
    """Test PartitionSpec.compute_key() returns same key for same partition."""
    stream_id = uuid4()
    track_id = uuid4()
    dt1 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC)
    dt2 = datetime(2025, 1, 15, 18, 30, 0, tzinfo=UTC)  # Same day, different time

    data1 = {
        "data_stream_id": stream_id,
        "datetime": dt1,
        "data_type": "audio",
        "track_id": track_id,
    }

    data2 = {
        "data_stream_id": stream_id,
        "datetime": dt2,  # Different time, same day
        "data_type": "audio",
        "track_id": track_id,
    }

    # Same partition = same key
    assert data_row_partition_spec.compute_key(data1) == data_row_partition_spec.compute_key(data2)


def test_partition_spec_compute_key_different_day(data_row_partition_spec):
    """Test PartitionSpec.compute_key() returns different key for different days."""
    stream_id = uuid4()
    track_id = uuid4()

    data1 = {
        "data_stream_id": stream_id,
        "datetime": datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
        "data_type": "audio",
        "track_id": track_id,
    }

    data2 = {
        "data_stream_id": stream_id,
        "datetime": datetime(2025, 1, 16, 12, 0, 0, tzinfo=UTC),  # Next day
        "data_type": "audio",
        "track_id": track_id,
    }

    # Different day = different key
    assert data_row_partition_spec.compute_key(data1) != data_row_partition_spec.compute_key(data2)


def test_partition_spec_compute_key_different_data_type(data_row_partition_spec):
    """Test PartitionSpec.compute_key() returns different key for different data types."""
    stream_id = uuid4()
    track_id = uuid4()
    dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    data1 = {
        "data_stream_id": stream_id,
        "datetime": dt,
        "data_type": "audio",
        "track_id": track_id,
    }

    data2 = {
        "data_stream_id": stream_id,
        "datetime": dt,
        "data_type": "video",  # Different type
        "track_id": track_id,
    }

    # Different data_type = different key
    assert data_row_partition_spec.compute_key(data1) != data_row_partition_spec.compute_key(data2)


def test_partition_spec_compute_key_different_track(data_row_partition_spec):
    """Test PartitionSpec.compute_key() returns different key for different tracks."""
    stream_id = uuid4()
    dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    data1 = {
        "data_stream_id": stream_id,
        "datetime": dt,
        "data_type": "audio",
        "track_id": uuid4(),
    }

    data2 = {
        "data_stream_id": stream_id,
        "datetime": dt,
        "data_type": "audio",
        "track_id": uuid4(),  # Different track
    }

    # Different track_id = different key
    assert data_row_partition_spec.compute_key(data1) != data_row_partition_spec.compute_key(data2)


def test_partition_spec_compute_key_metadata_row_format(metadata_row_partition_spec):
    """Test PartitionSpec.compute_key() returns correct format for MetadataRow data."""
    stream_id = uuid4()
    dt = datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC)

    data = {
        "data_stream_id": stream_id,
        "datetime": dt,
        "latitude": 37.7749,
        "longitude": -122.4194,
    }

    key = metadata_row_partition_spec.compute_key(data)

    # Should be bytes
    assert isinstance(key, bytes)

    # Decode to verify format
    key_str = key.decode("utf-8")

    # Should contain stream_id and day
    assert str(stream_id) in key_str
    assert "2025-01-15" in key_str

    # Verify format is exactly: stream_id|day
    parts = key_str.split("|")
    assert len(parts) == 2
    assert parts[0] == str(stream_id)
    assert parts[1] == "2025-01-15"


def test_partition_spec_compute_key_metadata_same_partition(metadata_row_partition_spec):
    """Test PartitionSpec.compute_key() returns same key for same partition."""
    stream_id = uuid4()
    dt1 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC)
    dt2 = datetime(2025, 1, 15, 22, 30, 0, tzinfo=UTC)  # Same day, different time

    data1 = {
        "data_stream_id": stream_id,
        "datetime": dt1,
    }

    data2 = {
        "data_stream_id": stream_id,
        "datetime": dt2,  # Different time, same day
    }

    # Same partition = same key
    assert metadata_row_partition_spec.compute_key(data1) == metadata_row_partition_spec.compute_key(data2)


def test_partition_spec_compute_key_metadata_different_day(metadata_row_partition_spec):
    """Test PartitionSpec.compute_key() returns different key for different days."""
    stream_id = uuid4()

    data1 = {
        "data_stream_id": stream_id,
        "datetime": datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
    }

    data2 = {
        "data_stream_id": stream_id,
        "datetime": datetime(2025, 1, 16, 12, 0, 0, tzinfo=UTC),  # Next day
    }

    # Different day = different key
    assert metadata_row_partition_spec.compute_key(data1) != metadata_row_partition_spec.compute_key(data2)


def test_partition_spec_compute_key_metadata_different_stream(metadata_row_partition_spec):
    """Test PartitionSpec.compute_key() returns different key for different streams."""
    dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    data1 = {
        "data_stream_id": uuid4(),
        "datetime": dt,
    }

    data2 = {
        "data_stream_id": uuid4(),  # Different stream
        "datetime": dt,
    }

    # Different stream_id = different key
    assert metadata_row_partition_spec.compute_key(data1) != metadata_row_partition_spec.compute_key(data2)


def test_partition_spec_compute_key_month_boundary(data_row_partition_spec):
    """Test PartitionSpec.compute_key() handles month boundaries correctly."""
    stream_id = uuid4()
    track_id = uuid4()

    data1 = {
        "data_stream_id": stream_id,
        "datetime": datetime(2025, 1, 31, 23, 59, 59, tzinfo=UTC),
        "data_type": "audio",
        "track_id": track_id,
    }

    data2 = {
        "data_stream_id": stream_id,
        "datetime": datetime(2025, 2, 1, 0, 0, 1, tzinfo=UTC),
        "data_type": "audio",
        "track_id": track_id,
    }

    # Different days across month boundary
    key1 = data_row_partition_spec.compute_key(data1)
    key2 = data_row_partition_spec.compute_key(data2)
    assert key1 != key2
    assert b"2025-01-31" in key1
    assert b"2025-02-01" in key2


# =============================================================================
# Tests for to_pyarrow() behavior
# =============================================================================


def test_data_row_to_pyarrow_sets_created_datetime(data_row_field_id_map):
    """Test DataRow.to_pyarrow() auto-sets created_datetime to now."""
    stream_id = uuid4()
    track_id = uuid4()
    dt = datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC)

    row = DataRow(
        data_stream_id=stream_id,
        datetime=dt,
        vector=[1.0, 2.0, 3.0],
        data_type="audio",
        track_id=track_id,
        vector_start_bound=0.0,
        vector_end_bound=100.0,
    )

    mock_now = datetime(2025, 6, 15, 10, 0, 0, tzinfo=UTC)
    with patch("horizon_data_core.base_types.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_now
        table = row.to_pyarrow(data_row_field_id_map)

    created_datetime_col = table.column("created_datetime")
    assert created_datetime_col[0].as_py() == mock_now


def test_data_row_to_pyarrow_converts_uuids_to_strings(data_row_field_id_map):
    """Test DataRow.to_pyarrow() converts UUIDs to strings."""
    stream_id = uuid4()
    track_id = uuid4()
    dt = datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC)

    row = DataRow(
        data_stream_id=stream_id,
        datetime=dt,
        vector=[1.0],
        data_type="audio",
        track_id=track_id,
        vector_start_bound=0.0,
        vector_end_bound=100.0,
    )

    table = row.to_pyarrow(data_row_field_id_map)

    assert table.column("data_stream_id")[0].as_py() == str(stream_id)
    assert table.column("track_id")[0].as_py() == str(track_id)


def test_data_row_to_pyarrow_uses_field_ids_from_map(data_row_field_id_map):
    """Test DataRow.to_pyarrow() uses field IDs from the field ID map."""
    stream_id = uuid4()
    track_id = uuid4()
    dt = datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC)

    row = DataRow(
        data_stream_id=stream_id,
        datetime=dt,
        vector=[1.0],
        data_type="audio",
        track_id=track_id,
        vector_start_bound=0.0,
        vector_end_bound=100.0,
    )

    table = row.to_pyarrow(data_row_field_id_map)
    schema = table.schema

    # Verify field IDs are from the map, not hardcoded
    assert schema.field("data_stream_id").metadata[b"PARQUET:field_id"] == b"1"
    assert schema.field("datetime").metadata[b"PARQUET:field_id"] == b"2"
    assert schema.field("vector").metadata[b"PARQUET:field_id"] == b"3"
    assert schema.field("data_type").metadata[b"PARQUET:field_id"] == b"4"


def test_metadata_row_to_pyarrow_sets_created_datetime(metadata_row_field_id_map):
    """Test MetadataRow.to_pyarrow() auto-sets created_datetime to now."""
    stream_id = uuid4()
    dt = datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC)

    row = MetadataRow(
        data_stream_id=stream_id,
        datetime=dt,
        latitude=37.0,
        longitude=-122.0,
    )

    mock_now = datetime(2025, 6, 15, 10, 0, 0, tzinfo=UTC)
    with patch("horizon_data_core.base_types.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_now
        table = row.to_pyarrow(metadata_row_field_id_map)

    created_datetime_col = table.column("created_datetime")
    assert created_datetime_col[0].as_py() == mock_now


def test_metadata_row_to_pyarrow_converts_uuid_to_string(metadata_row_field_id_map):
    """Test MetadataRow.to_pyarrow() converts UUID to string."""
    stream_id = uuid4()
    dt = datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC)

    row = MetadataRow(
        data_stream_id=stream_id,
        datetime=dt,
        latitude=37.0,
        longitude=-122.0,
    )

    table = row.to_pyarrow(metadata_row_field_id_map)

    assert table.column("data_stream_id")[0].as_py() == str(stream_id)


def test_metadata_row_to_pyarrow_handles_nulls(metadata_row_field_id_map):
    """Test MetadataRow.to_pyarrow() handles nullable fields correctly."""
    stream_id = uuid4()
    dt = datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC)

    row = MetadataRow(
        data_stream_id=stream_id,
        datetime=dt,
        latitude=None,
        longitude=None,
        altitude=None,
        speed=None,
        heading=None,
    )

    table = row.to_pyarrow(metadata_row_field_id_map)

    assert table.column("latitude")[0].as_py() is None
    assert table.column("longitude")[0].as_py() is None
    assert table.column("altitude")[0].as_py() is None
    assert table.column("speed")[0].as_py() is None
    assert table.column("heading")[0].as_py() is None


def test_metadata_row_to_pyarrow_uses_field_ids_from_map(metadata_row_field_id_map):
    """Test MetadataRow.to_pyarrow() uses field IDs from the field ID map."""
    stream_id = uuid4()
    dt = datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC)

    row = MetadataRow(
        data_stream_id=stream_id,
        datetime=dt,
        latitude=37.0,
        longitude=-122.0,
    )

    table = row.to_pyarrow(metadata_row_field_id_map)
    schema = table.schema

    # Verify field IDs are from the map, not hardcoded
    assert schema.field("data_stream_id").metadata[b"PARQUET:field_id"] == b"1"
    assert schema.field("datetime").metadata[b"PARQUET:field_id"] == b"2"
    assert schema.field("latitude").metadata[b"PARQUET:field_id"] == b"3"
    assert schema.field("longitude").metadata[b"PARQUET:field_id"] == b"4"


# =============================================================================
# Tests for BasePyarrowModel enforcement
# =============================================================================


def test_base_pyarrow_model_pyarrow_schema_raises(data_row_field_id_map):
    """Test BasePyarrowModel.pyarrow_schema() raises NotImplementedError."""
    with pytest.raises(NotImplementedError, match="Subclasses must implement pyarrow_schema"):
        BasePyarrowModel.pyarrow_schema(data_row_field_id_map)


def test_base_pyarrow_model_to_pyarrow_raises(data_row_field_id_map):
    """Test BasePyarrowModel.to_pyarrow() raises NotImplementedError."""
    model = BasePyarrowModel()
    with pytest.raises(NotImplementedError, match="Subclasses must implement to_pyarrow"):
        model.to_pyarrow(data_row_field_id_map)
