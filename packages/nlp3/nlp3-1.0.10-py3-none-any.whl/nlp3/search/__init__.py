"""
NLP3 Optimized Search Engine

Fast code search with indexing, caching, and semantic search.
Implements multi-layer search architecture for large repositories.
"""

__version__ = "0.1.0"
__author__ = "WronAI"

from .core import OptimizedSearchEngine, SearchQuery
from .indexing import InvertedIndex, VectorIndex, SearchResult, SearchType
from .parsing import IncrementalParser
from .cache import ASTCache, QueryCache

__all__ = [
    "OptimizedSearchEngine",
    "SearchQuery", 
    "SearchResult",
    "SearchType",
    "InvertedIndex",
    "VectorIndex",
    "IncrementalParser",
    "ASTCache",
    "QueryCache"
]
