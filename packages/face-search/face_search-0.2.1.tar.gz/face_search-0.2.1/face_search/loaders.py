"""
Image loading utilities
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple

from .interfaces import ImageLoader


class CVImageLoader(ImageLoader):
    """OpenCV-based image loader."""
    
    def __init__(self, max_size: int = 1280):
        self.max_size = max_size
        self._extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', 
                           '.JPG', '.JPEG', '.PNG', '.WEBP', '.BMP')
    
    def load(self, path: Path) -> np.ndarray:
        """Load and resize image."""
        try:
            # Handle non-ASCII paths
            img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                return None
            
            # Resize if needed (max_size=0 means no resize)
            if self.max_size > 0:
                h, w = img.shape[:2]
                if max(h, w) > self.max_size:
                    scale = self.max_size / max(h, w)
                    img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            
            # Convert BGR to RGB
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception:
            return None
    
    def supported_extensions(self) -> Tuple[str, ...]:
        return self._extensions
