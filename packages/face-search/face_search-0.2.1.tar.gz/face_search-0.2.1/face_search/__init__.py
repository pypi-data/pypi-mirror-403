"""
face-finder: AI-powered face search for photo libraries
"""

__version__ = "0.1.0"
__author__ = "Emin Genç"

from .core import FaceFinder
from .models import SearchResult, IndexStats, ContextualMatch
from .cooccurrence import CooccurrenceTracker, CooccurrenceMatch

__all__ = [
    "FaceFinder", 
    "SearchResult", 
    "IndexStats", 
    "ContextualMatch",
    "CooccurrenceTracker",
    "CooccurrenceMatch"
]
