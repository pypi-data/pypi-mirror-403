"""IO Managers for Dagster.

This moddle includes:
- PostgresDataFrameIOManager: for writing Pandas DFs to Postgres tables and back.
"""

import math
from collections.abc import Mapping
from typing import Any, Final, Self, TypeGuard

from dagster import ConfigurableIOManager, InputContext, OutputContext, get_dagster_logger
from pandas import DataFrame, read_sql
from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.engine import Engine

from .database import construct_query_statement, create_upsert_method

logger = get_dagster_logger()

# Number of coordinates in a PostgreSQL point (longitude, latitude)
POINT_COORDINATE_COUNT: Final[int] = 2


class PostgresDataframeIOManager(ConfigurableIOManager):
    """An IO manager to read/write to or from Pandas dataframes and Postgres tables."""

    username: str = "postgres"
    password: str = "postgres"  # noqa: S105
    hostname: str = "localhost"
    port: int = 5432
    database_name: str = "postgres"
    ssl_mode: str | None = None
    if_exists: str = "append"
    query_columns_list: list[str] | None = None
    query_predicate: str | None = None

    def _load_input_context_metadata(
        self: Self,
        context: InputContext,
    ) -> Mapping[str, Any]:
        """Load and validate input context metadata."""
        upstream_metadata: Mapping[str, Any] = {}
        input_metadata: Mapping[str, Any] = {}

        if context.upstream_output and context.upstream_output.metadata:
            upstream_metadata = context.upstream_output.metadata

        if context.metadata:
            input_metadata = context.metadata

        metadata = {**upstream_metadata, **input_metadata}

        if not metadata:
            msg = "upstream output or input metadata must be defined."
            raise ValueError(msg)

        return metadata

    def _load_output_context_metadata(
        self: Self,
        context: OutputContext,
    ) -> Mapping[str, Any]:
        """Load and validate output context metadata."""
        if not context.metadata:
            msg = "context.metadata cannot be `None`."
            raise ValueError(msg)
        return context.metadata

    def _get_schema(self: Self, metadata: Mapping[str, Any]) -> str:
        """Get a PostgreSQL schema from a Dagster context."""
        schema_name = metadata.get("schema_name")
        if schema_name is None:
            msg = "'schema_name' cannot be `None`."
            raise ValueError(msg)
        if not isinstance(schema_name, str):
            msg = f"Expected 'schema_name' to be of type str. Got {type(schema_name)} instead."
            raise TypeError(msg)
        return schema_name

    def _get_table_name(self: Self, metadata: Mapping[str, Any]) -> str:
        """Get a PostgreSQL table name from a Dagster context."""
        table_name = metadata.get("table_name")
        if table_name is None:
            msg = "'table_name' cannot be `None`."
            raise ValueError(msg)
        if not isinstance(table_name, str):
            msg = f"Expected 'table_name' to be of type str. Got {type(table_name)} instead."
            raise TypeError(msg)
        return table_name

    def _get_table_path(
        self: "PostgresDataframeIOManager",
        metadata: Mapping[str, Any],
    ) -> tuple[str, str]:
        """Get a PostgreSQL schema and table name from a Dagster context."""
        schema_name = self._get_schema(metadata)
        table_name = self._get_table_name(metadata)
        return (schema_name, table_name)

    def _get_connection_string(
        self: "PostgresDataframeIOManager",
        metadata: Mapping[str, Any],
    ) -> str:
        """Return the postgres connection string from context metadata."""
        username = metadata.get("username", self.username)
        hostname = metadata.get("hostname", self.hostname)
        database_name = metadata.get("database_name", self.database_name)
        port = metadata.get("port", self.port)
        return f"postgresql://{username}:{self.password}@{hostname}:{port}/{database_name}"

    def _get_engine(self: "PostgresDataframeIOManager", metadata: Mapping[str, Any]) -> Engine:
        ssl_mode = metadata.get("ssl_mode", self.ssl_mode)
        connect_args = {}
        # Psycopg2 does not support sslmode=no-verify, so we need to use a dummy sslrootcert for dev mode connections
        if ssl_mode == "no-verify":
            connect_args = {"sslmode": "require", "sslrootcert": "/path/to/empty/file"}
        else:
            connect_args = {"sslmode": ssl_mode}
        return create_engine(self._get_connection_string(metadata), connect_args=connect_args)

    def _get_table(self: "PostgresDataframeIOManager", metadata: Mapping[str, Any], engine: Engine) -> Table:
        (schema_name, table_name) = self._get_table_path(metadata)
        metadata_obj = MetaData(schema=schema_name)
        return Table(table_name, metadata_obj, autoload_with=engine)

    def _get_join(
        self: "PostgresDataframeIOManager",
        metadata: Mapping[str, Any],
        engine: Engine,
    ) -> list[tuple[Table, str]] | None:
        join_query = metadata.get("join", None)
        if not join_query:
            return None

        if is_list_of_str_tuples(join_query) is False:
            msg = (
                f"Expected 'join_query' to be of type list[tuple[str,str]]."
                f"Got {join_query}, type:{type(join_query)} instead."
            )
            raise TypeError(msg)

        schema_name = self._get_schema(metadata)
        metadata_obj = MetaData(schema=schema_name)
        join_list: list[tuple[Table, str]] = []
        for join_name, on in join_query:
            join_table = Table(join_name, metadata_obj, autoload_with=engine)
            join_list.append((join_table, on))
        return join_list

    def handle_output(
        self: "PostgresDataframeIOManager",
        context: OutputContext,
        dataframe: DataFrame | None,
    ) -> None:
        """Return the number of DB rows modified or `None`.

        Write the supplied dataframe object to postgres and create the target table from a schema definition if
        the table does not already exist.
        """
        if dataframe is None:
            return

        metadata = self._load_output_context_metadata(context)
        schema_name, table_name = self._get_table_path(metadata)
        schema_table_name = f"{schema_name}.{table_name}"
        engine = self._get_engine(metadata)
        should_upsert = metadata.get("should_upsert")
        for column in dataframe.columns:
            if dataframe[column].dtype == "timedelta64[ns]":  # pragma: no cover
                dataframe[column] = dataframe[column].apply(str)
            # Convert tuple positions to PostgreSQL point string format: "(lon,lat)"
            elif column == "position" and dataframe[column].dtype == "object" and len(dataframe) > 0:
                # Check if values are tuples (for point type)
                sample_value = dataframe[column].iloc[0]
                if isinstance(sample_value, tuple) and len(sample_value) == POINT_COORDINATE_COUNT:

                    def convert_to_point(x: tuple[float, float] | None | float) -> str | None:
                        if isinstance(x, tuple) and len(x) == POINT_COORDINATE_COUNT:
                            return f"({x[0]},{x[1]})"
                        if x is None or (isinstance(x, float) and math.isnan(x)):
                            return None
                        msg = f"Expected tuple of length {POINT_COORDINATE_COUNT} or None, got {type(x)}: {x}"
                        raise TypeError(msg)

                    dataframe[column] = dataframe[column].apply(convert_to_point)
        rows_affected = dataframe.to_sql(
            name=table_name,
            schema=schema_name,
            con=engine,
            index=False,
            if_exists="append",
            method=create_upsert_method(schema_name, table_name) if should_upsert else None,
        )

        context.add_output_metadata(
            {
                "db": self.database_name,
                "schema_table_name": schema_table_name,
                "dataframe_rows": len(dataframe),
                "records_affected": rows_affected,
            },
        )

    def load_input(
        self: "PostgresDataframeIOManager",
        context: InputContext,
    ) -> DataFrame:
        """Run a postgres query and converts the result back into a DataFrame."""
        metadata = self._load_input_context_metadata(context)
        engine = self._get_engine(metadata)
        table = self._get_table(metadata, engine)
        query_columns_list = metadata.get("columns")
        query_join = self._get_join(metadata, engine)
        query_predicate = metadata.get("predicate", lambda _: None)(context)
        statement = construct_query_statement(table, query_columns_list, query_join, query_predicate)
        logger.info("Executing: %s", statement)
        return read_sql(statement, engine)


def is_list_of_str_tuples(value: Any) -> TypeGuard[list[tuple[str, str]]]:  # noqa: ANN401
    """Typecheck of the value is a list of tuples of 2 strings."""
    return isinstance(value, list) and all(
        isinstance(t, tuple) and len(t) == 2 and all(isinstance(e, str) for e in t)  # noqa: PLR2004
        for t in value
    )
