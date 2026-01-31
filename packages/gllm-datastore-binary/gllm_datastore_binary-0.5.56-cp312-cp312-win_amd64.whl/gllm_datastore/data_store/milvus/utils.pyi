from gllm_core.schema import Chunk
from gllm_datastore.constants import CHUNK_KEYS as CHUNK_KEYS
from pymilvus import AsyncMilvusClient
from typing import Any

def get_sort_value(chunk: Chunk, order_by: str) -> Any:
    '''Get the value to sort by from a chunk.

    Args:
        chunk (Chunk): Chunk to get the value from.
        order_by (str): The field to sort by (e.g., "id", "content", "score", "metadata.key").

    Returns:
        Any: The value to sort by, or None if not found.
    '''
def get_nested_value(obj: dict[str, Any], key_path: str) -> Any:
    '''Get a nested value from a dictionary using dot notation.

    Args:
        obj (dict[str, Any]): Dictionary to traverse.
        key_path (str): Dot-separated path to the value (e.g., "user.profile.name").

    Returns:
        Any: The value at the specified path, or None if not found.
    '''
def extract_entity_field(entity: Any, field_name: str, default: Any) -> Any:
    """Extract field from entity with standardized access pattern.

    This utility function handles both object attribute access and dictionary access
    for Milvus entity objects.

    Args:
        entity (Any): Entity object from Milvus search result.
        field_name (str): Name of the field to extract.
        default (Any): Default value if field not found.

    Returns:
        Any: Field value or default.
    """
def prepare_metadata_updates(update_values: dict[str, Any]) -> dict[str, Any]:
    """Prepare metadata updates from update_values dictionary.

    Extracts metadata updates from update_values, handling both explicit
    CHUNK_KEYS.METADATA key and direct metadata field updates. This function
    unifies the metadata update logic used across vector and fulltext capabilities.

    Args:
        update_values (dict[str, Any]): Values to update.

    Returns:
        dict[str, Any]: Combined metadata updates dictionary.
    """
def merge_metadata(current: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """Merge metadata updates into current metadata.

    Args:
        current (dict[str, Any]): Current metadata dictionary.
        updates (dict[str, Any]): Updates to apply.

    Returns:
        dict[str, Any]: Merged metadata dictionary.
    """
def create_base_schema(client: AsyncMilvusClient, query_field: str, id_max_length: int, content_max_length: int) -> Any:
    """Create base Milvus collection schema with common fields.

    This function creates the base schema with id, query_field, and metadata fields.
    Vector field should be added separately if needed.

    Args:
        client (AsyncMilvusClient): Milvus client instance.
        query_field (str): Field name for text content.
        id_max_length (int): Maximum length for ID field.
        content_max_length (int): Maximum length for content field.

    Returns:
        Schema: Base schema object.

    Raises:
        RuntimeError: If schema creation fails.
    """
