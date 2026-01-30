"""Tests for IcebergRepository."""

from datetime import UTC, datetime
from pandas import DataFrame
from pyarrow import ipc
from unittest.mock import Mock
from uuid import uuid4

import io
import pyarrow as pa
import pytest

from horizon_data_core.base_types import DataRow, MetadataRow
from horizon_data_core.iceberg_repository import IcebergRepository, _serialize_to_arrow_ipc
from horizon_data_core.kafka_producer import KafkaProducer
from horizon_data_core.schema_discovery import FieldIdMap, PartitionFieldInfo, PartitionSpec


@pytest.fixture
def mock_producer():
    """Mock KafkaProducer."""
    producer = Mock(spec=KafkaProducer)
    producer.topic = "test.topic"
    producer.flush = Mock(return_value=0)
    return producer


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


@pytest.fixture
def sample_data_row():
    """Create a sample DataRow."""
    return DataRow(
        data_stream_id=uuid4(),
        datetime=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
        vector=[1.0, 2.0, 3.0],
        data_type="audio",
        track_id=uuid4(),
        vector_start_bound=0.0,
        vector_end_bound=100.0,
    )


@pytest.fixture
def sample_metadata_row():
    """Create a sample MetadataRow."""
    return MetadataRow(
        data_stream_id=uuid4(),
        datetime=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
        latitude=37.7749,
        longitude=-122.4194,
        altitude=10.0,
        speed=5.5,
        heading=90.0,
    )


def test_serialize_to_arrow_ipc_single_batch():
    """Test Arrow IPC serialization with single batch."""
    schema = pa.schema([pa.field("id", pa.int64()), pa.field("name", pa.string())])
    table = pa.table({"id": [1, 2, 3], "name": ["a", "b", "c"]}, schema=schema)

    result = _serialize_to_arrow_ipc(table)

    assert isinstance(result, bytes)
    assert len(result) > 0


    reader = ipc.open_stream(io.BytesIO(result))
    decoded = reader.read_all()
    assert decoded.num_rows == 3
    assert decoded.column_names == ["id", "name"]


def test_serialize_to_arrow_ipc_multiple_batches():
    """Test Arrow IPC serialization handles multiple batches."""
    schema = pa.schema([pa.field("value", pa.int64())])

    # Create table with multiple batches using properly named columns
    batch1 = pa.record_batch(DataFrame({"value": [1, 2]}), schema=schema)
    batch2 = pa.record_batch(DataFrame({"value": [3, 4]}), schema=schema)
    table = pa.Table.from_batches([batch1, batch2])

    result = _serialize_to_arrow_ipc(table)

    assert isinstance(result, bytes)

    reader = ipc.open_stream(io.BytesIO(result))
    decoded = reader.read_all()
    assert decoded.num_rows == 4  # All rows from both batches


def test_iceberg_repository_init(mock_producer, data_row_field_id_map, data_row_partition_spec):
    """Test IcebergRepository initialization."""
    repo = IcebergRepository[DataRow](mock_producer, data_row_field_id_map, data_row_partition_spec)

    assert repo.producer == mock_producer
    assert repo.field_id_map == data_row_field_id_map
    assert repo.partition_spec == data_row_partition_spec


def test_iceberg_repository_insert_data_row(mock_producer, data_row_field_id_map, data_row_partition_spec, sample_data_row):
    """Test inserting a DataRow."""
    repo = IcebergRepository[DataRow](mock_producer, data_row_field_id_map, data_row_partition_spec)

    result = repo.insert(sample_data_row)

    # Verify returned unchanged
    assert result == sample_data_row

    # Verify producer.produce was called
    mock_producer.produce.assert_called_once()
    call_args = mock_producer.produce.call_args
    key, payload = call_args[0]

    # Verify key is correct format (computed from partition spec)
    assert isinstance(key, bytes)
    assert str(sample_data_row.data_stream_id).encode() in key

    # Verify payload is Arrow IPC bytes
    assert isinstance(payload, bytes)
    assert len(payload) > 0


def test_iceberg_repository_insert_metadata_row(mock_producer, metadata_row_field_id_map, metadata_row_partition_spec, sample_metadata_row):
    """Test inserting a MetadataRow."""
    repo = IcebergRepository[MetadataRow](mock_producer, metadata_row_field_id_map, metadata_row_partition_spec)

    result = repo.insert(sample_metadata_row)

    assert result == sample_metadata_row
    mock_producer.produce.assert_called_once()


def test_iceberg_repository_insert_batch_empty(mock_producer, data_row_field_id_map, data_row_partition_spec):
    """Test insert_batch with empty list."""
    repo = IcebergRepository[DataRow](mock_producer, data_row_field_id_map, data_row_partition_spec)

    result = repo.insert_batch([])

    assert result == []
    mock_producer.produce.assert_not_called()


def test_iceberg_repository_insert_batch_single_key(mock_producer, data_row_field_id_map, data_row_partition_spec):
    """Test insert_batch with records sharing same partition key."""
    repo = IcebergRepository[DataRow](mock_producer, data_row_field_id_map, data_row_partition_spec)

    # Create rows with same partition key
    stream_id = uuid4()
    track_id = uuid4()
    dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    rows = [
        DataRow(
            data_stream_id=stream_id,
            datetime=dt,
            vector=[float(i)],
            data_type="audio",
            track_id=track_id,
            vector_start_bound=0.0,
            vector_end_bound=100.0,
        )
        for i in range(3)
    ]

    result = repo.insert_batch(rows)

    assert result == rows
    # Should produce exactly one message (all same key)
    assert mock_producer.produce.call_count == 1

    # Verify the message contains all rows
    call_args = mock_producer.produce.call_args[0]
    payload = call_args[1]


    reader = ipc.open_stream(io.BytesIO(payload))
    decoded = reader.read_all()
    assert decoded.num_rows == 3


def test_iceberg_repository_insert_batch_multiple_keys(mock_producer, data_row_field_id_map, data_row_partition_spec):
    """Test insert_batch groups by partition key."""
    repo = IcebergRepository[DataRow](mock_producer, data_row_field_id_map, data_row_partition_spec)

    # Create rows with different partition keys (different days)
    stream_id = uuid4()
    track_id = uuid4()

    rows = [
        DataRow(
            data_stream_id=stream_id,
            datetime=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),  # Day 1
            vector=[1.0],
            data_type="audio",
            track_id=track_id,
            vector_start_bound=0.0,
            vector_end_bound=100.0,
        ),
        DataRow(
            data_stream_id=stream_id,
            datetime=datetime(2025, 1, 16, 12, 0, 0, tzinfo=UTC),  # Day 2
            vector=[2.0],
            data_type="audio",
            track_id=track_id,
            vector_start_bound=0.0,
            vector_end_bound=100.0,
        ),
        DataRow(
            data_stream_id=stream_id,
            datetime=datetime(2025, 1, 15, 18, 0, 0, tzinfo=UTC),  # Day 1 again
            vector=[3.0],
            data_type="audio",
            track_id=track_id,
            vector_start_bound=0.0,
            vector_end_bound=100.0,
        ),
    ]

    result = repo.insert_batch(rows)

    assert result == rows
    # Should produce 2 messages (2 different days)
    assert mock_producer.produce.call_count == 2

    # Verify grouping by checking each call
    calls = mock_producer.produce.call_args_list
    keys = [call[0][0] for call in calls]
    assert len(set(keys)) == 2  # Two distinct keys


def test_iceberg_repository_insert_batch_different_streams(mock_producer, data_row_field_id_map, data_row_partition_spec):
    """Test insert_batch with different data streams."""
    repo = IcebergRepository[DataRow](mock_producer, data_row_field_id_map, data_row_partition_spec)

    # Different stream IDs = different keys
    rows = [
        DataRow(
            data_stream_id=uuid4(),
            datetime=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
            vector=[1.0],
            data_type="audio",
            track_id=uuid4(),
            vector_start_bound=0.0,
            vector_end_bound=100.0,
        )
        for _ in range(3)
    ]

    result = repo.insert_batch(rows)

    assert result == rows
    # Each row has different stream_id, so 3 separate messages
    assert mock_producer.produce.call_count == 3


def test_iceberg_repository_flush(mock_producer, data_row_field_id_map, data_row_partition_spec):
    """Test flush delegates to producer."""
    repo = IcebergRepository[DataRow](mock_producer, data_row_field_id_map, data_row_partition_spec)
    mock_producer.flush.return_value = 0

    result = repo.flush(timeout=5.0)

    assert result == 0
    mock_producer.flush.assert_called_once_with(5.0)


def test_iceberg_repository_flush_with_remaining(mock_producer, data_row_field_id_map, data_row_partition_spec):
    """Test flush returns remaining message count."""
    repo = IcebergRepository[DataRow](mock_producer, data_row_field_id_map, data_row_partition_spec)
    mock_producer.flush.return_value = 3

    result = repo.flush(timeout=1.0)

    assert result == 3


def test_iceberg_repository_upsert_not_supported(mock_producer, data_row_field_id_map, data_row_partition_spec, sample_data_row):
    """Test upsert raises NotImplementedError."""
    repo = IcebergRepository[DataRow](mock_producer, data_row_field_id_map, data_row_partition_spec)

    with pytest.raises(NotImplementedError, match="Upsert not supported"):
        repo.upsert(sample_data_row)


def test_iceberg_repository_list_not_supported(mock_producer, data_row_field_id_map, data_row_partition_spec):
    """Test list raises NotImplementedError."""
    repo = IcebergRepository[DataRow](mock_producer, data_row_field_id_map, data_row_partition_spec)

    with pytest.raises(NotImplementedError, match="Read operations not supported"):
        repo.list()


def test_iceberg_repository_get_not_supported(mock_producer, data_row_field_id_map, data_row_partition_spec):
    """Test get raises NotImplementedError."""
    repo = IcebergRepository[DataRow](mock_producer, data_row_field_id_map, data_row_partition_spec)

    with pytest.raises(NotImplementedError, match="Read operations not supported"):
        repo.get(id=uuid4())
