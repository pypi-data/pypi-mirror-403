"""SDK for Horizon Data Core operations."""
# Do not lint for exception strings being assigned to variables first
# ruff: noqa: EM101
# ruff: noqa: EM102
# Do not lint for logger f-strings
# Do not lint for long messages in exceptions
# ruff: noqa: TRY003

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from types import TracebackType
from typing import Any, Literal, overload
from uuid import UUID

from pydantic import BaseModel
from pyiceberg.catalog import Catalog, load_catalog
from sqlalchemy import inspect, select
from sqlalchemy.dialects.postgresql import insert

from horizon_data_core.logging import log_calls

from .base_types import (
    BasePostgresModel,
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
from .iceberg_repository import IcebergRepository
from .kafka_config import KafkaConfig, StorageBackend
from .kafka_producer import KafkaProducer
from .orm_types import (
    BeamgramSpecificationOrm,
    BearingTimeRecordSpecificationOrm,
    DataRowOrm,
    DataStreamOrm,
    EntityBeamgramSpecificationOrm,
    EntityBearingTimeRecordSpecificationOrm,
    EntityOrm,
    HorizonPublicOrm,
    MetadataRowOrm,
    MissionEntityOrm,
    MissionOrm,
    OntologyClassOrm,
    OntologyOrm,
)
from .schema_discovery import FieldIdMap, PartitionSpec, discover_field_ids, discover_partition_spec

logger = logging.getLogger(__name__)

# Phantom type markers for backend variants
type PostgresBackend = Literal["postgres"]
type IcebergBackend = Literal["iceberg"]


class BaseRepository[B: BaseModel](ABC):
    """Base repository for database operations.

    Defines a basic set of operations:
        - insert        Create a new database entry
        - insert_batch  Create several new database entries
        - upsert        Create (or update) a new database entry (if matching entry exists)
        - upsert_batch  Create (or update) several new entries (if matching entry exists)
        - read          Return the entry given its id
        - update        Update an existing entry, error if it does not already exist
        - delete        Remove an existing entry
        - list          Return a list of entries (possibly empty) from a list of filter conditions
    """

    def __init__(self, client: Client) -> None:
        """Initialize the base repository.

        Args:
            client: Database client for operations
        """
        self.client = client

    @abstractmethod
    def insert(self, model: B) -> B:
        """Insert a new record."""

    @abstractmethod
    def insert_batch(self, models: list[B]) -> list[B]:
        """Create a new record batch."""

    @abstractmethod
    def upsert(self, model: B, unique_fields: list[str], merge_fields: list[str]) -> B:
        """Insert a new record or update if it already exists."""

    @abstractmethod
    def upsert_batch(self, models: list[B], unique_fields: list[str], merge_fields: list[str]) -> list[B]:
        """Insert a new record or update if it already exists."""

    @abstractmethod
    def read(self, id: UUID) -> B | None:
        """Read a record by ID."""

    @abstractmethod
    def update(self, model: B) -> B:
        """Update an existing record."""

    @abstractmethod
    def delete(self, id: UUID) -> bool:
        """Delete a record by ID."""

    @abstractmethod
    def list(self, **filters: Any) -> list[B]:  # noqa: ANN401
        """List records with optional filters."""


class PostgresRepository[P: BasePostgresModel, O: HorizonPublicOrm](BaseRepository[P]):
    """Repository for PostgreSQL operations."""

    def __init__(
        self, model_class: type[P], orm_class: type[O], client: Client, organization_id: UUID | None = None
    ) -> None:
        """Initialize the PostgreSQL repository.

        Args:
            client: PostgreSQL client for database operations
            model_class: The model class this repository handles
            organization_id: Organization ID for multi-tenancy (optional)

        Raises:
            ValueError: If no ORM class is found for the model class
        """
        super().__init__(client)
        self.model_class = model_class
        self.organization_id = organization_id
        self.orm_class = orm_class

    def _base_model_to_orm(self, model: P) -> O:
        """Convert BaseModel to SQLAlchemy ORM model."""
        model_dict = model.model_dump(exclude_none=True)
        # Ensure organization_id is set if its part of the model
        if "organization_id" in self.model_class.model_fields:
            model_dict["organization_id"] = self.organization_id
        # Modified datetime is set by trigger on the database side, but has a NOT NULL constraint
        # (abuck) I couldn't figure out how to get around the NOT NULL constraint so we just set it to "now"
        # in the SDK and allow a user to send "None".
        model.modified_datetime = datetime.now(UTC)
        orm = self.orm_class(**model_dict)
        orm.modified_datetime = datetime.now(UTC)
        return orm

    def _orm_to_base_model(self, orm_instance: O) -> P:
        """Convert SQLAlchemy ORM model to BaseModel."""
        mapper = inspect(orm_instance.__class__)
        assert mapper is not None  # inspect will raise an exception rather than returning None
        orm_dict = {column.name: getattr(orm_instance, column.name) for column in mapper.columns}
        return self.model_class(**orm_dict)

    @log_calls(logger, level=logging.DEBUG)
    def insert(self, model: P) -> P:
        """Insert a new record in PostgreSQL.

        Args:
            model: The model instance to create

        Returns:
            The inserted model instance with updated fields (e.g., generated ID)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        with self.client.session() as session:
            # Convert all models to ORM instances
            orm_instance = self._base_model_to_orm(model)
            session.add(orm_instance)
            session.commit()
            # Convert back to models
            return self._orm_to_base_model(orm_instance)

    def insert_batch(self, models: list[P]) -> list[P]:
        """Create a new record batch in PostgreSQL.

        Args:
            models: List of model instances to create

        Returns:
            List of created model instances with updated fields or empty list if input is empty

        Raises:
            SQLAlchemyError: If database operation fails
        """
        # Early return for empty input
        if not models:
            logger.warning("Empty input provided to upsert_batch. No action taken.")
            return []

        with self.client.session() as session:
            # Convert all models to ORM instances
            orm_instances = [self._base_model_to_orm(m) for m in models]
            session.add_all(orm_instances)
            session.commit()
            # Convert back to models
            return [self._orm_to_base_model(orm) for orm in orm_instances]

    def upsert(
        self,
        model: P,
        unique_fields: list[str] | None = None,  # Natural key columns
        merge_fields: list[str] | None = None,  # Columns to update on conflict
    ) -> P:
        """
        Upsert using PostgreSQL's ON CONFLICT.

        Args:
            model: The model to upsert
            unique_fields: Columns that define uniqueness (e.g., ['name', 'mission_id'])
            merge_fields: Columns to update on conflict (None = all except conflict_columns)

        Returns:
            The created or updated model instance

        Raises:
            SQLAlchemyError: If database operation fails
        """
        with self.client.session() as session:
            orm_instance = self._base_model_to_orm(model)
            orm_class = self.orm_class

            # Get all columns
            inspector = inspect(orm_class)
            assert inspector is not None  # inspect will raise an exception rather than returning None
            table_columns = inspector.columns
            all_columns = table_columns.keys()

            # Default: use primary key as conflict column
            if unique_fields is None:
                unique_fields = [c.key for c in table_columns if c.primary_key]

            # Default: update all columns except conflict columns
            if merge_fields is None:
                merge_fields = [c for c in all_columns if c not in unique_fields]

            # Build values dict
            values = {c: getattr(orm_instance, c, None) for c in all_columns}

            # Build statement
            insert_stmt = insert(orm_class).values(**values)
            stmt = insert_stmt.on_conflict_do_update(
                index_elements=unique_fields, set_={col: getattr(insert_stmt.excluded, col) for col in merge_fields}
            ).returning(orm_class)

            result = session.execute(stmt)
            merged_instance = result.scalar_one()

            session.commit()
            session.refresh(merged_instance)
            return self._orm_to_base_model(merged_instance)

    def upsert_batch(
        self,
        models: list[P],
        unique_fields: list[str] | None = None,
        merge_fields: list[str] | None = None,
    ) -> list[P]:
        """
        Batch upsert using PostgreSQL's ON CONFLICT.

        Args:
            models: List of models to upsert
            unique_fields: Columns that define uniqueness
            merge_fields: Columns to update on conflict
        """
        # Early return for empty input
        if not models:
            logger.warning("Empty input provided to upsert_batch. No action taken.")
            return []

        with self.client.session() as session:
            # Convert all models to ORM instances
            orm_instances = [self._base_model_to_orm(m) for m in models]
            orm_class = self.orm_class

            # Get all columns
            inspector = inspect(orm_class)
            assert inspector is not None  # inspect will raise an exception rather than returning None
            table_columns = inspector.columns
            all_columns = table_columns.keys()

            # Default: use primary key as conflict column
            if unique_fields is None:
                unique_fields = [c.key for c in table_columns if c.primary_key]

            if merge_fields is None:
                merge_fields = [c for c in all_columns if c not in unique_fields]

            # Build list of value dicts
            values_list = [{col: getattr(orm, col, None) for col in all_columns} for orm in orm_instances]

            # Build INSERT statement with multiple rows
            insert_stmt = insert(orm_class).values(values_list)
            stmt = insert_stmt.on_conflict_do_update(
                index_elements=unique_fields, set_={col: getattr(insert_stmt.excluded, col) for col in merge_fields}
            ).returning(orm_class)

            # Execute and get all results
            result = session.execute(stmt)
            merged_instances = result.scalars().all()

            session.commit()

            # Convert back to models
            return [self._orm_to_base_model(orm) for orm in merged_instances]

    def read(self, id: UUID) -> P | None:
        """Read a record by ID from PostgreSQL.

        Args:
            id: The UUID of the record to read

        Returns:
            The model instance if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        with self.client.session() as session:
            orm_instance = session.get(self.orm_class, id)
            if orm_instance:
                return self._orm_to_base_model(orm_instance)
            return None

    def update(self, model: P) -> P:
        """Update an existing record in PostgreSQL.

        Args:
            model: The model instance with updated fields

        Returns:
            The updated model instance

        Raises:
            ValueError: If record with the given ID is not found
            SQLAlchemyError: If database operation fails
        """
        with self.client.session() as session:
            orm_instance = session.get(self.orm_class, model.id)
            if not orm_instance:
                raise ValueError(f"Record with ID {model.id} not found")

            # Update fields
            model_dict = model.model_dump(exclude_none=True)
            for key, value in model_dict.items():
                if hasattr(orm_instance, key):
                    setattr(orm_instance, key, value)

            session.commit()
            session.refresh(orm_instance)
            return self._orm_to_base_model(orm_instance)

    def delete(self, id: UUID) -> bool:
        """Delete a record by ID from PostgreSQL.

        Args:
            id: The UUID of the record to delete

        Returns:
            True if the record was deleted, False if it didn't exist

        Raises:
            SQLAlchemyError: If database operation fails
        """
        with self.client.session() as session:
            orm_instance = session.get(self.orm_class, id)
            if orm_instance:
                session.delete(orm_instance)
                session.commit()
                return True
            return False

    def list(self, **filters: dict[str, Any]) -> list[P]:
        """List records with optional filters from PostgreSQL.

        Args:
            **filters: Keyword arguments where keys are field names and values are filter values

        Returns:
            List of model instances matching the filters

        Raises:
            SQLAlchemyError: If database operation fails
        """
        with self.client.session() as session:
            query = select(self.orm_class)

            # Apply filters
            for key, value in filters.items():
                if hasattr(self.orm_class, key):
                    query = query.where(getattr(self.orm_class, key) == value)

            orm_instances = session.execute(query).scalars().all()
            return [self._orm_to_base_model(instance) for instance in orm_instances]


class HorizonSDK[BackendType: (PostgresBackend, IcebergBackend)]:
    """Main SDK class for Horizon Data Core operations.

    Generic over BackendType to provide type-safe repository access based on storage backend.
    """

    # Repository attributes typed based on backend
    data_rows: PostgresRepository[DataRow, DataRowOrm] | IcebergRepository[DataRow]
    metadata_rows: PostgresRepository[MetadataRow, MetadataRowOrm] | IcebergRepository[MetadataRow]

    # Overloads to ensure proper typing based on storage_backend
    @overload
    def __init__(
        self: "HorizonSDK[Literal['postgres']]",
        postgres_client: Client,
        catalog_properties: dict[str, str | None],
        organization_id: UUID | None = None,
        iceberg_batch_size: int = 16,
        max_retries: int = 10,
        storage_backend: Literal[StorageBackend.POSTGRES] = StorageBackend.POSTGRES,
        kafka_config: None = None,
    ) -> None:
        pass

    @overload
    def __init__(
        self: "HorizonSDK[Literal['iceberg']]",
        postgres_client: Client,
        catalog_properties: dict[str, str | None],
        organization_id: UUID | None = None,
        iceberg_batch_size: int = 16,
        max_retries: int = 10,
        *,
        storage_backend: Literal[StorageBackend.ICEBERG],
        kafka_config: KafkaConfig,
    ) -> None:
        pass

    def __init__(
        self,
        postgres_client: Client,
        # Iceberg repositories were deprecated after version 0.3.6. This will be removed in version 0.5.0
        catalog_properties: dict[str, str | None],  # noqa: ARG002
        organization_id: UUID | None = None,
        # Iceberg repositories were deprecated after version 0.3.6. This will be removed in version 0.5.0
        iceberg_batch_size: int = 16,  # noqa: ARG002
        # Iceberg repositories were deprecated after version 0.3.6. This will be removed in version 0.5.0
        max_retries: int = 10,  # noqa: ARG002
        # Storage backend configuration for data_row and metadata_row tables
        storage_backend: StorageBackend = StorageBackend.POSTGRES,
        kafka_config: KafkaConfig | None = None,
    ) -> None:
        """Initialize the Horizon SDK.

        Args:
            postgres_client: PostgreSQL client for database operations
            catalog_properties: (DEPRECATED) Properties for the Iceberg catalog
            organization_id: Organization ID for multi-tenancy (optional)
            iceberg_batch_size: (DEPRECATED) Batch size for Iceberg operations (default: 16)
            max_retries: (DEPRECATED) Maximum retry attempts for failed operations (default: 10)
            storage_backend: Storage backend for data_row/metadata_row (postgres or iceberg)
            kafka_config: Kafka configuration (required if storage_backend=ICEBERG)

        Raises:
            ValueError: If storage_backend is ICEBERG but kafka_config is not provided
        """
        self.catalog_properties: dict[str, str | None] = {}
        self.postgres_client = postgres_client
        self.organization_id = organization_id
        self.storage_backend = storage_backend

        # Initialize repositories for PostgreSQL metadata models
        self.entities = PostgresRepository(Entity, EntityOrm, postgres_client, organization_id)
        self.data_streams = PostgresRepository(DataStream, DataStreamOrm, postgres_client, organization_id)
        self.missions = PostgresRepository(Mission, MissionOrm, postgres_client, organization_id)
        self.mission_entities = PostgresRepository(MissionEntity, MissionEntityOrm, postgres_client, organization_id)
        self.ontologies = PostgresRepository(Ontology, OntologyOrm, postgres_client, organization_id)
        self.ontology_classes = PostgresRepository(OntologyClass, OntologyClassOrm, postgres_client, organization_id)
        self.beamgram_specifications = PostgresRepository(
            BeamgramSpecification, BeamgramSpecificationOrm, postgres_client, organization_id
        )
        self.entity_beamgram_specifications = PostgresRepository(
            EntityBeamgramSpecification, EntityBeamgramSpecificationOrm, postgres_client, organization_id
        )
        self.bearing_time_record_specifications: PostgresRepository[
            BearingTimeRecordSpecification, BearingTimeRecordSpecificationOrm
        ] = PostgresRepository(
            BearingTimeRecordSpecification, BearingTimeRecordSpecificationOrm, postgres_client, organization_id
        )
        self.entity_bearing_time_record_specifications = PostgresRepository(
            EntityBearingTimeRecordSpecification,
            EntityBearingTimeRecordSpecificationOrm,
            postgres_client,
            organization_id,
        )

        # Initialize data_row and metadata_row repositories (polymorphic based on storage_backend)
        if storage_backend == StorageBackend.ICEBERG:
            if kafka_config is None:
                raise ValueError("kafka_config is required when storage_backend=ICEBERG")

            # Discover field IDs from Iceberg catalog at init time
            # Field IDs are immutable once assigned, so this can be cached forever
            catalog_props: dict[str, str] = {}
            if kafka_config.catalog_warehouse is not None:
                catalog_props["warehouse"] = kafka_config.catalog_warehouse

            self._data_row_field_ids: FieldIdMap = discover_field_ids(
                kafka_config.catalog_uri,
                kafka_config.data_row_table,
                **catalog_props,
            )
            self._metadata_row_field_ids: FieldIdMap = discover_field_ids(
                kafka_config.catalog_uri,
                kafka_config.metadata_row_table,
                **catalog_props,
            )

            # Discover partition specs for computing Kafka partition keys
            self._data_row_partition_spec: PartitionSpec = discover_partition_spec(
                kafka_config.catalog_uri,
                kafka_config.data_row_table,
                **catalog_props,
            )
            self._metadata_row_partition_spec: PartitionSpec = discover_partition_spec(
                kafka_config.catalog_uri,
                kafka_config.metadata_row_table,
                **catalog_props,
            )

            # Validate SDK models have all required fields in catalog
            # This fails fast if SDK has fields not in the Iceberg table
            data_row_fields = {
                "data_stream_id",
                "datetime",
                "vector",
                "data_type",
                "track_id",
                "vector_start_bound",
                "vector_end_bound",
                "created_datetime",
            }
            metadata_row_fields = {
                "data_stream_id",
                "datetime",
                "latitude",
                "longitude",
                "altitude",
                "speed",
                "heading",
                "pitch",
                "roll",
                "speed_over_ground",
                "created_datetime",
            }
            self._data_row_field_ids.validate_columns(data_row_fields)
            self._metadata_row_field_ids.validate_columns(metadata_row_fields)

            # Create separate producers for each topic to ensure proper partitioning
            producer_config = kafka_config.to_confluent_config()
            bootstrap_servers = str(producer_config.pop("bootstrap.servers"))

            data_row_producer = KafkaProducer(
                bootstrap_servers,
                kafka_config.data_row_topic,
                **producer_config,
            )
            metadata_row_producer = KafkaProducer(
                bootstrap_servers,
                kafka_config.metadata_row_topic,
                **producer_config,
            )

            self.data_rows = IcebergRepository[DataRow](
                data_row_producer, self._data_row_field_ids, self._data_row_partition_spec
            )
            self.metadata_rows = IcebergRepository[MetadataRow](
                metadata_row_producer, self._metadata_row_field_ids, self._metadata_row_partition_spec
            )
            logger.info("Initialized SDK with Iceberg storage backend (eventual consistency)")
        else:
            self.data_rows = PostgresRepository(DataRow, DataRowOrm, postgres_client, organization_id)
            self.metadata_rows = PostgresRepository(MetadataRow, MetadataRowOrm, postgres_client, organization_id)
            logger.info("Initialized SDK with Postgres storage backend")

    def __enter__(self) -> "HorizonSDK":
        """Enter context manager - returns self for use in 'with' statement."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager - flush and close Kafka producers if using Iceberg backend.

        Ensures all queued messages are delivered before context exits. This prevents
        message loss when using the SDK in a context manager.

        Args:
            exc_type: Exception type if an exception occurred, else None
            exc_val: Exception instance if an exception occurred, else None
            exc_tb: Traceback object if an exception occurred, else None

        Note:
            Only performs cleanup for Iceberg backend. Postgres backend requires no cleanup.
            Exceptions during cleanup are logged but not suppressed.
        """
        # Only cleanup if using Iceberg backend
        if isinstance(self.data_rows, IcebergRepository):
            try:
                self.data_rows.producer.close()
            except Exception:
                logger.exception("Failed to close data_rows producer")

        if isinstance(self.metadata_rows, IcebergRepository):
            try:
                self.metadata_rows.producer.close()
            except Exception:
                logger.exception("Failed to close metadata_rows producer")

    def refresh_iceberg_catalog(self) -> Catalog:
        """Refresh the Iceberg catalog.

        DEPRECATED after v0.3.6
        """
        self.iceberg_catalog = load_catalog("rest", **self.catalog_properties)
        return self.iceberg_catalog

    def tick(self) -> None:
        """Tick the Iceberg repository.

        DEPRECATED after version 0.3.6.
        """
        return

    # Entity-BeamgramSpecification operations
    def create_entity_beamgram_specification(
        self, entity_beamgram_specification: EntityBeamgramSpecification
    ) -> EntityBeamgramSpecification:
        """Create a new entity-beamgram specification relationship."""
        return self.entity_beamgram_specifications.insert(entity_beamgram_specification)

    def list_entity_beamgram_specifications(self, **filters: Any) -> list[EntityBeamgramSpecification]:  # noqa: ANN401
        """List entity-beamgram specification relationships with optional filters."""
        return self.entity_beamgram_specifications.list(**filters)

    # Entity-BearingTimeRecordSpecification operations
    def create_entity_bearing_time_record_specification(
        self, entity_bearing_time_record_specification: EntityBearingTimeRecordSpecification
    ) -> EntityBearingTimeRecordSpecification:
        """Create a new entity-btr specification relationship."""
        return self.entity_bearing_time_record_specifications.insert(entity_bearing_time_record_specification)

    def list_entity_bearing_time_record_specifications(
        self,
        **filters: Any,  # noqa: ANN401
    ) -> list[EntityBearingTimeRecordSpecification]:
        """List entity-btr specification relationships with optional filters."""
        return self.entity_bearing_time_record_specifications.list(**filters)

    # PostgreSQL operations
    def create_entity(self, entity: Entity) -> Entity:
        """Create a new entity.

        Args:
            entity: The entity instance to create

        Returns:
            The created entity with updated fields (e.g., generated ID)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        logger.debug(
            "SDK: Creating entity",
            extra={"entity": entity},
        )
        return self.entities.upsert(entity)

    def create_or_update_entity(self, entity: Entity) -> Entity:
        """Create a new entity or update if it already exists.

        Uses custom datetime logic for start_datetime and end_datetime fields:
        - Updates start_datetime if new value is earlier than existing
        - Updates end_datetime if new value is later than existing

        Args:
            entity: The entity instance to create or update

        Returns:
            The created or updated entity

        Raises:
            SQLAlchemyError: If database operation fails
        """
        logger.debug(
            "SDK: Creating or updating entity",
            extra={"entity": entity},
        )

        # Custom logic for start_datetime and end_datetime fields:
        # - Updates start_datetime if new value is earlier than existing
        # - Keep start_datetime if new value is None and existing value is not None
        # - Updates end_datetime if new value is later than existing
        # - Keep end_datetime if new value is None and existing value is not None
        if entity.id is not None:
            existing_entity = self.entities.read(entity.id)
            if existing_entity is not None:
                updated_entity = entity

                # Keep start_datetime if both values are set and new value is later than existing
                # Keep start_datetime if new value is None and existing value is not None
                if (
                    updated_entity.start_datetime is not None
                    and existing_entity.start_datetime is not None
                    and updated_entity.start_datetime > existing_entity.start_datetime
                ) or (updated_entity.start_datetime is None and existing_entity.start_datetime is not None):
                    updated_entity.start_datetime = existing_entity.start_datetime

                # Keep end_datetime if both values are set and new value is later than existing
                # Keep end_datetime if new value is None and existing value is not None
                if (
                    updated_entity.end_datetime is not None
                    and existing_entity.end_datetime is not None
                    and updated_entity.end_datetime < existing_entity.end_datetime
                ) or (updated_entity.end_datetime is None and existing_entity.end_datetime is not None):
                    updated_entity.end_datetime = existing_entity.end_datetime

                return self.entities.upsert(updated_entity)
        # If no existing entity or no ID, do regular upsert
        return self.entities.upsert(entity)

    def read_entity(self, id: UUID) -> Entity | None:
        """Read an entity by ID.

        Args:
            id: The UUID of the entity to read

        Returns:
            The entity if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.entities.read(id)

    def update_entity(self, entity: Entity) -> Entity:
        """Update an existing entity.

        Args:
            entity: The entity instance with updated fields

        Returns:
            The updated entity

        Raises:
            ValueError: If entity with the given ID is not found
            SQLAlchemyError: If database operation fails
        """
        return self.entities.update(entity)

    def delete_entity(self, id: UUID) -> bool:
        """Delete an entity by ID.

        Args:
            id: The UUID of the entity to delete

        Returns:
            True if the entity was deleted, False if it didn't exist

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.entities.delete(id)

    def list_entities(self, **filters: Any) -> list[Entity]:  # noqa: ANN401
        """List entities with optional filters.

        Args:
            **filters: Keyword arguments where keys are field names and values are filter values

        Returns:
            List of entities matching the filters

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.entities.list(**filters)

    def create_data_stream(self, data_stream: DataStream) -> DataStream:
        """Create a new data stream.

        Args:
            data_stream: The data stream instance to create

        Returns:
            The created data stream with updated fields (e.g., generated ID)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.data_streams.upsert(data_stream)

    def read_data_stream(self, id: UUID) -> DataStream | None:
        """Read a data stream by ID.

        Args:
            id: The UUID of the data stream to read

        Returns:
            The data stream if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.data_streams.read(id)

    def update_data_stream(self, data_stream: DataStream) -> DataStream:
        """Update an existing data stream.

        Args:
            data_stream: The data stream instance with updated fields

        Returns:
            The updated data stream

        Raises:
            ValueError: If data stream with the given ID is not found
            SQLAlchemyError: If database operation fails
        """
        return self.data_streams.upsert(data_stream)

    def delete_data_stream(self, id: UUID) -> bool:
        """Delete a data stream by ID.

        Args:
            id: The UUID of the data stream to delete

        Returns:
            True if the data stream was deleted, False if it didn't exist

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.data_streams.delete(id)

    def list_data_streams(self, **filters: Any) -> list[DataStream]:  # noqa: ANN401
        """List data streams with optional filters.

        Args:
            **filters: Keyword arguments where keys are field names and values are filter values

        Returns:
            List of data streams matching the filters

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.data_streams.list(**filters)

    def create_mission(self, mission: Mission) -> Mission:
        """Create a new mission.

        Args:
            mission: The mission instance to create

        Returns:
            The created mission with updated fields (e.g., generated ID)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.missions.insert(mission)

    def read_mission(self, id: UUID) -> Mission | None:
        """Read a mission by ID.

        Args:
            id: The UUID of the mission to read

        Returns:
            The mission if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.missions.read(id)

    def update_mission(self, mission: Mission) -> Mission:
        """Update an existing mission.

        Args:
            mission: The mission instance with updated fields

        Returns:
            The updated mission

        Raises:
            ValueError: If mission with the given ID is not found
            SQLAlchemyError: If database operation fails
        """
        return self.missions.update(mission)

    def delete_mission(self, id: UUID) -> bool:
        """Delete a mission by ID.

        Args:
            id: The UUID of the mission to delete

        Returns:
            True if the mission was deleted, False if it didn't exist

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.missions.delete(id)

    def list_missions(self, **filters: Any) -> list[Mission]:  # noqa: ANN401
        """List missions with optional filters.

        Args:
            **filters: Keyword arguments where keys are field names and values are filter values

        Returns:
            List of missions matching the filters

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.missions.list(**filters)

    def create_mission_entity(self, mission_entity: MissionEntity) -> MissionEntity:
        """Create a new mission-entity relationship.

        Args:
            mission_entity: The mission-entity relationship instance to create

        Returns:
            The created mission-entity relationship with updated fields (e.g., generated ID)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.mission_entities.insert(mission_entity)

    def read_mission_entity(self, id: UUID) -> MissionEntity | None:
        """Read a mission-entity relationship by ID.

        Args:
            id: The UUID of the mission-entity relationship to read

        Returns:
            The mission-entity relationship if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.mission_entities.read(id)

    def update_mission_entity(self, mission_entity: MissionEntity) -> MissionEntity:
        """Update an existing mission-entity relationship.

        Args:
            mission_entity: The mission-entity relationship instance with updated fields

        Returns:
            The updated mission-entity relationship

        Raises:
            ValueError: If mission-entity relationship with the given ID is not found
            SQLAlchemyError: If database operation fails
        """
        return self.mission_entities.update(mission_entity)

    def delete_mission_entity(self, id: UUID) -> bool:
        """Delete a mission-entity relationship by ID.

        Args:
            id: The UUID of the mission-entity relationship to delete

        Returns:
            True if the mission-entity relationship was deleted, False if it didn't exist

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.mission_entities.delete(id)

    def list_mission_entities(self, **filters: Any) -> list[MissionEntity]:  # noqa: ANN401
        """List mission-entity relationships with optional filters.

        Args:
            **filters: Keyword arguments where keys are field names and values are filter values

        Returns:
            List of mission-entity relationships matching the filters

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.mission_entities.list(**filters)

    def create_ontology(self, ontology: Ontology) -> Ontology:
        """Create a new ontology.

        Args:
            ontology: The ontology instance to create

        Returns:
            The created ontology with updated fields (e.g., generated ID)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.ontologies.upsert(ontology)

    def read_ontology(self, id: UUID) -> Ontology | None:
        """Read an ontology by ID.

        Args:
            id: The UUID of the ontology to read

        Returns:
            The ontology if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.ontologies.read(id)

    def update_ontology(self, ontology: Ontology) -> Ontology:
        """Update an existing ontology.

        Args:
            ontology: The ontology instance with updated fields

        Returns:
            The updated ontology

        Raises:
            ValueError: If ontology with the given ID is not found
            SQLAlchemyError: If database operation fails
        """
        return self.ontologies.update(ontology)

    def delete_ontology(self, id: UUID) -> bool:
        """Delete an ontology by ID.

        Args:
            id: The UUID of the ontology to delete

        Returns:
            True if the ontology was deleted, False if it didn't exist

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.ontologies.delete(id)

    def list_ontologies(self, **filters: Any) -> list[Ontology]:  # noqa: ANN401
        """List ontologies with optional filters.

        Args:
            **filters: Keyword arguments where keys are field names and values are filter values

        Returns:
            List of ontologies matching the filters

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.ontologies.list(**filters)

    def create_ontology_class(self, ontology_class: OntologyClass) -> OntologyClass:
        """Create a new ontology class.

        Args:
            ontology_class: The ontology class instance to create

        Returns:
            The created ontology class with updated fields (e.g., generated ID)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.ontology_classes.upsert(ontology_class)

    def read_ontology_class(self, id: UUID) -> OntologyClass | None:
        """Read an ontology class by ID.

        Args:
            id: The UUID of the ontology class to read

        Returns:
            The ontology class if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.ontology_classes.read(id)

    def update_ontology_class(self, ontology_class: OntologyClass) -> OntologyClass:
        """Update an existing ontology class.

        Args:
            ontology_class: The ontology class instance with updated fields

        Returns:
            The updated ontology class

        Raises:
            ValueError: If ontology class with the given ID is not found
            SQLAlchemyError: If database operation fails
        """
        return self.ontology_classes.update(ontology_class)

    def delete_ontology_class(self, id: UUID) -> bool:
        """Delete an ontology class by ID.

        Args:
            id: The UUID of the ontology class to delete

        Returns:
            True if the ontology class was deleted, False if it didn't exist

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.ontology_classes.delete(id)

    def list_ontology_classes(self, **filters: Any) -> list[OntologyClass]:  # noqa: ANN401
        """List ontology classes with optional filters.

        Args:
            **filters: Keyword arguments where keys are field names and values are filter values

        Returns:
            List of ontology classes matching the filters

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.ontology_classes.list(**filters)

    # BeamgramSpecification operations
    def create_beamgram_specification(self, beamgram_specification: BeamgramSpecification) -> BeamgramSpecification:
        """Create a new beamgram specification.

        Args:
            beamgram_specification: The beamgram specification instance to create

        Returns:
            The created beamgram specification with updated fields (e.g., generated ID)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.beamgram_specifications.upsert(beamgram_specification)

    def create_or_update_beamgram_specification(
        self, beamgram_specification: BeamgramSpecification
    ) -> BeamgramSpecification:
        """Create a new beamgram specification or update if it already exists.

        Args:
            beamgram_specification: The beamgram specification instance to create or update

        Returns:
            The created or updated beamgram specification

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.beamgram_specifications.upsert(beamgram_specification)

    def read_beamgram_specification(self, id: UUID) -> BeamgramSpecification | None:
        """Read a beamgram specification by ID.

        Args:
            id: The UUID of the beamgram specification to read

        Returns:
            The beamgram specification if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.beamgram_specifications.read(id)

    def update_beamgram_specification(self, beamgram_specification: BeamgramSpecification) -> BeamgramSpecification:
        """Update an existing beamgram specification.

        Args:
            beamgram_specification: The beamgram specification instance with updated fields

        Returns:
            The updated beamgram specification

        Raises:
            ValueError: If beamgram specification with the given ID is not found
            SQLAlchemyError: If database operation fails
        """
        return self.beamgram_specifications.update(beamgram_specification)

    def delete_beamgram_specification(self, id: UUID) -> bool:
        """Delete a beamgram specification by ID.

        Args:
            id: The UUID of the beamgram specification to delete

        Returns:
            True if the beamgram specification was deleted, False if it didn't exist

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.beamgram_specifications.delete(id)

    def list_beamgram_specifications(self, **filters: Any) -> list[BeamgramSpecification]:  # noqa: ANN401
        """List beamgram specifications with optional filters.

        Args:
            **filters: Keyword arguments where keys are field names and values are filter values

        Returns:
            List of beamgram specifications matching the filters

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.beamgram_specifications.list(**filters)

    # BearingTimeRecordSpecification operations
    def create_bearing_time_record_specification(
        self, bearing_time_record_specification: BearingTimeRecordSpecification
    ) -> BearingTimeRecordSpecification:
        """Create a new bearing-time record specification.

        Args:
            bearing_time_record_specification: The bearing-time record specification instance to create

        Returns:
            The created bearing-time record specification with updated fields (e.g., generated ID)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.bearing_time_record_specifications.upsert(bearing_time_record_specification)

    def create_or_update_bearing_time_record_specification(
        self, bearing_time_record_specification: BearingTimeRecordSpecification
    ) -> BearingTimeRecordSpecification:
        """Create a new bearing-time record specification or update if it already exists.

        Args:
            bearing_time_record_specification: The bearing-time record specification instance to create or update

        Returns:
            The created or updated bearing-time record specification

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.bearing_time_record_specifications.upsert(bearing_time_record_specification)

    def read_bearing_time_record_specification(self, id: UUID) -> BearingTimeRecordSpecification | None:
        """Read a bearing-time record specification by ID.

        Args:
            id: The UUID of the bearing-time record specification to read

        Returns:
            The bearing-time record specification if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.bearing_time_record_specifications.read(id)

    def update_bearing_time_record_specification(
        self, bearing_time_record_specification: BearingTimeRecordSpecification
    ) -> BearingTimeRecordSpecification:
        """Update an existing bearing-time record specification.

        Args:
            bearing_time_record_specification: The bearing-time record specification instance with updated fields

        Returns:
            The updated bearing-time record specification

        Raises:
            ValueError: If bearing-time record specification with the given ID is not found
            SQLAlchemyError: If database operation fails
        """
        return self.bearing_time_record_specifications.update(bearing_time_record_specification)

    def delete_bearing_time_record_specification(self, id: UUID) -> bool:
        """Delete a bearing-time record specification by ID.

        Args:
            id: The UUID of the bearing-time record specification to delete

        Returns:
            True if the bearing-time record specification was deleted, False if it didn't exist

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.bearing_time_record_specifications.delete(id)

    def list_bearing_time_record_specifications(self, **filters: Any) -> list[BearingTimeRecordSpecification]:  # noqa: ANN401
        """List bearing-time record specifications with optional filters.

        Args:
            **filters: Keyword arguments where keys are field names and values are filter values

        Returns:
            List of bearing-time record specifications matching the filters

        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self.bearing_time_record_specifications.list(**filters)

    # buffer_name parameter is deprecated and will be removed in v0.5.0
    def create_data_row(self, data_row: DataRow, buffer_name: str | None = None) -> DataRow:  # noqa: ARG002
        """Create a new data row in data_row table.

        Routes to either Postgres or Iceberg (via Kafka) based on storage_backend configuration.

        Args:
            data_row: The data row instance to create
            buffer_name: (DEPRECATED) Optional buffer name for batching writes

        Returns:
            The data row instance (unchanged)

        Raises:
            KafkaException: If Kafka write fails (when using Iceberg backend)
            SQLAlchemyError: If Postgres write fails (when using Postgres backend)
        """
        return self.data_rows.insert(data_row)

    def create_data_row_batch(self, data_rows: list[DataRow], buffer_name: str | None = None) -> list[DataRow]:  # noqa: ARG002
        """Create a new data row batch in data_row table.

        Routes to either Postgres or Iceberg based on storage_backend configuration.

        Args:
            data_rows: The list of data row instances to create
            buffer_name: (DEPRECATED) Optional buffer name for batching writes

        Returns:
            The data row instances (unchanged)

        Raises:
            KafkaException: If Kafka write fails (when using Iceberg backend)
            SQLAlchemyError: If Postgres write fails (when using Postgres backend)

        Note:
            For Iceberg backend: Data is eventually consistent (30-60s visibility latency).
            Batch sizes of 100-1000 records recommended for optimal performance.
        """
        return self.data_rows.insert_batch(data_rows)

    def list_data_rows(self, **filters: Any) -> list[DataRow]:  # noqa: ANN401
        """List data rows with optional filters from Iceberg table.

        Args:
            **filters: Iceberg scan parameters including:

        Returns:
            List of data rows matching the filters

        Raises:
            Exception: If Iceberg scan operation fails
        """
        return self.data_rows.list(**filters)

    # Iceberg operations removed after v0.3.6. buffer_name parameter is deprecated and will be removed in v0.5.0
    def create_metadata_row(self, metadata_row: MetadataRow, buffer_name: str | None = None) -> MetadataRow:  # noqa: ARG002
        """Create a new metadata row in Iceberg table.

        Args:
            metadata_row: The metadata row instance to create
            buffer_name: (DEPRECATED) Optional buffer name for batching writes

        Returns:
            The metadata row instance (unchanged)

        Raises:
            CommitFailedException: If write operation fails after retries
        """
        return self.metadata_rows.insert(metadata_row)

    def list_metadata_rows(self, **filters: Any) -> list[MetadataRow]:  # noqa: ANN401
        """List metadata rows with optional filters from Iceberg table.

        Args:
            **filters: Postgres query values parameters including:

        Returns:
            List of metadata rows matching the filters

        Raises:
            Exception: If Iceberg scan operation fails
        """
        return self.metadata_rows.list(**filters)
