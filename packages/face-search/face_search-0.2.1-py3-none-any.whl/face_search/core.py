"""
Main FaceFinder class - Facade pattern
"""

from pathlib import Path
from typing import List, Optional, Set, Tuple
from tqdm import tqdm
import numpy as np
import multiprocessing as mp

from .models import SearchResult, IndexStats, ContextualMatch
from .interfaces import FaceDetector, FaceEmbedder, VectorIndex, ImageLoader
from .detectors import DetectorFactory
from .embedders import EmbedderFactory
from .index import FAISSIndex
from .loaders import CVImageLoader
from .cache import ReferenceLoader
from .cooccurrence import CooccurrenceTracker, CooccurrenceMatch


# ============ HYBRID SEARCH SETTINGS ============
# Tune these to balance precision vs recall

# Tier 1: Very confident single match (any ref)
STRONG_MATCH_THRESHOLD = 0.22        # If ANY ref matches this close → accept

# Tier 2: Partial agreement (not all refs need to match - some may be side/angle shots)
VOTE_THRESHOLD = 0.42                # A ref "votes yes" if distance below this
MIN_VOTES_ABSOLUTE = 2               # At least this many refs must vote yes
MIN_VOTE_RATIO = 0.35                # OR this fraction of refs vote yes (whichever is less strict)

# Tier 3: Consensus via median (robust to outlier refs)
MEDIAN_THRESHOLD = 0.55              # Accept if MEDIAN distance below this

# Search settings
SEARCH_BUFFER = 0.25                 # Extra threshold when gathering candidates

# Two-pass (use top results as additional refs)
TWO_PASS_ENABLED = False             # Disable if refs come from the dataset itself
TWO_PASS_TOP_N = 5                   # Number of top matches to use as new refs
TWO_PASS_STRONG_THRESHOLD = 0.15     # Only use matches below this distance

# Co-occurrence / Social Context settings
COOCCURRENCE_ENABLED = True          # Enable co-occurrence tracking
COOCCURRENCE_CLUSTER_THRESHOLD = 0.4 # Threshold for clustering faces
CONTEXT_BOOST_WEIGHT = 0.15          # Max distance reduction from context (15%)
CONTEXT_MIN_COOCCURRENCES = 2        # Min historical sightings to trust context

# Processing settings
BATCH_SIZE = 128                     # Batch size for embedding inference


def _check_gpu() -> bool:
    """Check if GPU is available for TensorFlow."""
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices('GPU')
        if not gpus:
            # print("ℹ️ No GPU detected by TensorFlow")
            return False
        return True
    except ImportError:
        # print("ℹ️ TensorFlow not installed or not found")
        return False
    except Exception as e:
        print(f"⚠️ GPU check failed: {e}")
        return False


# Global worker state (initialized once per process)
_worker_state = {}


def _init_worker(detector_name: str, max_size: int, min_face_size: int):
    """Initialize worker process with reusable detector/embedder."""
    global _worker_state
    from face_search.detectors import DetectorFactory
    from face_search.embedders import EmbedderFactory
    from face_search.loaders import CVImageLoader
    
    _worker_state['loader'] = CVImageLoader(max_size=max_size)
    _worker_state['detector'] = DetectorFactory.create(detector_name)
    _worker_state['embedder'] = EmbedderFactory.create("facenet512")
    _worker_state['min_face_size'] = min_face_size


def _process_single_image(args: tuple) -> List[tuple]:
    """
    Process a single image for multiprocessing.
    Returns list of (embedding, metadata) tuples.
    """
    file_path, min_confidence = args
    global _worker_state
    
    results = []
    try:
        loader = _worker_state['loader']
        detector = _worker_state['detector']
        embedder = _worker_state['embedder']
        min_face_size = _worker_state.get('min_face_size', 0)
        
        img = loader.load(file_path)
        if img is None:
            return results
        
        faces = detector.detect(img)
        
        # Collect valid faces for batch embedding
        valid_faces = []
        valid_metadata = []
        
        for i, face_data in enumerate(faces):
            conf = face_data.get('confidence', 1.0)
            if conf < min_confidence:
                continue
            
            # Optional min face size filter
            if min_face_size > 0:
                area = face_data.get('facial_area', {})
                w = area.get('w', 0)
                h = area.get('h', 0)
                if w < min_face_size or h < min_face_size:
                    continue
            
            face_img = (face_data['face'] * 255).astype(np.uint8)
            valid_faces.append(face_img)
            valid_metadata.append({
                'file_path': str(file_path),
                'file_name': file_path.name,
                'face_index': i,
                'confidence': conf
            })
        
        # Batch embed all valid faces
        if valid_faces:
            embeddings = embedder.embed_batch(valid_faces)
            for emb, meta in zip(embeddings, valid_metadata):
                if emb is not None:
                    results.append((emb, meta))
    except Exception as e:
        print(f"❌ Error processing {file_path.name}: {e}")
    
    return results


def _process_batch(args: tuple) -> List[tuple]:
    """Process a batch of images in one worker call with batched embeddings."""
    file_paths, min_confidence = args
    global _worker_state
    
    loader = _worker_state['loader']
    detector = _worker_state['detector']
    embedder = _worker_state['embedder']
    min_face_size = _worker_state.get('min_face_size', 0)
    
    # Accumulate faces across multiple images for batch embedding
    all_faces = []  # (face_img, metadata)
    all_results = []
    
    for file_path in file_paths:
        try:
            img = loader.load(file_path)
            if img is None:
                continue
            
            faces = detector.detect(img)
            
            for i, face_data in enumerate(faces):
                conf = face_data.get('confidence', 1.0)
                if conf < min_confidence:
                    continue
                
                # Optional min face size filter
                if min_face_size > 0:
                    area = face_data.get('facial_area', {})
                    w = area.get('w', 0)
                    h = area.get('h', 0)
                    if w < min_face_size or h < min_face_size:
                        continue
                
                face_img = (face_data['face'] * 255).astype(np.uint8)
                meta = {
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'face_index': i,
                    'confidence': conf
                }
                all_faces.append((face_img, meta))
                
                # Batch embed when we hit batch size
                if len(all_faces) >= BATCH_SIZE:
                    face_imgs = [f[0] for f in all_faces]
                    metas = [f[1] for f in all_faces]
                    embeddings = embedder.embed_batch(face_imgs)
                    for emb, m in zip(embeddings, metas):
                        if emb is not None:
                            all_results.append((emb, m))
                    all_faces = []
        except Exception as e:
            print(f"❌ Error processing batch item {file_path.name}: {e}")
            continue
    
    # Process remaining faces
    if all_faces:
        face_imgs = [f[0] for f in all_faces]
        metas = [f[1] for f in all_faces]
        embeddings = embedder.embed_batch(face_imgs)
        for emb, m in zip(embeddings, metas):
            if emb is not None:
                all_results.append((emb, m))
    
    return all_results


class FaceFinder:
    """
    Main face finder class - simple facade over complex internals.
    
    Example:
        finder = FaceFinder()
        finder.build("/path/to/photos")
        finder.load_references("./reference_faces")
        matches = finder.search(threshold=0.5)
        
    With context-aware search:
        # Context verification uses co-occurrence to boost confidence
        matches = finder.search_with_context(threshold=0.5)
    """
    
    def __init__(self,
                 detector: Optional[FaceDetector] = None,
                 embedder: Optional[FaceEmbedder] = None,
                 index: Optional[VectorIndex] = None,
                 image_loader: Optional[ImageLoader] = None,
                 index_file: Path = Path("./face_index.faiss"),
                 min_confidence: float = 0.3,
                 enable_cooccurrence: bool = COOCCURRENCE_ENABLED):
        """
        Initialize FaceFinder.
        
        Args:
            detector: Face detector (default: opencv)
            embedder: Face embedder (default: facenet512)
            index: Vector index (default: FAISS)
            image_loader: Image loader (default: OpenCV)
            index_file: Where to save/load index
            min_confidence: Minimum face detection confidence
            enable_cooccurrence: Enable co-occurrence tracking for context-aware search
        """
        self.detector = detector or DetectorFactory.create("opencv")
        self.embedder = embedder or EmbedderFactory.create("facenet512")
        self.index = index or FAISSIndex(dimension=self.embedder.embedding_dim)
        self.image_loader = image_loader or CVImageLoader()
        self.index_file = Path(index_file)
        self.min_confidence = min_confidence
        self.max_size = 1280  # Default max image dimension
        
        self.ref_embeddings: List[np.ndarray] = []
        self.ref_names: List[str] = []
        self._indexed_files: Set[str] = set()  # Track indexed files for incremental
        self._has_gpu = _check_gpu()
        
        # Co-occurrence tracking
        self.enable_cooccurrence = enable_cooccurrence
        self.cooccurrence_tracker: Optional[CooccurrenceTracker] = None
        if enable_cooccurrence:
            self.cooccurrence_tracker = CooccurrenceTracker(
                cluster_threshold=COOCCURRENCE_CLUSTER_THRESHOLD
            )
    
    def build(self, 
              source_dir: Path,
              detector_name: Optional[str] = None,
              show_progress: bool = True,
              batch_size: int = 1000,
              max_size: int = 1280,
              workers: int = 0,
              incremental: bool = False,
              min_face_size: int = 0) -> int:
        """
        Build face index from photos.
        
        Args:
            source_dir: Directory containing photos
            detector_name: Override detector (opencv, ssd, mtcnn, retinaface)
            show_progress: Show progress bar
            batch_size: Batch size for FAISS inserts
            max_size: Max image dimension (smaller = faster)
            workers: Number of parallel workers (0 = auto, 1 = single-threaded)
            incremental: Only index new files (requires existing index)
            min_face_size: Minimum face size in pixels (0 = no filter, 40+ recommended)
            
        Returns:
            Number of faces indexed
        """
        source_dir = Path(source_dir)
        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")
        
        # Override detector if requested
        detector_name = detector_name or self.detector.name
        if detector_name:
            self.detector = DetectorFactory.create(detector_name)
        
        self.max_size = max_size
        self.image_loader = CVImageLoader(max_size=max_size)
        
        # Find all images (single pass, case-insensitive)
        extensions = self.image_loader.supported_extensions()
        ext_set = {ext.lower() for ext in extensions}
        files = [p for p in source_dir.rglob("*") if p.is_file() and p.suffix.lower() in ext_set]
        files.sort()
        
        if not files:
            raise ValueError(f"No images found in {source_dir}")
        
        # Incremental: filter out already indexed files
        if incremental and self.index_file.with_suffix('.faiss').exists():
            try:
                self.load()
                self._indexed_files = {meta['file_path'] for meta in self.index.metadata}
                original_count = len(files)
                files = [f for f in files if str(f) not in self._indexed_files]
                if show_progress:
                    print(f"📊 Incremental: {original_count - len(files):,} already indexed, {len(files):,} new")
                if not files:
                    return self.index.size()
            except Exception:
                self.index.clear()
        else:
            # Clear existing index
            self.index.clear()
            self._indexed_files = set()
        
        # Determine workers
        if workers == 0:
            # Auto: use most cores, leave 1-2 for system
            cpu_count = mp.cpu_count()
            workers = max(1, cpu_count - 1) if cpu_count <= 4 else max(4, cpu_count - 2)
        
        # Store min_face_size for filtering
        self._min_face_size = min_face_size
        
        start_faces = self.index.size()  # Start from existing if incremental
        total_faces = start_faces
        
        # Single-threaded mode (simpler, works with GPU)
        if workers == 1 or self._has_gpu:
            total_faces = self._build_single_threaded(
                files, detector_name, batch_size, show_progress, total_faces
            )
        else:
            # Multi-process mode (CPU-optimized with worker pooling)
            total_faces = self._build_multiprocess(
                files, detector_name, max_size, batch_size, workers, show_progress, total_faces, min_face_size
            )
        
        # Track source directory
        new_faces = total_faces - start_faces
        if new_faces > 0:
            self.index.add_source(str(source_dir.resolve()), new_faces)
        
        # Build co-occurrence data if enabled
        if self.enable_cooccurrence and self.cooccurrence_tracker:
            if show_progress:
                print("🔗 Building co-occurrence graph...")
            self._build_cooccurrence_data(show_progress)
        
        # Save index
        self.save()
        
        return total_faces
    
    def _build_single_threaded(self, files: List[Path], detector_name: str,
                                batch_size: int, show_progress: bool,
                                total_faces: int) -> int:
        """Single-threaded build (GPU-friendly) with batch embedding."""
        embeddings_batch = []
        metadata_batch = []
        
        detector = self.detector
        embedder = self.embedder
        image_loader = self.image_loader
        min_confidence = self.min_confidence
        min_face_size = getattr(self, '_min_face_size', 0)
        index_add = self.index.add
        
        # Accumulate faces for batch embedding
        pending_faces = []  # (face_img, metadata)
        EMBED_BATCH_SIZE = 32  # Batch faces for embedding
        
        pbar = tqdm(files, desc="Indexing", disable=not show_progress)
        
        for file_path in pbar:
            try:
                img = image_loader.load(file_path)
                if img is None:
                    continue
                
                faces = detector.detect(img)
                
                for i, face_data in enumerate(faces):
                    conf = face_data.get('confidence', 1.0)
                    if conf < min_confidence:
                        continue
                    
                    # Optional min face size filter
                    if min_face_size > 0:
                        area = face_data.get('facial_area', {})
                        w = area.get('w', 0)
                        h = area.get('h', 0)
                        if w < min_face_size or h < min_face_size:
                            continue
                    
                    face_img = (face_data['face'] * 255).astype(np.uint8)
                    meta = {
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'face_index': i,
                        'confidence': conf
                    }
                    pending_faces.append((face_img, meta))
                    
                    # Batch embed when we hit batch size
                    if len(pending_faces) >= EMBED_BATCH_SIZE:
                        face_imgs = [f[0] for f in pending_faces]
                        metas = [f[1] for f in pending_faces]
                        embs = embedder.embed_batch(face_imgs)
                        for emb, m in zip(embs, metas):
                            if emb is not None:
                                embeddings_batch.append(emb)
                                metadata_batch.append(m)
                                total_faces += 1
                        pending_faces = []
                
                # Insert to FAISS when batch is full
                if len(embeddings_batch) >= batch_size:
                    index_add(np.array(embeddings_batch), metadata_batch)
                    embeddings_batch = []
                    metadata_batch = []
                
                pbar.set_postfix({"faces": total_faces})
                
            except Exception:
                continue
        
        # Process remaining pending faces
        if pending_faces:
            face_imgs = [f[0] for f in pending_faces]
            metas = [f[1] for f in pending_faces]
            embs = embedder.embed_batch(face_imgs)
            for emb, m in zip(embs, metas):
                if emb is not None:
                    embeddings_batch.append(emb)
                    metadata_batch.append(m)
                    total_faces += 1
        
        if embeddings_batch:
            index_add(np.array(embeddings_batch), metadata_batch)
        
        return total_faces
    
    def _build_multiprocess(self, files: List[Path], detector_name: str,
                            max_size: int, batch_size: int, workers: int,
                            show_progress: bool, total_faces: int,
                            min_face_size: int = 0) -> int:
        """Multi-process build (CPU-optimized with worker pooling and smarter chunking)."""
        embeddings_batch = []
        metadata_batch = []
        index_add = self.index.add
        min_confidence = self.min_confidence
        
        # Smarter chunking: smaller chunks for better load balancing
        # Use ~10 files per chunk - lets faster workers grab more work
        chunk_size = 10
        file_chunks = []
        for i in range(0, len(files), chunk_size):
            file_chunks.append(files[i:i + chunk_size])
        
        # Prepare args: (file_paths_batch, min_confidence)
        args_list = [(chunk, min_confidence) for chunk in file_chunks]
        
        # Use Pool with initializer (reuses detector/embedder per worker)
        from multiprocessing import Pool
        
        with Pool(
            processes=workers,
            initializer=_init_worker,
            initargs=(detector_name, max_size, min_face_size)
        ) as pool:
            pbar = tqdm(
                pool.imap_unordered(_process_batch, args_list),
                total=len(args_list),
                desc=f"Indexing ({workers} workers)",
                disable=not show_progress
            )
            
            for results in pbar:
                for emb, meta in results:
                    embeddings_batch.append(emb)
                    metadata_batch.append(meta)
                    total_faces += 1
                
                # Batch insert to FAISS
                if len(embeddings_batch) >= batch_size:
                    index_add(np.array(embeddings_batch), metadata_batch)
                    embeddings_batch = []
                    metadata_batch = []
                
                pbar.set_postfix({"faces": total_faces})
        
        # Final batch
        if embeddings_batch:
            index_add(np.array(embeddings_batch), metadata_batch)
        
        return total_faces
    
    def _build_cooccurrence_data(self, show_progress: bool = True) -> None:
        """
        Build co-occurrence data from indexed faces.
        
        Groups faces by image and records which faces appear together.
        This enables context-aware search later.
        """
        if not self.cooccurrence_tracker:
            return
        
        # Clear existing data if rebuilding
        self.cooccurrence_tracker.clear()
        
        # Group faces by image path
        image_faces: dict = {}  # image_path -> [(face_idx, embedding)]
        
        for face_idx, meta in enumerate(self.index.metadata):
            file_path = meta['file_path']
            if file_path not in image_faces:
                image_faces[file_path] = []
            
            # Reconstruct embedding from FAISS
            embedding = self.index.index.reconstruct(face_idx)
            image_faces[file_path].append((face_idx, embedding))
        
        # Process each image with multiple faces
        multi_face_images = {k: v for k, v in image_faces.items() if len(v) >= 2}
        
        pbar = tqdm(
            multi_face_images.items(),
            desc="Building co-occurrence",
            disable=not show_progress
        )
        
        for image_path, faces in pbar:
            face_indices = [f[0] for f in faces]
            embeddings = [f[1] for f in faces]
            self.cooccurrence_tracker.add_image_faces(image_path, face_indices, embeddings)
        
        if show_progress:
            stats = self.cooccurrence_tracker.stats()
            print(f"   📊 {stats['total_clusters']} clusters, {stats['unique_pairs']} co-occurring pairs")

    def load_references(self, ref_dir: Path, use_cache: bool = True) -> int:
        """
        Load reference face embeddings.
        
        Args:
            ref_dir: Directory containing reference photos
            use_cache: Use cached embeddings if available
            
        Returns:
            Number of reference faces loaded
        """
        ref_dir = Path(ref_dir)
        if not ref_dir.exists():
            raise FileNotFoundError(f"Reference directory not found: {ref_dir}")
        
        ref_loader = ReferenceLoader(
            detector=self.detector,
            embedder=self.embedder,
            image_loader=self.image_loader
        )
        
        self.ref_embeddings, self.ref_names = ref_loader.load(ref_dir, use_cache)
        
        return len(self.ref_embeddings)
    
    def check_reference_quality(self) -> dict:
        """
        Analyze reference faces for consistency.
        
        Computes pairwise distances between refs to detect:
        - Inconsistent refs (might be different people)
        - Outlier refs (one bad photo)
        
        Returns:
            dict with:
            - 'consistent': bool - True if refs seem to be same person
            - 'avg_distance': float - Average pairwise distance
            - 'outliers': list - Names of refs that seem different
            - 'warning': str - Human-readable warning if issues found
        """
        if len(self.ref_embeddings) < 2:
            return {'consistent': True, 'avg_distance': 0, 'outliers': [], 'warning': None}
        
        # Only compare original refs (not flipped)
        original_embs = []
        original_names = []
        for emb, name in zip(self.ref_embeddings, self.ref_names):
            if "_flip" not in name:
                original_embs.append(emb)
                original_names.append(name)
        
        if len(original_embs) < 2:
            return {'consistent': True, 'avg_distance': 0, 'outliers': [], 'warning': None}
        
        # Compute pairwise distances
        n = len(original_embs)
        distances = []
        per_ref_avg = []
        
        for i in range(n):
            ref_distances = []
            for j in range(n):
                if i != j:
                    d = float(np.linalg.norm(original_embs[i] - original_embs[j]))
                    distances.append(d)
                    ref_distances.append(d)
            per_ref_avg.append(np.mean(ref_distances))
        
        avg_dist = np.mean(distances)
        
        # Find outliers (refs that are far from others)
        # Same person different angles can be 0.5-0.9, so be generous
        OUTLIER_THRESHOLD = 1.0  # Only flag if avg distance to others > 1.0 (very far)
        outliers = [original_names[i] for i, d in enumerate(per_ref_avg) if d > OUTLIER_THRESHOLD]
        
        # Consistency check - be generous since angles/expressions vary a lot
        # Same person: avg pairwise typically 0.3-0.7
        # Different people: avg pairwise typically 0.9+
        consistent = avg_dist < 0.85 and len(outliers) == 0
        
        warning = None
        if not consistent:
            if outliers:
                warning = f"⚠️ Check refs: {', '.join(outliers)} seem different from others."
            elif avg_dist > 0.9:
                warning = f"⚠️ Refs very different (avg: {avg_dist:.2f}). Might include different people."
        
        return {
            'consistent': consistent,
            'avg_distance': float(avg_dist),
            'outliers': outliers,
            'warning': warning
        }
    
    def search(self, 
               threshold: float = MEDIAN_THRESHOLD,
               top_k: int = 100,
               combine_refs: bool = True,
               strong_match_threshold: float = STRONG_MATCH_THRESHOLD,
               two_pass: bool = TWO_PASS_ENABLED) -> List[SearchResult]:
        """
        Search for faces matching loaded references.
        
        Uses smart 3-tier hybrid matching when multiple references provided:
        - Tier 1: Strong single match (any ref matches very close)
        - Tier 2: Majority vote (>50% of refs agree it's a match)
        - Tier 3: Median consensus (median distance is low)
        
        Two-pass search (if enabled):
        - Pass 1: Find matches with original refs
        - Pass 2: Use top strong matches as additional refs, search again
        - Catches photos where person looks different from original refs
        
        Args:
            threshold: Distance threshold for consensus match (0-1, lower = stricter)
            top_k: Max results per reference face
            combine_refs: If True, use hybrid matching with multiple refs.
                         If False, use best single match only.
            strong_match_threshold: Distance below which a single match is accepted (default 0.2)
            two_pass: If True, use top matches as additional refs for second pass
            
        Returns:
            List of SearchResult objects, deduplicated by file path and content
        """
        if not self.ref_embeddings:
            raise ValueError("No reference faces loaded. Call load_references() first.")
        
        if self.index.size() == 0:
            raise ValueError("Index is empty. Call build() or load() first.")
        
        # Store original refs for potential two-pass
        original_ref_embeddings = self.ref_embeddings.copy()
        original_ref_names = self.ref_names.copy()
        
        # First pass
        if combine_refs and len(self.ref_embeddings) > 1:
            matches = self._search_hybrid(threshold, top_k, strong_match_threshold)
        else:
            matches = self._search_individual(threshold, top_k)
        
        # Two-pass: Use top strong matches as additional refs
        if two_pass and matches:
            # Get top N strong matches (very confident)
            strong_matches = [m for m in matches if m.distance <= TWO_PASS_STRONG_THRESHOLD][:TWO_PASS_TOP_N]
            
            if strong_matches:
                # Get embeddings for these matches
                new_ref_embs = []
                new_ref_names = []
                
                for m in strong_matches:
                    # Find embedding in index
                    for idx, meta in enumerate(self.index.metadata):
                        if meta['file_path'] == m.file_path and meta.get('face_index', 0) == m.face_index:
                            emb = self.index.index.reconstruct(idx)
                            new_ref_embs.append(emb)
                            new_ref_names.append(f"pass2_{m.file_name}")
                            break
                
                if new_ref_embs:
                    # Combine original + new refs
                    self.ref_embeddings = original_ref_embeddings + new_ref_embs
                    self.ref_names = original_ref_names + new_ref_names
                    
                    # Second pass with expanded refs
                    if combine_refs:
                        pass2_matches = self._search_hybrid(threshold, top_k, strong_match_threshold)
                    else:
                        pass2_matches = self._search_individual(threshold, top_k)
                    
                    # Merge results (union, keeping best distance)
                    existing_paths = {m.file_path for m in matches}
                    for m in pass2_matches:
                        if m.file_path not in existing_paths:
                            matches.append(m)
                            existing_paths.add(m.file_path)
                    
                    # Re-sort
                    matches.sort(key=lambda x: x.distance)
                    
                    # Restore original refs
                    self.ref_embeddings = original_ref_embeddings
                    self.ref_names = original_ref_names
        
        # Final layer: remove duplicate images (same photo in different folders)
        return self._dedupe_by_image(matches)
    
    def search_with_context(self,
                            threshold: float = MEDIAN_THRESHOLD,
                            top_k: int = 100,
                            context_boost: float = CONTEXT_BOOST_WEIGHT,
                            min_cooccurrences: int = CONTEXT_MIN_COOCCURRENCES,
                            combine_refs: bool = True,
                            strong_match_threshold: float = STRONG_MATCH_THRESHOLD) -> List[ContextualMatch]:
        """
        Context-aware search using co-occurrence analysis.
        
        This method enhances search by considering who else appears in the photo:
        - If the target face appears with familiar companions (people they're often seen with),
          the confidence is boosted
        - If surrounding faces are strangers, no boost is applied
        
        This helps in cases where:
        - Face is partially obscured or at an angle
        - Photo quality is poor
        - Person looks different due to aging/makeup/lighting
        
        Example:
            If Alice always appears with Bob and Carol, and we find a face that looks
            somewhat like Alice next to Bob and Carol, we can be more confident it's Alice.
        
        Args:
            threshold: Base distance threshold for matching
            top_k: Max results per reference
            context_boost: Max distance reduction from context (0-1, default 0.15 = 15%)
            min_cooccurrences: Min historical sightings to trust context
            combine_refs: Use hybrid matching with multiple refs
            strong_match_threshold: Threshold for strong single match
            
        Returns:
            List of ContextualMatch objects with context scores and details
        """
        if not self.ref_embeddings:
            raise ValueError("No reference faces loaded. Call load_references() first.")
        
        if self.index.size() == 0:
            raise ValueError("Index is empty. Call build() or load() first.")
        
        if not self.cooccurrence_tracker:
            # Fall back to regular search if co-occurrence not available
            matches = self.search(threshold, top_k, combine_refs, strong_match_threshold)
            return [
                ContextualMatch(
                    result=m,
                    context_score=0.0,
                    familiar_faces=[],
                    total_cooccurrences=0,
                    nearby_faces_in_image=0
                )
                for m in matches
            ]
        
        # Get initial matches with looser threshold (we'll filter with context)
        search_threshold = min(threshold + context_boost + 0.1, 1.0)
        
        if combine_refs and len(self.ref_embeddings) > 1:
            initial_matches = self._search_hybrid(search_threshold, top_k * 2, strong_match_threshold)
        else:
            initial_matches = self._search_individual(search_threshold, top_k * 2)
        
        # Find which cluster the reference belongs to
        ref_cluster, ref_cluster_dist = self.cooccurrence_tracker.get_cluster_for_embedding(
            self.ref_embeddings[0]  # Use first ref as primary
        )
        
        # Process each match with context
        contextual_matches = []
        
        # Group faces by image for context lookup
        image_face_indices = {}  # image_path -> [face_idx]
        for idx, meta in enumerate(self.index.metadata):
            fp = meta['file_path']
            if fp not in image_face_indices:
                image_face_indices[fp] = []
            image_face_indices[fp].append(idx)
        
        for match in initial_matches:
            # Find other faces in the same image
            other_face_indices = image_face_indices.get(match.file_path, [])
            # Exclude the matched face itself
            other_face_indices = [
                idx for idx in other_face_indices 
                if self.index.metadata[idx].get('face_index', 0) != match.face_index
            ]
            
            nearby_faces = len(other_face_indices)
            context_score = 0.0
            familiar_faces = []
            total_cooccurrences = 0
            
            if ref_cluster is not None and nearby_faces > 0:
                # Get clusters for nearby faces
                nearby_clusters = []
                nearby_distances = []
                
                for idx in other_face_indices:
                    cluster_id = self.cooccurrence_tracker.get_cluster_for_face(idx)
                    if cluster_id is not None:
                        nearby_clusters.append(cluster_id)
                        # Get distance to cluster center
                        emb = self.index.index.reconstruct(idx)
                        _, dist = self.cooccurrence_tracker.get_cluster_for_embedding(emb)
                        nearby_distances.append(dist)
                
                if nearby_clusters:
                    # Compute context score
                    cooc_result = self.cooccurrence_tracker.compute_context_score(
                        ref_cluster, nearby_clusters, nearby_distances
                    )
                    
                    # Only trust context if we have sufficient historical data
                    if cooc_result.total_cooccurrences >= min_cooccurrences:
                        context_score = cooc_result.context_score
                        familiar_faces = cooc_result.familiar_faces
                        total_cooccurrences = cooc_result.total_cooccurrences
            
            # Apply context boost to distance
            boosted_distance = match.distance
            context_boost_applied = False
            
            if context_score > 0:
                # Reduce distance based on context (stronger context = bigger reduction)
                boost_factor = 1.0 - (context_score * context_boost)
                boosted_distance = match.distance * boost_factor
                context_boost_applied = True
            
            # Check if boosted match passes threshold
            if boosted_distance <= threshold:
                boosted_result = SearchResult(
                    file_path=match.file_path,
                    file_name=match.file_name,
                    distance=boosted_distance,
                    face_index=match.face_index,
                    context_score=context_score,
                    context_boost_applied=context_boost_applied
                )
                
                contextual_matches.append(ContextualMatch(
                    result=boosted_result,
                    context_score=context_score,
                    familiar_faces=familiar_faces,
                    total_cooccurrences=total_cooccurrences,
                    nearby_faces_in_image=nearby_faces
                ))
        
        # Sort by boosted distance
        contextual_matches.sort(key=lambda x: x.result.distance)
        
        # Dedupe
        seen_paths = set()
        deduped = []
        for cm in contextual_matches:
            if cm.result.file_path not in seen_paths:
                deduped.append(cm)
                seen_paths.add(cm.result.file_path)
        
        return deduped
    
    def get_cooccurrence_stats(self) -> Optional[dict]:
        """
        Get statistics about the co-occurrence graph.
        
        Returns:
            dict with cluster counts, pair counts, top co-occurring pairs, etc.
            None if co-occurrence tracking is disabled.
        """
        if not self.cooccurrence_tracker:
            return None
        return self.cooccurrence_tracker.stats()
    
    def get_companions(self, ref_embedding: Optional[np.ndarray] = None, 
                       min_count: int = 2) -> List[Tuple[int, int]]:
        """
        Get faces that frequently appear with the reference person.
        
        Args:
            ref_embedding: Reference embedding (uses loaded ref if None)
            min_count: Minimum co-occurrence count
            
        Returns:
            List of (cluster_id, count) for frequent companions
        """
        if not self.cooccurrence_tracker:
            return []
        
        if ref_embedding is None:
            if not self.ref_embeddings:
                return []
            ref_embedding = self.ref_embeddings[0]
        
        cluster_id, _ = self.cooccurrence_tracker.get_cluster_for_embedding(ref_embedding)
        if cluster_id is None:
            return []
        
        return self.cooccurrence_tracker.get_frequent_companions(cluster_id, min_count)

    def _search_hybrid(self, threshold: float, top_k: int, strong_threshold: float) -> List[SearchResult]:
        """
        Smart hybrid search with 4-tier acceptance:
        
        Tier 1 - SNIPER (Strong Single): If ANY single ref matches very close (<= 0.22) → instant accept.
                 (Handles perfect frontal matches even if others disagree).
                 
        Tier 2 - DOUBLE TAP (Verified): If TWO different refs match reasonably well (<= 0.32).
                 (More robust than sniper, statistically stronger than voting).

        Tier 3 - MAJORITY VOTE (Crowd): If enough refs "vote yes" based on user threshold.
                 (Robust to mixed quality or single bad reference).
        
        Tier 4 - MEDIAN CONSENSUS (Average): If median distance is low → accept.
                 (Catch-all for general similarity).
        
        This design handles:
        - Mixed quality refs (some frontal, some angled)
        - Accidental bad refs (wrong person in ref folder)
        - Same person with different appearances across photos
        """
        # Use provided threshold or default
        strong_th = strong_threshold if strong_threshold else STRONG_MATCH_THRESHOLD
        
        # Get candidates with generous threshold
        search_threshold = min(threshold + SEARCH_BUFFER, 1.0)
        
        # Group refs by base name (original + flip count as one ref)
        ref_groups = {}  # base_name -> [ref_indices]
        for idx, name in enumerate(self.ref_names):
            base_name = name.replace("_flip", "")
            if base_name not in ref_groups:
                ref_groups[base_name] = []
            ref_groups[base_name].append(idx)
        
        num_unique_refs = len(ref_groups)
        group_names = list(ref_groups.keys())
        
        # Track distances per file from each reference GROUP
        file_distances = {}  # file_path -> {group_idx: best_distance}
        file_meta = {}       # file_path -> metadata
        file_best = {}       # file_path -> best single distance
        
        for ref_idx, emb in enumerate(self.ref_embeddings):
            ref_name = self.ref_names[ref_idx]
            base_name = ref_name.replace("_flip", "")
            group_idx = group_names.index(base_name)
            
            results = self.index.search(emb, k=top_k * 2, threshold=search_threshold)
            
            for idx, distance in results:
                meta = self.index.get_metadata(idx)
                if not meta:
                    continue
                
                file_path = meta['file_path']
                
                if file_path not in file_distances:
                    file_distances[file_path] = {}
                    file_meta[file_path] = meta
                    file_best[file_path] = float('inf')
                
                # Track best distance per GROUP
                if group_idx not in file_distances[file_path]:
                    file_distances[file_path][group_idx] = distance
                else:
                    file_distances[file_path][group_idx] = min(
                        file_distances[file_path][group_idx], distance
                    )
                
                # Track overall best
                file_best[file_path] = min(file_best[file_path], distance)
        
        # Calculate scores and filter with 3-tier logic
        matches = []
        
        # Determine strictness based on user input
        active_th = threshold if threshold else MEDIAN_THRESHOLD
        
        # Dynamic strictness: more refs => stricter acceptance
        ref_strict = min(0.08, max(0.0, (num_unique_refs - 3) * 0.01))
        
        # Vote threshold: stricter with more refs.
        # Capped to prevent junk votes, and never looser than strong+0.05.
        vote_th = min(active_th * 1.05, 0.58) - ref_strict
        vote_th = max(vote_th, strong_th + 0.05)
        
        for file_path, group_distances in file_distances.items():
            best_single = file_best[file_path]
            
            # Get distances from each ref group (1.2 penalty for missing - higher penalty)
            all_distances = [group_distances.get(i, 1.2) for i in range(num_unique_refs)]
            
            # Calculate metrics
            median_dist = float(np.median(all_distances))
            sorted_distances = sorted(all_distances)
            top2_avg = float(np.mean(sorted_distances[:2])) if len(sorted_distances) >= 2 else sorted_distances[0]
            
            # Count how many refs "vote yes" (weighted by strength)
            # Stronger matches should contribute more to consensus.
            strong_vote_th = strong_th + 0.03
            mid_vote_th = min(strong_th + 0.10, vote_th)
            votes = 0.0
            for d in all_distances:
                if d <= strong_vote_th:
                    votes += 2.0  # very strong
                elif d <= mid_vote_th:
                    votes += 1.0  # solid
                elif d <= vote_th:
                    votes += 0.5  # weak-but-acceptable
            agreement_ratio = votes / max(1, num_unique_refs)
            
            # === 5-TIER ACCEPTANCE STRATEGY ===
            
            # Tier 0: The "Ultra Sniper" (Near-perfect match)
            ultra_th = max(0.0, strong_th - 0.02)
            tier0 = best_single <= ultra_th
            
            # Tier 1: The "Sniper" (Strong Single Match)
            # Trust any SINGLE reference that matches extremely well. 
            # This handles cases where only 1 perfect angle exists in the refs.
            tier1 = best_single <= strong_th
            
            # Tier 2: The "Twin Strong" (Top-2 Average)
            # If the best TWO refs are both very strong on average, accept.
            twin_th = strong_th + 0.04
            tier2 = top2_avg <= twin_th
            
            # Tier 3: The "Double Tap" (Verified Match)
            # TIGHTENED: Now requires 2 matches within +0.05 of strong threshold (was +0.10).
            # e.g., if Strong=0.22, DoubleTap=0.27. 
            # This filters out "lucky" double matches on generic faces.
            double_th = max(strong_th + 0.03, (strong_th + 0.05) - (ref_strict * 0.5))
            strong_votes = sum(1 for d in all_distances if d <= double_th)
            tier3 = strong_votes >= 2
            
            # Tier 4: Majority Vote (Crowd Wisdom)
            # SCALING STRICTNESS: The more reference images we have, the higher the standard.
            # - Small set (<4): Just need confirmation (33-50%).
            # - Medium set (4-8): Need Majority (>50%).
            # - Large set (>8): Need Supermajority (>60%).
            # This reduces false positives significantly when users provide lots of training data.
            if num_unique_refs < 3:
                min_votes = 1.0
            elif num_unique_refs <= 5:
                min_votes = max(2.0, num_unique_refs * 0.45)
            elif num_unique_refs <= 8:
                min_votes = num_unique_refs * 0.55
            else:
                min_votes = num_unique_refs * 0.60
                
            # Require at least one reasonably strong match to avoid "many weak votes"
            tier4 = votes >= min_votes and best_single <= (active_th - (0.03 + ref_strict * 0.5))
            
            # Tier 5: Median Consensus (Average Appearance)
            # Agreement-aware median limit: stricter when agreement is weak, lenient when agreement is strong.
            if agreement_ratio < 0.40:
                median_limit = active_th - 0.06 - (ref_strict * 0.5)
            elif agreement_ratio < 0.60:
                median_limit = active_th - 0.03 - (ref_strict * 0.5)
            else:
                median_limit = active_th - (ref_strict * 0.5)
            tier5 = median_dist <= median_limit and any(d <= (active_th - 0.05) for d in all_distances)
            
            if tier0 or tier1 or tier2 or tier3 or tier4 or tier5:
                meta = file_meta[file_path]
                
                # Score: prioritize strong matches, then use median for ranking
                if tier0 or tier1:
                    final_distance = best_single
                elif tier2:
                    final_distance = top2_avg
                elif tier3:
                    # Reward double tap matches with a boosted score
                    final_distance = (best_single + median_dist) / 2 * 0.9 
                else:
                    # Weight between best single and median
                    final_distance = 0.3 * best_single + 0.7 * median_dist
                
                result = SearchResult(
                    file_path=file_path,
                    file_name=meta['file_name'],
                    distance=final_distance,
                    face_index=meta['face_index']
                )
                matches.append(result)
        
        # Sort by distance
        matches.sort(key=lambda x: x.distance)
        return matches
    
    def _search_individual(self, threshold: float, top_k: int) -> List[SearchResult]:
        """Search using best single match (original behavior)."""
        # Collect all matches
        all_matches = {}  # file_path -> (distance, SearchResult)
        
        for emb, name in zip(self.ref_embeddings, self.ref_names):
            results = self.index.search(emb, k=top_k, threshold=threshold)
            
            for idx, distance in results:
                meta = self.index.get_metadata(idx)
                if not meta:
                    continue
                
                file_path = meta['file_path']
                
                # Keep best match per file
                if file_path not in all_matches or distance < all_matches[file_path][0]:
                    result = SearchResult(
                        file_path=file_path,
                        file_name=meta['file_name'],
                        distance=distance,
                        face_index=meta['face_index']
                    )
                    all_matches[file_path] = (distance, result)
        
        # Sort by distance and return
        matches = [r for _, r in sorted(all_matches.values(), key=lambda x: x[0])]
        return matches
    
    def _dedupe_by_image(self, matches: List[SearchResult]) -> List[SearchResult]:
        """
        Remove duplicate images (same photo in different folders).
        
        Step-by-step verification:
        1. Group by file size (fast filter)
        2. Check image dimensions
        3. Pixel-level comparison with OpenCV (final verification)
        
        Only removes if images are truly identical copies.
        """
        import cv2
        import os
        
        if len(matches) <= 1:
            return matches
        
        # Step 1: Group by file size (very fast)
        size_groups = {}  # file_size -> [match_indices]
        for i, m in enumerate(matches):
            try:
                file_size = os.path.getsize(m.file_path)
                if file_size not in size_groups:
                    size_groups[file_size] = []
                size_groups[file_size].append(i)
            except (OSError, IOError):
                continue
        
        # Only check groups with potential duplicates (same size)
        keep = [True] * len(matches)
        
        for file_size, indices in size_groups.items():
            if len(indices) < 2:
                continue  # No potential duplicates
            
            # Step 2 & 3: Compare images in this size group
            for i_idx in range(len(indices)):
                i = indices[i_idx]
                if not keep[i]:
                    continue
                
                img_i = None  # Lazy load
                
                for j_idx in range(i_idx + 1, len(indices)):
                    j = indices[j_idx]
                    if not keep[j]:
                        continue
                    
                    # Lazy load first image
                    if img_i is None:
                        img_i = cv2.imread(matches[i].file_path)
                        if img_i is None:
                            break  # Can't read, skip this image
                    
                    img_j = cv2.imread(matches[j].file_path)
                    if img_j is None:
                        continue
                    
                    # Step 2: Check dimensions
                    if img_i.shape != img_j.shape:
                        continue  # Different dimensions, not duplicates
                    
                    # Step 3: Pixel-level comparison
                    # Use normalized difference - allows for minor compression artifacts
                    diff = cv2.absdiff(img_i, img_j)
                    mean_diff = diff.mean()
                    
                    # Threshold: < 1.0 means nearly identical (allows minor JPEG artifacts)
                    if mean_diff < 1.0:
                        # Confirmed duplicate - keep the one with better match distance
                        # (matches are already sorted by distance, so i is better or equal)
                        keep[j] = False
        
        deduped = [m for m, k in zip(matches, keep) if k]
        
        if len(deduped) < len(matches):
            removed = len(matches) - len(deduped)
            # Could log: f"Removed {removed} duplicate images"
        
        return deduped
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save index and co-occurrence data to disk."""
        path = path or self.index_file
        self.index.save(path)
        
        # Save co-occurrence data
        if self.enable_cooccurrence and self.cooccurrence_tracker:
            cooc_path = Path(path).with_suffix('.cooccurrence.pkl')
            self.cooccurrence_tracker.save(cooc_path)
    
    def load(self, path: Optional[Path] = None) -> None:
        """Load index and co-occurrence data from disk."""
        path = path or self.index_file
        if not path.with_suffix('.faiss').exists():
            raise FileNotFoundError(f"Index not found: {path}")
        self.index.load(path)
        
        # Load co-occurrence data if available
        if self.enable_cooccurrence:
            cooc_path = Path(path).with_suffix('.cooccurrence.pkl')
            if cooc_path.exists():
                if not self.cooccurrence_tracker:
                    self.cooccurrence_tracker = CooccurrenceTracker(
                        cluster_threshold=COOCCURRENCE_CLUSTER_THRESHOLD
                    )
                self.cooccurrence_tracker.load(cooc_path)
    
    def stats(self) -> IndexStats:
        """Get index statistics."""
        unique_images = len(set(
            meta['file_path'] for meta in self.index.metadata
        ))
        
        index_size = 0
        if self.index_file.with_suffix('.faiss').exists():
            index_size = self.index_file.with_suffix('.faiss').stat().st_size
            if self.index_file.with_suffix('.pkl').exists():
                index_size += self.index_file.with_suffix('.pkl').stat().st_size
        
        # Co-occurrence stats
        cooc_clusters = 0
        cooc_pairs = 0
        if self.cooccurrence_tracker:
            cooc_stats = self.cooccurrence_tracker.stats()
            cooc_clusters = cooc_stats['total_clusters']
            cooc_pairs = cooc_stats['unique_pairs']
        
        return IndexStats(
            total_faces=self.index.size(),
            total_images=unique_images,
            embedding_dim=self.embedder.embedding_dim,
            detector_used=self.detector.name,
            index_size_mb=index_size / 1024 / 1024,
            cooccurrence_clusters=cooc_clusters,
            cooccurrence_pairs=cooc_pairs
        )
