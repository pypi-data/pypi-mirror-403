"""
Data models for face-finder
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import numpy as np


@dataclass
class SearchResult:
    """A single search result."""
    file_path: str
    file_name: str
    distance: float
    face_index: int
    context_score: float = 0.0  # Co-occurrence context score (0-1)
    context_boost_applied: bool = False  # Whether context was used to boost
    
    @property
    def path(self) -> Path:
        return Path(self.file_path)
    
    @property
    def combined_score(self) -> float:
        """Combined score considering both embedding distance and context."""
        if self.context_score > 0:
            # Context can reduce effective distance by up to 20%
            context_factor = 1.0 - (self.context_score * 0.2)
            return self.distance * context_factor
        return self.distance


@dataclass
class ContextualMatch:
    """
    Extended search result with co-occurrence context.
    
    This is returned when using context-aware search, providing
    additional information about why a match was boosted or verified.
    """
    result: SearchResult
    context_score: float  # 0-1, higher = more familiar context
    familiar_faces: List[int]  # Cluster IDs of recognized companions
    total_cooccurrences: int  # Historical co-occurrence count
    nearby_faces_in_image: int  # Number of other faces in this image


@dataclass
class IndexStats:
    """Statistics about the face index."""
    total_faces: int
    total_images: int
    embedding_dim: int
    detector_used: str
    index_size_mb: float
    # Co-occurrence stats
    cooccurrence_clusters: int = 0
    cooccurrence_pairs: int = 0


@dataclass
class FaceEmbedding:
    """A face embedding with metadata."""
    embedding: np.ndarray  # 512-dim vector
    file_path: str
    file_name: str
    face_index: int
    confidence: float
    cluster_id: Optional[int] = None  # Co-occurrence cluster assignment
