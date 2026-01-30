"""
Caching layers for AST and query results.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import json
import time
import logging
import hashlib
from datetime import datetime, timedelta

from ..code_model import CodeNode
from .indexing import SearchResult, SearchType


@dataclass
class CacheEntry:
    """Cache entry with TTL"""
    data: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def touch(self):
        """Update access statistics"""
        self.access_count += 1
        self.last_accessed = datetime.now()


class ASTCache:
    """
    Cache for parsed ASTs to avoid re-parsing unchanged files.
    Uses file content hash as cache key.
    """
    
    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.ttl = timedelta(hours=ttl_hours)
        self.cache_file = self.cache_dir / "ast_cache.json"
        
        self._cache: Dict[str, CacheEntry] = {}
        self.logger = logging.getLogger(__name__)
        self._load_cache()
    
    def get(self, file_path: str, file_hash: str) -> Optional[List[CodeNode]]:
        """
        Get cached AST for file.
        
        Args:
            file_path: Path to file
            file_hash: MD5 hash of file content
            
        Returns:
            Cached CodeNodes or None if not found/expired
        """
        cache_key = self._get_cache_key(file_path, file_hash)
        
        if cache_key not in self._cache:
            return None
        
        entry = self._cache[cache_key]
        
        if entry.is_expired:
            self._remove_entry(cache_key)
            return None
        
        entry.touch()
        self._save_cache()  # Update access stats
        
        self.logger.debug(f"AST cache hit: {file_path}")
        return entry.data
    
    def set(self, file_path: str, file_hash: str, nodes: List[CodeNode]):
        """
        Cache AST for file.
        
        Args:
            file_path: Path to file
            file_hash: MD5 hash of file content
            nodes: Parsed CodeNodes
        """
        cache_key = self._get_cache_key(file_path, file_hash)
        
        entry = CacheEntry(
            data=nodes,
            created_at=datetime.now(),
            expires_at=datetime.now() + self.ttl
        )
        
        self._cache[cache_key] = entry
        self._save_cache()
        
        self.logger.debug(f"AST cache set: {file_path}")
    
    def invalidate_file(self, file_path: str):
        """Remove cached AST for specific file"""
        keys_to_remove = []
        for cache_key in self._cache.keys():
            if cache_key.startswith(f"{file_path}:"):
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            self._remove_entry(key)
        
        self.logger.debug(f"AST cache invalidated: {file_path}")
    
    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        self._save_cache()
    
    def cleanup_expired(self):
        """Remove expired entries"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            self._remove_entry(key)
        
        if expired_keys:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired AST cache entries")
    
    def get_size(self) -> Dict[str, int]:
        """Get cache statistics"""
        total_entries = len(self._cache)
        expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired)
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "cache_size_mb": self._estimate_cache_size()
        }
    
    def _get_cache_key(self, file_path: str, file_hash: str) -> str:
        """Generate cache key for file"""
        return f"{file_path}:{file_hash}"
    
    def _remove_entry(self, cache_key: str):
        """Remove cache entry"""
        if cache_key in self._cache:
            del self._cache[cache_key]
    
    def _estimate_cache_size(self) -> int:
        """Estimate cache size in MB"""
        try:
            import pickle
            total_size = 0
            for entry in self._cache.values():
                total_size += len(pickle.dumps(entry.data))
            return total_size // (1024 * 1024)  # Convert to MB
        except:
            return 0
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            data = {}
            for key, entry in self._cache.items():
                # Convert CodeNodes to dict for JSON serialization
                if isinstance(entry.data, list) and entry.data and isinstance(entry.data[0], CodeNode):
                    serialized_data = [node.to_dict() for node in entry.data]
                else:
                    serialized_data = entry.data
                
                data[key] = {
                    "data": serialized_data,
                    "created_at": entry.created_at.isoformat(),
                    "expires_at": entry.expires_at.isoformat(),
                    "access_count": entry.access_count,
                    "last_accessed": entry.last_accessed.isoformat()
                }
            
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save AST cache: {e}")
    
    def _load_cache(self):
        """Load cache from disk"""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            self._cache = {}
            for key, entry_data in data.items():
                # Reconstruct CodeNodes from dict
                serialized_data = entry_data["data"]
                if isinstance(serialized_data, list) and serialized_data:
                    try:
                        from ..code_model import CodeNode
                        reconstructed_data = [CodeNode.from_dict(node_dict) for node_dict in serialized_data]
                    except:
                        reconstructed_data = serialized_data
                else:
                    reconstructed_data = serialized_data
                
                entry = CacheEntry(
                    data=reconstructed_data,
                    created_at=datetime.fromisoformat(entry_data["created_at"]),
                    expires_at=datetime.fromisoformat(entry_data["expires_at"]),
                    access_count=entry_data["access_count"],
                    last_accessed=datetime.fromisoformat(entry_data["last_accessed"])
                )
                
                self._cache[key] = entry
                
        except Exception as e:
            self.logger.warning(f"Failed to load AST cache: {e}")
            self._cache = {}


class QueryCache:
    """
    Cache for search query results to avoid recomputation.
    Uses query hash as cache key.
    """
    
    def __init__(self, cache_dir: Path, ttl_minutes: int = 30, max_entries: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_entries = max_entries
        self.cache_file = self.cache_dir / "query_cache.json"
        
        self._cache: Dict[str, CacheEntry] = {}
        self._hit_count = 0
        self._miss_count = 0
        
        self.logger = logging.getLogger(__name__)
        self._load_cache()
    
    def get(self, query_hash: str) -> Optional[List[SearchResult]]:
        """
        Get cached search results.
        
        Args:
            query_hash: Hash of search query
            
        Returns:
            Cached search results or None
        """
        if query_hash not in self._cache:
            self._miss_count += 1
            return None
        
        entry = self._cache[query_hash]
        
        if entry.is_expired:
            self._remove_entry(query_hash)
            self._miss_count += 1
            return None
        
        entry.touch()
        self._hit_count += 1
        self._save_cache()
        
        self.logger.debug(f"Query cache hit: {query_hash[:8]}...")
        return entry.data
    
    def set(self, query_hash: str, results: List[SearchResult]):
        """
        Cache search results.
        
        Args:
            query_hash: Hash of search query
            results: Search results to cache
        """
        # Enforce max entries limit
        if len(self._cache) >= self.max_entries:
            self._evict_lru()
        
        entry = CacheEntry(
            data=results,
            created_at=datetime.now(),
            expires_at=datetime.now() + self.ttl
        )
        
        self._cache[query_hash] = entry
        self._save_cache()
        
        self.logger.debug(f"Query cache set: {query_hash[:8]}...")
    
    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0
        self._save_cache()
    
    def cleanup_expired(self):
        """Remove expired entries"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            self._remove_entry(key)
        
        if expired_keys:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired query cache entries")
    
    def get_hit_rate(self) -> float:
        """Get cache hit rate"""
        total_requests = self._hit_count + self._miss_count
        if total_requests == 0:
            return 0.0
        return self._hit_count / total_requests
    
    def get_size(self) -> Dict[str, int]:
        """Get cache statistics"""
        total_entries = len(self._cache)
        expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired)
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": f"{self.get_hit_rate():.2%}"
        }
    
    def _remove_entry(self, cache_key: str):
        """Remove cache entry"""
        if cache_key in self._cache:
            del self._cache[cache_key]
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self._cache:
            return
        
        # Find entry with oldest last_accessed
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )
        
        self._remove_entry(lru_key)
        self.logger.debug(f"Evicted LRU query cache entry: {lru_key[:8]}...")
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            data = {}
            for key, entry in self._cache.items():
                # Convert SearchResult objects to dict
                if isinstance(entry.data, list) and entry.data:
                    serialized_data = [result.to_dict() for result in entry.data]
                else:
                    serialized_data = entry.data
                
                data[key] = {
                    "data": serialized_data,
                    "created_at": entry.created_at.isoformat(),
                    "expires_at": entry.expires_at.isoformat(),
                    "access_count": entry.access_count,
                    "last_accessed": entry.last_accessed.isoformat()
                }
            
            # Save cache and stats
            cache_data = {
                "entries": data,
                "hit_count": self._hit_count,
                "miss_count": self._miss_count
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save query cache: {e}")
    
    def _load_cache(self):
        """Load cache from disk"""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Load stats
            self._hit_count = cache_data.get("hit_count", 0)
            self._miss_count = cache_data.get("miss_count", 0)
            
            # Load entries
            data = cache_data.get("entries", {})
            self._cache = {}
            
            for key, entry_data in data.items():
                # Reconstruct SearchResult objects from dict
                serialized_data = entry_data["data"]
                if isinstance(serialized_data, list) and serialized_data:
                    try:
                        from .core import SearchResult, SearchType
                        reconstructed_data = []
                        for result_dict in serialized_data:
                            # Reconstruct CodeNode
                            from ..code_model import CodeNode
                            node = CodeNode.from_dict(result_dict["node"])
                            
                            # Reconstruct SearchResult
                            result = SearchResult(
                                node=node,
                                score=result_dict["score"],
                                search_type=SearchType(result_dict["search_type"]),
                                explanation=result_dict.get("explanation", ""),
                                matched_terms=result_dict.get("matched_terms", [])
                            )
                            reconstructed_data.append(result)
                    except:
                        reconstructed_data = serialized_data
                else:
                    reconstructed_data = serialized_data
                
                entry = CacheEntry(
                    data=reconstructed_data,
                    created_at=datetime.fromisoformat(entry_data["created_at"]),
                    expires_at=datetime.fromisoformat(entry_data["expires_at"]),
                    access_count=entry_data["access_count"],
                    last_accessed=datetime.fromisoformat(entry_data["last_accessed"])
                )
                
                self._cache[key] = entry
                
        except Exception as e:
            self.logger.warning(f"Failed to load query cache: {e}")
            self._cache = {}


class CacheManager:
    """
    Unified cache manager for all caching layers.
    """
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.ast_cache = ASTCache(self.cache_dir / "ast")
        self.query_cache = QueryCache(self.cache_dir / "query")
        
        self.logger = logging.getLogger(__name__)
    
    def cleanup_all(self):
        """Cleanup expired entries in all caches"""
        self.ast_cache.cleanup_expired()
        self.query_cache.cleanup_expired()
    
    def clear_all(self):
        """Clear all caches"""
        self.ast_cache.clear()
        self.query_cache.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics for all caches"""
        return {
            "ast_cache": self.ast_cache.get_size(),
            "query_cache": self.query_cache.get_size()
        }
