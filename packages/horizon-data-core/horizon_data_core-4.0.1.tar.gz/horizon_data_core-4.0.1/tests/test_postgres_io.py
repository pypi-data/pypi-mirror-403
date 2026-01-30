import os
import re
from typing import Any

import pytest
from dagster import build_input_context, build_output_context
from horizon_data_core.base_types import EntityKind
from horizon_data_core.helpers import create_predicate, list_to_dataframe, name_to_uuid
from horizon_data_core.resources.database import (
    PostgresSessionResource,
    construct_query_statement,
)
from horizon_data_core.resources.postgres_dataframe_io_manager import (
    PostgresDataframeIOManager,
    is_list_of_str_tuples,
)
from pandas import DataFrame
from sqlalchemy import text

postgres_kwargs: dict[str, Any] = {
    "username": os.environ.get("OWNER_PGUSER"),
    "password": os.environ.get("OWNER_PGPASSWORD"),
    "database_name": os.environ.get("PGDATABASE"),
    "hostname": os.environ.get("PGHOST", "localhost"),
    "port": int(os.environ.get("PGPORT", 5432)),
}


engine = PostgresSessionResource(**postgres_kwargs).get_engine()


def has_schema(schema_name: str) -> bool:
    session = PostgresSessionResource(**postgres_kwargs).get_session()
    res = session.execute(
        text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema_name"),
        {"schema_name": schema_name},
    )
    return res.fetchone() is not None


if has_schema("horizon_public"):
    SCHEMA_NAME = "horizon_public"
elif has_schema("underway_public"):
    SCHEMA_NAME = "underway_public"
else:
    raise ValueError("Expected schema horizon_public or underway_public to exist.")
print(f"Using schema: {SCHEMA_NAME}")


def remove_sql_formatting(string: str) -> str:
    """Replaces the following occurences with a single whitespace:
    - multiple consecutive whitespace
    - newline
    - tabs

    Also remove leading and trailing whitespace.
    """
    return re.sub(r"\s+", " ", string).strip(" ")


def mock_entity_kind_list() -> list[EntityKind]:
    return [
        EntityKind(
            id=name_to_uuid("Boeing Test-Frame"),
            name="Boeing Test-Frame",
            short_description="Test text.",
            long_description="A test set of longer text.",
            image_url=f"{name_to_uuid('Boeing Test-Frame')}.jpeg",
        ),
        EntityKind(
            id=name_to_uuid("SSN-99"),
            name="S",
            short_description="Test text.",
            long_description="A test set of longer text.",
            image_url=f"{name_to_uuid('SSN-99')}.jpeg",
        ),
    ]


def mock_entity_kind_dataframe() -> DataFrame:
    return list_to_dataframe(mock_entity_kind_list())


def test_cleanup_table() -> None:
    """Ensure we can delete records."""
    session = PostgresSessionResource(**postgres_kwargs).get_session()
    res = session.execute(text(f"DELETE FROM {SCHEMA_NAME}.entity_kind"))
    session.commit()
    assert res is not None


def test_postgres_io_workflow() -> None:
    """Test a stateful workflow:
    - 1. Ensure that a list of objects can be written to PostgreSQL.
    - 2. Ensure that the list of objects can be recovered from PostgreSQL.
    - 3. Using postgres_connection_resource, ensure we can run an arbitrary query on PostgreSQL and get the result back.
    - 4. Using PostgresDataframeIOManager, ensure we can run an arbitrary query on PostgreSQL and get the result back
        as a list of objects.
    """

    def test_postgres_io_manager_handle_output(
        io_manager: PostgresDataframeIOManager,
    ) -> None:
        """Check that the `PostgresIOManager` can insert the mock data as records in PostgreSQL."""
        entity_kind_context = build_output_context(
            metadata={
                "schema_name": SCHEMA_NAME,
                "table_name": "entity_kind",
                "should_upsert": True,
            },
        )
        io_manager.handle_output(
            entity_kind_context,
            mock_entity_kind_dataframe(),
        )

    def test_postgres_io_manager_handle_input(
        io_manager: PostgresDataframeIOManager,
    ) -> None:
        """Check that the pg io manager can use the load_input method to recover the list of objects."""
        context = build_input_context(
            metadata={
                "schema_name": SCHEMA_NAME,
                "table_name": "entity_kind",
            },
        )
        entity_kind_dataframe = io_manager.load_input(context)
        assert len(entity_kind_dataframe) == len(mock_entity_kind_dataframe())

    def test_postgres_io_manager_handle_input_from_output_context(
        io_manager: PostgresDataframeIOManager,
    ) -> None:
        """
        Check that the pg io manager can use the load_input method to recover the list of objects using the
        upstream_output metadata.
        """
        context = build_input_context(
            upstream_output=build_output_context(
                metadata={
                    "schema_name": SCHEMA_NAME,
                    "table_name": "entity_kind",
                },
            ),
        )
        entity_kind_dataframe = io_manager.load_input(context)
        assert len(entity_kind_dataframe) == len(mock_entity_kind_dataframe())

    def test_postgres_connection_resource_aggregation() -> None:
        """Use the postgres connection resource to run an arbitrary query."""
        session = PostgresSessionResource(**postgres_kwargs).get_session()
        res = session.execute(text(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.entity_kind"))
        count = res.fetchall()[0][0]
        assert count == len(mock_entity_kind_dataframe())

    def test_postgres_io_manager_handle_queried_input() -> None:
        """Set the io manager to load data using an arbitary query and get the results back."""
        io_manager = PostgresDataframeIOManager(
            **postgres_kwargs,
        )
        entity_kind_id = mock_entity_kind_list()[1].id
        context = build_input_context(
            metadata={
                "schema_name": SCHEMA_NAME,
                "table_name": "entity_kind",
                "columns": ["id"],
                "predicate": create_predicate(f"id = '{entity_kind_id}'"),
            },
        )
        singleton_result_dataframe = io_manager.load_input(context)
        singleton_mock_dataframe = DataFrame(
            {"id": [f"{entity_kind_id}"]},
        )
        assert all(singleton_result_dataframe == singleton_mock_dataframe)

    io_manager = PostgresDataframeIOManager(
        **postgres_kwargs,
    )
    test_postgres_io_manager_handle_output(io_manager)
    test_postgres_io_manager_handle_input(io_manager)
    test_postgres_io_manager_handle_input_from_output_context(io_manager)
    test_postgres_connection_resource_aggregation()
    test_postgres_io_manager_handle_queried_input()


def test_postgres_io_manager_handle_empty_output() -> None:
    """Test the situation where nothing is handed to the io manager."""
    io_manager = PostgresDataframeIOManager(
        **postgres_kwargs,
    )
    context = build_output_context(
        metadata={"schema_name": SCHEMA_NAME, "table_name": "entity_kind"},
    )
    io_manager.handle_output(context, None)


def test_construct_query_statement_default() -> None:
    """Ensure that the constructed default query is what we expect."""
    table = PostgresSessionResource(**postgres_kwargs).get_table(
        engine,
        SCHEMA_NAME,
        "entity_kind",
    )
    statement = construct_query_statement(table)
    expected = sorted(
        remove_sql_formatting(
            f"""
        SELECT
        {SCHEMA_NAME}.entity_kind.id,
        {SCHEMA_NAME}.entity_kind.created_datetime,
        {SCHEMA_NAME}.entity_kind.modified_datetime,
        {SCHEMA_NAME}.entity_kind.image_url,
        {SCHEMA_NAME}.entity_kind.name,
        {SCHEMA_NAME}.entity_kind.short_description,
        {SCHEMA_NAME}.entity_kind.long_description,
        {SCHEMA_NAME}.entity_kind.organization_id,
        {SCHEMA_NAME}.entity_kind.content_vector
        FROM
            {SCHEMA_NAME}.entity_kind
        """,
        ).split(),
    )
    received = sorted(remove_sql_formatting(str(statement)).split())
    message = f"Received: {received} does not match expected: {expected}."
    assert expected == received, message


def test_construct_query_statement_with_column_subsets_and_predicates() -> None:
    """Ensure that a query constructed with column subsets and predicates is what we expect."""
    entity_kind_id = mock_entity_kind_list()[0].id
    table = PostgresSessionResource(**postgres_kwargs).get_table(
        engine,
        SCHEMA_NAME,
        "entity_kind",
    )
    statement = construct_query_statement(
        table=table,
        query_column_list=["id"],
        query_predicate=f"id = '{entity_kind_id}'",
    )
    expected = remove_sql_formatting(
        f"""
    SELECT {SCHEMA_NAME}.entity_kind.id
    FROM {SCHEMA_NAME}.entity_kind
    WHERE id = '{entity_kind_id}'
    """,  # noqa: S608
    )
    received = remove_sql_formatting(str(statement))
    message = f"Recevied: {received} does not match expected: {expected}."
    assert expected == received, message


def test_construct_query_statement_with_join() -> None:
    entity_kind_id = mock_entity_kind_list()[0].id
    io_manager = PostgresDataframeIOManager(**postgres_kwargs)
    table = PostgresSessionResource(**postgres_kwargs).get_table(
        engine,
        SCHEMA_NAME,
        "entity",
    )
    statement = construct_query_statement(
        table=table,
        query_column_list=["id"],
        query_predicate=f"id = '{entity_kind_id}'",
        query_join=io_manager._get_join(  # noqa: SLF001
            {"join": [("entity_kind", "kind_id")], "schema_name": SCHEMA_NAME},
            io_manager._get_engine({}),  # noqa: SLF001
        ),
    )
    expected = remove_sql_formatting(
        f"""
    SELECT {SCHEMA_NAME}.entity.id
    FROM {SCHEMA_NAME}.entity
    JOIN {SCHEMA_NAME}.entity_kind ON {SCHEMA_NAME}.entity_kind.id = {SCHEMA_NAME}.entity.kind_id
    WHERE id = '{entity_kind_id}'
    """,  # noqa: S608
    )
    received = remove_sql_formatting(str(statement))
    message = f"Recevied: {received} does not match expected: {expected}."
    assert expected == received, message


def test_bad_construct_query_statement() -> None:
    """Ensure that the function raises an error if the desired column subset is incorrectly specified."""
    table = PostgresSessionResource(**postgres_kwargs).get_table(
        engine,
        SCHEMA_NAME,
        "entity_kind",
    )
    with pytest.raises(TypeError):
        construct_query_statement(
            table=table,
            query_column_list="id, date",  # type: ignore[arg-type]
        )


def test_postgres_io_manager_input_no_metadata() -> None:
    """Ensure that specifying no metadata throws an error."""
    context = build_input_context(
        metadata=None,
    )
    io_manager = PostgresDataframeIOManager(
        **postgres_kwargs,
    )
    with pytest.raises(ValueError, match="upstream output or input metadata must be defined."):
        io_manager.load_input(context)


def test_postgres_io_manager_output_no_metadata() -> None:
    """Ensure that specifying no metadata throws an error."""
    context = build_output_context(
        metadata=None,
    )
    io_manager = PostgresDataframeIOManager(
        **postgres_kwargs,
    )
    entity_kind_dataframe = mock_entity_kind_dataframe()
    with pytest.raises(ValueError, match="context.metadata cannot be `None`."):
        io_manager.handle_output(context, entity_kind_dataframe)


def test_postgres_io_manager_no_schema_name() -> None:
    """Ensure that specifying no schema name throws an error."""
    context = build_output_context(
        metadata={"table_name": "entity_kind"},
    )
    io_manager = PostgresDataframeIOManager(
        **postgres_kwargs,
    )
    entity_kind_dataframe = mock_entity_kind_dataframe()
    with pytest.raises(ValueError, match="'schema_name' cannot be `None`."):
        io_manager.handle_output(context, entity_kind_dataframe)


def test_postgres_io_manager_no_table_name() -> None:
    context = build_output_context(
        metadata={"schema_name": SCHEMA_NAME},
    )
    io_manager = PostgresDataframeIOManager(
        **postgres_kwargs,
    )
    entity_kind_dataframe = mock_entity_kind_dataframe()
    with pytest.raises(ValueError, match="'table_name' cannot be `None`."):
        io_manager.handle_output(context, entity_kind_dataframe)


def test_postgres_io_manager_nonstring_schema() -> None:
    int_schema = 1
    context = build_input_context(
        metadata={"schema_name": int_schema},
    )
    io_manager = PostgresDataframeIOManager(
        **postgres_kwargs,
    )
    with pytest.raises(
        TypeError,
    ):
        io_manager.load_input(context)


def test_postgres_io_manager_nonstring_tablename() -> None:
    int_tablename = 1
    context = build_input_context(
        metadata={"schema_name": SCHEMA_NAME, "table_name": int_tablename},
    )
    io_manager = PostgresDataframeIOManager(
        **postgres_kwargs,
    )
    with pytest.raises(
        TypeError,
    ):
        io_manager.load_input(context)


def test_postgres_io_manager_bad_join() -> None:
    test_cleanup_table()
    bad_join = [1, 2]
    context = build_input_context(
        metadata={
            "schema_name": SCHEMA_NAME,
            "table_name": "entity_kind",
            "join": bad_join,
        },
    )
    io_manager = PostgresDataframeIOManager(
        **postgres_kwargs,
    )
    metadata = io_manager._load_input_context_metadata(context)  # noqa: SLF001
    engine = io_manager._get_engine(metadata)  # noqa: SLF001

    mock_entity_kind_dataframe()
    with pytest.raises(
        TypeError,
    ):
        io_manager._get_join(metadata, engine)  # noqa: SLF001


def test_postgres_io_manager_join() -> None:
    test_cleanup_table()
    join = [("entity_kind", "kind_id")]
    context = build_input_context(
        metadata={
            "schema_name": SCHEMA_NAME,
            "table_name": "entity_kind",
            "join": join,
        },
    )
    io_manager = PostgresDataframeIOManager(
        **postgres_kwargs,
    )
    metadata = io_manager._load_input_context_metadata(context)  # noqa: SLF001
    engine = io_manager._get_engine(metadata)  # noqa: SLF001

    mock_entity_kind_dataframe()
    io_manager._get_join(metadata, engine)  # noqa: SLF001


def test_is_list_of_str_tuples() -> None:
    assert is_list_of_str_tuples([1, 2]) is False
    assert is_list_of_str_tuples([("hello", "world"), ("entity_kind", "kind_id")]) is True

