"""Database resources for use in Dagster."""

from collections.abc import Callable, Iterable
from typing import Any

from dagster import ConfigurableResource
from pandas.io.sql import SQLTable
from sqlalchemy import Connection, Engine, MetaData, Select, Table, create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker


class PostgresSessionResource(ConfigurableResource):
    """Resource for creating a Postgress session."""

    username: str = "postgres"
    password: str = "postgres"  # noqa: S105
    hostname: str = "localhost"
    port: int = 5432
    database_name: str = "postgres"
    ssl_mode: str | None = None

    def _get_connection_str(self: "PostgresSessionResource") -> str:
        """Return a Postgres session for Dagster."""
        return f"postgresql://{self.username}:{self.password}@{self.hostname}:{self.port}/{self.database_name}"

    def get_engine(self: "PostgresSessionResource") -> Engine:
        """Return an engine for accessing Postgres with Dagster."""
        return create_engine(
            self._get_connection_str(),
            connect_args={"sslmode": self.ssl_mode},
        )

    def get_session(self: "PostgresSessionResource") -> Session:
        """Return a Postgres session for Dagster."""
        return sessionmaker(bind=self.get_engine())()

    def get_table(
        self: "PostgresSessionResource",
        engine: Engine,
        schema_name: str,
        table_name: str,
    ) -> Table:
        """Acquire a table type definition for query statements."""
        metadata = MetaData(schema=schema_name)
        return Table(table_name, metadata, autoload_with=engine)


def construct_query_statement(
    table: Table,
    query_column_list: list[str] | None = None,
    query_join: list[tuple[Table, str]] | None = None,
    query_predicate: str | None = None,
) -> Select:
    """Return a sqlalchemy query statement."""
    if not query_column_list:
        statement = select(table)
    else:
        if not isinstance(query_column_list, list):
            msg = f"Expected query_column_list to be of type list. Got {type(query_column_list)} instead."
            raise TypeError(msg)
        columns = [table.c[col] for col in query_column_list]
        statement = select(*columns)
    if query_join:
        for join, on in query_join:
            statement = statement.join(join, join.c.id == table.c[on])
    if query_predicate:
        statement = statement.where(text(query_predicate))
    return statement


def create_upsert_method(
    schema_name: str,
    table_name: str,
) -> Callable[[SQLTable, Connection, list[str], Iterable[tuple[Any, ...]]], None]:
    """Return an upsert method for a specific schema and table."""

    def upsert(
        _table: SQLTable,
        conn: Connection,
        keys: list[str],
        data_iterator: Iterable[tuple[Any, ...]],
    ) -> None:
        """Perform an upsert compatible with Pandas's expected method function structure."""
        columns: str = ", ".join([f'"{k}"' for k in keys])
        insert_values: str = ", ".join([f":{k}" for k in keys])
        update_values: str = ", ".join([f'"{k}" = EXCLUDED."{k}"' for k in keys if k != "id"])

        upsert_query: str = f"""
            INSERT INTO {schema_name}.{table_name} ({columns})
            VALUES ({insert_values})
            ON CONFLICT (id)
            DO UPDATE SET {update_values}
        """  # noqa: S608

        prepared_statement = text(upsert_query)

        for data_chunk in data_iterator:
            statement_parameters = dict(zip(keys, data_chunk, strict=True))
            conn.execute(prepared_statement, statement_parameters)

    return upsert
