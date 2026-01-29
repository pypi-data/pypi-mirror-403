"""
Co-occurrence tracking for social context verification.

This module tracks which faces appear together in photos to enable
context-aware face verification. When multiple faces are found in the
same image, we build a "social graph" that can later be used to boost
confidence in face matches.

Example:
    If Alice, Bob, and Carol frequently appear together, and we find
    a face that looks like Alice next to Bob and Carol, we can be
    more confident it's actually Alice.
"""

import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class CooccurrenceMatch:
    """Result from co-occurrence analysis."""
    face_id: int
    context_score: float  # 0-1, higher = more familiar context
    familiar_faces: List[int]  # IDs of co-occurring faces we've seen together
    total_cooccurrences: int  # Total times we've seen this combo


class CooccurrenceTracker:
    """
    Tracks which faces appear together in photos.
    
    Builds a co-occurrence matrix where entry (i, j) represents
    how many times face cluster i appeared with face cluster j.
    
    Uses face embeddings to build clusters via approximate matching,
    then tracks co-occurrences at the cluster level.
    """
    
    def __init__(self, cluster_threshold: float = 0.4):
        """
        Initialize tracker.
        
        Args:
            cluster_threshold: Max embedding distance to consider same cluster
        """
        self.cluster_threshold = cluster_threshold
        
        # Cluster centers: cluster_id -> representative embedding
        self.cluster_centers: Dict[int, np.ndarray] = {}
        
        # Co-occurrence counts: (cluster_i, cluster_j) -> count
        # Stored symmetrically: if (i,j) exists, (j,i) has same value
        self.cooccurrence_counts: Dict[Tuple[int, int], int] = defaultdict(int)
        
        # Image to clusters mapping: image_path -> set of cluster_ids
        self.image_clusters: Dict[str, Set[int]] = {}
        
        # Face to cluster mapping: face_idx -> cluster_id
        # face_idx is global index in FAISS
        self.face_to_cluster: Dict[int, int] = {}
        
        # Next cluster ID
        self._next_cluster_id = 0
        
        # Statistics
        self.total_images_processed = 0
        self.total_faces_clustered = 0
    
    def _find_or_create_cluster(self, embedding: np.ndarray) -> int:
        """
        Find existing cluster for embedding or create new one.
        
        Args:
            embedding: Face embedding vector
            
        Returns:
            Cluster ID
        """
        embedding = embedding / max(np.linalg.norm(embedding), 1e-12)
        
        # Find closest existing cluster
        best_cluster = None
        best_distance = float('inf')
        
        for cluster_id, center in self.cluster_centers.items():
            distance = 1 - np.dot(embedding, center)  # Cosine distance
            if distance < best_distance:
                best_distance = distance
                best_cluster = cluster_id
        
        # If close enough to existing cluster, use it
        if best_cluster is not None and best_distance <= self.cluster_threshold:
            # Update cluster center (running average)
            old_center = self.cluster_centers[best_cluster]
            # Weight towards existing center to prevent drift
            new_center = 0.9 * old_center + 0.1 * embedding
            self.cluster_centers[best_cluster] = new_center / max(np.linalg.norm(new_center), 1e-12)
            return best_cluster
        
        # Create new cluster
        new_id = self._next_cluster_id
        self._next_cluster_id += 1
        self.cluster_centers[new_id] = embedding
        return new_id
    
    def add_image_faces(self, image_path: str, face_indices: List[int], 
                        embeddings: List[np.ndarray]) -> List[int]:
        """
        Record faces from a single image and update co-occurrence matrix.
        
        Args:
            image_path: Path to the image
            face_indices: FAISS indices for each face
            embeddings: Embedding vectors for each face
            
        Returns:
            List of cluster IDs assigned to each face
        """
        if len(face_indices) != len(embeddings):
            raise ValueError("face_indices and embeddings must have same length")
        
        # Assign each face to a cluster
        cluster_ids = []
        for face_idx, emb in zip(face_indices, embeddings):
            cluster_id = self._find_or_create_cluster(emb)
            cluster_ids.append(cluster_id)
            self.face_to_cluster[face_idx] = cluster_id
        
        # Store image -> clusters mapping
        cluster_set = set(cluster_ids)
        self.image_clusters[image_path] = cluster_set
        
        # Update co-occurrence counts for all pairs
        cluster_list = list(cluster_set)
        for i in range(len(cluster_list)):
            for j in range(i + 1, len(cluster_list)):
                ci, cj = cluster_list[i], cluster_list[j]
                # Store with smaller ID first for consistency
                key = (min(ci, cj), max(ci, cj))
                self.cooccurrence_counts[key] += 1
        
        self.total_images_processed += 1
        self.total_faces_clustered += len(face_indices)
        
        return cluster_ids
    
    def get_cluster_for_face(self, face_idx: int) -> Optional[int]:
        """Get cluster ID for a face index."""
        return self.face_to_cluster.get(face_idx)
    
    def get_cluster_for_embedding(self, embedding: np.ndarray) -> Tuple[Optional[int], float]:
        """
        Find the best matching cluster for an embedding.
        
        Returns:
            (cluster_id, distance) or (None, inf) if no match
        """
        embedding = embedding / max(np.linalg.norm(embedding), 1e-12)
        
        best_cluster = None
        best_distance = float('inf')
        
        for cluster_id, center in self.cluster_centers.items():
            distance = 1 - np.dot(embedding, center)
            if distance < best_distance:
                best_distance = distance
                best_cluster = cluster_id
        
        if best_distance <= self.cluster_threshold:
            return best_cluster, best_distance
        return None, float('inf')
    
    def get_cooccurrence_count(self, cluster_a: int, cluster_b: int) -> int:
        """Get number of times two clusters appeared together."""
        key = (min(cluster_a, cluster_b), max(cluster_a, cluster_b))
        return self.cooccurrence_counts.get(key, 0)
    
    def get_frequent_companions(self, cluster_id: int, min_count: int = 2) -> List[Tuple[int, int]]:
        """
        Get clusters that frequently appear with a given cluster.
        
        Args:
            cluster_id: The cluster to find companions for
            min_count: Minimum co-occurrence count to include
            
        Returns:
            List of (companion_cluster_id, count) sorted by count descending
        """
        companions = []
        
        for (ci, cj), count in self.cooccurrence_counts.items():
            if count < min_count:
                continue
            if ci == cluster_id:
                companions.append((cj, count))
            elif cj == cluster_id:
                companions.append((ci, count))
        
        companions.sort(key=lambda x: x[1], reverse=True)
        return companions
    
    def compute_context_score(self, 
                               target_cluster: int, 
                               nearby_clusters: List[int],
                               nearby_distances: Optional[List[float]] = None) -> CooccurrenceMatch:
        """
        Compute a context score based on whether nearby faces are familiar.
        
        The score measures how "expected" the surrounding faces are given
        our knowledge of who the target usually appears with.
        
        Args:
            target_cluster: Cluster ID of the face we're verifying
            nearby_clusters: Cluster IDs of other faces in the same image
            nearby_distances: Optional distances of nearby faces to their clusters
                             (used to weight the score)
        
        Returns:
            CooccurrenceMatch with context score and details
        """
        if not nearby_clusters:
            return CooccurrenceMatch(
                face_id=target_cluster,
                context_score=0.0,
                familiar_faces=[],
                total_cooccurrences=0
            )
        
        # Get all companions of target
        companions = dict(self.get_frequent_companions(target_cluster, min_count=1))
        
        if not companions:
            return CooccurrenceMatch(
                face_id=target_cluster,
                context_score=0.0,
                familiar_faces=[],
                total_cooccurrences=0
            )
        
        # Calculate how many nearby faces are expected companions
        familiar_faces = []
        total_cooccurrences = 0
        weighted_score = 0.0
        max_possible_score = 0.0
        
        for i, nearby_cluster in enumerate(nearby_clusters):
            if nearby_cluster in companions:
                count = companions[nearby_cluster]
                familiar_faces.append(nearby_cluster)
                total_cooccurrences += count
                
                # Weight by co-occurrence frequency and optionally by embedding confidence
                weight = np.log1p(count)  # Log scale to prevent single high count from dominating
                if nearby_distances and i < len(nearby_distances):
                    # Closer matches (lower distance) contribute more
                    confidence = max(0, 1 - nearby_distances[i])
                    weight *= confidence
                
                weighted_score += weight
            
            max_possible_score += np.log1p(max(companions.values()) if companions else 1)
        
        # Normalize score to 0-1
        if max_possible_score > 0:
            context_score = min(1.0, weighted_score / max_possible_score)
        else:
            context_score = 0.0
        
        # Bonus for having multiple familiar faces
        if len(familiar_faces) >= 2:
            context_score = min(1.0, context_score * 1.2)
        
        return CooccurrenceMatch(
            face_id=target_cluster,
            context_score=context_score,
            familiar_faces=familiar_faces,
            total_cooccurrences=total_cooccurrences
        )
    
    def save(self, path: Path) -> None:
        """Save co-occurrence data to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert numpy arrays to lists for pickling
        cluster_centers_serializable = {
            k: v.tolist() for k, v in self.cluster_centers.items()
        }
        
        data = {
            'cluster_threshold': self.cluster_threshold,
            'cluster_centers': cluster_centers_serializable,
            'cooccurrence_counts': dict(self.cooccurrence_counts),
            'image_clusters': {k: list(v) for k, v in self.image_clusters.items()},
            'face_to_cluster': self.face_to_cluster,
            'next_cluster_id': self._next_cluster_id,
            'total_images_processed': self.total_images_processed,
            'total_faces_clustered': self.total_faces_clustered,
        }
        
        with open(path, 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, path: Path) -> None:
        """Load co-occurrence data from disk."""
        path = Path(path)
        
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        self.cluster_threshold = data['cluster_threshold']
        self.cluster_centers = {
            k: np.array(v) for k, v in data['cluster_centers'].items()
        }
        self.cooccurrence_counts = defaultdict(int, data['cooccurrence_counts'])
        self.image_clusters = {k: set(v) for k, v in data['image_clusters'].items()}
        self.face_to_cluster = data['face_to_cluster']
        self._next_cluster_id = data['next_cluster_id']
        self.total_images_processed = data['total_images_processed']
        self.total_faces_clustered = data['total_faces_clustered']
    
    def stats(self) -> dict:
        """Get statistics about co-occurrence tracking."""
        # Count total co-occurrence pairs
        total_pairs = len(self.cooccurrence_counts)
        total_cooccurrences = sum(self.cooccurrence_counts.values())
        
        # Find most frequent pairs
        top_pairs = sorted(
            self.cooccurrence_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_clusters': len(self.cluster_centers),
            'total_images': self.total_images_processed,
            'total_faces': self.total_faces_clustered,
            'unique_pairs': total_pairs,
            'total_cooccurrences': total_cooccurrences,
            'top_pairs': top_pairs,
            'avg_faces_per_image': (
                self.total_faces_clustered / max(1, self.total_images_processed)
            ),
        }
    
    def clear(self) -> None:
        """Clear all tracking data."""
        self.cluster_centers = {}
        self.cooccurrence_counts = defaultdict(int)
        self.image_clusters = {}
        self.face_to_cluster = {}
        self._next_cluster_id = 0
        self.total_images_processed = 0
        self.total_faces_clustered = 0
