from _typeshed import Incomplete
from gllm_datastore.core.filters import FilterClause as FilterClause, FilterCondition as FilterCondition, FilterOperator as FilterOperator, QueryFilter as QueryFilter, QueryOptions as QueryOptions
from sqlalchemy import Select, Table
from sqlalchemy.sql.expression import ColumnElement

class SQLQueryTranslator:
    """Translates QueryFilter and FilterClause objects to SQLAlchemy ColumnElement expressions.

    This class encapsulates all query translation logic for SQL data stores.
    It works with reflected Table objects (not DeclarativeBase models) and supports
    both direct column access and JSON field paths.
    """
    table: Incomplete
    def __init__(self, table: Table) -> None:
        """Initialize the SQL query translator.

        Args:
            table (Table): SQLAlchemy Table object for column resolution.
        """
    def translate(self, filters: QueryFilter | None) -> ColumnElement | None:
        """Translate a structured QueryFilter into a SQLAlchemy ColumnElement expression.

        This is the main entry point for filter translation. It handles None filters
        and delegates to internal translation methods.

        Args:
            filters (QueryFilter | None): Structured QueryFilter to translate. Defaults to None.

        Returns:
            ColumnElement | None: A SQLAlchemy condition expression or None if no filters are provided.
        """
    def apply_filters(self, query: Select, filters: QueryFilter | None) -> Select:
        """Apply filters to a SQLAlchemy Select query.

        Args:
            query (Select): SQLAlchemy Select query.
            filters (QueryFilter | None): Query filters to apply. Defaults to None.

        Returns:
            Select: Query with filters applied.
        """
    def apply_options(self, query: Select, options: QueryOptions | None) -> Select:
        """Apply query options to a SQLAlchemy Select query.

        Args:
            query (Select): SQLAlchemy Select query.
            options (QueryOptions | None): Query options to apply. Defaults to None.

        Returns:
            Select: Query with options applied.
        """
