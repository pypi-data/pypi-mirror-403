from gllm_core.schema.chunk import Chunk
from gllm_datastore.core.filters import QueryFilter as QueryFilter
from gllm_datastore.data_store.sql.constants import SQL_COLUMNS as SQL_COLUMNS
from gllm_datastore.data_store.sql.query_translator import SQLQueryTranslator as SQLQueryTranslator
from sqlalchemy import Table
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

def row_to_chunk(row: Row) -> Chunk:
    """Convert a database row to a Chunk object.

    Args:
        row (Row): Database row with _mapping attribute.

    Returns:
        Chunk: Chunk object created from the row data.
    """
async def execute_select(session: AsyncSession, table: Table, filters: QueryFilter | None) -> list[Row]:
    """Execute a select query on a table with filters.

    Args:
        session (AsyncSession): Database session.
        table (Table): SQLAlchemy table.
        filters (QueryFilter | None): Query filters.

    Returns:
        list[Row]: List of result rows.
    """
async def execute_update(session: AsyncSession, table: Table, update_values: dict[str, Any], rows: list[Row]) -> None:
    """Execute update operations on table rows.

    Args:
        session (AsyncSession): Database session.
        table (Table): SQLAlchemy table.
        update_values (dict[str, Any]): Values to update.
        rows (list[Row]): Rows to update.

    Raises:
        ValueError: If table has no primary key.
    """
async def execute_delete(session: AsyncSession, table: Table, rows: list[Row]) -> None:
    """Execute delete operations on table rows.

    Args:
        session (AsyncSession): Database session.
        table (Table): SQLAlchemy table.
        rows (list[Row]): Rows to delete.

    Raises:
        ValueError: If table has no primary key.
    """
async def execute_update_with_filters(session: AsyncSession, table: Table, update_values: dict[str, Any], filters: QueryFilter | None) -> None:
    """Execute update operations using filters directly.

    This function constructs a single atomic UPDATE statement with WHERE conditions
    derived from the filters, avoiding the need to fetch rows first.

    Args:
        session (AsyncSession): Database session.
        table (Table): SQLAlchemy table.
        update_values (dict[str, Any]): Values to update.
        filters (QueryFilter | None): Query filters to apply as WHERE conditions.

    Returns:
        None: No return value.
    """
async def execute_delete_with_filters(session: AsyncSession, table: Table, filters: QueryFilter | None) -> None:
    """Execute delete operations using filters directly.

    This function constructs a single atomic DELETE statement with WHERE conditions
    derived from the filters, avoiding the need to fetch rows first.

    Args:
        session (AsyncSession): Database session.
        table (Table): SQLAlchemy table.
        filters (QueryFilter | None): Query filters to apply as WHERE conditions.

    Returns:
        None: No return value.
    """
