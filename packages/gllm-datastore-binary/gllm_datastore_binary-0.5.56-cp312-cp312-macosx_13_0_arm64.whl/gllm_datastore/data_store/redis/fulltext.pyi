from _typeshed import Incomplete
from gllm_core.schema.chunk import Chunk
from gllm_datastore.constants import CHUNK_KEYS as CHUNK_KEYS, DefaultBatchSize as DefaultBatchSize, FIELD_CONFIG_NAME as FIELD_CONFIG_NAME, FIELD_CONFIG_TYPE as FIELD_CONFIG_TYPE, FieldType as FieldType
from gllm_datastore.core.capabilities.encryption_capability import EncryptionCapability as EncryptionCapability
from gllm_datastore.core.filters import FilterClause as FilterClause, QueryFilter as QueryFilter, QueryOptions as QueryOptions
from gllm_datastore.data_store.redis.query import apply_options_to_query as apply_options_to_query, check_index_exists as check_index_exists, delete_keys_batched as delete_keys_batched, execute_search_query as execute_search_query, get_doc_ids_for_deletion as get_doc_ids_for_deletion, get_filterable_fields_from_index as get_filterable_fields_from_index, infer_filterable_fields_from_chunks as infer_filterable_fields_from_chunks, normalize_field_name_for_schema as normalize_field_name_for_schema, parse_redis_documents as parse_redis_documents, prepare_chunk_document as prepare_chunk_document, process_doc_ids_in_batches as process_doc_ids_in_batches, process_update_batch_with_encryption as process_update_batch_with_encryption, sanitize_key as sanitize_key, strip_index_prefix as strip_index_prefix, validate_chunk_content as validate_chunk_content, validate_chunk_list as validate_chunk_list, validate_metadata_fields as validate_metadata_fields
from gllm_datastore.data_store.redis.query_translator import RedisQueryTranslator as RedisQueryTranslator
from redis.asyncio.client import Redis
from typing import Any

FUZZY_MATCH_MAX_DISTANCE: int

class RedisFulltextCapability:
    """Redis implementation of FulltextCapability protocol.

    Attributes:
        index_name (str): Name of the Redis index.
        client (Redis): Redis client instance.
    """
    index_name: Incomplete
    client: Incomplete
    def __init__(self, index_name: str, client: Redis, encryption: EncryptionCapability | None = None) -> None:
        """Initialize the Redis fulltext capability.

        Schema will be automatically inferred from chunks when creating a new index,
        or auto-detected from an existing index when performing operations.

        Args:
            index_name (str): Name of the Redis index.
            client (Redis): Redis client instance.
            encryption (EncryptionCapability | None, optional): Encryption capability for field-level
                encryption. Defaults to None.
        """
    async def create(self, data: Chunk | list[Chunk]) -> None:
        '''Create new records in the datastore.

        This method will automatically encrypt the content and metadata of the chunks if encryption is enabled
        following the encryption configuration.

        If the index does not exist and no filterable_fields were provided,
        the schema will be inferred from the chunks being created.

        Examples:
            Create a new chunk.
            ```python
            await fulltext_capability.create(Chunk(content="Test chunk", metadata={"category": "test"}))
            ```

        Args:
            data (Chunk | list[Chunk]): Data to create (single item or collection).

        Raises:
            ValueError: If data structure is invalid or chunk content is invalid.
        '''
    async def retrieve(self, filters: FilterClause | QueryFilter | None = None, options: QueryOptions | None = None) -> list[Chunk]:
        """Read records from the datastore with optional filtering.

        Args:
            filters (FilterClause | QueryFilter | None, optional): Query filters to apply. Defaults to None.
            options (QueryOptions | None, optional): Query options for sorting and pagination. Defaults to None,
                in which case the default limit of 10 is used.

        Returns:
            list[Chunk]: List of matched chunks after applying filters and options.
        """
    async def retrieve_fuzzy(self, query: str, max_distance: int = 2, filters: FilterClause | QueryFilter | None = None, options: QueryOptions | None = None) -> list[Chunk]:
        """Find records that fuzzy match the query within distance threshold.

        Args:
            query (str): Text to fuzzy match against.
            max_distance (int): Maximum edit distance for matches. Defaults to 2.
                Maximum value is 3 (limitation of Redis Vector Search).
            filters (FilterClause | QueryFilter | None, optional): Optional metadata filters to apply.
                Defaults to None.
            options (QueryOptions | None, optional): Query options, only limit is used here. Defaults to None.

        Returns:
            list[Chunk]: Matched chunks ordered by relevance/distance.

        Raises:
            ValueError: If max_distance is greater than 3.

        Note:
            Maximum fuzzy distance is 3. This is a limitation of the Redis Search module.
        """
    async def update(self, update_values: dict[str, Any], filters: FilterClause | QueryFilter | None = None) -> None:
        '''Update existing records in the datastore.

        This method will automatically encrypt the content and metadata in update_values if encryption is enabled
        following the encryption configuration.

        Warning:
            Filters cannot target encrypted fields. While update_values are encrypted before
            being written, the filters used to identify which documents to update are NOT encrypted.
            If you try to update documents based on an encrypted metadata field (e.g.,
            `filters=F.eq("metadata.secret", "val")`), the filter will fail to match because
            the filter value is not encrypted but the stored data is. Always use non-encrypted
            fields (like \'id\') in filters when working with encrypted data.

        Processes updates in batches to avoid loading all matching documents into memory.
        1. Get document IDs matching the filters.
        2. In batch, get document data via document IDs.
        3. In batch, update the document data.

        Examples:
            Update certain metadata of a chunk with specific filters:
                ```python
                from gllm_datastore.core.filters import filter as F

                await fulltext_capability.update(
                    update_values={"metadata": {"status": "published"}},
                    filters=F.eq("id", "chunk_id"),
                )
                ```

            Update encrypted data (encryption must be enabled):
                ```python
                from gllm_datastore.core.filters import filter as F

                # Correct: Use non-encrypted \'id\' field in filter
                await fulltext_capability.update(
                    update_values={"metadata": {"secret_value": "new_secret"}},
                    filters=F.eq("id", "chunk_id")
                )

                # Incorrect: Using encrypted field in filter will fail to match
                # await fulltext_capability.update(
                #     update_values={"metadata": {"status": "published"}},
                #     filters=F.eq("metadata.secret_key", "value")  # Won\'t match!
                # )
                ```

        Args:
            update_values (dict[str, Any]): Mapping of fields to new values to apply.
            filters (FilterClause | QueryFilter | None, optional): Filters to select records to update.
                Cannot use encrypted fields in filters. Defaults to None.

        Raises:
            Exception: If Redis operations fail.
        '''
    async def delete(self, filters: FilterClause | QueryFilter | None = None, options: QueryOptions | None = None) -> None:
        """Delete records from the datastore.

        Processes deletions in batches to avoid loading all matching documents into memory.
        For delete operations, only document IDs are retrieved (not full content) to minimize memory usage.

        Args:
            filters (FilterClause | QueryFilter | None, optional): Filters to select records to delete.
                Defaults to None.
            options (QueryOptions | None, optional): Query options for sorting and limiting deletions
                (for eviction-like operations). Defaults to None.

        Raises:
            Exception: If Redis operations fail.
        """
    async def clear(self) -> None:
        """Clear all records from the datastore."""
