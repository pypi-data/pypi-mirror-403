"""Public API for Horizon Data Core operations."""

import logging
from typing import Any
from uuid import UUID, uuid4

from .base_types import (
    BeamgramSpecification,
    BearingTimeRecordSpecification,
    DataRow,
    DataStream,
    Entity,
    EntityBeamgramSpecification,
    EntityBearingTimeRecordSpecification,
    MetadataRow,
    Mission,
    MissionEntity,
    Ontology,
    OntologyClass,
)
from .client import Client
from .sdk import HorizonSDK

# API scoped singleton SDK instance - will be initialized by users
_sdk: HorizonSDK | None = None


logger = logging.getLogger(__name__)


def initialize_sdk(
    client: Client,
    catalog_properties: dict[str, str | None],
    organization_id: UUID | None,
    iceberg_batch_size: int = 32,
    max_retries: int = 10,
) -> HorizonSDK:
    """Initialize the global SDK instance.

    This function sets up the global SDK instance that is used by all API functions.
    Must be called before using any other API functions.

    Args:
        client: PostgreSQL client for database operations
        iceberg_catalog: Iceberg catalog for table operations
        organization_id: Organization ID for multi-tenancy (can be None)
        iceberg_batch_size: Batch size for Iceberg operations (default: 32)
        max_retries: Maximum retry attempts for failed operations (default: 10)

    Raises:
        RuntimeError: If SDK is already initialized
    """
    # TODO(abuck): Refactor thehis to a singleton class instance pattern # noqa: FIX002
    # https://github.com/spear-ai/horizon/issues/998
    #  Alternatively, we could do away with the global SDK and just let users construct their own SDK instance
    #  and pass it around as needed.
    global _sdk  # noqa: PLW0603
    _sdk = HorizonSDK(client, catalog_properties, organization_id, iceberg_batch_size, max_retries)
    return _sdk


def get_horizon_sdk() -> HorizonSDK:
    """Get the global SDK instance."""
    return _ensure_sdk_initialized()


def _ensure_sdk_initialized() -> HorizonSDK:
    """Ensure the SDK is initialized."""
    if _sdk is None:
        message = "SDK not initialized. Call initialize_sdk() first."
        logger.error(message)
        raise RuntimeError(message)
    return _sdk


def create_entity_beamgram_specification(
    entity_id: UUID, beamgram_specification_id: UUID
) -> EntityBeamgramSpecification:
    """Create a new entity-beamgram specification relationship."""
    entity_beamgram_specification = EntityBeamgramSpecification(
        id=uuid4(), entity_id=entity_id, beamgram_specification_id=beamgram_specification_id
    )
    return _ensure_sdk_initialized().create_entity_beamgram_specification(entity_beamgram_specification)


def create_entity_bearing_time_record_specification(
    entity_id: UUID, bearing_time_record_specification_id: UUID
) -> EntityBearingTimeRecordSpecification:
    """Create a new entity-btr specification relationship."""
    entity_bearing_time_record_specification = EntityBearingTimeRecordSpecification(
        id=uuid4(), entity_id=entity_id, bearing_time_record_specification_id=bearing_time_record_specification_id
    )
    return _ensure_sdk_initialized().create_entity_bearing_time_record_specification(
        entity_bearing_time_record_specification
    )


# Entity operations
def create_entity(entity: Entity) -> Entity:
    """Create a new entity.

    Args:
        entity: The entity instance to create

    Returns:
        The created entity with updated fields (e.g., generated ID)

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    logger.debug(
        "Creating entity",
        extra={"entity": entity},
    )
    return _ensure_sdk_initialized().create_entity(entity)


def upsert_entity(entity: Entity) -> Entity:
    """Create a new entity or update if it already exists.

    Args:
        entity: The entity instance to create or update

    Returns:
        The created or updated entity

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    logger.debug(
        "Creating or updating entity",
        extra={"entity": entity},
    )
    return _ensure_sdk_initialized().create_or_update_entity(entity)


def read_entity(id: UUID) -> Entity | None:
    """Read an entity by ID.

    Args:
        id: The UUID of the entity to read

    Returns:
        The entity if found, None otherwise

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().read_entity(id)


def update_entity(entity: Entity) -> Entity:
    """Update an existing entity.

    Args:
        entity: The entity instance with updated fields

    Returns:
        The updated entity

    Raises:
        RuntimeError: If SDK is not initialized
        ValueError: If entity with the given ID is not found
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().update_entity(entity)


def delete_entity(id: UUID) -> bool:
    """Delete an entity by ID.

    Args:
        id: The UUID of the entity to delete

    Returns:
        True if the entity was deleted, False if it didn't exist

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().delete_entity(id)


def list_entities(**filters: Any) -> list[Entity]:  # noqa: ANN401
    """List entities with optional filters.

    Args:
        **filters: Keyword arguments where keys are field names and values are filter values

    Returns:
        List of entities matching the filters

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().list_entities(**filters)


# DataStream operations
def create_data_stream(platform: Entity, data_stream_name: str) -> DataStream:
    """Create a new data stream, or return the existing matching one.

    Args:
        platform: The platform this data_stream belongs to
        data_stream_name: The name of the stream or sensor

    Returns:
        The created data stream with updated fields (e.g., generated ID)

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    data_stream = DataStream.from_platform_and_name(platform, data_stream_name)
    return _ensure_sdk_initialized().create_data_stream(data_stream)


def read_data_stream(id: UUID) -> DataStream | None:
    """Read a data stream by ID.

    Args:
        id: The UUID of the data stream to read

    Returns:
        The data stream if found, None otherwise

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().read_data_stream(id)


def update_data_stream(data_stream: DataStream) -> DataStream:
    """Update an existing data stream.

    Args:
        data_stream: The data stream instance with updated fields

    Returns:
        The updated data stream

    Raises:
        RuntimeError: If SDK is not initialized
        ValueError: If data stream with the given ID is not found
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().update_data_stream(data_stream)


def delete_data_stream(id: UUID) -> bool:
    """Delete a data stream by ID.

    Args:
        id: The UUID of the data stream to delete

    Returns:
        True if the data stream was deleted, False if it didn't exist

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().delete_data_stream(id)


def list_data_streams(**filters: Any) -> list[DataStream]:  # noqa: ANN401
    """List data streams with optional filters.

    Args:
        **filters: Keyword arguments where keys are field names and values are filter values

    Returns:
        List of data streams matching the filters

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().list_data_streams(**filters)


# Mission operations
def create_mission(mission: Mission) -> Mission:
    """Create a new mission.

    Args:
        mission: The mission instance to create

    Returns:
        The created mission with updated fields (e.g., generated ID)

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().create_mission(mission)


def read_mission(id: UUID) -> Mission | None:
    """Read a mission by ID.

    Args:
        id: The UUID of the mission to read

    Returns:
        The mission if found, None otherwise

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().read_mission(id)


def update_mission(mission: Mission) -> Mission:
    """Update an existing mission.

    Args:
        mission: The mission instance with updated fields

    Returns:
        The updated mission

    Raises:
        RuntimeError: If SDK is not initialized
        ValueError: If mission with the given ID is not found
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().update_mission(mission)


def delete_mission(id: UUID) -> bool:
    """Delete a mission by ID.

    Args:
        id: The UUID of the mission to delete

    Returns:
        True if the mission was deleted, False if it didn't exist

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().delete_mission(id)


def list_missions(**filters: Any) -> list[Mission]:  # noqa: ANN401
    """List missions with optional filters.

    Args:
        **filters: Keyword arguments where keys are field names and values are filter values

    Returns:
        List of missions matching the filters

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().list_missions(**filters)


# MissionEntity operations
def create_mission_entity(mission_entity: MissionEntity) -> MissionEntity:
    """Create a new mission-entity relationship.

    Args:
        mission_entity: The mission-entity relationship instance to create

    Returns:
        The created mission-entity relationship with updated fields (e.g., generated ID)

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().create_mission_entity(mission_entity)


def read_mission_entity(id: UUID) -> MissionEntity | None:
    """Read a mission-entity relationship by ID.

    Args:
        id: The UUID of the mission-entity relationship to read

    Returns:
        The mission-entity relationship if found, None otherwise

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().read_mission_entity(id)


def update_mission_entity(mission_entity: MissionEntity) -> MissionEntity:
    """Update an existing mission-entity relationship.

    Args:
        mission_entity: The mission-entity relationship instance with updated fields

    Returns:
        The updated mission-entity relationship

    Raises:
        RuntimeError: If SDK is not initialized
        ValueError: If mission-entity relationship with the given ID is not found
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().update_mission_entity(mission_entity)


def delete_mission_entity(id: UUID) -> bool:
    """Delete a mission-entity relationship by ID.

    Args:
        id: The UUID of the mission-entity relationship to delete

    Returns:
        True if the mission-entity relationship was deleted, False if it didn't exist

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().delete_mission_entity(id)


def list_mission_entities(**filters: Any) -> list[MissionEntity]:  # noqa: ANN401
    """List mission-entity relationships with optional filters.

    Args:
        **filters: Keyword arguments where keys are field names and values are filter values

    Returns:
        List of mission-entity relationships matching the filters

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().list_mission_entities(**filters)


# Ontology operations
def create_ontology(ontology: Ontology) -> Ontology:
    """Create a new ontology.

    Args:
        ontology: The ontology instance to create

    Returns:
        The created ontology with updated fields (e.g., generated ID)

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().create_ontology(ontology)


def read_ontology(id: UUID) -> Ontology | None:
    """Read an ontology by ID.

    Args:
        id: The UUID of the ontology to read

    Returns:
        The ontology if found, None otherwise

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().read_ontology(id)


def update_ontology(ontology: Ontology) -> Ontology:
    """Update an existing ontology.

    Args:
        ontology: The ontology instance with updated fields

    Returns:
        The updated ontology

    Raises:
        RuntimeError: If SDK is not initialized
        ValueError: If ontology with the given ID is not found
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().update_ontology(ontology)


def delete_ontology(id: UUID) -> bool:
    """Delete an ontology by ID.

    Args:
        id: The UUID of the ontology to delete

    Returns:
        True if the ontology was deleted, False if it didn't exist

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().delete_ontology(id)


def list_ontologies(**filters: Any) -> list[Ontology]:  # noqa: ANN401
    """List ontologies with optional filters.

    Args:
        **filters: Keyword arguments where keys are field names and values are filter values

    Returns:
        List of ontologies matching the filters

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().list_ontologies(**filters)


# OntologyClass operations
def create_ontology_class(ontology_class: OntologyClass) -> OntologyClass:
    """Create a new ontology class.

    Args:
        ontology_class: The ontology class instance to create

    Returns:
        The created ontology class with updated fields (e.g., generated ID)

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().create_ontology_class(ontology_class)


def read_ontology_class(id: UUID) -> OntologyClass | None:
    """Read an ontology class by ID.

    Args:
        id: The UUID of the ontology class to read

    Returns:
        The ontology class if found, None otherwise

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().read_ontology_class(id)


def update_ontology_class(ontology_class: OntologyClass) -> OntologyClass:
    """Update an existing ontology class.

    Args:
        ontology_class: The ontology class instance with updated fields

    Returns:
        The updated ontology class

    Raises:
        RuntimeError: If SDK is not initialized
        ValueError: If ontology class with the given ID is not found
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().update_ontology_class(ontology_class)


def delete_ontology_class(id: UUID) -> bool:
    """Delete an ontology class by ID.

    Args:
        id: The UUID of the ontology class to delete

    Returns:
        True if the ontology class was deleted, False if it didn't exist

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().delete_ontology_class(id)


def list_ontology_classes(**filters: Any) -> list[OntologyClass]:  # noqa: ANN401
    """List ontology classes with optional filters.

    Args:
        **filters: Keyword arguments where keys are field names and values are filter values

    Returns:
        List of ontology classes matching the filters

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().list_ontology_classes(**filters)


# BeamgramSpecification operations
def create_beamgram_specification(beamgram_specification: BeamgramSpecification) -> BeamgramSpecification:
    """Create a new beamgram specification.

    Args:
        beamgram_specification: The beamgram specification instance to create

    Returns:
        The created beamgram specification with updated fields (e.g., generated ID)

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().create_beamgram_specification(beamgram_specification)


def create_or_update_beamgram_specification(beamgram_specification: BeamgramSpecification) -> BeamgramSpecification:
    """Create a new beamgram specification or update if it already exists.

    Args:
        beamgram_specification: The beamgram specification instance to create or update

    Returns:
        The created or updated beamgram specification

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().create_or_update_beamgram_specification(beamgram_specification)


def read_beamgram_specification(id: UUID) -> BeamgramSpecification | None:
    """Read a beamgram specification by ID.

    Args:
        id: The UUID of the beamgram specification to read

    Returns:
        The beamgram specification if found, None otherwise

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().read_beamgram_specification(id)


def update_beamgram_specification(beamgram_specification: BeamgramSpecification) -> BeamgramSpecification:
    """Update an existing beamgram specification.

    Args:
        beamgram_specification: The beamgram specification instance with updated fields

    Returns:
        The updated beamgram specification

    Raises:
        RuntimeError: If SDK is not initialized
        ValueError: If beamgram specification with the given ID is not found
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().update_beamgram_specification(beamgram_specification)


def delete_beamgram_specification(id: UUID) -> bool:
    """Delete a beamgram specification by ID.

    Args:
        id: The UUID of the beamgram specification to delete

    Returns:
        True if the beamgram specification was deleted, False if it didn't exist

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().delete_beamgram_specification(id)


def list_beamgram_specifications(**filters: Any) -> list[BeamgramSpecification]:  # noqa: ANN401
    """List beamgram specifications with optional filters.

    Args:
        **filters: Keyword arguments where keys are field names and values are filter values

    Returns:
        List of beamgram specifications matching the filters

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().list_beamgram_specifications(**filters)


# BearingTimeRecordSpecification operations
def create_bearing_time_record_specification(
    bearing_time_record_specification: BearingTimeRecordSpecification,
) -> BearingTimeRecordSpecification:
    """Create a new bearing-time record specification.

    Args:
        bearing_time_record_specification: The bearing-time record specification instance to create

    Returns:
        The created bearing-time record specification with updated fields (e.g., generated ID)

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().create_bearing_time_record_specification(bearing_time_record_specification)


def create_or_update_bearing_time_record_specification(
    bearing_time_record_specification: BearingTimeRecordSpecification,
) -> BearingTimeRecordSpecification:
    """Create a new bearing-time record specification or update if it already exists.

    Args:
        bearing_time_record_specification: The bearing-time record specification instance to create or update

    Returns:
        The created or updated bearing-time record specification

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().create_or_update_bearing_time_record_specification(
        bearing_time_record_specification
    )


def read_bearing_time_record_specification(id: UUID) -> BearingTimeRecordSpecification | None:
    """Read a bearing-time record specification by ID.

    Args:
        id: The UUID of the bearing-time record specification to read

    Returns:
        The bearing-time record specification if found, None otherwise

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().read_bearing_time_record_specification(id)


def update_bearing_time_record_specification(
    bearing_time_record_specification: BearingTimeRecordSpecification,
) -> BearingTimeRecordSpecification:
    """Update an existing bearing-time record specification.

    Args:
        bearing_time_record_specification: The bearing-time record specification instance with updated fields

    Returns:
        The updated bearing-time record specification

    Raises:
        RuntimeError: If SDK is not initialized
        ValueError: If bearing-time record specification with the given ID is not found
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().update_bearing_time_record_specification(bearing_time_record_specification)


def delete_bearing_time_record_specification(id: UUID) -> bool:
    """Delete a bearing-time record specification by ID.

    Args:
        id: The UUID of the bearing-time record specification to delete

    Returns:
        True if the bearing-time record specification was deleted, False if it didn't exist

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().delete_bearing_time_record_specification(id)


def list_bearing_time_record_specifications(**filters: Any) -> list[BearingTimeRecordSpecification]:  # noqa: ANN401
    """List bearing-time record specifications with optional filters.

    Args:
        **filters: Keyword arguments where keys are field names and values are filter values

    Returns:
        List of bearing-time record specifications matching the filters

    Raises:
        RuntimeError: If SDK is not initialized
        SQLAlchemyError: If database operation fails
    """
    return _ensure_sdk_initialized().list_bearing_time_record_specifications(**filters)


# Iceberg operations
def create_data_row(data_row: DataRow, buffer_name: str | None = None) -> DataRow:
    """Create a new data row in Iceberg table.

    Args:
        data_row: The data row instance to create
        buffer_name: Optional buffer name for batching writes

    Returns:
        The data row instance (unchanged)

    Raises:
        RuntimeError: If SDK is not initialized
        CommitFailedException: If write operation fails after retries
    """
    return _ensure_sdk_initialized().create_data_row(data_row, buffer_name)


def create_data_rows(data_rows: list[DataRow], buffer_name: str | None = None) -> list[DataRow]:
    """Create a new data rows in Iceberg table.

    Args:
        data_rows: The list of data row instances to create
        buffer_name: Optional buffer name for batching writes

    Returns:
        The list of data row instances (unchanged)
    """
    return _ensure_sdk_initialized().create_data_row_batch(data_rows, buffer_name)


def list_data_rows(**filters: Any) -> list[DataRow]:  # noqa: ANN401
    """List data rows with optional filters from Iceberg table.

    Args:
        **filters: Iceberg scan parameters including:
            - row_filter: str | boolean_expr = True
            - selected_fields: tuple[str] = ("*",)
            - case_sensitive: bool = True
            - snapshot_id: str | None = None
            - options: Properties = {}
            - limit: int | None = None

    Returns:
        List of data rows matching the filters

    Raises:
        RuntimeError: If SDK is not initialized
        Exception: If Iceberg scan operation fails
    """
    return _ensure_sdk_initialized().list_data_rows(**filters)


def create_metadata_row(metadata_row: MetadataRow, buffer_name: str | None = None) -> MetadataRow:
    """Create a new metadata row in Iceberg table.

    Args:
        metadata_row: The metadata row instance to create
        buffer_name: Optional buffer name for batching writes

    Returns:
        The metadata row instance (unchanged)

    Raises:
        RuntimeError: If SDK is not initialized
        CommitFailedException: If write operation fails after retries
    """
    return _ensure_sdk_initialized().create_metadata_row(metadata_row, buffer_name)


def list_metadata_rows(**filters: Any) -> list[MetadataRow]:  # noqa: ANN401
    """List metadata rows with optional filters from Iceberg table.

    Args:
        **filters: Iceberg scan parameters including:
            - row_filter: str | boolean_expr = True
            - selected_fields: tuple[str] = ("*",)
            - case_sensitive: bool = True
            - snapshot_id: str | None = None
            - options: Properties = {}
            - limit: int | None = None

    Returns:
        List of metadata rows matching the filters

    Raises:
        RuntimeError: If SDK is not initialized
        Exception: If Iceberg scan operation fails
    """
    return _ensure_sdk_initialized().list_metadata_rows(**filters)
