from _typeshed import Incomplete
from gllm_datastore.constants import DEFAULT_REQUEST_TIMEOUT as DEFAULT_REQUEST_TIMEOUT
from gllm_datastore.core.capabilities.encryption_capability import EncryptionCapability as EncryptionCapability
from gllm_datastore.core.filters.schema import FilterClause as FilterClause, QueryFilter as QueryFilter
from gllm_datastore.data_store._elastic_core.client_factory import EngineType as EngineType, create_client as create_client
from gllm_datastore.data_store._elastic_core.elastic_like_core import ElasticLikeCore as ElasticLikeCore
from gllm_datastore.data_store.base import BaseDataStore as BaseDataStore, CapabilityType as CapabilityType
from gllm_datastore.data_store.opensearch.fulltext import OpenSearchFulltextCapability as OpenSearchFulltextCapability
from gllm_datastore.data_store.opensearch.query_translator import OpenSearchQueryTranslator as OpenSearchQueryTranslator
from gllm_datastore.data_store.opensearch.vector import OpenSearchVectorCapability as OpenSearchVectorCapability
from gllm_datastore.encryptor.encryptor import BaseEncryptor as BaseEncryptor
from gllm_inference.em_invoker.em_invoker import BaseEMInvoker
from opensearchpy import AsyncOpenSearch
from typing import Any

class OpenSearchDataStore(BaseDataStore):
    '''OpenSearch data store with multiple capability support.

    This is the explicit public API for OpenSearch. Users know they\'re
    using OpenSearch, not a generic "elastic-like" datastore.

    Attributes:
        engine (str): Always "opensearch" for explicit identification.
            This attribute ensures users know they\'re using OpenSearch, not a generic
            "elastic-like" datastore.
        index_name (str): The name of the OpenSearch index.
        client (AsyncOpenSearch): AsyncOpenSearch client.
    '''
    engine: str
    client: Incomplete
    index_name: Incomplete
    def __init__(self, index_name: str, client: AsyncOpenSearch | None = None, url: str | None = None, cloud_id: str | None = None, api_key: str | None = None, username: str | None = None, password: str | None = None, request_timeout: int = ..., connection_params: dict[str, Any] | None = None) -> None:
        '''Initialize the OpenSearch data store.

        Args:
            index_name (str): The name of the OpenSearch index to use for operations.
                This index name will be used for all queries and operations.
            client (AsyncOpenSearch | None, optional): Pre-configured OpenSearch client instance.
                If provided, it will be used instead of creating a new client from url/cloud_id.
                Must be an instance of AsyncOpenSearch. Defaults to None.
            url (str | None, optional): The URL of the OpenSearch server.
                For example, "http://localhost:9200". Either url or cloud_id must be provided
                if client is None. Defaults to None.
            cloud_id (str | None, optional): The cloud ID of the OpenSearch cluster.
                Used for OpenSearch Service connections. Either url or cloud_id must be provided
                if client is None. Defaults to None.
            api_key (str | None, optional): The API key for authentication.
                If provided, will be used for authentication. Mutually exclusive with username/password.
                Defaults to None.
            username (str | None, optional): The username for basic authentication.
                Must be provided together with password. Mutually exclusive with api_key.
                Defaults to None.
            password (str | None, optional): The password for basic authentication.
                Must be provided together with username. Mutually exclusive with api_key.
                Defaults to None.
            request_timeout (int, optional): The request timeout in seconds.
                Defaults to DEFAULT_REQUEST_TIMEOUT.
            connection_params (dict[str, Any] | None, optional): Additional connection parameters
                for OpenSearch client. These will be merged with automatically detected parameters
                (authentication, SSL settings). User-provided params take precedence. Defaults to None.
                Available parameters include:
                1. http_auth (tuple[str, str] | None): HTTP authentication tuple (username, password).
                2. use_ssl (bool): Whether to use SSL/TLS. Defaults to True for HTTPS URLs.
                3. verify_certs (bool): Whether to verify SSL certificates. Defaults to True for HTTPS URLs.
                    Set to False to use self-signed certificates (not recommended for production).
                4. ssl_show_warn (bool): Whether to show SSL warnings. Defaults to True for HTTPS URLs.
                5. ssl_assert_hostname (str | None): SSL hostname assertion. Defaults to None.
                6. max_retries (int): Maximum number of retries for requests. Defaults to 3.
                7. retry_on_timeout (bool): Whether to retry on timeouts. Defaults to True.
                8. client_cert (str | None): Path to the client certificate file. Defaults to None.
                9. client_key (str | None): Path to the client private key file. Defaults to None.
                10. root_cert (str | None): Path to the root certificate file. Defaults to None.
                11. Additional kwargs: Any other parameters accepted by OpenSearch client constructor.

        Raises:
            ValueError: If neither url nor cloud_id is provided when client is None.
            TypeError: If client is provided but is not an instance of AsyncOpenSearch.
        '''
    @property
    def supported_capabilities(self) -> list[str]:
        """Return list of currently supported capabilities.

        Returns:
            list[str]: List of capability names that are supported.
                Currently returns [CapabilityType.FULLTEXT, CapabilityType.VECTOR].
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
            filters (FilterClause | QueryFilter | None, optional): Query filters to apply.

        Returns:
            int: The total number of records matching the filters.
        '''
    @property
    def fulltext(self) -> OpenSearchFulltextCapability:
        """Access fulltext capability if supported.

        This method uses the logic of its parent class to return the fulltext capability handler.
        This method overrides the parent class to return the OpenSearchFulltextCapability handler for better
        type hinting.

        Returns:
            OpenSearchFulltextCapability: Fulltext capability handler.

        Raises:
            NotSupportedException: If fulltext capability is not supported.
        """
    @property
    def vector(self) -> OpenSearchVectorCapability:
        """Access vector capability if supported.

        This method uses the logic of its parent class to return the vector capability handler.
        This method overrides the parent class to return the OpenSearchVectorCapability handler for better
        type hinting.

        Returns:
            OpenSearchVectorCapability: Vector capability handler.

        Raises:
            NotSupportedException: If vector capability is not supported.
        """
    def with_fulltext(self, index_name: str | None = None, query_field: str = 'text') -> OpenSearchDataStore:
        '''Configure fulltext capability and return datastore instance.

        Overrides parent for better type hinting.

        Args:
            index_name (str | None, optional): Index name for fulltext operations.
                Uses datastore\'s default if None. Defaults to None.
            query_field (str, optional): Field name for text queries. Defaults to "text".

        Returns:
            OpenSearchDataStore: Self for method chaining.
        '''
    def with_encryption(self, encryptor: BaseEncryptor, fields: set[str] | list[str]) -> OpenSearchDataStore:
        """Enable encryption for specified fields.

        Note:
            Encrypted fields (content and metadata fields specified in encryption configuration)
            must be serializable to strings. Non-string values will be converted to strings
            before encryption.

        Warning:
            When encryption is enabled for fields, some search and filter operations may be
            limited or broken. Encrypted fields cannot be used in filters for update or delete
            operations, as the filter values are not encrypted and will not match the encrypted
            data stored in the index. Use non-encrypted fields (like 'id') for filtering when
            working with encrypted data.

        Args:
            encryptor (BaseEncryptor): The encryptor instance to use. Must not be None.
            fields (set[str] | list[str]): Set or list of field names to encrypt. Must not be empty.

        Returns:
            OpenSearchDataStore: Self for method chaining.

        Raises:
            ValueError: If encryptor is None or fields is empty.
        """
    def with_vector(self, em_invoker: BaseEMInvoker, index_name: str | None = None, query_field: str = 'text', vector_query_field: str = 'vector', retrieval_strategy: Any = None, distance_strategy: str | None = None) -> OpenSearchDataStore:
        '''Configure vector capability and return datastore instance.

        Overrides parent for better type hinting.

        Args:
            em_invoker (BaseEMInvoker): Embedding model for vectorization.
            index_name (str | None, optional): Index name. Uses datastore\'s default if None.
            query_field (str, optional): Field name for text queries. Defaults to "text".
            vector_query_field (str, optional): Field name for vector queries. Defaults to "vector".
            retrieval_strategy: Not used (kept for API compatibility). Defaults to None.
            distance_strategy (str | None, optional): Distance strategy (e.g., "l2", "cosine"). Defaults to None.

        Returns:
            OpenSearchDataStore: Self for method chaining.

        Note:
            Connection parameters are configured at the data store level during initialization.
            See OpenSearchDataStore.__init__ for connection_params details.
        '''
    @classmethod
    def translate_query_filter(cls, query_filter: FilterClause | QueryFilter, **kwargs: Any) -> dict[str, Any] | None:
        """Translate QueryFilter or FilterClause to OpenSearch native filter syntax.

        This method delegates to the OpenSearchQueryTranslator and returns the result as a dictionary.

        Args:
            query_filter (FilterClause | QueryFilter): The filter to translate.
                Can be a single FilterClause, a QueryFilter with multiple clauses and logical conditions.
                FilterClause objects are automatically converted to QueryFilter.
            **kwargs: Additional parameters (unused, kept for compatibility with base class).

        Returns:
            dict[str, Any] | None: The translated filter as an OpenSearch DSL dictionary.
                Returns None for empty filters.
                The dictionary format matches OpenSearch Query DSL syntax.
        """
