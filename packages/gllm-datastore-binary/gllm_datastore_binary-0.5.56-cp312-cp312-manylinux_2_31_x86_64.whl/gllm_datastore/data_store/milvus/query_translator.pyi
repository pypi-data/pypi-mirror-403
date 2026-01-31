from _typeshed import Incomplete
from gllm_datastore.constants import CHUNK_KEYS as CHUNK_KEYS
from gllm_datastore.core.filters.schema import FilterClause as FilterClause, FilterCondition as FilterCondition, FilterOperator as FilterOperator, QueryFilter as QueryFilter

class MilvusQueryTranslator:
    """Translates QueryFilter and FilterClause objects to Milvus expression syntax.

    This class encapsulates all query translation logic for Milvus, converting
    structured FilterClause and QueryFilter objects into Milvus expression strings
    that can be used in query() and search() operations.

    Attributes:
        METADATA_PREFIX (str): Prefix for metadata fields in dot notation.
        MIN_METADATA_PARTS (int): Minimum number of parts in a metadata field path.
    """
    METADATA_PREFIX: Incomplete
    MIN_METADATA_PARTS: int
    def translate(self, filters: QueryFilter | None = None) -> str | None:
        """Translate QueryFilter to Milvus expression string.

        This is the main entry point for query translation. It handles None filters
        and delegates to internal translation methods.

        Args:
            filters (QueryFilter | None, optional): Structured QueryFilter to translate. Defaults to None.

        Returns:
            str | None: A Milvus expression string or None if no filters are provided.
        """
