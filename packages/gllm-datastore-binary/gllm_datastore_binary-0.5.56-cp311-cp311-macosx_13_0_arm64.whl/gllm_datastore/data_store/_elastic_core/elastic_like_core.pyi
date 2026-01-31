from _typeshed import Incomplete
from elasticsearch import AsyncElasticsearch
from elasticsearch.dsl import AttrDict as ESAttrDict
from gllm_core.schema import Chunk
from gllm_datastore.constants import CHUNK_KEYS as CHUNK_KEYS, METADATA_KEYS as METADATA_KEYS
from gllm_datastore.core.capabilities.encryption_capability import EncryptionCapability as EncryptionCapability
from gllm_datastore.data_store._elastic_core.constants import ELASTIC_RESPONSE_KEYS as ELASTIC_RESPONSE_KEYS
from opensearchpy import AsyncOpenSearch
from opensearchpy.helpers.utils import AttrDict as OSAttrDict
from typing import Any

AttrDict = ESAttrDict | OSAttrDict

class ElasticLikeCore:
    """Shared core implementation for Elasticsearch-like datastores.

    This class contains the common logic shared between Elasticsearch and OpenSearch.
    Product-specific datastores delegate to this core and override methods where needed.

    Attributes:
        index_name (str): The name of the index used for all operations.
        client (AsyncElasticsearch | AsyncOpenSearch): The Elasticsearch or OpenSearch client.
            Used for all index and document operations.
        _logger (Logger): Logger instance for this core. Used for logging operations and errors.
    """
    index_name: Incomplete
    client: Incomplete
    def __init__(self, index_name: str, client: AsyncElasticsearch | AsyncOpenSearch, encryption: EncryptionCapability | None = None) -> None:
        """Initialize the shared core.

        Args:
            index_name (str): The name of the index to use for operations.
                This index name will be used for all queries and operations.
            client (AsyncElasticsearch | AsyncOpenSearch): The Elasticsearch or OpenSearch client.
                Must be a properly configured async client instance.
            encryption (EncryptionCapability | None, optional): Encryption capability for field-level encryption.
                Defaults to None.
        """
    async def check_index_exists(self) -> bool:
        """Check if index exists.

        Returns:
            bool: True if the index exists, False otherwise.
        """
    async def get_index_count(self) -> int:
        """Get document count for the index.

        Returns:
            int: The total number of documents in the index.
        """
    async def get_index_count_with_filters(self, query: dict[str, Any] | None = None) -> int:
        """Get document count for the index with optional query filters.

        Args:
            query (dict[str, Any] | None, optional): Elasticsearch/OpenSearch query DSL.
                If None, returns total count. Defaults to None.

        Returns:
            int: The total number of documents matching the query.
        """
    async def create_chunks(self, data: Chunk | list[Chunk], query_field: str = ..., **kwargs: Any) -> None:
        """Create new records in the datastore using bulk API.

        Args:
            data (Chunk | list[Chunk]): Data to create (single item or collection).
            query_field (str, optional): The field name to use for text content. Defaults to CHUNK_KEYS.TEXT.
            **kwargs: Backend-specific parameters forwarded to bulk API.

        Raises:
            ValueError: If data structure is invalid.
        """
    def create_chunks_from_hits(self, hits: list[AttrDict], query_field: str = ...) -> list[Chunk]:
        """Create Chunk objects from Elasticsearch/OpenSearch hits.

        This method processes hits from Elasticsearch/OpenSearch DSL responses where hits are AttrDict
        objects (from elasticsearch.dsl or opensearchpy.helpers.utils). The _source field is accessed via
        attribute access and is always an AttrDict (nested dicts are automatically wrapped by _wrap function).

        Args:
            hits (list[AttrDict]): List of Elasticsearch/OpenSearch hits as AttrDict objects.
            query_field (str, optional): The field name to use for text content. Defaults to CHUNK_KEYS.TEXT.

        Returns:
            list[Chunk]: List of Chunk objects with decrypted fields if encryption is enabled.
        """
    @staticmethod
    def extract_response_suggestions(response: dict[str, Any], suggestion_key: str) -> list[str]:
        """Extract suggestions from Elasticsearch/OpenSearch autocomplete response.

        Args:
            response (dict[str, Any]): Elasticsearch/OpenSearch response.
            suggestion_key (str): The suggestion key in the response.

        Returns:
            list[str]: List of suggestions.
        """
    @staticmethod
    def extract_aggregation_buckets(response: dict[str, Any], aggregation_name: str) -> list[str]:
        """Extract bucket keys from Elasticsearch/OpenSearch aggregation response.

        Args:
            response (dict[str, Any]): Elasticsearch/OpenSearch response.
            aggregation_name (str): The aggregation name in the response.

        Returns:
            list[str]: List of bucket keys.
        """
    @staticmethod
    def extract_highlighted_text(response: dict[str, Any], field: str) -> list[str]:
        """Extract highlighted text from Elasticsearch/OpenSearch response.

        Args:
            response (dict[str, Any]): Elasticsearch/OpenSearch response.
            field (str): The field name to extract highlights from.

        Returns:
            list[str]: List of unique highlighted text snippets.
        """
    def validate_bm25_parameters(self, k1: float | None, b: float | None) -> bool:
        """Validate BM25 parameters.

        Args:
            k1 (float | None): BM25 parameter controlling term frequency saturation.
            b (float | None): BM25 parameter controlling document length normalization.

        Returns:
            bool: True if parameters are valid, False otherwise.
        """
