from _typeshed import Incomplete
from gllm_core.schema import Chunk
from gllm_datastore.constants import CHUNK_KEYS as CHUNK_KEYS, DEFAULT_TOP_K as DEFAULT_TOP_K
from gllm_datastore.core.filters import FilterClause as FilterClause, QueryFilter as QueryFilter, QueryOptions as QueryOptions
from gllm_datastore.data_store.milvus.query import apply_options as apply_options, prepare_update_entities as prepare_update_entities, query_update_records as query_update_records
from gllm_datastore.data_store.milvus.query_translator import MilvusQueryTranslator as MilvusQueryTranslator
from gllm_datastore.data_store.milvus.utils import create_base_schema as create_base_schema, extract_entity_field as extract_entity_field
from gllm_datastore.utils.converter import cosine_distance_to_similarity_score as cosine_distance_to_similarity_score, l2_distance_to_similarity_score as l2_distance_to_similarity_score
from gllm_inference.em_invoker.em_invoker import BaseEMInvoker
from gllm_inference.schema import Vector
from pymilvus import AsyncMilvusClient
from typing import Any

INDEX_PARAMS_MAP: dict[str, dict[str, Any]]
DISTANCE_METRIC_CONFIG: dict[str, dict[str, Any]]

class MilvusVectorCapability:
    '''Milvus implementation of VectorCapability protocol.

    This class provides vector similarity search operations using Milvus.

    Attributes:
        collection_name (str): The name of the Milvus collection.
        client (AsyncMilvusClient): Async Milvus client instance.
        em_invoker (BaseEMInvoker): Embedding model invoker for vectorization.
        dimension (int): Vector dimension.
        distance_metric (str): Distance metric ("L2", "IP", "COSINE").
        vector_field (str): Field name for dense vectors.
        id_max_length (int): Maximum length for ID field.
        content_max_length (int): Maximum length for content field.
    '''
    collection_name: Incomplete
    client: Incomplete
    dimension: Incomplete
    distance_metric: Incomplete
    vector_field: Incomplete
    id_max_length: Incomplete
    content_max_length: Incomplete
    def __init__(self, collection_name: str, client: AsyncMilvusClient, em_invoker: BaseEMInvoker, dimension: int, distance_metric: str = 'L2', vector_field: str = 'dense_vector', id_max_length: int = 100, content_max_length: int = 65535) -> None:
        '''Initialize the Milvus vector capability.

        Args:
            collection_name (str): The name of the Milvus collection.
            client (AsyncMilvusClient): The async Milvus client instance.
            em_invoker (BaseEMInvoker): The embedding model invoker.
            dimension (int): Vector dimension.
            distance_metric (str, optional): Distance metric. Defaults to "L2".
                Supported: "L2", "IP", "COSINE".
            vector_field (str, optional): Field name for dense vectors. Defaults to "dense_vector".
            id_max_length (int, optional): Maximum length for ID field. Defaults to 100.
            content_max_length (int, optional): Maximum length for content field. Defaults to 65535.
        '''
    @property
    def em_invoker(self) -> BaseEMInvoker:
        """Returns the EM Invoker instance.

        Returns:
            BaseEMInvoker: The EM Invoker instance.
        """
    async def ensure_index(self, index_type: str = 'IVF_FLAT', index_params: dict[str, Any] | None = None, query_field: str = 'content', **kwargs: Any) -> None:
        '''Ensure collection and vector index exist, creating them if necessary.

        This method is idempotent - if the collection and index already exist, it will skip
        creation and return early. Uses a lock to prevent race conditions when called
        concurrently from multiple coroutines.

        Args:
            index_type (str, optional): Index type. Defaults to "IVF_FLAT".
                Supported: "IVF_FLAT", "HNSW".
            index_params (dict[str, Any] | None, optional): Index-specific parameters.
                Defaults to None, in which case default parameters are used.
            query_field (str, optional): Field name for text content. Defaults to "content".
            **kwargs: Additional parameters.

        Raises:
            RuntimeError: If collection or index creation fails.
        '''
    async def create(self, data: Chunk | list[Chunk], **kwargs: Any) -> None:
        """Add chunks to the vector store with automatic embedding generation.

        Args:
            data (Chunk | list[Chunk]): Single chunk or list of chunks to add.
            **kwargs: Backend-specific parameters (e.g., partition_name).

        Raises:
            ValueError: If vector dimension mismatch occurs.
        """
    async def create_from_vector(self, chunk_vectors: list[tuple[Chunk, Vector]], **kwargs: Any) -> None:
        """Add pre-computed vectors directly.

        Args:
            chunk_vectors (list[tuple[Chunk, Vector]]): List of tuples containing chunks and their
                corresponding vectors.
            **kwargs: Backend-specific parameters (e.g., partition_name).

        Raises:
            ValueError: If vector dimension mismatch occurs.
        """
    async def retrieve(self, query: str, filters: FilterClause | QueryFilter | None = None, options: QueryOptions | None = None, **kwargs: Any) -> list[Chunk]:
        """Read records from the datastore using text-based similarity search with optional filtering.

        Args:
            query (str): Input text to embed and search with.
            filters (FilterClause | QueryFilter | None, optional): Query filters to apply.
                FilterClause objects are automatically converted to QueryFilter internally.
                Defaults to None.
            options (QueryOptions | None, optional): Query options like limit and sorting.
                Defaults to None.
            **kwargs: Backend-specific parameters (e.g., search_params).

        Returns:
            list[Chunk]: Query results ordered by similarity score.
        """
    async def retrieve_by_vector(self, vector: Vector, filters: FilterClause | QueryFilter | None = None, options: QueryOptions | None = None, search_params: dict[str, Any] | None = None, **kwargs: Any) -> list[Chunk]:
        """Direct vector similarity search.

        Args:
            vector (Vector): Query embedding vector.
            filters (FilterClause | QueryFilter | None, optional): Query filters to apply.
                FilterClause objects are automatically converted to QueryFilter internally.
                Defaults to None.
            options (QueryOptions | None, optional): Query options like limit and sorting.
                Defaults to None.
            search_params (dict[str, Any] | None, optional): Search parameters for Milvus.
                If None, default search parameters based on distance metric will be used.
                Defaults to None.
            **kwargs: Backend-specific parameters.

        Returns:
            list[Chunk]: List of chunks ordered by similarity score.
        """
    async def update(self, update_values: dict[str, Any], filters: FilterClause | QueryFilter | None = None, **kwargs: Any) -> None:
        """Update existing records in the datastore.

        Args:
            update_values (dict[str, Any]): Values to update. Supports content for updating document content
                and metadata for updating metadata. If content is updated, vectors are re-embedded.
            filters (FilterClause | QueryFilter | None, optional): Filters to select records to update.
                FilterClause objects are automatically converted to QueryFilter internally.
                Defaults to None.
            **kwargs: Backend-specific parameters (e.g., partition_name).

        Note:
            If filters is None, no operation is performed (no-op).
        """
    async def delete(self, filters: FilterClause | QueryFilter | None = None, **kwargs: Any) -> None:
        """Delete records from the datastore.

        Args:
            filters (FilterClause | QueryFilter | None, optional): Filters to select records to delete.
                FilterClause objects are automatically converted to QueryFilter internally.
                Defaults to None, in which case no operation is performed (no-op).
            **kwargs: Backend-specific parameters.

        Note:
            If filters is None, no operation is performed (no-op).
        """
    async def clear(self) -> None:
        """Clear all records from the datastore."""
