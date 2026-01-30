"""ORM types for the Horizon Data Core SDK."""

from collections.abc import Callable
from datetime import datetime as dt
from typing import Any

from sqlalchemy import Column, DateTime, Float, Integer, MetaData, String, Text, Uuid
from sqlalchemy.dialects.postgresql import ARRAY, CITEXT
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from sqlalchemy.types import Interval, UserDefinedType

schema_metadata = MetaData(schema="horizon_public")
HorizonPublicOrmBase = declarative_base(metadata=schema_metadata)


class HorizonPublicOrm(HorizonPublicOrmBase):
    """Abstract Base ORM Class for Horizon."""

    __abstract__ = True
    __table__ = None

    created_datetime: Mapped[dt] = mapped_column(DateTime, nullable=False)  # DB default is now()
    modified_datetime: Mapped[dt] = mapped_column(DateTime, nullable=False)  # DB default is now(), updates onupdate


class PostgreSQLPoint(UserDefinedType):
    """Custom type for PostgreSQL point.

    This serializes (longitude, latitude) pairs into "(lon,lat)" as required by the postgresql "POINT" type.

    The typing for this is incomplete, but that is due to how sqlAlchemy has created the
    UserDefinedType class from which this inherits.

    This type signature comes from SQLAlchemy's UserDefinedType class so we have to just
    ignore the Any type signature and the lint errors it throws for now.
    """

    cache_ok = True

    def get_col_spec(self, **kwargs: Any) -> str:  # noqa: ANN401, ARG002
        """Get the column specification for the point."""
        return "POINT"

    def bind_processor(self, dialect: Any) -> Callable[[tuple[float, float] | None | Any], str | None | Any]:  # noqa: ANN401, ARG002 # pyright: ignore[reportIncompatibleMethodOverride]
        """Bind the value to the database."""

        def process(value: tuple[float, float] | None | Any) -> str | None | Any:  # noqa: ANN401
            if value is None:
                return None
            if isinstance(value, tuple):
                return f"({value[0]},{value[1]})"
            return value

        return process

    def result_processor(self, dialect: Any, coltype: Any) -> Callable[[Any], Any]:  # noqa: ANN401, ARG002 # pyright: ignore[reportIncompatibleMethodOverride]
        """Process the value from the database."""

        def process(value: Any) -> Any:  # noqa: ANN401
            if value is None:
                return None
            if isinstance(value, str):
                # Parse "(x,y)" format
                coords = value.strip("()").split(",")
                return (float(coords[0]), float(coords[1]))
            return value

        return process


class EntityOrm(HorizonPublicOrm):
    """An instance of an entity, used for SQL ORM."""

    __tablename__ = "entity"

    id = Column(Uuid, primary_key=True)
    name = Column(CITEXT)
    kind_id = Column(Uuid)
    free_text = Column(Text)
    position = Column(PostgreSQLPoint)
    start_datetime = Column(DateTime)
    end_datetime = Column(DateTime)
    organization_id = Column(Uuid)

    def __repr__(self) -> str:
        """Return a string representation of the EntityOrm."""
        return (
            f"EntityOrm(id={self.id}, name={self.name}, position={self.position}, "
            f"organization_id={self.organization_id}, created_datetime={self.created_datetime}, "
            f"modified_datetime={self.modified_datetime}, kind_id={self.kind_id}, free_text={self.free_text})"
        )


class DataStreamOrm(HorizonPublicOrm):
    """A data stream of an entity."""

    __tablename__ = "data_stream"

    id = Column(Uuid, primary_key=True)
    entity_id = Column(Uuid)
    organization_id = Column(Uuid)
    name = Column(Text)


class DataRowOrm(HorizonPublicOrm):
    """A row of data in the data_row table.

    This is a timescaledb hypertable and requires slightly special handling.

    There is no id field or primary key as the data is segmented by partition and time.
    We can exclude the "id" field that is inherited from the base class.
    """

    __tablename__ = "data_row"

    data_stream_id = Column(Uuid, primary_key=True)
    datetime = Column(DateTime, primary_key=True)
    created_datetime: Mapped[dt] = mapped_column(DateTime, primary_key=True, default=dt.now)
    vector = Column(ARRAY(Float))
    data_type = Column(String, primary_key=True)
    track_id = Column(Uuid, primary_key=True)
    vector_start_bound = Column(Float)
    vector_end_bound = Column(Float)


class MetadataRowOrm(HorizonPublicOrm):
    """A row of data in the metadata_row table corresponding.

    This is a timescaledb hypertable and requires slightly special handling.

    There is no id field or primary key as the data is segmented by partition and time.
    We can exclude the "id" field that is inherited from the base class.
    """

    __tablename__ = "metadata_row"

    data_stream_id = Column(Uuid, primary_key=True)
    datetime = Column(DateTime, primary_key=True)
    created_datetime: Mapped[dt] = mapped_column(DateTime, primary_key=True, default=dt.now)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    speed = Column(Float)
    heading = Column(Float)
    pitch = Column(Float)
    roll = Column(Float)
    speed_over_ground = Column(Float)


class MissionOrm(HorizonPublicOrm):
    """A group that can group entities around some bounded time or purpose."""

    __tablename__ = "mission"

    id = Column(Uuid, primary_key=True)
    name = Column(CITEXT)
    start_datetime = Column(DateTime)
    end_datetime = Column(DateTime)
    position = Column(PostgreSQLPoint)
    free_text = Column(Text)
    organization_id = Column(Uuid)


class MissionEntityOrm(HorizonPublicOrm):
    """A relationship table that specifies entity association with a mission."""

    __tablename__ = "mission_entity"

    id = Column(Uuid, primary_key=True)
    mission_id = Column(Uuid)
    entity_id = Column(Uuid)
    organization_id = Column(Uuid)


class OntologyOrm(HorizonPublicOrm):
    """An ontology for organizing entities."""

    __tablename__ = "ontology"

    id = Column(Uuid, primary_key=True)
    name = Column(CITEXT)
    description = Column(Text)
    organization_id = Column(Uuid)


class OntologyClassOrm(HorizonPublicOrm):
    """A class within an ontology."""

    __tablename__ = "ontology_class"

    id = Column(Uuid, primary_key=True)
    ontology_id = Column(Uuid)
    parent_id = Column(Uuid)
    name = Column(CITEXT)
    description = Column(Text)
    order = Column(Integer)
    organization_id = Column(Uuid)
    relationship_type = Column(CITEXT)


class BeamgramSpecificationOrm(HorizonPublicOrm):
    """A specification for beamgram data processing."""

    __tablename__ = "beamgram_specification"

    id = Column(Uuid, primary_key=True)
    center_bearing = Column(Float)
    center_bin_width = Column(Float)
    min_frequency = Column(Float)
    max_frequency = Column(Float)
    nfft = Column(Integer)
    organization_id = Column(Uuid)
    elevation = Column(Float)
    update_rate = Column(Interval)
    normalizer = Column(Text)


class BearingTimeRecordSpecificationOrm(HorizonPublicOrm):
    """A specification for bearing-time record data processing."""

    __tablename__ = "bearing_time_record_specification"

    id = Column(Uuid, primary_key=True)
    min_frequency = Column(Float)
    max_frequency = Column(Float)
    nfft = Column(Integer)
    frequency_spacing = Column(Float)
    organization_id = Column(Uuid)
    elevation = Column(Float)
    update_rate = Column(Interval)
    normalizer = Column(Text)


class EntityBeamgramSpecificationOrm(HorizonPublicOrm):
    """A relationship table that specifies entity association with a beamgram specification."""

    __tablename__ = "entity_beamgram_specification"

    id = Column(Uuid, primary_key=True)
    entity_id = Column(Uuid)
    beamgram_specification_id = Column(Uuid)
    organization_id = Column(Uuid)


class EntityBearingTimeRecordSpecificationOrm(HorizonPublicOrm):
    """A relationship table that specifies entity association with a btr specification."""

    __tablename__ = "entity_bearing_time_record_specification"

    id = Column(Uuid, primary_key=True)
    entity_id = Column(Uuid)
    bearing_time_record_specification_id = Column(Uuid)
    organization_id = Column(Uuid)
