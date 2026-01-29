"""
Abstract base classes for SOLID architecture
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import numpy as np
from pathlib import Path


class FaceDetector(ABC):
    """Abstract base class for face detection."""
    
    @abstractmethod
    def detect(self, image: np.ndarray) -> List[dict]:
        """
        Detect faces in an image.
        
        Args:
            image: RGB image as numpy array
            
        Returns:
            List of face dictionaries with keys:
                - face: aligned face image (normalized 0-1)
                - confidence: detection confidence
                - facial_area: bounding box dict
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Detector name."""
        pass


class FaceEmbedder(ABC):
    """Abstract base class for face embedding extraction."""
    
    @abstractmethod
    def embed(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract embedding from face image.
        
        Args:
            face_image: Aligned face image
            
        Returns:
            Embedding vector (typically 512-dim)
        """
        pass
    
    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """Embedding dimensionality."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Embedder model name."""
        pass


class VectorIndex(ABC):
    """Abstract base class for vector similarity search."""
    
    @abstractmethod
    def add(self, embeddings: np.ndarray, metadata: List[dict]) -> None:
        """
        Add embeddings to the index.
        
        Args:
            embeddings: Array of shape (N, dim)
            metadata: List of metadata dicts for each embedding
        """
        pass
    
    @abstractmethod
    def search(self, query: np.ndarray, k: int, threshold: float) -> List[Tuple[int, float]]:
        """
        Search for similar embeddings.
        
        Args:
            query: Query embedding vector
            k: Number of results to return
            threshold: Distance threshold (0-1)
            
        Returns:
            List of (index, distance) tuples
        """
        pass
    
    @abstractmethod
    def save(self, path: Path) -> None:
        """Save index to disk."""
        pass
    
    @abstractmethod
    def load(self, path: Path) -> None:
        """Load index from disk."""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Number of vectors in index."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all vectors from index."""
        pass


class ImageLoader(ABC):
    """Abstract base class for image loading."""
    
    @abstractmethod
    def load(self, path: Path) -> np.ndarray:
        """
        Load image from disk.
        
        Args:
            path: Path to image file
            
        Returns:
            RGB image as numpy array, or None if failed
        """
        pass
    
    @abstractmethod
    def supported_extensions(self) -> Tuple[str, ...]:
        """Supported image file extensions."""
        pass
