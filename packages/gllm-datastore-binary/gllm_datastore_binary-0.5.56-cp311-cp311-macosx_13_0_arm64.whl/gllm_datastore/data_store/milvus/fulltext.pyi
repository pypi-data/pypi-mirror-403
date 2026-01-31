from _typeshed import Incomplete
from gllm_core.schema import Chunk
from gllm_datastore.constants import CHUNK_KEYS as CHUNK_KEYS
from gllm_datastore.core.filters import FilterClause as FilterClause, QueryFilter as QueryFilter, QueryOptions as QueryOptions
from gllm_datastore.data_store.milvus.query import execute_query as execute_query
from gllm_datastore.data_store.milvus.query_translator import MilvusQueryTranslator as MilvusQueryTranslator
from pymilvus import AsyncMilvusClient
from typing import Any

class MilvusFulltextCapability:
    """Milvus implementation of FulltextCapability protocol.

    This class provides document CRUD operations and filtering using Milvus.

    Attributes:
        collection_name (str): The name of the Milvus collection.
        client (AsyncMilvusClient): Async Milvus client instance.
        query_field (str): The field name to use for text content.
    """
    collection_name: Incomplete
    client: Incomplete
    query_field: Incomplete
    id_max_length: Incomplete
    content_max_length: Incomplete
    def __init__(self, collection_name: str, client: AsyncMilvusClient, query_field: str = 'content', id_max_length: int = 100, content_max_length: int = 65535) -> None:
        '''Initialize the Milvus fulltext capability.

        Args:
            collection_name (str): The name of the Milvus collection.
            client (AsyncMilvusClient): The async Milvus client instance.
            query_field (str, optional): The field name to use for text content. Defaults to "content".
            id_max_length (int, optional): Maximum length for ID field. Defaults to 100.
            content_max_length (int, optional): Maximum length for content field. Defaults to 65535.
        '''
    async def ensure_index(self) -> None:
        """Ensure collection exists with proper schema for fulltext capability.

        This method is idempotent - if the collection already exists, it will skip
        creation and return early.

        Raises:
            RuntimeError: If collection creation fails.
        """
    async def create(self, data: Chunk | list[Chunk], **kwargs: Any) -> None:
        """Create new records in the datastore.

        Args:
            data (Chunk | list[Chunk]): Data to create (single item or collection).
            **kwargs: Backend-specific parameters (e.g., partition_name).

        Raises:
            ValueError: If data structure is invalid.
        """
    async def retrieve(self, filters: FilterClause | QueryFilter | None = None, options: QueryOptions | None = None, **kwargs: Any) -> list[Chunk]:
        """Read records from the datastore with optional filtering.

        Args:
            filters (FilterClause | QueryFilter | None, optional): Query filters to apply.
                FilterClause objects are automatically converted to QueryFilter internally.
                Defaults to None.
            options (QueryOptions | None, optional): Query options like limit and sorting.
                Defaults to None.
            **kwargs: Backend-specific parameters.

        Returns:
            list[Chunk]: Query results.
        """
    async def retrieve_fuzzy(self, query: str, max_distance: int = 2, filters: FilterClause | QueryFilter | None = None, options: QueryOptions | None = None, max_candidates: int = 1000, **kwargs: Any) -> list[Chunk]:
        """Find records that fuzzy match the query within distance threshold.

        This method retrieves candidates from Milvus using metadata filters first,
        then performs client-side fuzzy matching using Levenshtein distance.
        The max_candidates parameter limits the initial query to reduce processing time,
        and the final limit from options is applied after sorting by distance.

        Args:
            query (str): Text to fuzzy match against.
            max_distance (int): Maximum edit distance for matches (Levenshtein distance). Defaults to 2.
            filters (FilterClause | QueryFilter | None, optional): Optional metadata filters to apply.
                FilterClause objects are automatically converted to QueryFilter internally.
                Defaults to None.
            options (QueryOptions | None, optional): Query options (limit, sorting, etc.). Defaults to None.
                The limit is applied client-side after distance sorting.
            max_candidates (int, optional): Maximum number of candidates to retrieve from Milvus
                before applying fuzzy matching. Defaults to 1000. This helps limit processing time
                for large datasets.
            **kwargs: Backend-specific parameters.

        Returns:
            list[Chunk]: Matched chunks ordered by distance (ascending) or by options.order_by if specified.
        """
    async def update(self, update_values: dict[str, Any], filters: FilterClause | QueryFilter | None = None, **kwargs: Any) -> None:
        '''Update existing records in the datastore.

        Args:
            update_values (dict[str, Any]): Values to update. Supports "content" for updating document content
                and "metadata" for updating metadata. Other keys are treated as direct metadata updates.
            filters (FilterClause | QueryFilter | None, optional): Filters to select records to update.
                FilterClause objects are automatically converted to QueryFilter internally.
                Defaults to None.
            **kwargs (Any): Backend-specific parameters (e.g., partition_name).

        Note:
            If filters is None, no operation is performed (no-op).
        '''
    async def delete(self, filters: FilterClause | QueryFilter | None = None, options: QueryOptions | None = None, **kwargs: Any) -> None:
        """Delete records from the datastore.

        Args:
            filters (FilterClause | QueryFilter | None, optional): Filters to select records to delete.
                FilterClause objects are automatically converted to QueryFilter internally.
                Defaults to None, in which case no operation is performed (no-op).
            options (QueryOptions | None, optional): Query options for sorting and limiting deletions.
                Defaults to None.
            **kwargs: Backend-specific parameters.

        Note:
            If filters is None, no operation is performed (no-op).
            When options with limit or order_by are provided, records are first retrieved
            and then deleted by ID. Otherwise, deletion uses filter expressions directly.
        """
    async def clear(self, **kwargs: Any) -> None:
        """Clear all records from the datastore.

        Args:
            **kwargs: Backend-specific parameters.
        """
