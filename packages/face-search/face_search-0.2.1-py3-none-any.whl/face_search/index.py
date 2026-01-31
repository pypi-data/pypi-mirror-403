"""
FAISS-based vector index implementation
"""

import pickle
import numpy as np
from pathlib import Path
from typing import List, Tuple
import faiss

from .interfaces import VectorIndex


class FAISSIndex(VectorIndex):
    """FAISS-based similarity search index."""
    
    def __init__(self, dimension: int = 512):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine after normalization)
        self.metadata: List[dict] = []
        self.sources: dict = {}  # Track source directories: {source_path: {"count": n, "added": timestamp}}
    
    def add(self, embeddings: np.ndarray, metadata: List[dict]) -> None:
        """Add normalized embeddings to index."""
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Expected {self.dimension}-dim embeddings, got {embeddings.shape[1]}")
        
        # Normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.clip(norms, 1e-12, None)
        embeddings_norm = embeddings / norms
        
        # Add to FAISS
        self.index.add(embeddings_norm.astype(np.float32))
        self.metadata.extend(metadata)
    
    def search(self, query: np.ndarray, k: int, threshold: float) -> List[Tuple[int, float]]:
        """
        Search for similar embeddings.
        
        Returns:
            List of (index, distance) where distance is 1 - similarity (0 = identical, 1 = different)
        """
        if len(self.metadata) == 0:
            return []
        
        # Normalize query
        query_norm = query / max(np.linalg.norm(query), 1e-12)
        query_norm = query_norm.reshape(1, -1).astype(np.float32)
        
        # Search (returns similarities since we use IndexFlatIP)
        similarities, indices = self.index.search(query_norm, min(k, self.size()))
        
        # Convert to distances (1 - similarity)
        results = []
        for idx, sim in zip(indices[0], similarities[0]):
            if idx < 0:  # FAISS uses -1 for no match
                continue
            distance = 1 - sim
            if distance <= threshold:
                results.append((int(idx), float(distance)))
        
        return results
    
    def save(self, path: Path) -> None:
        """Save index and metadata to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(path.with_suffix('.faiss')))
        
        # Save metadata
        with open(path.with_suffix('.pkl'), 'wb') as f:
            pickle.dump({
                'metadata': self.metadata,
                'dimension': self.dimension,
                'sources': self.sources
            }, f)
    
    def load(self, path: Path) -> None:
        """Load index and metadata from disk."""
        path = Path(path)
        
        # Load FAISS index
        self.index = faiss.read_index(str(path.with_suffix('.faiss')))
        
        # Load metadata
        with open(path.with_suffix('.pkl'), 'rb') as f:
            data = pickle.load(f)
            self.metadata = data['metadata']
            self.dimension = data['dimension']
            self.sources = data.get('sources', {})  # Backward compat
    
    def size(self) -> int:
        """Number of vectors in index."""
        return self.index.ntotal
    
    def clear(self) -> None:
        """Clear index."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        self.sources = {}
    
    def get_metadata(self, index: int) -> dict:
        """Get metadata for a specific index."""
        if 0 <= index < len(self.metadata):
            return self.metadata[index]
        return None
    
    def add_source(self, source_path: str, count: int) -> None:
        """Track a source directory."""
        from datetime import datetime
        if source_path in self.sources:
            self.sources[source_path]['count'] += count
            self.sources[source_path]['updated'] = datetime.now().isoformat()
        else:
            self.sources[source_path] = {
                'count': count,
                'added': datetime.now().isoformat()
            }
    
    def get_sources(self) -> dict:
        """Get all tracked source directories."""
        return self.sources.copy()
    
    def remove_source(self, source_path: str) -> int:
        """
        Remove all faces from a source directory.
        Returns number of faces removed.
        
        Note: FAISS doesn't support efficient deletion, so we rebuild.
        """
        source_path = str(source_path)
        
        # Find indices to keep
        keep_indices = []
        remove_count = 0
        for i, meta in enumerate(self.metadata):
            if not meta['file_path'].startswith(source_path):
                keep_indices.append(i)
            else:
                remove_count += 1
        
        if remove_count == 0:
            return 0
        
        # Rebuild index with kept entries
        if keep_indices:
            # Get embeddings for kept entries
            kept_embeddings = np.zeros((len(keep_indices), self.dimension), dtype=np.float32)
            for new_idx, old_idx in enumerate(keep_indices):
                kept_embeddings[new_idx] = self.index.reconstruct(old_idx)
            
            kept_metadata = [self.metadata[i] for i in keep_indices]
            
            # Clear and rebuild
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = []
            
            # Re-add (already normalized)
            self.index.add(kept_embeddings)
            self.metadata = kept_metadata
        else:
            self.clear()
        
        # Update sources tracking
        if source_path in self.sources:
            del self.sources[source_path]
        
        return remove_count
