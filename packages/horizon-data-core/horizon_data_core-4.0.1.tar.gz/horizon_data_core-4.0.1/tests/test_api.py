import os
from uuid import uuid4, UUID
from typing import Generator
import pytest
from datetime import datetime
from horizon_data_core.api import (
    create_entity_beamgram_specification,
    create_entity_bearing_time_record_specification,
    get_horizon_sdk,
    initialize_sdk,
    create_beamgram_specification,
    create_bearing_time_record_specification,
    create_entity,
    read_entity,
    update_entity,
    delete_entity,
    list_entities,
    upsert_entity,
    create_data_rows,
    create_data_stream,
    read_data_stream,
    update_data_stream,
    list_data_streams,
    create_mission,
    read_mission,
    update_mission,
    delete_mission,
    list_missions,
    create_mission_entity,
    read_mission_entity,
    update_mission_entity,
    delete_mission_entity,
    list_mission_entities,
)
from horizon_data_core.client import PostgresClient
from horizon_data_core.base_types import Entity, BeamgramSpecification, BearingTimeRecordSpecification, DataRow, DataStream
from sqlalchemy import text
import horizon_data_core.api as api_module
from horizon_data_core.sdk import HorizonSDK
from unittest.mock import Mock, patch


@pytest.fixture(autouse=True)
def reset_sdk() -> Generator[None, None, None]:
    """Reset the global SDK before and after each test."""
    # Reset before test
    api_module._sdk = None
    yield
    # Reset after test
    api_module._sdk = None


@pytest.fixture
def initialized_sdk() -> HorizonSDK:
    """Fixture to initialize SDK with database connection for tests that need it."""
    initialize_sdk(
        client=PostgresClient(
            user=os.environ.get("OWNER_PGUSER", "postgres"),
            password=os.environ.get("OWNER_PGPASSWORD", "password"),
            host=os.environ.get("PGHOST", "localhost"),
            port=int(os.environ.get("PGPORT", 5432)),
            database=os.environ.get("PGDATABASE", "horizon"),
            sslmode="disable",
            channel_binding="prefer",
        ),
        catalog_properties={
            "uri": "http://localhost:8181",
            "warehouse": "file://./iceberg/warehouse",
        },
        organization_id=None,
    )
    return get_horizon_sdk()


@pytest.fixture
def entity_kind_id(initialized_sdk: HorizonSDK) -> UUID:
    """Fixture to create an entity kind for use in entity tests."""
    kind_id = uuid4()
    with initialized_sdk.postgres_client.session() as session:
        session.execute(
            text("INSERT INTO horizon_public.entity_kind (id, name) VALUES (:id, :name)"),
            {"id": kind_id, "name": "Test Entity Kind"}
        )
        session.commit()
    return kind_id


def test_initialize_sdk() -> None:
    """Test that the SDK can be initialized."""
    with pytest.raises(RuntimeError):
        get_horizon_sdk()
    sdk = initialize_sdk(
        client=PostgresClient(
            # Because this is a lazy connection we don't need to use real values.
            user="postgres",
            password="password",
            host="localhost",
            port=5432,
            database="horizon",
        ),
        catalog_properties={
            "uri": "http://localhost:8181",
            "warehouse": "file://./iceberg/warehouse",
        },
        organization_id=None,
    )
    assert sdk is not None
    sdk = get_horizon_sdk()
    assert sdk is not None


def test_create_entity_beamgram_specification(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that the entity beamgram specification can be created."""
    # Create a beamgram specification
    beamgram_spec = create_beamgram_specification(BeamgramSpecification(id=uuid4()))
    beamgram_id = beamgram_spec.id
    assert beamgram_id is not None
    
    # Create an entity with the valid kind_id
    entity = create_entity(Entity(id=uuid4(), kind_id=entity_kind_id, name="Test Entity"))
    entity_id = entity.id
    assert entity_id is not None

    spec = create_entity_beamgram_specification(entity_id, beamgram_id)
    assert spec is not None
    assert spec.entity_id == entity_id
    assert spec.beamgram_specification_id == beamgram_id


def test_create_entity_bearing_time_record_specification(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that the entity bearing time record specification can be created."""
    # Create a bearing time record specification
    btr_spec = create_bearing_time_record_specification(BearingTimeRecordSpecification(id=uuid4()))
    btr_id = btr_spec.id
    assert btr_id is not None
    
    # Create an entity with the valid kind_id
    entity = create_entity(Entity(id=uuid4(), kind_id=entity_kind_id, name="Test Entity"))
    entity_id = entity.id
    assert entity_id is not None

    spec = create_entity_bearing_time_record_specification(entity_id, btr_id)
    assert spec is not None
    assert spec.entity_id == entity_id
    assert spec.bearing_time_record_specification_id == btr_id


# Entity CRUD Tests

def test_create_entity(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that API create_entity calls the SDK create_entity method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.create_entity = Mock()  # type: ignore[method-assign]
        create_entity(Entity(id=uuid4(), kind_id=entity_kind_id, name="Test Entity"))
        initialized_sdk.create_entity.assert_called_once()


def test_read_entity(initialized_sdk: HorizonSDK) -> None:
    """Test that API read_entity calls the SDK read_entity method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.read_entity = Mock()  # type: ignore[method-assign]
        read_entity(uuid4())
        initialized_sdk.read_entity.assert_called_once()


def test_read_entity_not_found(initialized_sdk: HorizonSDK) -> None:
    """Test that reading a non-existent entity returns None."""
    non_existent_id = uuid4()
    result = read_entity(non_existent_id)
    assert result is None


def test_update_entity(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that API update_entity calls the SDK update_entity method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.update_entity = Mock()  # type: ignore[method-assign]
        update_entity(Entity(id=uuid4(), kind_id=entity_kind_id, name="Test"))
        initialized_sdk.update_entity.assert_called_once()


def test_update_entity_not_found(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that updating a non-existent entity raises ValueError."""
    non_existent_entity = Entity(
        id=uuid4(),
        kind_id=entity_kind_id,
        name="Non-existent",
    )
    with pytest.raises(ValueError):
        update_entity(non_existent_entity)


def test_delete_entity(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that API delete_entity calls the SDK delete_entity method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.delete_entity = Mock()  # type: ignore[method-assign]
        delete_entity(uuid4())
        initialized_sdk.delete_entity.assert_called_once()


def test_delete_entity_not_found(initialized_sdk: HorizonSDK) -> None:
    """Test that deleting a non-existent entity returns False."""
    non_existent_id = uuid4()
    result = delete_entity(non_existent_id)
    assert result is False


def test_list_entities(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that API list_entities calls the SDK list_entities method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.list_entities = Mock()  # type: ignore[method-assign]
        list_entities()
        initialized_sdk.list_entities.assert_called_once()


def test_list_entities_with_filters(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that API list_entities calls the SDK list_entities method with filters."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.list_entities = Mock()  # type: ignore[method-assign]
        list_entities(name="Filtered Entity")
        initialized_sdk.list_entities.assert_called_once_with(name="Filtered Entity")


def test_upsert_entity_create(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that API upsert_entity calls the SDK create_or_update_entity method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.create_or_update_entity = Mock()  # type: ignore[method-assign]
        upsert_entity(Entity(id=uuid4(), kind_id=entity_kind_id, name="Upserted Entity"))
        initialized_sdk.create_or_update_entity.assert_called_once()


def test_upsert_entity_update(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that API upsert_entity calls the SDK create_or_update_entity method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.create_or_update_entity = Mock()  # type: ignore[method-assign]
        upsert_entity(Entity(id=uuid4(), kind_id=entity_kind_id, name="Upserted Name"))
        initialized_sdk.create_or_update_entity.assert_called_once()


def test_entity_operations_without_sdk() -> None:
    """Test that entity operations raise RuntimeError when SDK is not initialized."""
    entity_id = uuid4()
    entity = Entity(id=entity_id, kind_id=uuid4(), name="Test")
    
    with pytest.raises(RuntimeError):
        read_entity(entity_id)
    
    with pytest.raises(RuntimeError):
        update_entity(entity)
    
    with pytest.raises(RuntimeError):
        delete_entity(entity_id)
    
    with pytest.raises(RuntimeError):
        list_entities()
    
    with pytest.raises(RuntimeError):
        upsert_entity(entity)


def test_create_data_rows(initialized_sdk: HorizonSDK, entity_kind_id: UUID) -> None:
    """Test that API create_data_rows calls the SDK create_data_row_batch method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.create_data_row_batch = Mock()  # type: ignore[method-assign]
        create_data_rows([Mock()])
        initialized_sdk.create_data_row_batch.assert_called_once()

def test_create_data_stream(initialized_sdk: HorizonSDK) -> None:
    """Test that API create_data_stream calls the SDK create_data_stream method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.create_data_stream = Mock()  # type: ignore[method-assign]
        mock_platform = Mock()
        mock_platform.id = uuid4()
        create_data_stream(mock_platform, "TestDataStream")
        initialized_sdk.create_data_stream.assert_called_once()

def test_read_data_stream(initialized_sdk: HorizonSDK) -> None:
    """Test that API read_data_stream calls the SDK read_data_stream method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.read_data_stream = Mock()  # type: ignore[method-assign]
        read_data_stream(uuid4())
        initialized_sdk.read_data_stream.assert_called_once()

def test_update_data_stream(initialized_sdk: HorizonSDK) -> None:
    """Test that API update_data_stream calls the SDK update_data_stream method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.update_data_stream = Mock()  # type: ignore[method-assign]
        update_data_stream(Mock())
        initialized_sdk.update_data_stream.assert_called_once()

def test_list_data_streams(initialized_sdk: HorizonSDK) -> None:
    """Test that API list_data_streams calls the SDK list_data_streams method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.list_data_streams = Mock()  # type: ignore[method-assign]
        list_data_streams()
        initialized_sdk.list_data_streams.assert_called_once()

def test_create_mission(initialized_sdk: HorizonSDK) -> None:
    """Test that API create_mission calls the SDK create_mission method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.create_mission = Mock()  # type: ignore[method-assign]
        create_mission(Mock())
        initialized_sdk.create_mission.assert_called_once()

def test_read_mission(initialized_sdk: HorizonSDK) -> None:
    """Test that API read_mission calls the SDK read_mission method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.read_mission = Mock()  # type: ignore[method-assign]
        read_mission(uuid4())
        initialized_sdk.read_mission.assert_called_once()

def test_update_mission(initialized_sdk: HorizonSDK) -> None:
    """Test that API update_mission calls the SDK update_mission method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.update_mission = Mock()  # type: ignore[method-assign]
        update_mission(Mock())
        initialized_sdk.update_mission.assert_called_once()

def test_delete_mission(initialized_sdk: HorizonSDK) -> None:
    """Test that API delete_mission calls the SDK delete_mission method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.delete_mission = Mock()  # type: ignore[method-assign]
        delete_mission(uuid4())
        initialized_sdk.delete_mission.assert_called_once()

def test_list_missions(initialized_sdk: HorizonSDK) -> None:
    """Test that API list_missions calls the SDK list_missions method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.list_missions = Mock()  # type: ignore[method-assign]
        list_missions()
        initialized_sdk.list_missions.assert_called_once()

def test_create_mission_entity(initialized_sdk: HorizonSDK) -> None:
    """Test that API create_mission_entity calls the SDK create_mission_entity method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.create_mission_entity = Mock()  # type: ignore[method-assign]
        create_mission_entity(Mock())
        initialized_sdk.create_mission_entity.assert_called_once()

def test_read_mission_entity(initialized_sdk: HorizonSDK) -> None:
    """Test that API read_mission_entity calls the SDK read_mission_entity method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.read_mission_entity = Mock()  # type: ignore[method-assign]
        read_mission_entity(uuid4())
        initialized_sdk.read_mission_entity.assert_called_once()

def test_update_mission_entity(initialized_sdk: HorizonSDK) -> None:
    """Test that API update_mission_entity calls the SDK update_mission_entity method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.update_mission_entity = Mock()  # type: ignore[method-assign]
        update_mission_entity(Mock())
        initialized_sdk.update_mission_entity.assert_called_once()

def test_delete_mission_entity(initialized_sdk: HorizonSDK) -> None:
    """Test that API delete_mission_entity calls the SDK delete_mission_entity method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.delete_mission_entity = Mock()  # type: ignore[method-assign]
        delete_mission_entity(uuid4())
        initialized_sdk.delete_mission_entity.assert_called_once()

def test_list_mission_entities(initialized_sdk: HorizonSDK) -> None:
    """Test that API list_mission_entities calls the SDK list_mission_entities method."""
    with patch('horizon_data_core.api.get_horizon_sdk', return_value=initialized_sdk):
        initialized_sdk.list_mission_entities = Mock()  # type: ignore[method-assign]
        list_mission_entities()
        initialized_sdk.list_mission_entities.assert_called_once()
