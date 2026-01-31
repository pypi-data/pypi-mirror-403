from _typeshed import Incomplete

Base: Incomplete

class ChunkModel(Base):
    """SQLAlchemy model for the chunk table.

    Attributes:
        id (Column): The ID of the chunk.
        content (Column): The content of the chunk.
        chunk_metadata (Column): The metadata of the chunk stored as JSON.
    """
    __tablename__: str
    id: Incomplete
    content: Incomplete
    chunk_metadata: Incomplete
