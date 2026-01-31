from _typeshed import Incomplete
from gllm_datastore.core.filters import FilterClause as FilterClause, QueryFilter as QueryFilter
from gllm_datastore.data_store.base import BaseDataStore as BaseDataStore, CapabilityType as CapabilityType
from gllm_datastore.data_store.sql.fulltext import SQLFulltextCapability as SQLFulltextCapability
from gllm_datastore.data_store.sql.query import SQLQueryTranslator as SQLQueryTranslator
from gllm_datastore.data_store.sql.schema import Base as Base
from sqlalchemy import Table as Table, URL
from sqlalchemy.ext.asyncio import AsyncEngine
from typing import Any

class SQLDataStore(BaseDataStore):
    '''SQL data store with multiple capability support using async SQLAlchemy.

    This data store follows the "one instance = one table" pattern. Each instance
    operates on a single table specified at construction time. To work with multiple
    tables, create multiple instances sharing the same engine.

    Attributes:
        engine (AsyncEngine): SQLAlchemy async engine instance. Can be shared across
            multiple SQLDataStore instances for different tables with single connection pool.
        table_name (str): Name of the table this instance operates on. This is immutable
            after construction and defines the scope of all operations.
    '''
    engine: Incomplete
    table_name: Incomplete
    session: Incomplete
    def __init__(self, engine_or_url: AsyncEngine | str | URL, pool_size: int = 10, max_overflow: int = 10, table_name: str = 'chunks', **engine_kwargs: Any) -> None:
        '''Initialize the SQL data store with async support.

        This creates a data store instance scoped to a single table. Each instance
        operates exclusively on the table specified by `table_name`. To work with
        multiple tables, create multiple instances sharing the same engine.

        Examples:
            ```python
            # Single table usage
            datastore = SQLDataStore(
                engine_or_url="postgresql+asyncpg://user:pass@localhost/mydb",
                table_name="chunks"
            )

            # Multiple tables with shared engine (recommended pattern)
            # Both stores share the same connection pool
            engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/mydb")
            chunks_store = SQLDataStore(engine, table_name="chunks")
            users_store = SQLDataStore(engine, table_name="users")
            ```

        Args:
            engine_or_url (AsyncEngine | str | URL): AsyncEngine instance, database URL string, or URL object.
                For async support, async drivers are automatically added if not specified:
                1. PostgreSQL: "postgresql://..." -> "postgresql+asyncpg://..."
                2. MySQL: "mysql://..." -> "mysql+aiomysql://..."
                3. SQLite: "sqlite://..." -> "sqlite+aiosqlite://..."
                If a driver is already specified (e.g., "postgresql+asyncpg://"), it is used as-is.
                If an AsyncEngine is provided, it can be shared across multiple SQLDataStore instances.
            pool_size (int): The size of the database connection pool. Defaults to 10.
                Only used when creating a new engine from a URL. Ignored if AsyncEngine is provided.
            max_overflow (int): The maximum overflow size of the pool. Defaults to 10.
                Only used when creating a new engine from a URL. Ignored for SQLite or if AsyncEngine is provided.
            table_name (str): Name of the table this instance will operate on. Defaults to "chunks".
                This defines the scope of all operations for this instance and cannot be changed after construction.
            **engine_kwargs (Any): Additional keyword arguments for create_async_engine.
                Only used when creating a new engine from a URL.

        Raises:
            ValueError: If the database engine initialization fails or if engine_kwargs
                contains pool-related parameters that conflict with pool_size/max_overflow.
        '''
    async def initialize(self) -> None:
        '''Initialize the datastore by creating tables.

        This method must be called after instantiation to set up the database schema.

        Example:
            ```python
            datastore = SQLDataStore(engine_or_url="sqlite+aiosqlite:///./data.db")
            await datastore.initialize()
            datastore.with_fulltext()
            ```
        '''
    async def close(self) -> None:
        """Close the database engine and clean up connections.

        Example:
            ```python
            await datastore.close()
            ```
        """
    @property
    def supported_capabilities(self) -> list[CapabilityType]:
        """Return list of currently supported capabilities.

        Returns:
            list[CapabilityType]: List of capability names that are supported.
        """
    async def get_size(self, filters: FilterClause | QueryFilter | None = None) -> int:
        '''Get the total number of records in the datastore.

        Examples:
            ```python
            # Async usage
            count = await datastore.get_size()

            # With filters (using Query Filters)
            from gllm_datastore.core.filters import filter as F
            count = await datastore.get_size(filters=F.eq("status", "active"))
            ```

        Args:
            filters (FilterClause | QueryFilter | None, optional): Query filters to apply. Defaults to None.

        Returns:
            int: The total number of records matching the filters.

        Raises:
            RuntimeError: If the operation fails.
        '''
    @property
    def fulltext(self) -> SQLFulltextCapability:
        """Access fulltext capability if registered.

        This method overrides the parent class to return SQLFulltextCapability for better type hinting.

        Returns:
            SQLFulltextCapability: Fulltext capability handler.

        Raises:
            NotRegisteredException: If fulltext capability is not registered.
        """
    def with_fulltext(self) -> SQLDataStore:
        '''Configure fulltext capability and return datastore instance.

        Examples:
            ```python
            # Enable fulltext
            datastore.with_fulltext()

            # For multiple tables with shared engine
            engine = create_async_engine("postgresql+asyncpg://...")
            chunks_store = SQLDataStore(engine, table_name="chunks")
            users_store = SQLDataStore(engine, table_name="users")
            chunks_store.with_fulltext()
            users_store.with_fulltext()
            ```

        Returns:
            SQLDataStore: Self for method chaining.
        '''
    @classmethod
    def translate_query_filter(cls, query_filter: FilterClause | QueryFilter | None = None, table_name: str = 'chunks', engine_or_url: AsyncEngine | str | URL | None = None) -> str | None:
        '''Translate QueryFilter or FilterClause to SQL WHERE clause string.

        This method delegates to the SQLQueryTranslator and returns the result as a
        SQL WHERE clause string that can be used in SQL queries. The table structure
        is reflected from the database using the provided engine_or_url and table_name.

        Examples:
            ```python
            from gllm_datastore.core.filters import filter as F

            # With database URL string
            clause = F.eq("id", "test")
            result = SQLDataStore.translate_query_filter(
                clause,
                table_name="chunks",
                engine_or_url="postgresql://user:pass@localhost/mydb"
            )
            # Returns: "chunks.id = \'test\'"

            # With AsyncEngine instance
            from sqlalchemy.ext.asyncio import create_async_engine
            engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/mydb")
            filter_obj = F.and_(
                F.eq("id", "test"),
                F.gt("chunk_metadata.age", 25),
            )
            result = SQLDataStore.translate_query_filter(
                filter_obj,
                table_name="chunks",
                engine_or_url=engine
            )
            # Returns: "(chunks.id = \'test\' AND json_extract(chunks.chunk_metadata, \'$.age\') > 25)"

            # QueryFilter with OR condition
            filter_obj = F.or_(
                F.eq("id", "test1"),
                F.eq("id", "test2"),
            )
            result = SQLDataStore.translate_query_filter(
                filter_obj,
                table_name="chunks",
                engine_or_url="sqlite:///./data.db"
            )
            # Returns: "(chunks.id = \'test1\' OR chunks.id = \'test2\')"

            # Empty filter returns None
            result = SQLDataStore.translate_query_filter(
                None,
                table_name="chunks",
                engine_or_url="postgresql://user:pass@localhost/mydb"
            )
            # Returns: None
            ```

        Args:
            query_filter (FilterClause | QueryFilter): The filter to translate.
                Can be a single FilterClause or a QueryFilter with multiple clauses.
            table_name (str): Name of the table to reflect from the database. Defaults to "chunks".
            engine_or_url (AsyncEngine | str | URL | None): AsyncEngine instance, database URL string,
                or URL object for table reflection. Required. The table structure is reflected from the database.
                For async support, async drivers are automatically added if not specified:
                PostgreSQL -> postgresql+asyncpg://, MySQL -> mysql+aiomysql://,
                SQLite -> sqlite+aiosqlite://.

        Raises:
            ValueError: If engine_or_url is None.

        Returns:
            str: The translated filter as a SQL WHERE clause string.

        Raises:
            RuntimeError: If table reflection fails or table is not found in database.
        '''
