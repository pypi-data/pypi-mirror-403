"""Pinecone vector store implementation."""
from __future__ import annotations

import importlib.util
from typing import List, Sequence, Tuple, Optional
import uuid
import time

from hayagriva.config import PineconeConfig
from hayagriva.exceptions import MissingDependencyError
from hayagriva.utils.logger import get_logger

logger = get_logger(__name__)


class PineconeVectorStore:
    """Pinecone vector store wrapper."""

    def __init__(self, config: PineconeConfig) -> None:
        if importlib.util.find_spec("pinecone") is None:
            raise MissingDependencyError(
                "pinecone-client is required for Pinecone support. Install with `pip install pinecone-client`."
            )
        from pinecone import Pinecone, ServerlessSpec

        self.config = config
        self.pc = Pinecone(api_key=config.api_key)
        
        if config.host:
            # If host is provided, connect directly (skips index creation/check)
            logger.info(f"Connecting to Pinecone index at host: {config.host}")
            self.index = self.pc.Index(host=config.host)
        else:
            # Otherwise, ensure index exists and connect by name
            self._ensure_index(ServerlessSpec)
            self.index = self.pc.Index(config.index_name)

    def _ensure_index(self, ServerlessSpec):
        """Ensure the index exists in Pinecone."""
        existing_indexes = [i.name for i in self.pc.list_indexes()]
        
        if self.config.index_name not in existing_indexes:
            logger.info(f"Creating Pinecone index: {self.config.index_name}")
            # Default to serverless spec for simplicity, or make it configurable if needed
            # For now, we'll assume serverless on AWS us-east-1 as a safe default if not specified
            # But wait, config has 'environment'. Legacy used environment. 
            # New Pinecone client uses ServerlessSpec or PodSpec.
            # Let's try to use ServerlessSpec as it's the modern default.
            
            self.pc.create_index(
                name=self.config.index_name,
                dimension=self.config.dimension,
                metric=self.config.metric,
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            # Wait for index to be ready
            while not self.pc.describe_index(self.config.index_name).status['ready']:
                time.sleep(1)

    def add(self, embeddings, chunks: Sequence[str], metadata: Sequence[dict] | None = None) -> None:
        """Add embeddings and chunks to Pinecone."""
        if len(embeddings) != len(chunks):
            raise ValueError("Embeddings and chunks length mismatch")
        
        if len(chunks) == 0:
            return

        logger.info(f"Adding {len(chunks)} documents to Pinecone...")
        
        # Batch upsert
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch_embeddings = embeddings[i:i+batch_size]
            batch_chunks = chunks[i:i+batch_size]
            
            vectors = []
            for j, (vector, text) in enumerate(zip(batch_embeddings, batch_chunks)):
                # Pinecone metadata
                meta = {"text": text}
                if metadata and (i + j) < len(metadata):
                    # Merge additional metadata
                    meta.update(metadata[i + j])
                
                vectors.append({
                    "id": str(uuid.uuid4()),
                    "values": vector.tolist(),
                    "metadata": meta
                })
            
            self.index.upsert(vectors=vectors)
        
        logger.info("Successfully added documents to Pinecone.")

    def search(self, query_embedding, top_k: int = 4, query_text: str = "", **kwargs) -> List[Tuple[str, float]]:
        """Search for similar documents."""
        if importlib.util.find_spec("numpy") is None:
             raise MissingDependencyError("numpy is required.")
        import numpy as np

        vector = query_embedding.flatten().tolist()
        
        # Basic vector search
        # Pinecone supports filtering, but we'll stick to simple vector search for now
        # unless strategy is hybrid (which requires sparse vectors, not implemented yet)
        
        results = self.index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True
        )

        output = []
        for match in results.matches:
            text = match.metadata.get("text", "")
            score = match.score
            output.append((text, score))
            
        return output
