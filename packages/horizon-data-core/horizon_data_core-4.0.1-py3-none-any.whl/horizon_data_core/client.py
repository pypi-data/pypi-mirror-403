"""Client for Postgres operations."""

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cached_property
from typing import Protocol

from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


class Client(Protocol):
    """Client protocol for database operations."""

    @property
    def connection_string(self) -> URL:
        """The connection string for the Postgres client."""
        ...

    @cached_property
    def engine(self) -> Engine:
        """The engine for the Postgres client."""
        ...

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Get a session for the Postgres client."""
        ...


@dataclass
class PostgresClient:
    """Client for Postgres operations."""

    user: str
    password: str
    host: str
    port: str | int
    database: str
    dialect: str = "postgresql"
    driver: str = "psycopg2"
    sslmode: str = "require"
    channel_binding: str = "require"

    @property
    def connection_string(self) -> URL:
        """Get the connection string for the Postgres client."""
        return URL.create(
            drivername=f"{self.dialect}+{self.driver}",
            username=self.user,
            password=self.password,
            host=self.host,
            port=int(self.port),
            database=self.database,
            query={
                "sslmode": self.sslmode,
                "channel_binding": self.channel_binding,
            },
        )

    @cached_property
    def engine(self) -> Engine:
        """The engine for the Postgres client."""
        return create_engine(
            self.connection_string,
            connect_args={
                "sslmode": self.sslmode,
                "channel_binding": self.channel_binding,
            },
        )

    @cached_property
    def _session_factory(self) -> sessionmaker:
        return sessionmaker(bind=self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Get a session for the Postgres client."""
        session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
