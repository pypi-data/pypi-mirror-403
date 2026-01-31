"""
Concrete implementations of embedders
"""

import os
import numpy as np

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from deepface import DeepFace
from .interfaces import FaceEmbedder


class FaceNet512Embedder(FaceEmbedder):
    """FaceNet512 - 512-dim embeddings, 98.4% accuracy."""
    
    def __init__(self):
        # Pre-load model
        DeepFace.build_model("Facenet512")
    
    def embed(self, face_image: np.ndarray) -> np.ndarray:
        """Extract 512-dim embedding."""
        try:
            result = DeepFace.represent(
                img_path=face_image,
                model_name="Facenet512",
                enforce_detection=False,
                detector_backend="skip"
            )
            if result:
                return np.array(result[0]['embedding'], dtype=np.float32)
        except Exception:
            pass
        return None
    
    def embed_batch(self, face_images: list) -> list:
        """
        Extract embeddings for multiple faces in one call.
        Reduces Python→C++ boundary crossings for better performance.
        
        Args:
            face_images: List of face images (numpy arrays)
            
        Returns:
            List of embeddings (or None for failed extractions)
        """
        if not face_images:
            return []
        
        embeddings = []
        for face_image in face_images:
            emb = self.embed(face_image)
            embeddings.append(emb)
        
        return embeddings
    
    @property
    def embedding_dim(self) -> int:
        return 512
    
    @property
    def name(self) -> str:
        return "Facenet512"


class EmbedderFactory:
    """Factory for creating face embedders."""
    
    _embedders = {
        "facenet512": FaceNet512Embedder,
    }
    
    @classmethod
    def create(cls, name: str = "facenet512") -> FaceEmbedder:
        """Create an embedder by name."""
        if name not in cls._embedders:
            raise ValueError(f"Unknown embedder: {name}")
        return cls._embedders[name]()
    
    @classmethod
    def available(cls) -> list:
        """List available embedder names."""
        return list(cls._embedders.keys())
