from abc import ABC, abstractmethod
from gllm_core.schema import Node as Node
from gllm_datastore.graph_data_store.schema import RelationshipDirection as RelationshipDirection, SearchPosition as SearchPosition, Triplet as Triplet
from typing import Any

class AgenticGraphToolsMixin(ABC):
    """Mixin class providing agentic graph tools for graph exploration.

    This mixin adds methods for graph database operations including:
    - Safe query execution (read-only)
    - Neighborhood exploration
    - Node and relationship search
    - Context-sensitive autocomplete

    Note: Base query() method remains unchanged and allows write operations
    read_only_query() provides read-only guarantee for safety-critical scenarios
    """
    @abstractmethod
    async def read_only_query(self, query: str, parameters: dict[str, Any] | None = None, max_results: int = 100, timeout: int = 60) -> list[dict[str, Any]]:
        """Execute a validated read-only query.

        Differentiates from base query() by enforcing read-only validation
        Base query() allows write operations (CREATE, DELETE, MERGE, SET, REMOVE)
        This method blocks all write operations for safety

        Args:
            query (str): Query string to execute.
            parameters (dict[str, Any] | None, optional): Query parameters. Defaults to None.
            max_results (int, optional): Maximum results to return. Defaults to 100.
            timeout (int, optional): Query timeout in seconds. Defaults to 60.

        Returns:
            list[dict[str, Any]]: List of result dictionaries.

        Raises:
            NotImplementedError: This is an abstract method that must be implemented by subclasses.
        """
    @abstractmethod
    async def get_neighborhood(self, node_id: str | None = None, relationship_type: str | None = None, target_node_id: str | None = None, limit: int = 10) -> list[Triplet]:
        """Get graph patterns matching partial constraints.

        Provide at least one of: node_id, relationship_type, or target_node_id
        Returns up to N diverse patterns to help understand graph structure

        This method differs from traverse() in base graph_data_store
        - traverse() follows a specific path through the graph from a starting node
        - get_neighborhood() discovers patterns matching given constraints without
          requiring a specific traversal path or starting point.

        Args:
            node_id (str | None, optional): Source node ID (property-based). Defaults to None.
            relationship_type (str | None, optional): Relationship type to filter by. Defaults to None.
            target_node_id (str | None, optional): Target node ID (property-based). Defaults to None.
            limit (int, optional): Maximum number of patterns to return. Defaults to 10.

        Returns:
            list[Triplet]: List of triplets containing source-relationship-target patterns.

        Raises:
            NotImplementedError: This is an abstract method that must be implemented by subclasses.
        """
    @abstractmethod
    async def search_node(self, query: str, node_label: str | None = None, limit: int = 10) -> list[Node]:
        """Search for nodes using substring matching.

        Searches across common properties like id, name, title, description
        Uses case-insensitive substring matching

        Args:
            query (str): Search query string.
            node_label (str | None, optional): Optional node label to filter by. Defaults to None.
            limit (int, optional): Maximum number of results to return. Defaults to 10.

        Returns:
            list[Node]: List of matching nodes.

        Raises:
            NotImplementedError: This is an abstract method that must be implemented by subclasses.
        """
    @abstractmethod
    async def search_relationship(self, query: str, node_label: str | None = None, limit: int = 10) -> list[Triplet]:
        """Search for relationship types using substring matching.

        Returns relationship types that exist in graph with usage counts
        Helps avoid hallucinating relationship types

        Args:
            query (str): Search query string.
            node_label (str | None, optional): Optional node label to filter relationships. Defaults to None.
            limit (int, optional): Maximum number of results to return. Defaults to 10.

        Returns:
            list[Triplet]: List of triplets representing relationship types found in the graph.

        Raises:
            NotImplementedError: This is an abstract method that must be implemented by subclasses.
        """
    @abstractmethod
    async def search_rel_of_node(self, query: str, node_id: str, direction: RelationshipDirection = ..., limit: int = 10) -> list[Triplet]:
        """Search for relationship types for a specific node.

        More context-sensitive than general relationship search
        Only returns relationships that connect to the given node

        Args:
            query (str): Search query string.
            node_id (str, optional): Node ID to search relationships for. Defaults to None.
            direction (RelationshipDirection, optional): Relationship direction. Defaults to BOTH.
            limit (int, optional): Maximum number of results to return. Defaults to 10.

        Returns:
            list[Triplet]: List of triplets for the node.

        Raises:
            NotImplementedError: This is an abstract method that must be implemented by subclasses.
        """
    @abstractmethod
    async def search_target_of_rel(self, query: str, relationship_type: str, source_node_id: str | None = None, limit: int = 10) -> list[Node]:
        """Search for target nodes reachable via relationship type.

        If source_node_id provided, finds targets from that node only
        Otherwise finds all nodes reachable via relationship type

        Args:
            query (str): Search query string.
            relationship_type (str, optional): Relationship type to traverse. Defaults to None.
            source_node_id (str | None, optional): Optional source node to start from. Defaults to None.
            limit (int, optional): Maximum number of results to return. Defaults to 10.

        Returns:
            list[Node]: List of target nodes matching query.

        Raises:
            NotImplementedError: This is an abstract method that must be implemented by subclasses.
        """
    @abstractmethod
    async def search_autocomplete(self, query: str, query_pattern: str, search_var: str, limit: int = 10) -> list[Node]:
        """Context-sensitive search constrained by query pattern.

        Executes a partial query pattern and searches for nodes.
        that can be bound to search_var. Pattern provides context.

        Args:
            query (str): Search query string.
            query_pattern (str, optional): Partial query with variable placeholder. Defaults to None.
            search_var (str, optional): Variable name to search for (e.g., 'company'). Defaults to None.
            limit (int, optional): Maximum number of results to return. Defaults to 10.

        Returns:
            list[Node]: List of nodes matching query within pattern context.

        Raises:
            NotImplementedError: This is an abstract method that must be implemented by subclasses.
        """
    @abstractmethod
    async def search_constrained(self, query: str, position: SearchPosition, source_node_id: str | None = None, relationship_type: str | None = None, target_node_id: str | None = None, limit: int = 10) -> list[Node] | list[Triplet]:
        """Search for items in pattern position under constraints.

        Build a pattern with constraints and search for items in specified position (source, relationship, or target).

        Args:
            query (str): Search query string.
            position (SearchPosition): What to search for (SOURCE, RELATIONSHIP, or TARGET).
            source_node_id (str | None, optional): Constraint on source node. Defaults to None.
            relationship_type (str | None, optional): Constraint on relationship type. Defaults to None.
            target_node_id (str | None, optional): Constraint on target node. Defaults to None.
            limit (int, optional): Maximum number of results to return. Defaults to 10.

        Returns:
            list[Node] | list[Triplet]: List of nodes (if position is SOURCE/TARGET).
                or triplets (if position is RELATIONSHIP).

        Raises:
            NotImplementedError: This is an abstract method that must be implemented by subclasses.
        """
