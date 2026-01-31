from enum import StrEnum
from gllm_core.schema.graph import Edge, Node
from pydantic import BaseModel

class RelationshipDirection(StrEnum):
    """Direction for relationship traversal."""
    OUTGOING: str
    INCOMING: str
    BOTH: str

class SearchPosition(StrEnum):
    """Position in a graph pattern for constrained search."""
    SOURCE: str
    RELATIONSHIP: str
    TARGET: str

class Triplet(BaseModel):
    """Graph triplet pattern (source-relationship-target).

    Attributes:
        source (Node): Source node.
        relationship (Edge): A directed relationship from source to target.
        target (Node): Target node.
    """
    source: Node
    relationship: Edge
    target: Node
