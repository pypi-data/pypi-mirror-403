from _typeshed import Incomplete
from gllm_datastore.core.filters.schema import FilterClause as FilterClause, QueryFilter as QueryFilter
from gllm_datastore.data_store.base import BaseDataStore as BaseDataStore, CapabilityType as CapabilityType
from gllm_datastore.data_store.milvus.fulltext import MilvusFulltextCapability as MilvusFulltextCapability
from gllm_datastore.data_store.milvus.query_translator import MilvusQueryTranslator as MilvusQueryTranslator
from gllm_datastore.data_store.milvus.vector import MilvusVectorCapability as MilvusVectorCapability
from typing import Any

DEFAULT_ID_MAX_LENGTH: int
DEFAULT_CONTENT_MAX_LENGTH: int

class MilvusDataStore(BaseDataStore):
    """Milvus data store with multiple capability support.

    Attributes:
        uri (str): Milvus connection URI.
        token (str | None): Authentication token for Milvus Cloud.
        collection_name (str): The name of the Milvus collection.
        timeout (int): Connection timeout in seconds.
        client (AsyncMilvusClient): The async Milvus client instance.
    """
    uri: Incomplete
    token: Incomplete
    collection_name: Incomplete
    timeout: Incomplete
    id_max_length: Incomplete
    content_max_length: Incomplete
    client: Incomplete
    def __init__(self, uri: str, collection_name: str, token: str | None = None, timeout: int = 30, id_max_length: int = ..., content_max_length: int = ...) -> None:
        '''Initialize the Milvus data store.

        Args:
            uri (str): Milvus connection URI (e.g., "http://localhost:19530").
            collection_name (str): Collection name.
            token (str | None, optional): Authentication token for Milvus Cloud. Defaults to None.
            timeout (int, optional): Connection timeout in seconds. Defaults to 30.
            id_max_length (int, optional): Maximum length for ID field. Defaults to 100.
            content_max_length (int, optional): Maximum length for content field. Defaults to 65535.
        '''
    @property
    def supported_capabilities(self) -> list[CapabilityType]:
        """Return list of currently supported capabilities.

        Returns:
            list[CapabilityType]: List of capability names that are supported.
        """
    async def get_size(self, filters: FilterClause | QueryFilter | None = None) -> int:
        '''Get the total number of records in the datastore.

        Examples:
            1) Basic usage (no filters):
                ```python
                count = await datastore.get_size()
                ```

            2) With filters (using Query Filters):
                ```python
                from gllm_datastore.core.filters import filter as F
                count = await datastore.get_size(filters=F.eq("metadata.status", "active"))
                ```

        Args:
            filters (FilterClause | QueryFilter | None, optional): Query filters to apply.
                FilterClause objects are automatically converted to QueryFilter internally.
                Defaults to None.

        Returns:
            int: The total number of records matching the filters.

        Raises:
            RuntimeError: If the operation fails.
        '''
    @property
    def fulltext(self) -> MilvusFulltextCapability:
        """Access fulltext capability if supported.

        This method uses the logic of its parent class to return the fulltext capability handler.
        This method overrides the parent class to return the MilvusFulltextCapability handler for better
        type hinting.

        Returns:
            MilvusFulltextCapability: Fulltext capability handler.

        Raises:
            NotSupportedException: If fulltext capability is not supported.
        """
    @property
    def vector(self) -> MilvusVectorCapability:
        """Access vector capability if supported.

        This method uses the logic of its parent class to return the vector capability handler.
        This method overrides the parent class to return the MilvusVectorCapability handler for better
        type hinting.

        Returns:
            MilvusVectorCapability: Vector capability handler.

        Raises:
            NotSupportedException: If vector capability is not supported.
        """
    def with_fulltext(self, collection_name: str | None = None, query_field: str = 'content') -> MilvusDataStore:
        '''Configure fulltext capability and return datastore instance.

        This method uses the logic of its parent class to configure the fulltext capability.
        This method overrides the parent class for better type hinting.

        Args:
            collection_name (str | None, optional): Override collection name. Defaults to None,
                in which case the default class attribute will be utilized.
            query_field (str, optional): Field name for text content. Defaults to "content".

        Returns:
            MilvusDataStore: Self for method chaining.
        '''
    def with_vector(self, em_invoker: Any, collection_name: str | None = None, dimension: int | None = None, distance_metric: str = 'L2', vector_field: str = 'dense_vector', index_type: str = 'IVF_FLAT', index_params: dict[str, Any] | None = None, query_field: str = 'content') -> MilvusDataStore:
        '''Configure vector capability and return datastore instance.

        This method uses the logic of its parent class to configure the vector capability.
        This method overrides the parent class for better type hinting.

        Args:
            em_invoker (BaseEMInvoker): Embedding model invoker (required).
            collection_name (str | None, optional): Override collection name. Defaults to None,
                in which case the default class attribute will be utilized.
            dimension (int | None, optional): Vector dimension. Required if collection doesn\'t exist.
            distance_metric (str, optional): Distance metric. Defaults to "L2".
                Supported: "L2", "IP", "COSINE".
            vector_field (str, optional): Field name for dense vectors. Defaults to "dense_vector".
            index_type (str, optional): Index type. Defaults to "IVF_FLAT".
                Supported: "IVF_FLAT", "HNSW".
            index_params (dict[str, Any] | None, optional): Index-specific parameters.
                Defaults to None, in which case default parameters are used.
            query_field (str, optional): Field name for text content. Defaults to "content".

        Returns:
            MilvusDataStore: Self for method chaining.
        '''
    @classmethod
    def translate_query_filter(cls, query_filter: FilterClause | QueryFilter | None = None) -> str | None:
        '''Translate QueryFilter or FilterClause to Milvus expression syntax.

        This method uses MilvusQueryTranslator to translate filters and returns
        the result as a Milvus expression string.

        Examples:
            1. Translate a simple FilterClause:
                ```python
                from gllm_datastore.core.filters import filter as F

                filter_clause = F.eq("metadata.status", "active")
                result = MilvusDataStore.translate_query_filter(filter_clause)
                # result -> \'metadata["status"] == "active"\'
                ```

            2. Translate QueryFilter with metadata filters:
                ```python
                from gllm_datastore.core.filters import filter as F

                filters = F.and_(
                    F.eq("metadata.category", "tech"),
                    F.gte("metadata.price", 100),
                )
                result = MilvusDataStore.translate_query_filter(filters)
                # result -> \'(metadata["category"] == "tech" and metadata["price"] >= 100)\'
                ```

        Args:
            query_filter (FilterClause | QueryFilter | None, optional): The filter to translate.
                Can be a single FilterClause, a QueryFilter with multiple clauses. Defaults to None.

        Returns:
            str | None: The translated filter as a Milvus expression string.
                Returns None for empty filters.
        '''
