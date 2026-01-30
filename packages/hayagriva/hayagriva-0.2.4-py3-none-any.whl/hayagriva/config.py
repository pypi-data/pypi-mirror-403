"""Configuration utilities for Hayagriva."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfig:
    """Configuration for embedding and generation models."""

    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "gpt-4o"
    vector_store: str = "faiss"
    openai_api_key: Optional[str] = None


@dataclass
class ChunkingConfig:
    """Configuration for the text chunker."""

    chunk_size: int = 200
    overlap: int = 20
    strategy: str = "word"  # "word", "recursive", "semantic", "hierarchical"
    separators: list = field(default_factory=lambda: ["\n\n", "\n", " ", ""])
    semantic_threshold: float = 0.8
    parent_chunk_size: int = 1000


@dataclass
class RetrievalConfig:
    """Configuration for retrieval behavior."""

    top_k: int = 4
    similarity_threshold: float = 0.0
    strategy: str = "vector"  # "vector", "bm25", "hybrid"
    alpha: float = 0.5        # 0.0 = sparse (bm25), 1.0 = dense (vector)


@dataclass
class WeaviateConfig:
    """Configuration for Weaviate vector store."""
    
    url: str = "http://localhost:8080"
    api_key: Optional[str] = None
    index_name: str = "HayagrivaDocs"


@dataclass
class PineconeConfig:
    """Configuration for Pinecone vector store."""
    
    api_key: Optional[str] = None
    host: Optional[str] = None     # Direct host URL for the index (skips discovery)
    environment: str = "us-west1-gcp"  # Legacy
    index_name: str = "hayagriva-index"
    dimension: int = 384
    metric: str = "cosine"


@dataclass
class HayagrivaConfig:
    def __init__(
        self,
        backend="openai",
        api_key=None,
        model="gpt-4o-mini",
        embedding_model="all-MiniLM-L6-v2",
        vector_store="faiss",
        weaviate=None,
        pinecone=None,
        chunking=None,
        models=None,
        retrieval=None,
    ):
        self.backend = backend        # "openai" or "groq"
        self.api_key = api_key        # API key for chosen backend
        self.model = model            # model name for backend
        self.vector_store = vector_store # "faiss", "weaviate", or "pinecone"

        # Existing config objects
        self.chunking = chunking or ChunkingConfig()
        self.models = models or ModelConfig(embedding_model=embedding_model)
        self.retrieval = retrieval or RetrievalConfig()
        self.weaviate = weaviate or WeaviateConfig()
        self.pinecone = pinecone or PineconeConfig()
