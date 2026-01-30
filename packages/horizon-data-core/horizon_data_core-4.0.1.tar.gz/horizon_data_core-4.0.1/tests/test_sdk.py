import os
from uuid import uuid4, UUID
import pytest
from horizon_data_core.client import PostgresClient
from horizon_data_core.sdk import HorizonSDK, IcebergRepository
from horizon_data_core.base_types import Entity
from sqlalchemy import text
from unittest.mock import Mock


@pytest.fixture
def initialized_sdk() -> HorizonSDK:
    """Fixture to initialize SDK with database connection."""
    postgres_client = PostgresClient(
        user=os.environ.get("OWNER_PGUSER", "postgres"),
        password=os.environ.get("OWNER_PGPASSWORD", "password"),
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", 5432)),
        database=os.environ.get("PGDATABASE", "horizon"),
        sslmode="disable",
        channel_binding="prefer",
    )
    iceberg_catalog_properties: dict[str, str | None] = {
        "uri": "http://localhost:8181",
        "warehouse": "file://./iceberg/warehouse",
    }
    return HorizonSDK(postgres_client, iceberg_catalog_properties, None)


@pytest.fixture
def entity_kind_id(initialized_sdk: HorizonSDK) -> UUID:
    """Fixture to create an entity kind for use in repository tests."""
    kind_id = uuid4()
    with initialized_sdk.postgres_client.session() as session:
        session.execute(
            text("INSERT INTO horizon_public.entity_kind (id, name) VALUES (:id, :name)"),
            {"id": kind_id, "name": "Test Entity Kind"}
        )
        session.commit()
    return kind_id


def test_create_sdk() -> None:
    """Test that the SDK can be created."""
    postgres_client = PostgresClient(
        user="postgres",
        password="password",
        host="localhost",
        port=5432,
        database="horizon",
        sslmode="disable",
        channel_binding="prefer",
    )
    iceberg_catalog_properties: dict[str, str | None] = {
        "uri": "http://localhost:8181",
        "warehouse": "file://./iceberg/warehouse",
    }
    sdk = HorizonSDK(postgres_client, iceberg_catalog_properties, None)
    assert sdk is not None


# Repository Operation Tests

def test_repository_insert(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that repository insert() creates a new record."""
    entity = Entity(
        id=uuid4(),
        kind_id=entity_kind_id,
        name="Test Entity",
    )
    result = initialized_sdk.entities.insert(entity)
    assert result.id == entity.id
    assert result.name == "Test Entity"
    assert result.kind_id == entity_kind_id


def test_repository_insert_batch(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that repository insert_batch() creates multiple records."""
    entities = [
        Entity(id=uuid4(), kind_id=entity_kind_id, name="Entity 1"),
        Entity(id=uuid4(), kind_id=entity_kind_id, name="Entity 2"),
    ]
    result = initialized_sdk.entities.insert_batch(entities)
    assert len(result) == 2
    assert all(r.name in ["Entity 1", "Entity 2"] for r in result)


def test_repository_insert_batch_empty(initialized_sdk: HorizonSDK) -> None:
    """Test that repository insert_batch() returns empty list for empty input."""
    result = initialized_sdk.entities.insert_batch([])
    assert result == []


def test_repository_read(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that repository read() retrieves a record by ID."""
    entity = Entity(id=uuid4(), kind_id=entity_kind_id, name="Test Entity")
    created = initialized_sdk.entities.insert(entity)
    assert created.id is not None
    
    result = initialized_sdk.entities.read(created.id)
    assert result is not None
    assert result.id == created.id
    assert result.name == "Test Entity"


def test_repository_read_not_found(initialized_sdk: HorizonSDK) -> None:
    """Test that repository read() returns None for non-existent ID."""
    result = initialized_sdk.entities.read(uuid4())
    assert result is None


def test_repository_update(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that repository update() modifies an existing record."""
    entity = Entity(id=uuid4(), kind_id=entity_kind_id, name="Original Name")
    created = initialized_sdk.entities.insert(entity)
    assert created.id is not None
    
    updated_entity = Entity(id=created.id, kind_id=entity_kind_id, name="Updated Name")
    result = initialized_sdk.entities.update(updated_entity)
    assert result.name == "Updated Name"
    
    # Verify update persisted
    read_result = initialized_sdk.entities.read(created.id)
    assert read_result is not None
    assert read_result.name == "Updated Name"


def test_repository_delete(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that repository delete() removes a record."""
    entity = Entity(id=uuid4(), kind_id=entity_kind_id, name="Entity to delete")
    created = initialized_sdk.entities.insert(entity)
    assert created.id is not None
    
    deleted = initialized_sdk.entities.delete(created.id)
    assert deleted is True
    
    # Verify it's gone
    result = initialized_sdk.entities.read(created.id)
    assert result is None


def test_repository_delete_not_found(initialized_sdk: HorizonSDK) -> None:
    """Test that repository delete() returns False for non-existent ID."""
    result = initialized_sdk.entities.delete(uuid4())
    assert result is False


def test_repository_list(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that repository list() returns all records."""
    entity1 = initialized_sdk.entities.insert(Entity(id=uuid4(), kind_id=entity_kind_id, name="Entity 1"))
    entity2 = initialized_sdk.entities.insert(Entity(id=uuid4(), kind_id=entity_kind_id, name="entity 2"))
    
    result = initialized_sdk.entities.list()
    assert len(result) >= 2
    entity_ids = {e.id for e in result}
    assert entity1.id in entity_ids
    assert entity2.id in entity_ids


def test_repository_list_with_filters(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that repository list() filters records correctly."""
    entity1 = initialized_sdk.entities.insert(Entity(id=uuid4(), kind_id=entity_kind_id, name="Filtered Entity"))
    initialized_sdk.entities.insert(Entity(id=uuid4(), kind_id=entity_kind_id, name="Other Entity"))
    
    # Filter by name
    result = initialized_sdk.entities.list(name="Filtered Entity")  # type: ignore[arg-type]
    assert len(result) >= 1
    assert all(e.name == "Filtered Entity" for e in result)
    assert entity1.id in {e.id for e in result}
    
    # Filter by kind_id
    kind_result = initialized_sdk.entities.list(kind_id=entity_kind_id)  # type: ignore[arg-type]
    assert len(kind_result) >= 2
    assert all(e.kind_id == entity_kind_id for e in kind_result)


def test_repository_upsert_create(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that repository upsert() creates a new record when it doesn't exist."""
    entity = Entity(id=uuid4(), kind_id=entity_kind_id, name="New Entity")
    result = initialized_sdk.entities.upsert(entity, unique_fields=["id"], merge_fields=["name", "kind_id"])
    assert result.id == entity.id
    assert result.id is not None
    
    # Verify it was created
    read_result = initialized_sdk.entities.read(result.id)
    assert read_result is not None
    assert read_result.name == "New Entity"


def test_repository_upsert_update(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that repository upsert() updates an existing record."""
    entity = Entity(id=uuid4(), kind_id=entity_kind_id, name="Original Name")
    created = initialized_sdk.entities.insert(entity)
    assert created.id is not None
    
    # Upsert with updated name
    updated = Entity(id=created.id, kind_id=entity_kind_id, name="Upserted Name")
    result = initialized_sdk.entities.upsert(updated, unique_fields=["id"], merge_fields=["name"])
    assert result.name == "Upserted Name"
    
    # Verify update persisted
    read_result = initialized_sdk.entities.read(created.id)
    assert read_result is not None
    assert read_result.name == "Upserted Name"


def test_repository_upsert_batch(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that repository upsert_batch() creates or updates multiple records."""
    # Create one entity first
    existing = initialized_sdk.entities.insert(Entity(id=uuid4(), kind_id=entity_kind_id, name="Existing"))
    assert existing.id is not None
    
    # Upsert batch with one existing and one new
    entities = [
        Entity(id=existing.id, kind_id=entity_kind_id, name="Updated Existing"),
        Entity(id=uuid4(), kind_id=entity_kind_id, name="New Entity"),
    ]
    result = initialized_sdk.entities.upsert_batch(entities, unique_fields=["id"], merge_fields=["name", "kind_id"])
    assert len(result) == 2
    
    # Verify existing was updated
    read_existing = initialized_sdk.entities.read(existing.id)
    assert read_existing is not None
    assert read_existing.name == "Updated Existing"
    
    # Verify new was created
    new_ids = {e.id for e in result}
    assert entities[1].id in new_ids

def test_sdk_read_data_stream(initialized_sdk: HorizonSDK) -> None:
    """Test that SDK read_data_stream calls the repository read method."""
    initialized_sdk.data_streams.read = Mock()  # type: ignore[method-assign]
    initialized_sdk.read_data_stream(uuid4())
    initialized_sdk.data_streams.read.assert_called_once()

def test_sdk_update_data_stream(initialized_sdk: HorizonSDK) -> None:
    """Test that SDK update_data_stream calls the repository upsert method."""
    initialized_sdk.data_streams.upsert = Mock()  # type: ignore[method-assign]
    initialized_sdk.update_data_stream(Mock())
    initialized_sdk.data_streams.upsert.assert_called_once()

def test_sdk_delete_data_stream(initialized_sdk: HorizonSDK) -> None:
    """Test that SDK delete_data_stream calls the repository delete method."""
    initialized_sdk.data_streams.delete = Mock()  # type: ignore[method-assign]
    initialized_sdk.delete_data_stream(uuid4())
    initialized_sdk.data_streams.delete.assert_called_once()

def test_sdk_list_data_streams(initialized_sdk: HorizonSDK) -> None:
    """Test that SDK list_data_streams calls the repository list method."""
    initialized_sdk.data_streams.list = Mock()  # type: ignore[method-assign]
    initialized_sdk.list_data_streams()
    initialized_sdk.data_streams.list.assert_called_once()

def test_sdk_create_mission(initialized_sdk: HorizonSDK) -> None:
    """Test that SDK create_mission calls the repository insert method."""
    initialized_sdk.missions.insert = Mock()  # type: ignore[method-assign]
    initialized_sdk.create_mission(Mock())
    initialized_sdk.missions.insert.assert_called_once()

def test_sdk_read_mission(initialized_sdk: HorizonSDK) -> None:
    """Test that SDK read_mission calls the repository read method."""
    initialized_sdk.missions.read = Mock()  # type: ignore[method-assign]
    initialized_sdk.read_mission(Mock())
    initialized_sdk.missions.read.assert_called_once()

def test_sdk_update_mission(initialized_sdk: HorizonSDK) -> None:
    """Test that SDK update_mission calls the repository update method."""
    initialized_sdk.missions.update = Mock()  # type: ignore[method-assign]
    initialized_sdk.update_mission(Mock())
    initialized_sdk.missions.update.assert_called_once()

def test_sdk_delete_mission(initialized_sdk: HorizonSDK) -> None:
    """Test that SDK read_mission calls the repository delete method."""
    initialized_sdk.missions.delete = Mock()  # type: ignore[method-assign]
    initialized_sdk.delete_mission(Mock())
    initialized_sdk.missions.delete.assert_called_once()


# Iceberg Backend Tests


def test_sdk_iceberg_backend_requires_kafka_config() -> None:
    """Test that Iceberg backend requires kafka_config."""
    from horizon_data_core.kafka_config import StorageBackend

    postgres_client = PostgresClient(
        user="postgres",
        password="password",
        host="localhost",
        port=5432,
        database="horizon",
        sslmode="disable",
        channel_binding="prefer",
    )
    iceberg_catalog_properties: dict[str, str | None] = {
        "uri": "http://localhost:8181",
        "warehouse": "file://./iceberg/warehouse",
    }

    with pytest.raises(ValueError, match="kafka_config is required"):
        HorizonSDK(
            postgres_client,
            iceberg_catalog_properties,
            None,
            storage_backend=StorageBackend.ICEBERG,
            kafka_config=None,  # Missing!
        )


def test_sdk_iceberg_backend_initialization() -> None:
    """Test SDK initializes with Iceberg backend."""
    from unittest.mock import patch

    from horizon_data_core.iceberg_repository import IcebergRepository
    from horizon_data_core.kafka_config import KafkaConfig, StorageBackend
    from horizon_data_core.schema_discovery import FieldIdMap, PartitionFieldInfo, PartitionSpec

    postgres_client = PostgresClient(
        user="postgres",
        password="password",
        host="localhost",
        port=5432,
        database="horizon",
        sslmode="disable",
        channel_binding="prefer",
    )
    iceberg_catalog_properties: dict[str, str | None] = {
        "uri": "http://localhost:8181",
        "warehouse": "file://./iceberg/warehouse",
    }
    kafka_config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        data_row_topic="test.data_row",
        metadata_row_topic="test.metadata_row",
    )

    # Mock discover_field_ids to avoid catalog connection
    # Field IDs match actual Iceberg schema in horizon-database
    data_row_field_ids = FieldIdMap("horizon_public.data_row", {
        "data_stream_id": 1, "datetime": 2, "vector": 3, "data_type": 4,
        "track_id": 5, "vector_start_bound": 6, "vector_end_bound": 7,
        "created_datetime": 8, "vector.element": 10,
    })
    metadata_row_field_ids = FieldIdMap("horizon_public.metadata_row", {
        "data_stream_id": 1, "datetime": 2, "latitude": 3, "longitude": 4,
        "altitude": 5, "speed": 6, "heading": 7, "pitch": 8, "roll": 9,
        "speed_over_ground": 10, "created_datetime": 11,
    })

    # Mock partition specs
    data_row_partition_spec = PartitionSpec("horizon_public.data_row", [
        PartitionFieldInfo(source_field_name="data_stream_id", partition_name="data_stream_id", transform="identity"),
        PartitionFieldInfo(source_field_name="datetime", partition_name="datetime_day", transform="day"),
        PartitionFieldInfo(source_field_name="data_type", partition_name="data_type", transform="identity"),
        PartitionFieldInfo(source_field_name="track_id", partition_name="track_id", transform="identity"),
    ])
    metadata_row_partition_spec = PartitionSpec("horizon_public.metadata_row", [
        PartitionFieldInfo(source_field_name="data_stream_id", partition_name="data_stream_id", transform="identity"),
        PartitionFieldInfo(source_field_name="datetime", partition_name="datetime_day", transform="day"),
    ])

    with (
        patch("horizon_data_core.sdk.discover_field_ids") as mock_discover_fields,
        patch("horizon_data_core.sdk.discover_partition_spec") as mock_discover_spec,
    ):
        mock_discover_fields.side_effect = [data_row_field_ids, metadata_row_field_ids]
        mock_discover_spec.side_effect = [data_row_partition_spec, metadata_row_partition_spec]

        sdk = HorizonSDK(
            postgres_client,
            iceberg_catalog_properties,
            None,
            storage_backend=StorageBackend.ICEBERG,
            kafka_config=kafka_config,
        )

        # Verify repositories are IcebergRepository instances
        assert isinstance(sdk.data_rows, IcebergRepository)
        assert isinstance(sdk.metadata_rows, IcebergRepository)

        # Verify other repositories are still PostgresRepository
        from horizon_data_core.sdk import PostgresRepository

        assert isinstance(sdk.entities, PostgresRepository)
        assert isinstance(sdk.missions, PostgresRepository)


def test_sdk_iceberg_backend_separate_producers() -> None:
    """Test SDK creates separate producers for data_row and metadata_row."""
    from unittest.mock import patch

    from horizon_data_core.kafka_config import KafkaConfig, StorageBackend
    from horizon_data_core.schema_discovery import FieldIdMap, PartitionFieldInfo, PartitionSpec

    postgres_client = PostgresClient(
        user="postgres",
        password="password",
        host="localhost",
        port=5432,
        database="horizon",
        sslmode="disable",
        channel_binding="prefer",
    )
    iceberg_catalog_properties: dict[str, str | None] = {
        "uri": "http://localhost:8181",
        "warehouse": "file://./iceberg/warehouse",
    }
    kafka_config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        data_row_topic="horizon.data_row",
        metadata_row_topic="horizon.metadata_row",
    )

    # Mock discover_field_ids to avoid catalog connection
    # Field IDs match actual Iceberg schema in horizon-database
    data_row_field_ids = FieldIdMap("horizon_public.data_row", {
        "data_stream_id": 1, "datetime": 2, "vector": 3, "data_type": 4,
        "track_id": 5, "vector_start_bound": 6, "vector_end_bound": 7,
        "created_datetime": 8, "vector.element": 10,
    })
    metadata_row_field_ids = FieldIdMap("horizon_public.metadata_row", {
        "data_stream_id": 1, "datetime": 2, "latitude": 3, "longitude": 4,
        "altitude": 5, "speed": 6, "heading": 7, "pitch": 8, "roll": 9,
        "speed_over_ground": 10, "created_datetime": 11,
    })

    # Mock partition specs
    data_row_partition_spec = PartitionSpec("horizon_public.data_row", [
        PartitionFieldInfo(source_field_name="data_stream_id", partition_name="data_stream_id", transform="identity"),
        PartitionFieldInfo(source_field_name="datetime", partition_name="datetime_day", transform="day"),
        PartitionFieldInfo(source_field_name="data_type", partition_name="data_type", transform="identity"),
        PartitionFieldInfo(source_field_name="track_id", partition_name="track_id", transform="identity"),
    ])
    metadata_row_partition_spec = PartitionSpec("horizon_public.metadata_row", [
        PartitionFieldInfo(source_field_name="data_stream_id", partition_name="data_stream_id", transform="identity"),
        PartitionFieldInfo(source_field_name="datetime", partition_name="datetime_day", transform="day"),
    ])

    with (
        patch("horizon_data_core.sdk.discover_field_ids") as mock_discover_fields,
        patch("horizon_data_core.sdk.discover_partition_spec") as mock_discover_spec,
    ):
        mock_discover_fields.side_effect = [data_row_field_ids, metadata_row_field_ids]
        mock_discover_spec.side_effect = [data_row_partition_spec, metadata_row_partition_spec]

        sdk = HorizonSDK(
            postgres_client,
            iceberg_catalog_properties,
            None,
            storage_backend=StorageBackend.ICEBERG,
            kafka_config=kafka_config,
        )

        # Verify producers have correct topics
        assert sdk.data_rows.producer.topic == "horizon.data_row"
        assert sdk.metadata_rows.producer.topic == "horizon.metadata_row"

        # Verify they're different producer instances
        assert sdk.data_rows.producer is not sdk.metadata_rows.producer


def test_sdk_postgres_backend_default() -> None:
    """Test SDK defaults to Postgres backend."""
    from horizon_data_core.sdk import PostgresRepository

    postgres_client = PostgresClient(
        user="postgres",
        password="password",
        host="localhost",
        port=5432,
        database="horizon",
        sslmode="disable",
        channel_binding="prefer",
    )
    iceberg_catalog_properties: dict[str, str | None] = {
        "uri": "http://localhost:8181",
        "warehouse": "file://./iceberg/warehouse",
    }

    # No storage_backend specified = defaults to POSTGRES
    sdk = HorizonSDK(postgres_client, iceberg_catalog_properties, None)

    # Verify repositories are PostgresRepository instances
    assert isinstance(sdk.data_rows, PostgresRepository)
    assert isinstance(sdk.metadata_rows, PostgresRepository)


def test_sdk_context_manager_iceberg_backend() -> None:
    """Test SDK context manager closes Kafka producers for Iceberg backend."""
    from unittest.mock import Mock, patch

    from horizon_data_core.kafka_config import KafkaConfig, StorageBackend
    from horizon_data_core.schema_discovery import FieldIdMap, PartitionFieldInfo, PartitionSpec

    postgres_client = PostgresClient(
        user="postgres",
        password="password",
        host="localhost",
        port=5432,
        database="horizon",
        sslmode="disable",
        channel_binding="prefer",
    )
    iceberg_catalog_properties: dict[str, str | None] = {
        "uri": "http://localhost:8181",
        "warehouse": "file://./iceberg/warehouse",
    }
    kafka_config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        data_row_topic="horizon.data_row",
        metadata_row_topic="horizon.metadata_row",
    )

    # Mock discover_field_ids to avoid catalog connection
    # Field IDs match actual Iceberg schema in horizon-database
    data_row_field_ids = FieldIdMap("horizon_public.data_row", {
        "data_stream_id": 1, "datetime": 2, "vector": 3, "data_type": 4,
        "track_id": 5, "vector_start_bound": 6, "vector_end_bound": 7,
        "created_datetime": 8, "vector.element": 10,
    })
    metadata_row_field_ids = FieldIdMap("horizon_public.metadata_row", {
        "data_stream_id": 1, "datetime": 2, "latitude": 3, "longitude": 4,
        "altitude": 5, "speed": 6, "heading": 7, "pitch": 8, "roll": 9,
        "speed_over_ground": 10, "created_datetime": 11,
    })

    # Mock partition specs
    data_row_partition_spec = PartitionSpec("horizon_public.data_row", [
        PartitionFieldInfo(source_field_name="data_stream_id", partition_name="data_stream_id", transform="identity"),
        PartitionFieldInfo(source_field_name="datetime", partition_name="datetime_day", transform="day"),
        PartitionFieldInfo(source_field_name="data_type", partition_name="data_type", transform="identity"),
        PartitionFieldInfo(source_field_name="track_id", partition_name="track_id", transform="identity"),
    ])
    metadata_row_partition_spec = PartitionSpec("horizon_public.metadata_row", [
        PartitionFieldInfo(source_field_name="data_stream_id", partition_name="data_stream_id", transform="identity"),
        PartitionFieldInfo(source_field_name="datetime", partition_name="datetime_day", transform="day"),
    ])

    # Mock KafkaProducer to track close() calls
    with (
        patch("horizon_data_core.sdk.discover_field_ids") as mock_discover_fields,
        patch("horizon_data_core.sdk.discover_partition_spec") as mock_discover_spec,
        patch("horizon_data_core.sdk.KafkaProducer") as MockProducer,
    ):
        mock_discover_fields.side_effect = [data_row_field_ids, metadata_row_field_ids]
        mock_discover_spec.side_effect = [data_row_partition_spec, metadata_row_partition_spec]
        mock_data_producer = Mock()
        mock_metadata_producer = Mock()
        MockProducer.side_effect = [mock_data_producer, mock_metadata_producer]

        # Use SDK in context manager
        with HorizonSDK(
            postgres_client,
            iceberg_catalog_properties,
            None,
            storage_backend=StorageBackend.ICEBERG,
            kafka_config=kafka_config,
        ) as sdk:
            # Verify SDK is returned
            assert sdk is not None

        # Verify close() was called on both producers
        mock_data_producer.close.assert_called_once()
        mock_metadata_producer.close.assert_called_once()


def test_sdk_context_manager_postgres_backend() -> None:
    """Test SDK context manager works with Postgres backend (no-op)."""
    postgres_client = PostgresClient(
        user="postgres",
        password="password",
        host="localhost",
        port=5432,
        database="horizon",
        sslmode="disable",
        channel_binding="prefer",
    )
    iceberg_catalog_properties: dict[str, str | None] = {
        "uri": "http://localhost:8181",
        "warehouse": "file://./iceberg/warehouse",
    }

    # Use SDK in context manager with Postgres backend
    with HorizonSDK(postgres_client, iceberg_catalog_properties, None) as sdk:
        # Verify SDK is returned
        assert sdk is not None
        # No exception should be raised - Postgres backend has no cleanup


def test_sdk_context_manager_exception_during_close() -> None:
    """Test SDK context manager handles exceptions during producer close."""
    from unittest.mock import Mock, patch

    from horizon_data_core.kafka_config import KafkaConfig, StorageBackend
    from horizon_data_core.schema_discovery import FieldIdMap, PartitionFieldInfo, PartitionSpec

    postgres_client = PostgresClient(
        user="postgres",
        password="password",
        host="localhost",
        port=5432,
        database="horizon",
        sslmode="disable",
        channel_binding="prefer",
    )
    iceberg_catalog_properties: dict[str, str | None] = {
        "uri": "http://localhost:8181",
        "warehouse": "file://./iceberg/warehouse",
    }
    kafka_config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        data_row_topic="horizon.data_row",
        metadata_row_topic="horizon.metadata_row",
    )

    # Mock discover_field_ids to avoid catalog connection
    # Field IDs match actual Iceberg schema in horizon-database
    data_row_field_ids = FieldIdMap("horizon_public.data_row", {
        "data_stream_id": 1, "datetime": 2, "vector": 3, "data_type": 4,
        "track_id": 5, "vector_start_bound": 6, "vector_end_bound": 7,
        "created_datetime": 8, "vector.element": 10,
    })
    metadata_row_field_ids = FieldIdMap("horizon_public.metadata_row", {
        "data_stream_id": 1, "datetime": 2, "latitude": 3, "longitude": 4,
        "altitude": 5, "speed": 6, "heading": 7, "pitch": 8, "roll": 9,
        "speed_over_ground": 10, "created_datetime": 11,
    })

    # Mock partition specs
    data_row_partition_spec = PartitionSpec("horizon_public.data_row", [
        PartitionFieldInfo(source_field_name="data_stream_id", partition_name="data_stream_id", transform="identity"),
        PartitionFieldInfo(source_field_name="datetime", partition_name="datetime_day", transform="day"),
        PartitionFieldInfo(source_field_name="data_type", partition_name="data_type", transform="identity"),
        PartitionFieldInfo(source_field_name="track_id", partition_name="track_id", transform="identity"),
    ])
    metadata_row_partition_spec = PartitionSpec("horizon_public.metadata_row", [
        PartitionFieldInfo(source_field_name="data_stream_id", partition_name="data_stream_id", transform="identity"),
        PartitionFieldInfo(source_field_name="datetime", partition_name="datetime_day", transform="day"),
    ])

    # Mock KafkaProducer to raise exception on close
    with (
        patch("horizon_data_core.sdk.discover_field_ids") as mock_discover_fields,
        patch("horizon_data_core.sdk.discover_partition_spec") as mock_discover_spec,
        patch("horizon_data_core.sdk.KafkaProducer") as MockProducer,
    ):
        mock_discover_fields.side_effect = [data_row_field_ids, metadata_row_field_ids]
        mock_discover_spec.side_effect = [data_row_partition_spec, metadata_row_partition_spec]
        mock_data_producer = Mock()
        mock_metadata_producer = Mock()
        mock_data_producer.close.side_effect = Exception("Kafka connection failed")
        MockProducer.side_effect = [mock_data_producer, mock_metadata_producer]

        # Should not raise exception - errors are logged
        with HorizonSDK(
            postgres_client,
            iceberg_catalog_properties,
            None,
            storage_backend=StorageBackend.ICEBERG,
            kafka_config=kafka_config,
        ) as sdk:
            assert sdk is not None

        # Both close() should be attempted despite first one failing
        mock_data_producer.close.assert_called_once()
        mock_metadata_producer.close.assert_called_once()