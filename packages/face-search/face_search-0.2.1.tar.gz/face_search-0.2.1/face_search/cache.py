"""
Reference face caching
"""

import pickle
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np

from .interfaces import FaceDetector, FaceEmbedder, ImageLoader


class ReferenceCache:
    """Smart caching for reference face embeddings."""
    
    def __init__(self, cache_file: Path = Path(".ref_cache.pkl")):
        self.cache_file = cache_file
    
    def _compute_folder_hash(self, ref_dir: Path, extensions: Tuple[str, ...]) -> str:
        """Compute hash of reference folder state."""
        ext_set = {ext.lower() for ext in extensions}
        files = sorted([f for f in ref_dir.iterdir() if f.suffix.lower() in ext_set])
        state = []
        for f in files:
            stat = f.stat()
            state.append(f"{f.name}|{stat.st_size}|{stat.st_mtime_ns}")
        return hashlib.md5("\n".join(state).encode()).hexdigest()
    
    def load(self, ref_dir: Path, extensions: Tuple[str, ...]) -> Optional[Tuple[List[np.ndarray], List[str]]]:
        """Load cached embeddings if valid."""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file, 'rb') as f:
                cache = pickle.load(f)
            
            current_hash = self._compute_folder_hash(ref_dir, extensions)
            if cache.get('hash') == current_hash:
                return cache['embeddings'], cache['names']
        except Exception:
            pass
        
        return None
    
    def save(self, ref_dir: Path, extensions: Tuple[str, ...], 
             embeddings: List[np.ndarray], names: List[str]) -> None:
        """Save embeddings to cache."""
        try:
            folder_hash = self._compute_folder_hash(ref_dir, extensions)
            cache = {
                'hash': folder_hash,
                'embeddings': embeddings,
                'names': names
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache, f)
        except Exception:
            pass


class ReferenceLoader:
    """Load and cache reference face embeddings."""
    
    def __init__(self, 
                 detector: FaceDetector,
                 embedder: FaceEmbedder,
                 image_loader: ImageLoader,
                 cache_file: Optional[Path] = None):
        self.detector = detector
        self.embedder = embedder
        self.image_loader = image_loader
        self.cache = ReferenceCache(cache_file or Path(".ref_cache.pkl"))
    
    def load(self, ref_dir: Path, use_cache: bool = True, augment: bool = True) -> Tuple[List[np.ndarray], List[str]]:
        """
        Load reference face embeddings.
        
        Args:
            ref_dir: Directory containing reference photos
            use_cache: Use cached embeddings if available
            augment: Add horizontally flipped versions (improves asymmetric face matching)
        
        Returns:
            (embeddings, names) - Lists of embeddings and corresponding file names
        """
        import cv2
        
        extensions = self.image_loader.supported_extensions()
        
        # Try cache first (cache stores both original + flipped if augment was used)
        if use_cache:
            cached = self.cache.load(ref_dir, extensions)
            if cached:
                return cached
        
        # Load fresh
        embeddings = []
        names = []
        
        ref_files = [f for f in ref_dir.iterdir() if f.suffix in extensions]
        
        for file_path in ref_files:
            img = self.image_loader.load(file_path)
            if img is None:
                continue
            
            # Detect faces in original
            faces = self.detector.detect(img)
            if not faces:
                continue
            
            # Embed each face (original)
            for face_data in faces:
                face_img = (face_data['face'] * 255).astype(np.uint8)
                emb = self.embedder.embed(face_img)
                if emb is not None:
                    embeddings.append(emb)
                    names.append(file_path.name)
                    
                    # Add flipped version for better asymmetric face matching
                    if augment:
                        flipped = cv2.flip(face_img, 1)  # Horizontal flip
                        flipped_emb = self.embedder.embed(flipped)
                        if flipped_emb is not None:
                            embeddings.append(flipped_emb)
                            names.append(f"{file_path.name}_flip")
        
        # Save to cache (includes augmented if enabled)
        if embeddings and use_cache:
            self.cache.save(ref_dir, extensions, embeddings, names)
        
        return embeddings, names
