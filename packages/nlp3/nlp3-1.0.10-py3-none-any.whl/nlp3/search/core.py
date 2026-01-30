"""
Core search engine combining all optimization layers.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
import time
import logging
from pathlib import Path

from ..code_model import CodeNode, CodeRepository
from .indexing import InvertedIndex, VectorIndex, SearchType, SearchResult
from .parsing import IncrementalParser
from .cache import ASTCache, QueryCache


@dataclass
class SearchQuery:
    """Search query with options"""
    text: str
    search_type: SearchType = SearchType.HYBRID
    node_types: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    file_patterns: Optional[List[str]] = None
    limit: int = 50
    min_score: float = 0.1
    
    def __post_init__(self):
        if isinstance(self.search_type, str):
            self.search_type = SearchType(self.search_type)


class OptimizedSearchEngine:
    """
    Multi-layer search engine with indexing, caching, and incremental parsing.
    
    Architecture:
    1. IncrementalParser - Parses only changed files
    2. ASTCache - Caches parsed ASTs
    3. InvertedIndex - Fast syntactic search (Whoosh)
    4. VectorIndex - Semantic search (FAISS)
    5. QueryCache - Caches query results
    """
    
    def __init__(self, repository_path: str, index_dir: str = ".nlp3_index"):
        self.repository_path = Path(repository_path)
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.parser = IncrementalParser(repository_path)
        self.ast_cache = ASTCache(self.index_dir / "ast_cache")
        self.query_cache = QueryCache(self.index_dir / "query_cache")
        self.inverted_index = InvertedIndex(self.index_dir / "text_index")
        self.vector_index = VectorIndex(self.index_dir / "vector_index")
        
        self.logger = logging.getLogger(__name__)
        self._repository: Optional[CodeRepository] = None
        
    @property
    def repository(self) -> CodeRepository:
        """Lazy load repository"""
        if self._repository is None:
            self._repository = self.parser.parse_repository()
        return self._repository
    
    def index_repository(self, force_reindex: bool = False) -> Dict[str, Any]:
        """
        Index the entire repository with all optimization layers.
        
        Args:
            force_reindex: Force complete reindexing
            
        Returns:
            Indexing statistics
        """
        start_time = time.time()
        
        # Parse repository (incremental if not forced)
        self.logger.info(f"Indexing repository: {self.repository_path}")
        repository = self.parser.parse_repository(force_reparse=force_reindex)
        
        # Clear indices if forced
        if force_reindex:
            self.inverted_index.clear()
            self.vector_index.clear()
            self.query_cache.clear()
        
        # Index all nodes
        all_nodes = self._collect_all_nodes(repository)
        
        # Build inverted index
        text_start = time.time()
        self.inverted_index.index_nodes(all_nodes)
        text_time = time.time() - text_start
        
        # Build vector index
        vector_start = time.time()
        self.vector_index.index_nodes(all_nodes)
        vector_time = time.time() - vector_start
        
        total_time = time.time() - start_time
        
        stats = {
            "total_nodes": len(all_nodes),
            "total_files": repository.total_files,
            "text_index_time": text_time,
            "vector_index_time": vector_time,
            "total_time": total_time,
            "languages": repository.language_distribution
        }
        
        self.logger.info(f"Indexing completed: {stats}")
        return stats
    
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Search using optimized multi-layer approach.
        
        Args:
            query: Search query with options
            
        Returns:
            List of search results
        """
        # Check query cache first
        cache_key = self._get_cache_key(query)
        cached_result = self.query_cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Cache hit for query: {query.text}")
            return cached_result
        
        start_time = time.time()
        results = []
        
        # Route to appropriate search method
        if query.search_type == SearchType.SYNTACTIC:
            results = self._syntactic_search(query)
        elif query.search_type == SearchType.SEMANTIC:
            results = self._semantic_search(query)
        else:  # HYBRID
            results = self._hybrid_search(query)
        
        # Apply filters
        results = self._apply_filters(results, query)
        
        # Sort by score and limit
        results.sort(key=lambda r: r.score, reverse=True)
        results = results[:query.limit]
        
        # Filter by minimum score
        results = [r for r in results if r.score >= query.min_score]
        
        search_time = time.time() - start_time
        
        # Cache results
        self.query_cache.set(cache_key, results)
        
        self.logger.debug(f"Search completed in {search_time:.3f}s: {len(results)} results")
        return results
    
    def _syntactic_search(self, query: SearchQuery) -> List[SearchResult]:
        """Fast syntactic search using inverted index"""
        return self.inverted_index.search(query.text, limit=query.limit * 2)
    
    def _semantic_search(self, query: SearchQuery) -> List[SearchResult]:
        """Semantic search using vector index"""
        return self.vector_index.search(query.text, limit=query.limit * 2)
    
    def _hybrid_search(self, query: SearchQuery) -> List[SearchResult]:
        """Combined syntactic + semantic search"""
        syntactic_results = self._syntactic_search(query)
        semantic_results = self._semantic_search(query)
        
        # Merge and re-score
        merged_results = self._merge_results(syntactic_results, semantic_results)
        return merged_results
    
    def _merge_results(self, syntactic: List[SearchResult], semantic: List[SearchResult]) -> List[SearchResult]:
        """Merge syntactic and semantic results with combined scoring"""
        node_scores = {}
        
        # Add syntactic scores (weight: 0.6)
        for result in syntactic:
            node_id = result.node.id
            if node_id not in node_scores:
                node_scores[node_id] = {"node": result.node, "syntactic": 0, "semantic": 0}
            node_scores[node_id]["syntactic"] = result.score * 0.6
        
        # Add semantic scores (weight: 0.4)
        for result in semantic:
            node_id = result.node.id
            if node_id not in node_scores:
                node_scores[node_id] = {"node": result.node, "syntactic": 0, "semantic": 0}
            node_scores[node_id]["semantic"] = result.score * 0.4
        
        # Create combined results
        combined = []
        for node_id, scores in node_scores.items():
            combined_score = scores["syntactic"] + scores["semantic"]
            if combined_score > 0:
                result = SearchResult(
                    node=scores["node"],
                    score=combined_score,
                    search_type=SearchType.HYBRID,
                    explanation=f"Syntactic: {scores['syntactic']:.2f}, Semantic: {scores['semantic']:.2f}"
                )
                combined.append(result)
        
        return combined
    
    def _apply_filters(self, results: List[SearchResult], query: SearchQuery) -> List[SearchResult]:
        """Apply node type, language, and file pattern filters"""
        filtered = results
        
        # Node type filter
        if query.node_types:
            filtered = [r for r in filtered if r.node.node_type.value in query.node_types]
        
        # Language filter
        if query.languages:
            filtered = [r for r in filtered if r.node.language.value in query.languages]
        
        # File pattern filter
        if query.file_patterns:
            import fnmatch
            filtered = [
                r for r in filtered 
                if any(fnmatch.fnmatch(r.node.file_path, pattern) for pattern in query.file_patterns)
            ]
        
        return filtered
    
    def _collect_all_nodes(self, repository: CodeRepository) -> List[CodeNode]:
        """Flatten all nodes from repository"""
        all_nodes = []
        for module in repository.modules:
            all_nodes.extend(self._flatten_nodes(module))
        return all_nodes
    
    def _flatten_nodes(self, node: CodeNode) -> List[CodeNode]:
        """Recursively flatten node tree"""
        nodes = [node]
        for child in node.children:
            nodes.extend(self._flatten_nodes(child))
        return nodes
    
    def _get_cache_key(self, query: SearchQuery) -> str:
        """Generate cache key for query"""
        import hashlib
        key_data = f"{query.text}:{query.search_type.value}:{query.limit}:{query.min_score}"
        if query.node_types:
            key_data += f":types:{','.join(query.node_types)}"
        if query.languages:
            key_data += f":langs:{','.join(query.languages)}"
        if query.file_patterns:
            key_data += f":patterns:{','.join(query.file_patterns)}"
        
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        repo_stats = self.repository.get_statistics()
        
        return {
            "repository": repo_stats,
            "indexing": {
                "text_index_size": self.inverted_index.get_size(),
                "vector_index_size": self.vector_index.get_size(),
                "ast_cache_size": self.ast_cache.get_size(),
                "query_cache_size": self.query_cache.get_size()
            },
            "performance": {
                "last_index_time": getattr(self, '_last_index_time', None),
                "cache_hit_rate": self.query_cache.get_hit_rate()
            }
        }
    
    def update_index(self, changed_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Update index for changed files (incremental update).
        
        Args:
            changed_files: List of changed file paths (auto-detected if None)
            
        Returns:
            Update statistics
        """
        start_time = time.time()
        
        # Detect changed files if not provided
        if changed_files is None:
            changed_files = self.parser.get_changed_files()
        
        if not changed_files:
            return {"updated_files": 0, "time": 0}
        
        self.logger.info(f"Updating index for {len(changed_files)} changed files")
        
        # Parse changed files
        updated_nodes = []
        for file_path in changed_files:
            # Convert string to Path if needed
            file_path_obj = Path(file_path) if isinstance(file_path, str) else file_path
            
            # Remove old nodes from indices
            self._remove_file_from_indices(file_path_obj)
            
            # Parse and add new nodes
            nodes = self.parser.parse_file(file_path_obj)
            updated_nodes.extend(nodes)
        
        # Update indices
        self.inverted_index.index_nodes(updated_nodes)
        self.vector_index.index_nodes(updated_nodes)
        
        # Clear query cache (indices changed)
        self.query_cache.clear()
        
        update_time = time.time() - start_time
        self._last_index_time = update_time
        
        return {
            "updated_files": len(changed_files),
            "updated_nodes": len(updated_nodes),
            "time": update_time
        }
    
    def _remove_file_from_indices(self, file_path: str):
        """Remove all nodes from a file from indices"""
        # Find nodes to remove
        nodes_to_remove = []
        for module in self.repository.modules:
            if module.file_path == file_path:
                nodes_to_remove.extend(self._flatten_nodes(module))
        
        # Remove from indices
        for node in nodes_to_remove:
            self.inverted_index.remove_node(node.id)
            self.vector_index.remove_node(node.id)
