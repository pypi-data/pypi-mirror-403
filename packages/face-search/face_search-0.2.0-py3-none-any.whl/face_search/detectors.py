"""
Concrete implementations of detectors
"""

import os
import numpy as np
from typing import List

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from deepface import DeepFace
from .interfaces import FaceDetector


class OpenCVDetector(FaceDetector):
    """Fast OpenCV Haar Cascade detector."""
    
    def detect(self, image: np.ndarray) -> List[dict]:
        try:
            return DeepFace.extract_faces(
                img_path=image,
                detector_backend="opencv",
                enforce_detection=False,
                align=True,
                expand_percentage=0
            )
        except Exception:
            return []
    
    @property
    def name(self) -> str:
        return "opencv"


class SSDDetector(FaceDetector):
    """Fast SSD (Single Shot Detector)."""
    
    def detect(self, image: np.ndarray) -> List[dict]:
        try:
            return DeepFace.extract_faces(
                img_path=image,
                detector_backend="ssd",
                enforce_detection=False,
                align=True,
                expand_percentage=0
            )
        except Exception:
            return []
    
    @property
    def name(self) -> str:
        return "ssd"


class MTCNNDetector(FaceDetector):
    """MTCNN - good balance of speed and accuracy."""
    
    def detect(self, image: np.ndarray) -> List[dict]:
        try:
            return DeepFace.extract_faces(
                img_path=image,
                detector_backend="mtcnn",
                enforce_detection=False,
                align=True,
                expand_percentage=0
            )
        except Exception:
            return []
    
    @property
    def name(self) -> str:
        return "mtcnn"


class RetinaFaceDetector(FaceDetector):
    """RetinaFace - most accurate detector."""
    
    def detect(self, image: np.ndarray) -> List[dict]:
        try:
            return DeepFace.extract_faces(
                img_path=image,
                detector_backend="retinaface",
                enforce_detection=False,
                align=True,
                expand_percentage=0
            )
        except Exception:
            return []
    
    @property
    def name(self) -> str:
        return "retinaface"


class DetectorFactory:
    """Factory for creating face detectors."""
    
    _detectors = {
        "opencv": OpenCVDetector,
        "ssd": SSDDetector,
        "mtcnn": MTCNNDetector,
        "retinaface": RetinaFaceDetector,
    }
    
    @classmethod
    def create(cls, name: str) -> FaceDetector:
        """Create a detector by name."""
        if name not in cls._detectors:
            raise ValueError(f"Unknown detector: {name}. Choose from: {list(cls._detectors.keys())}")
        return cls._detectors[name]()
    
    @classmethod
    def available(cls) -> List[str]:
        """List available detector names."""
        return list(cls._detectors.keys())
