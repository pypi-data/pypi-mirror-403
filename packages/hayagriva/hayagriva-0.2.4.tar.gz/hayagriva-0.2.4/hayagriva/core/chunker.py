"""Text chunker implementations."""
from __future__ import annotations

from typing import Iterable, List, Tuple, Optional
import re

from hayagriva.config import ChunkingConfig
from hayagriva.core.embeddings import SentenceTransformerEmbeddings
from hayagriva.utils.logger import get_logger

logger = get_logger(__name__)


class BaseChunker:
    """Base class for chunkers."""
    
    def __init__(self, config: ChunkingConfig | None = None) -> None:
        self.config = config or ChunkingConfig()

    def chunk(self, documents: Iterable[str]) -> Tuple[List[str], List[dict]]:
        """Return chunks and corresponding metadata."""
        raise NotImplementedError


class WordChunker(BaseChunker):
    """Chunk text using a whitespace-based window."""

    def chunk(self, documents: Iterable[str]) -> Tuple[List[str], List[dict]]:
        chunks: List[str] = []
        metadata: List[dict] = []
        
        for doc in documents:
            words = doc.split()
            size = self.config.chunk_size
            overlap = self.config.overlap
            start = 0
            while start < len(words):
                end = start + size
                chunk_words = words[start:end]
                if chunk_words:
                    chunks.append(" ".join(chunk_words))
                    metadata.append({})
                start += size - overlap if size > overlap else size
        return chunks, metadata


class RecursiveChunker(BaseChunker):
    """Recursively chunk text using a list of separators."""

    def chunk(self, documents: Iterable[str]) -> Tuple[List[str], List[dict]]:
        chunks: List[str] = []
        metadata: List[dict] = []
        
        separators = self.config.separators
        
        for doc in documents:
            doc_chunks = self._recursive_split(doc, separators, self.config.chunk_size)
            chunks.extend(doc_chunks)
            metadata.extend([{} for _ in doc_chunks])
            
        return chunks, metadata

    def _recursive_split(self, text: str, separators: List[str], chunk_size: int) -> List[str]:
        """Split text recursively."""
        final_chunks = []
        
        # Get the current separator
        separator = separators[0]
        new_separators = separators[1:]
        
        # Split the text
        if separator == "":
            splits = list(text) # Character split
        else:
            splits = text.split(separator)
            
        # Now combine splits into chunks
        good_splits = []
        
        for split in splits:
            if not split.strip():
                continue
                
            # If split is small enough, keep it
            # Note: We are approximating size by length of string / 5 (avg word length) + spaces
            # Or just use character count? Config says chunk_size (int). 
            # WordChunker used words. Let's assume chunk_size is roughly words.
            # 1 word ~ 5 chars.
            if len(split.split()) < chunk_size:
                good_splits.append(split)
            else:
                # Split is too big, recurse
                if new_separators:
                    sub_chunks = self._recursive_split(split, new_separators, chunk_size)
                    good_splits.extend(sub_chunks)
                else:
                    # No more separators, just take it (or force split)
                    good_splits.append(split)
        
        # Merge good splits into final chunks
        current_chunk = []
        current_len = 0
        
        for split in good_splits:
            split_len = len(split.split())
            if current_len + split_len > chunk_size:
                if current_chunk:
                    # Join with the separator we split by (approximation)
                    # Actually, we lost the separator. Let's join with space or newline
                    join_char = separator if separator != "" else ""
                    if separator in ["\n", "\n\n"]:
                        join_char = separator
                    else:
                        join_char = " "
                        
                    final_chunks.append(join_char.join(current_chunk))
                
                current_chunk = [split]
                current_len = split_len
            else:
                current_chunk.append(split)
                current_len += split_len
                
        if current_chunk:
            join_char = separator if separator in ["\n", "\n\n"] else " "
            final_chunks.append(join_char.join(current_chunk))
            
        return final_chunks


class SemanticChunker(BaseChunker):
    """Chunk text based on semantic similarity between sentences."""
    
    def __init__(self, config: ChunkingConfig | None = None, embedder: Optional[SentenceTransformerEmbeddings] = None) -> None:
        super().__init__(config)
        self.embedder = embedder
        
    def chunk(self, documents: Iterable[str]) -> Tuple[List[str], List[dict]]:
        if not self.embedder:
            raise ValueError("SemanticChunker requires an embedder.")
            
        import numpy as np
        
        chunks: List[str] = []
        metadata: List[dict] = []
        
        for doc in documents:
            # 1. Split into sentences (simple split)
            sentences = re.split(r'(?<=[.?!])\s+', doc)
            if not sentences:
                continue
                
            # 2. Embed sentences
            embeddings = self.embedder.embed(sentences)
            
            # 3. Calculate cosine similarity between adjacent sentences
            # Norms are already handled by embedder? No, SentenceTransformer returns raw.
            # But we can use dot product if normalized.
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            normalized = embeddings / norms
            
            similarities = []
            for i in range(len(normalized) - 1):
                sim = np.dot(normalized[i], normalized[i+1])
                similarities.append(sim)
                
            # 4. Group sentences
            current_chunk = [sentences[0]]
            
            for i, sim in enumerate(similarities):
                if sim >= self.config.semantic_threshold:
                    current_chunk.append(sentences[i+1])
                else:
                    chunks.append(" ".join(current_chunk))
                    metadata.append({})
                    current_chunk = [sentences[i+1]]
            
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                metadata.append({})
                
        return chunks, metadata


class HierarchicalChunker(BaseChunker):
    """Create parent chunks and child chunks."""
    
    def chunk(self, documents: Iterable[str]) -> Tuple[List[str], List[dict]]:
        chunks: List[str] = []
        metadata: List[dict] = []
        
        # Use WordChunker logic for simplicity
        word_chunker = WordChunker(self.config)
        
        for doc in documents:
            # 1. Create Parent Chunks
            # Temporarily override config for parent size
            original_size = self.config.chunk_size
            self.config.chunk_size = self.config.parent_chunk_size
            
            parent_chunks, _ = word_chunker.chunk([doc])
            
            # Restore config
            self.config.chunk_size = original_size
            
            # 2. Create Child Chunks from Parent Chunks
            for parent in parent_chunks:
                child_chunks, _ = word_chunker.chunk([parent])
                
                for child in child_chunks:
                    chunks.append(child)
                    metadata.append({"parent_text": parent})
                    
        return chunks, metadata
