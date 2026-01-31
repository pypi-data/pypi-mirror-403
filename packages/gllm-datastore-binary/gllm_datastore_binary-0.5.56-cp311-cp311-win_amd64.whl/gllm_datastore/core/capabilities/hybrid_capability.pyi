from _typeshed import Incomplete
from enum import StrEnum
from gllm_core.schema.chunk import Chunk as Chunk
from gllm_datastore.core.filters import FilterClause as FilterClause, QueryFilter as QueryFilter, QueryOptions as QueryOptions
from gllm_inference.em_invoker.em_invoker import BaseEMInvoker
from gllm_inference.schema import Vector
from pydantic import BaseModel
from typing import Any, Protocol

class HybridSearchType(StrEnum):
    """Types of searches that can be combined in hybrid search."""
    FULLTEXT: str
    VECTOR: str

class SearchConfig(BaseModel):
    '''Configuration for a single search component in hybrid search.

    Examples:
        FULLTEXT search configuration:
            ```python
            config = SearchConfig(
                search_type=HybridSearchType.FULLTEXT,
                field="text",
                weight=0.3
            )
            ```

        VECTOR search configuration:
            ```python
            config = SearchConfig(
                search_type=HybridSearchType.VECTOR,
                field="embedding",
                em_invoker=em_invoker,
                weight=0.5
            )
            ```

    Attributes:
        search_type (HybridSearchType): Type of search (FULLTEXT or VECTOR).
        field (str): Field name in the index (e.g., "text", "embedding").
        weight (float): Weight for this search in hybrid search. Defaults to 1.0.
        em_invoker (BaseEMInvoker | None): Embedding model invoker required for VECTOR type.
            Defaults to None.
        top_k (int | None): Per-search top_k limit (optional). Defaults to None.
        extra_kwargs (dict[str, Any]): Additional search-specific parameters.
            Defaults to empty dict.
    '''
    search_type: HybridSearchType
    field: str
    weight: float
    em_invoker: BaseEMInvoker | None
    top_k: int | None
    extra_kwargs: dict[str, Any]
    @classmethod
    def validate_top_k(cls, v: int | None) -> int | None:
        """Validate that top_k is positive if provided.

        Args:
            v (int | None): top_k value.

        Returns:
            int | None: Validated top_k value.

        Raises:
            ValueError: If top_k is provided but not positive.
        """
    @classmethod
    def validate_field_not_empty(cls, v: str) -> str:
        """Validate that field name is not empty.

        Args:
            v (str): Field name value.

        Returns:
            str: Validated field name.

        Raises:
            ValueError: If field name is empty.
        """
    model_config: Incomplete
    def validate_search_requirements(self) -> SearchConfig:
        """Validate configuration based on search type.

        Returns:
            SearchConfig: Validated configuration instance.

        Raises:
            ValueError: If required fields are missing for the search type.
        """

class HybridCapability(Protocol):
    """Protocol for hybrid search combining different retrieval paradigms.

    This protocol defines the interface for datastores that support hybrid search
    operations combining multiple retrieval strategies (fulltext, vector).
    """
    async def create(self, chunks: list[Chunk], **kwargs) -> None:
        """Create chunks with automatic generation of all configured search fields.

        This method automatically generates and indexes all fields required by the
        configured searches in with_hybrid(). For each chunk:

        1. FULLTEXT search: Indexes text content in the configured field name.
        2. VECTOR search: Generates dense embedding using the configured em_invoker
           and indexes it in the configured field name.

        Args:
            chunks (list[Chunk]): List of chunks to create and index.
            **kwargs (Any, optional): Datastore-specific parameters.
        """
    async def create_from_vectors(self, chunks: list[Chunk], dense_vectors: dict[str, list[tuple[Chunk, Vector]]] | None = None, **kwargs) -> None:
        """Create chunks with pre-computed vectors for multiple fields.

        Allows indexing pre-computed vectors for multiple vector fields at once.
        Field names must match those configured in with_hybrid().

        Args:
            chunks (list[Chunk]): Chunks to index.
            dense_vectors (dict[str, list[tuple[Chunk, Vector]]] | None, optional): Dict mapping field names
                to lists of (chunk, vector) tuples. Defaults to None.
            **kwargs (Any, optional): Datastore-specific parameters.
        """
    async def retrieve(self, query: str, fusion_mode: str | None = None, filters: FilterClause | QueryFilter | None = None, options: QueryOptions | None = None, **kwargs) -> list[Chunk]:
        """Retrieve using hybrid search combining different retrieval paradigms.

        Args:
            query (str): Query text to search with.
            fusion_mode (str | None, optional): Fusion mode to use. Defaults to None, in which case the default fusion
                mode from with_hybrid() is used.
            filters (FilterClause | QueryFilter | None, optional): Query filters to apply.
                FilterClause objects are automatically converted to QueryFilter internally.
                Defaults to None.
            options (QueryOptions | None, optional): Query options like limit and sorting. Defaults to None.
            **kwargs (Any, optional): Datastore-specific parameters.

        Returns:
            list[Chunk]: Query results ordered by relevance.
        """
    async def retrieve_by_vectors(self, query: str | None = None, dense_vector: Vector | None = None, fusion_mode: str | None = None, filters: FilterClause | QueryFilter | None = None, options: QueryOptions | None = None, **kwargs) -> list[Chunk]:
        """Hybrid search using pre-computed vectors.

        Args:
            query (str | None, optional): Optional query text (for fulltext search). Defaults to None.
            dense_vector (Vector | None, optional): Pre-computed dense vector for VECTOR search.
                Defaults to None.
            fusion_mode (str | None, optional): Fusion mode to use. Defaults to None, in which case the default fusion
                mode from with_hybrid() is used.
            filters (FilterClause | QueryFilter | None, optional): Query filters to apply.
                FilterClause objects are automatically converted to QueryFilter internally.
                Defaults to None.
            options (QueryOptions | None, optional): Query options like limit and sorting. Defaults to None.
            **kwargs (Any): Datastore-specific parameters.

        Returns:
            list[Chunk]: Query results ordered by relevance.
        """
    async def update(self, update_values: dict[str, Any], filters: FilterClause | QueryFilter | None = None, **kwargs) -> None:
        """Update existing records in the datastore.

        Args:
            update_values (dict[str, Any]): Values to update.
            filters (FilterClause | QueryFilter | None, optional): Filters to select records to update.
                FilterClause objects are automatically converted to QueryFilter internally.
                Defaults to None.
            **kwargs (Any): Datastore-specific parameters.
        """
    async def delete(self, filters: FilterClause | QueryFilter | None = None, **kwargs) -> None:
        """Delete records from the datastore.

        Args:
            filters (FilterClause | QueryFilter | None, optional): Filters to select records to delete.
                FilterClause objects are automatically converted to QueryFilter internally.
                Defaults to None.
            **kwargs (Any): Datastore-specific parameters.

        Note:
            If filters is None, no operation is performed (no-op).
        """
    async def clear(self, **kwargs) -> None:
        """Clear all records from the datastore.

        Args:
            **kwargs (Any): Datastore-specific parameters.
        """
