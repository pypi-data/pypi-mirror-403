from _typeshed import Incomplete
from gllm_core.schema import Chunk
from gllm_datastore.constants import CHUNK_KEYS as CHUNK_KEYS, DEFAULT_FETCH_K as DEFAULT_FETCH_K, DEFAULT_TOP_K as DEFAULT_TOP_K
from gllm_datastore.core.capabilities.encryption_capability import EncryptionCapability as EncryptionCapability
from gllm_datastore.core.filters.schema import FilterClause as FilterClause, QueryFilter as QueryFilter, QueryOptions as QueryOptions
from gllm_datastore.data_store._elastic_core.elastic_like_core import ElasticLikeCore as ElasticLikeCore
from gllm_datastore.data_store._elastic_core.query_translator import convert_filter_clause as convert_filter_clause
from gllm_datastore.data_store.opensearch.query import delete_by_id as delete_by_id, delete_by_query as delete_by_query, update_by_query as update_by_query
from gllm_datastore.data_store.opensearch.query_translator import OpenSearchQueryTranslator as OpenSearchQueryTranslator
from gllm_datastore.utils.converter import from_langchain as from_langchain, to_langchain as to_langchain
from gllm_inference.em_invoker.em_invoker import BaseEMInvoker
from gllm_inference.schema import Vector
from opensearchpy import AsyncOpenSearch
from typing import Any

class OpenSearchVectorCapability:
    """OpenSearch implementation of VectorCapability protocol.

    This class provides document CRUD operations and vector search using OpenSearch.
    Uses LangChain's OpenSearchVectorSearch for create and retrieve operations,
    and direct OpenSearch client for update and delete operations.

    Attributes:
        index_name (str): The name of the OpenSearch index.
        vector_store (OpenSearchVectorSearch): The vector store instance.
        client (AsyncOpenSearch): AsyncOpenSearch client for direct operations.
        em_invoker (BaseEMInvoker): The embedding model to perform vectorization.
    """
    index_name: Incomplete
    client: Incomplete
    query_field: Incomplete
    vector_query_field: Incomplete
    vector_store: Incomplete
    def __init__(self, index_name: str, em_invoker: BaseEMInvoker, client: AsyncOpenSearch, opensearch_url: str | None = None, query_field: str = 'text', vector_query_field: str = 'vector', retrieval_strategy: Any = None, distance_strategy: str | None = None, connection_params: dict[str, Any] | None = None, encryption: EncryptionCapability | None = None) -> None:
        '''Initialize the OpenSearch vector capability.

        OpenSearchVectorSearch creates its own sync and async clients internally
        based on the provided connection parameters. The async client is used
        for operations like update, delete, and clear.

        Args:
            index_name (str): The name of the OpenSearch index.
            em_invoker (BaseEMInvoker): The embedding model to perform vectorization.
            client (AsyncOpenSearch): The OpenSearch client for direct operations.
            opensearch_url (str | None, optional): The URL of the OpenSearch server.
                Used for LangChain\'s OpenSearchVectorSearch initialization.
                If None, will be extracted from client connection info. Defaults to None.
            query_field (str, optional): The field name for text queries. Defaults to "text".
            vector_query_field (str, optional): The field name for vector queries. Defaults to "vector".
            retrieval_strategy: Not used with OpenSearchVectorSearch (kept for API compatibility).
            distance_strategy (str | None, optional): The distance strategy for retrieval.
                For example, "l2" for Euclidean distance, "l2squared" for squared Euclidean distance,
                "cosine" for cosine similarity, etc. Defaults to None.
            connection_params (dict[str, Any] | None, optional): Additional connection parameters
                to override defaults. These will be merged with automatically detected parameters
                (authentication, SSL settings). User-provided params take precedence. Defaults to None.
                Available parameters include:
                1. http_auth (tuple[str, str] | None): HTTP authentication tuple (username, password).
                2. use_ssl (bool): Whether to use SSL/TLS. Defaults to True for HTTPS URLs.
                3. verify_certs (bool): Whether to verify SSL certificates. Defaults to True for HTTPS URLs.
                4. ssl_show_warn (bool): Whether to show SSL warnings. Defaults to True for HTTPS URLs.
                5. ssl_assert_hostname (str | None): SSL hostname assertion. Defaults to None.
                6. max_retries (int): Maximum number of retries for requests. Defaults to 3.
                7. retry_on_timeout (bool): Whether to retry on timeouts. Defaults to True.
                8. client_cert (str | None): Path to the client certificate file. Defaults to None.
                9. client_key (str | None): Path to the client private key file. Defaults to None.
                10. root_cert (str | None): Path to the root certificate file. Defaults to None.
                11. Additional kwargs: Any other parameters accepted by OpenSearch client constructor.
            encryption (EncryptionCapability | None, optional): Encryption capability for field-level
                encryption. Defaults to None.
        '''
    @property
    def em_invoker(self) -> BaseEMInvoker:
        """Returns the EM Invoker instance.

        Returns:
            BaseEMInvoker: The EM Invoker instance.
        """
    async def ensure_index(self, mapping: dict[str, Any] | None = None, index_settings: dict[str, Any] | None = None, dimension: int | None = None, distance_strategy: str | None = None) -> None:
        '''Ensure OpenSearch index exists, creating it if necessary.

        This method is idempotent - if the index already exists, it will skip creation
        and return early.

        Args:
            mapping (dict[str, Any] | None, optional): Custom mapping dictionary to use
                for index creation. If provided, this mapping will be used directly.
                The mapping should follow OpenSearch mapping format. Defaults to None,
                in which default mapping will be used.
            index_settings (dict[str, Any] | None, optional): Custom index settings.
                These settings will be merged with any default settings. Defaults to None.
            dimension (int | None, optional): Vector dimension. If not provided and mapping
                is not provided, will be inferred from em_invoker by generating a test embedding.
            distance_strategy (str | None, optional): Distance strategy for vector similarity.
                Supported values: "l2", "l2squared", "cosine", "innerproduct", etc.
                Only used when building default mapping. Defaults to "l2" if not specified.

        Raises:
            ValueError: If mapping is invalid or required parameters are missing.
            RuntimeError: If index creation fails.
        '''
    async def create(self, data: Chunk | list[Chunk], **kwargs: Any) -> None:
        '''Create new records in the datastore.

        This method will automatically encrypt the content and metadata of the chunks if encryption is enabled
        following the encryption configuration. When encryption is enabled, embeddings are generated from
        plaintext first, then chunks are encrypted, ensuring that embeddings represent the original content
        rather than encrypted ciphertext.

        Examples:
            ```python
            from gllm_datastore.core.filters import filter as F

            # Create a single chunk
            await vector_capability.create(data=Chunk(content="Hello, world!", metadata={"source": "test"}))
            ```

        Args:
            data (Chunk | list[Chunk]): Data to create (single item or collection).
            **kwargs: Datastore-specific parameters.

        Raises:
            ValueError: If data structure is invalid.
        '''
    async def create_from_vector(self, chunk_vectors: list[tuple[Chunk, Vector]], **kwargs: Any) -> list[str]:
        '''Add pre-computed embeddings directly.

        This method will automatically encrypt the content and metadata of the chunks if encryption is enabled
        following the encryption configuration.

        Examples:
            ```python
            from gllm_datastore.core.filters import filter as F

            # Create a single chunk
            await vector_capability.create_from_vector(
                chunk_vectors=[
                    (Chunk(content="Hello, world!", metadata={"source": "test"}), Vector([0.1, 0.2, 0.3])),
                    (Chunk(content="Hello, another world!", metadata={"source": "test"}), Vector([0.4, 0.5, 0.6])),
                ]
            )
            ```

        Args:
            chunk_vectors (list[tuple[Chunk, Vector]]): List of tuples containing chunks and their
                corresponding vectors.
            **kwargs: Datastore-specific parameters.

        Returns:
            list[str]: List of IDs of the added documents.
        '''
    async def retrieve(self, query: str, filters: FilterClause | QueryFilter | None = None, options: QueryOptions | None = None, **kwargs: Any) -> list[Chunk]:
        '''Semantic search using text query converted to vector.

        This method will automatically decrypt the content and metadata of the chunks if encryption is enabled
        following the encryption configuration.

        Warning:
            Filters cannot target encrypted fields. If you try to filter by an encrypted metadata
            field (e.g., `filters=F.eq("metadata.secret", "val")`), the filter will fail to match
            because the filter value is not encrypted but the stored data is. Always use non-encrypted
            fields in filters when working with encrypted data.

        Examples:
            ```python
            from gllm_datastore.core.filters import filter as F

            # Direct FilterClause usage - using non-encrypted field
            await vector_capability.retrieve(
                query="What is the capital of France?",
                filters=F.eq("id", "document_id"),
                options=QueryOptions(limit=10),
            )

            # Multiple filters - using non-encrypted fields
            filters = F.and_(F.eq("id", "doc1"), F.eq("id", "doc2"))
            await vector_capability.retrieve(query="What is the capital of France?", filters=filters)
            ```

        Args:
            query (str): Text query to embed and search for.
            filters (FilterClause | QueryFilter | None, optional): Filters to apply to the search.
                FilterClause objects are automatically converted to QueryFilter internally.
                Cannot use encrypted fields in filters. Defaults to None.
            options (QueryOptions | None, optional): Options to apply to the search. Defaults to None.
            **kwargs: Datastore-specific parameters.

        Returns:
            list[Chunk]: List of chunks ordered by relevance score.
        '''
    async def retrieve_by_vector(self, vector: Vector, filters: FilterClause | QueryFilter | None = None, options: QueryOptions | None = None, **kwargs: Any) -> list[Chunk]:
        '''Direct vector similarity search.

        Warning:
            Filters cannot target encrypted fields. If you try to filter by an encrypted metadata
            field (e.g., `filters=F.eq("metadata.secret", "val")`), the filter will fail to match
            because the filter value is not encrypted but the stored data is. Always use non-encrypted
            fields in filters when working with encrypted data.

        Examples:
            ```python
            from gllm_datastore.core.filters import filter as F

            # Direct FilterClause usage - using non-encrypted field
            await vector_capability.retrieve_by_vector(
                vector=[0.1, 0.2, 0.3],
                filters=F.eq("id", "document_id"),
                options=QueryOptions(limit=10),
            )

            # Multiple filters - using non-encrypted fields
            filters = F.and_(F.eq("id", "doc1"), F.eq("id", "doc2"))
            await vector_capability.retrieve_by_vector(vector=[0.1, 0.2, 0.3], filters=filters)
            ```

        Args:
            vector (Vector): Query embedding vector.
            filters (FilterClause | QueryFilter | None, optional): Filters to apply to the search.
                FilterClause objects are automatically converted to QueryFilter internally.
                Cannot use encrypted fields in filters. Defaults to None.
            options (QueryOptions | None, optional): Options to apply to the search. Defaults to None.
            **kwargs: Datastore-specific parameters.

        Returns:
            list[Chunk]: List of chunks ordered by similarity score.
        '''
    async def update(self, update_values: dict[str, Any], filters: FilterClause | QueryFilter | None = None, **kwargs: Any) -> None:
        '''Update existing records in the datastore.

        This method will automatically encrypt the content and metadata in update_values if encryption is enabled
        following the encryption configuration.

        Warning:
            Filters cannot target encrypted fields. While update_values are encrypted before
            being written, the filters used to identify which documents to update are NOT encrypted.
            If you try to update documents based on an encrypted metadata field (e.g.,
            `filters=F.eq("metadata.secret", "val")`), the filter will fail to match because
            the filter value is not encrypted but the stored data is. Always use non-encrypted
            fields (like "id") in filters when working with encrypted data.

        Examples:
            ```python
            from gllm_datastore.core.filters import filter as F

            # Update content - using non-encrypted field for filter
            await vector_capability.update(
                update_values={"content": "new_content"},
                filters=F.eq("id", "unique_id"),
            )

            # Update metadata - using non-encrypted field for filter
            await vector_capability.update(
                update_values={"metadata": {"status": "published"}},
                filters=F.eq("id", "unique_id"),
            )
            ```

        Args:
            update_values (dict[str, Any]): Values to update.
            filters (FilterClause | QueryFilter | None, optional): Filters to select records to update.
                FilterClause objects are automatically converted to QueryFilter internally.
                Cannot use encrypted fields in filters. Defaults to None.
            **kwargs: Datastore-specific parameters.
        '''
    async def delete(self, filters: FilterClause | QueryFilter | None = None, **kwargs: Any) -> None:
        '''Delete records from the data store based on filters.

        Warning:
            Filters cannot target encrypted fields. If you try to delete documents based on
            an encrypted metadata field (e.g., filters=F.eq("metadata.secret", "val")), the
            filter will fail to match because the filter value is not encrypted but the stored
            data is. Always use non-encrypted fields (like \'id\') in filters when working with
            encrypted data.

        Examples:
            ```python
            from gllm_datastore.core.filters import filter as F

            # Delete a single chunk
            await vector_capability.delete(filters=F.eq("id", "document_id"))
            ```

        Args:
            filters (FilterClause | QueryFilter | None, optional): Filters to select records for deletion.
                FilterClause objects are automatically converted to QueryFilter internally.
                Cannot use encrypted fields in filters. Defaults to None.
            **kwargs: Datastore-specific parameters.
        '''
    async def delete_by_id(self, id: str | list[str], **kwargs: Any) -> None:
        '''Delete records from the data store based on IDs.

        Examples:
            ```python
            from gllm_datastore.core.filters import filter as F

            # Delete a single chunk
            await vector_capability.delete_by_id(id="document_id")
            ```

        Args:
            id (str | list[str]): ID or list of IDs to delete.
            **kwargs: Datastore-specific parameters.
        '''
    async def clear(self, **kwargs: Any) -> None:
        """Clear all records from the datastore.

        Examples:
            ```python
            from gllm_datastore.core.filters import filter as F

            # Clear all chunks
            await vector_capability.clear()
            ```

        Args:
            **kwargs: Datastore-specific parameters.
        """
