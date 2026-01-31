from abc import ABC, abstractmethod
from enum import StrEnum
from gllm_datastore.cache import Cache as Cache
from gllm_datastore.core.capabilities import EncryptionCapability as EncryptionCapability, FulltextCapability as FulltextCapability, GraphCapability as GraphCapability, HybridCapability as HybridCapability, SearchConfig as SearchConfig, VectorCapability as VectorCapability
from gllm_datastore.core.filters.schema import FilterClause as FilterClause, QueryFilter as QueryFilter
from gllm_datastore.data_store.exceptions import NotRegisteredException as NotRegisteredException, NotSupportedException as NotSupportedException
from gllm_datastore.encryptor.encryptor import BaseEncryptor as BaseEncryptor
from gllm_inference.em_invoker.em_invoker import BaseEMInvoker
from typing import Any, Self

class CapabilityType(StrEnum):
    """Enumeration of supported capability types."""
    FULLTEXT: str
    GRAPH: str
    HYBRID: str
    VECTOR: str

class BaseDataStore(ABC):
    """Base class for datastores with multiple capabilities.

    This class provides the infrastructure for capability composition and
    delegation. Datastores inherit from this class and register capability
    handlers based on their configuration.
    """
    def __init__(self) -> None:
        """Initialize the datastore with specified capabilities."""
    @property
    @abstractmethod
    def supported_capabilities(self) -> list[CapabilityType]:
        """Return list of currently supported capabilities.

        A data store might have more capabilities than the ones that are currently registered.
        Each data store should implement this method to return the list of supported capabilities.

        Returns:
            list[str]: List of capability names that are supported.

        Raises:
            NotImplementedError: If the method is not implemented by subclass.
        """
    @abstractmethod
    async def get_size(self, filters: FilterClause | QueryFilter | None = None) -> int:
        """Asynchronously get the total number of records in the datastore.

        This method is async-first: subclasses should implement an async
        `get_size` that performs query operations using the datastore's
        capabilities (fulltext, vector, etc.). Implementations should accept
        either a `FilterClause` or a `QueryFilter` or `None`.

        Args:
            filters (FilterClause | QueryFilter | None, optional): Query filters to apply.
                FilterClause objects are automatically converted to QueryFilter internally.
                Defaults to None.

        Returns:
            int: The total number of records matching the filters.

        Raises:
            NotImplementedError: If the method is not implemented by subclass.
        """
    @property
    def registered_capabilities(self) -> list[CapabilityType]:
        """Return list of currently registered capabilities.

        Returns:
            list[str]: List of capability names that are registered and available.
        """
    @property
    def fulltext(self) -> FulltextCapability:
        """Access fulltext capability if supported.

        Returns:
            FulltextCapability: Fulltext capability handler.

        Raises:
            NotSupportedException: If fulltext capability is not supported.
        """
    @property
    def vector(self) -> VectorCapability:
        """Access vector capability if supported.

        Returns:
            VectorCapability: Vector capability handler.

        Raises:
            NotSupportedException: If vector capability is not supported
        """
    @property
    def graph(self) -> GraphCapability:
        """Access graph capability if supported.

        Returns:
            GraphCapability: Graph capability handler.

        Raises:
            NotSupportedException: If graph capability is not supported.
        """
    @property
    def hybrid(self) -> HybridCapability:
        """Access hybrid capability if supported.

        Returns:
            HybridCapability: Hybrid capability handler.

        Raises:
            NotSupportedException: If hybrid capability is not supported.
            NotRegisteredException: If hybrid capability is not registered.
        """
    def with_fulltext(self, **kwargs) -> Self:
        """Configure fulltext capability and return datastore instance.

        Args:
            **kwargs: Fulltext capability configuration parameters.

        Returns:
            Self: Self for method chaining.
        """
    def with_vector(self, em_invoker: BaseEMInvoker, **kwargs) -> Self:
        """Configure vector capability and return datastore instance.

        Args:
            em_invoker (BaseEMInvoker): Embedding model invoker (required).
            **kwargs: Vector capability configuration parameters.

        Returns:
            Self: Self for method chaining.
        """
    def with_graph(self, **kwargs) -> Self:
        """Configure graph capability and return datastore instance.

        Args:
            **kwargs: Graph capability configuration parameters.

        Returns:
            Self: Self for method chaining.
        """
    def with_encryption(self, encryptor: BaseEncryptor, fields: set[str] | list[str]) -> Self:
        """Enable encryption for specified fields.

        Encryption works transparently - users don't need to access it directly.
        It's automatically used by fulltext and vector capabilities.

        Args:
            encryptor (BaseEncryptor): The encryptor instance to use. Must not be None.
            fields (set[str] | list[str]): Set or list of field names to encrypt. Must not be empty.

        Returns:
            Self: Self for method chaining.

        Raises:
            ValueError: If encryptor is None or fields is empty.
        """
    def with_hybrid(self, config: list[SearchConfig], **kwargs) -> Self:
        """Configure hybrid capability and return datastore instance.

        Args:
            config (list[SearchConfig]): List of search configurations for hybrid search.
            **kwargs: Additional hybrid capability configuration parameters.

        Returns:
            Self: Self for method chaining.
        """
    def as_cache(self, eviction_manager: Any | None = None, matching_strategy: Any = None) -> Cache:
        """Create a Cache instance from this datastore.

        Args:
            eviction_manager (Any | None, optional): Optional eviction manager for cache eviction.
                Defaults to None.
            matching_strategy (Any, optional): Default matching strategy for cache retrieval.
                Defaults to None.

        Returns:
            Cache: Instance wrapping this datastore.

        Raises:
            ValueError: If required capabilities not registered.
        """
    @classmethod
    def translate_query_filter(cls, query_filter: FilterClause | QueryFilter, **kwargs) -> Any:
        """Translate QueryFilter or FilterClause to datastore's native filter syntax.

        This method provides a public interface for converting the GLLM DataStore's
        QueryFilter DSL into each datastore's native filter format. Subclasses must
        implement this method to provide their specific translation logic.

        Args:
            query_filter (FilterClause | QueryFilter): The filter to translate.
                Can be a single FilterClause or a QueryFilter with multiple clauses.
            **kwargs: Additional keyword arguments for the datastore's native filter syntax.

        Returns:
            Any: The translated filter in the datastore's native format.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
