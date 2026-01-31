from _typeshed import Incomplete
from gllm_core.schema.chunk import Chunk
from gllm_datastore.core.filters import FilterClause as FilterClause, QueryFilter as QueryFilter, QueryOptions as QueryOptions
from gllm_datastore.data_store.sql.query import execute_delete_with_filters as execute_delete_with_filters, execute_update_with_filters as execute_update_with_filters, row_to_chunk as row_to_chunk
from gllm_datastore.data_store.sql.query_translator import SQLQueryTranslator as SQLQueryTranslator
from gllm_datastore.data_store.sql.schema import Base as Base, ChunkModel as ChunkModel
from sqlalchemy import func as func
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import DeclarativeBase
from typing import Any

class SQLFulltextCapability:
    """SQL implementation of FulltextCapability protocol using async SQLAlchemy.

    This capability creates its own session factory from the engine, making it
    self-contained and independent of the data store's session configuration.

    Attributes:
        engine (AsyncEngine): SQLAlchemy async engine instance.
        session_factory (async_sessionmaker): Async session factory created from engine.
        table_name (str): Name of the table this capability operates on. This is immutable
            and defines the scope of all operations.
        _table (Table | None): Cached SQLAlchemy Table object. Initialized lazily on first use.
        _metadata (MetaData): SQLAlchemy metadata instance for table reflection.
    """
    engine: Incomplete
    table_name: Incomplete
    session_factory: Incomplete
    def __init__(self, engine: AsyncEngine, table_name: str) -> None:
        """Initialize the SQL fulltext capability with async support.

        Args:
            engine (AsyncEngine): SQLAlchemy async engine instance.
            table_name (str): Name of the table this capability will operate on.
                This defines the scope of all operations and cannot be changed after initialization.
        """
    async def create(self, data: Chunk | list[Chunk] | DeclarativeBase | list[DeclarativeBase]) -> None:
        '''Create new records in the datastore.

        This method accepts both Chunk and DeclarativeBase instances.
        1. If data is a Chunk, it will be converted to a ChunkModel instance with flattened metadata.
        2. If data is a DeclarativeBase, it will be added directly to the database.

        Examples:
            1. Create a single record using a Chunk.
            ```python
            # Create a single chunk
            chunk = Chunk(id="1", content="Test content", metadata={"source": "test"})
            await datastore.fulltext.create(chunk)

            # Bulk create
            chunks = [
                Chunk(id=str(i), content=f"Test content {i}", metadata={"source": "test"})
                for i in range(10)
            ]
            await datastore.fulltext.create(chunks)
            ```

            2. Create a single record using a declarative base model.
            ```python
            # Create a single user
            user = UserModel(id="1", name="John", email="john@example.com")
            await datastore.fulltext.create(user)

            # Bulk create
            users = [UserModel(id=str(i), name=f"User{i}") for i in range(10)]
            await datastore.fulltext.create(users)
            ```

        Args:
            data (Chunk | list[Chunk] | DeclarativeBase | list[DeclarativeBase]):
                Data to create (single item or collection). Chunk instances will be converted
                to ChunkModel. DeclarativeBase instances will be added directly to the database.

        Raises:
            RuntimeError: If the creation fails.
        '''
    async def retrieve(self, filters: FilterClause | QueryFilter | None = None, options: QueryOptions | None = None) -> list[Chunk]:
        '''Read records from the datastore with optional filtering.

        This method operates on this capability\'s table (specified at initialization).
        It returns Chunk objects matching the filters and options.

        Examples:
            ```python
            # Retrieve all records from the instance\'s table
            chunks = await datastore.fulltext.retrieve()

            # Retrieve with filters
            chunks = await datastore.fulltext.retrieve(
                filters=F.eq("status", "active")
            )

            # Retrieve with options (using CHUNK_KEYS.ID for column name)
            chunks = await datastore.fulltext.retrieve(
                options=QueryOptions(order_by=CHUNK_KEYS.ID, order_desc=True, limit=10)
            )
            ```

        Args:
            filters (FilterClause | QueryFilter | None, optional): Query filters to apply.
                Defaults to None.
            options (QueryOptions | None, optional): Query options for sorting and pagination.
                Defaults to None.

        Returns:
            list[Chunk]: List of Chunk objects from this capability\'s table.

        Raises:
            RuntimeError: If the read operation fails.
        '''
    async def update(self, update_values: dict[str, Any], filters: FilterClause | QueryFilter | None = None) -> None:
        '''Update existing records in the datastore.

        This method operates on this capability\'s table (specified at initialization).
        Updates records matching the filters with the provided values.

        Examples:
            ```python
            # Update all records (no filters)
            await datastore.fulltext.update(
                {"status": "active"}
            )

            # Update with filters (using CHUNK_KEYS constants)
            await datastore.fulltext.update(
                {CHUNK_KEYS.CONTENT: "Updated content"},
                filters=F.eq(CHUNK_KEYS.ID, "chunk_123")
            )
            ```

        Args:
            update_values (dict[str, Any]): Mapping of fields to new values to apply.
            filters (FilterClause | QueryFilter | None, optional): Filters to select records to update.
                Defaults to None. If None, no records will be updated (safety measure).

        Raises:
            RuntimeError: If the update operation fails.
        '''
    async def delete(self, filters: FilterClause | QueryFilter | None = None) -> None:
        '''Delete records from the datastore.

        This method operates on this capability\'s table (specified at initialization).
        Deletes records matching the provided filters.

        Examples:
            ```python
            # Delete with filters (using CHUNK_KEYS.ID)
            await datastore.fulltext.delete(
                filters=F.eq(CHUNK_KEYS.ID, "chunk_123")
            )

            # Delete multiple records
            await datastore.fulltext.delete(
                filters=F.in_("status", ["deleted", "archived"])
            )
            ```

        Args:
            filters (FilterClause | QueryFilter | None, optional): Filters to select records to delete.
                Defaults to None. If None, no records will be deleted (safety measure).

        Raises:
            RuntimeError: If the delete operation fails.
        '''
