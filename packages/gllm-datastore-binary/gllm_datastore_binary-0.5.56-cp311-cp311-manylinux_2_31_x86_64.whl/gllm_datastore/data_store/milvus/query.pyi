import logging
from gllm_core.schema import Chunk
from gllm_datastore.constants import CHUNK_KEYS as CHUNK_KEYS
from gllm_datastore.core.filters import FilterClause as FilterClause, QueryFilter as QueryFilter, QueryOptions as QueryOptions
from gllm_datastore.data_store.milvus.query_translator import MilvusQueryTranslator as MilvusQueryTranslator
from gllm_datastore.data_store.milvus.utils import get_sort_value as get_sort_value, merge_metadata as merge_metadata, prepare_metadata_updates as prepare_metadata_updates
from pymilvus import AsyncMilvusClient
from typing import Any

async def execute_query(client: AsyncMilvusClient, collection_name: str, query_field: str, filters: FilterClause | QueryFilter | None = None, options: QueryOptions | None = None, query_translator: MilvusQueryTranslator | None = None, **kwargs: Any) -> list[dict[str, Any]]:
    """Execute a query against Milvus and return raw results.

    This helper function extracts common query execution logic used by
    retrieve() and retrieve_fuzzy() methods.

    Args:
        client (AsyncMilvusClient): The async Milvus client instance.
        collection_name (str): The name of the Milvus collection.
        query_field (str): The field name to use for text content.
        filters (FilterClause | QueryFilter | None, optional): Query filters to apply.
            FilterClause objects are automatically converted to QueryFilter internally.
            Defaults to None.
        options (QueryOptions | None, optional): Query options like limit.
            Defaults to None.
        query_translator (MilvusQueryTranslator | None, optional): Query translator instance.
            If None, a new instance will be created. Defaults to None.
        **kwargs: Backend-specific parameters.

    Returns:
        list[dict[str, Any]]: Raw query results from Milvus.
    """
def apply_options(chunks: list[Chunk], options: QueryOptions) -> list[Chunk]:
    """Apply query options (sorting, limiting) to results.

    This helper function extracts common query options logic used by
    retrieve() and retrieve_by_vector() methods in both fulltext and vector capabilities.

    Args:
        chunks (list[Chunk]): List of chunks to process.
        options (QueryOptions): Query options to apply.

    Returns:
        list[Chunk]: Filtered and sorted list of chunks.
    """
def convert_query_results_to_chunks(results: list[dict[str, Any]], query_field: str) -> list[Chunk]:
    """Convert Milvus query results to Chunk objects.

    This utility function handles conversion of query results (from client.query)
    to Chunk objects, used by both fulltext and vector capabilities.

    Args:
        results (list[dict[str, Any]]): Results from Milvus query.
        query_field (str): Field name for text content.

    Returns:
        list[Chunk]: List of Chunk objects.
    """
async def query_update_records(client: AsyncMilvusClient, collection_name: str, filters: FilterClause | QueryFilter | None, query_translator: MilvusQueryTranslator, output_fields: list[str], logger: logging.Logger) -> list[dict[str, Any]] | None:
    """Query records to update based on filters.

    This function extracts common query logic used by update() methods in both
    fulltext and vector capabilities.

    Args:
        client (AsyncMilvusClient): The async Milvus client instance.
        collection_name (str): The name of the Milvus collection.
        filters (FilterClause | QueryFilter | None): Filters to select records.
        query_translator (MilvusQueryTranslator): Query translator instance.
        output_fields (list[str]): List of field names to return in query results.
        logger (logging.Logger): Logger instance for logging.

    Returns:
        list[dict[str, Any]] | None: Query results or None if no records to update.
    """
def prepare_update_entities(results: list[dict[str, Any]], update_values: dict[str, Any], query_field: str) -> list[dict[str, Any]]:
    """Prepare update entities from query results.

    This function extracts common entity preparation logic used by update() methods
    in both fulltext and vector capabilities.

    Args:
        results (list[dict[str, Any]]): Query results from Milvus.
        update_values (dict[str, Any]): Values to update.
        query_field (str): Field name for text content.

    Returns:
        list[dict[str, Any]]: List of prepared entity dictionaries.
    """
