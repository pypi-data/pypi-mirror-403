"""
Indexing layer for fast syntactic and semantic search.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
import logging
import re
import hashlib
from enum import Enum

from ..code_model import CodeNode


class SearchType(Enum):
    """Search types"""
    SYNTACTIC = "syntactic"  # Fast text search
    SEMANTIC = "semantic"    # Vector similarity
    HYBRID = "hybrid"        # Combined approach


@dataclass
class SearchResult:
    """Search result with metadata"""
    node: CodeNode
    score: float
    search_type: SearchType
    explanation: str = ""
    matched_terms: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node": self.node.to_dict(),
            "score": self.score,
            "search_type": self.search_type.value,
            "explanation": self.explanation,
            "matched_terms": self.matched_terms
        }


class TextTokenizer:
    """Advanced tokenizer for code search"""
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tokenize code text with camelCase/snake_case splitting"""
        if not text:
            return []
        
        tokens = []
        
        # Split camelCase and PascalCase
        camel_split = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?![a-z])', text)
        tokens.extend(camel_split)
        
        # Split snake_case and kebab-case
        snake_split = re.split(r'[_\-]+', text)
        tokens.extend(snake_split)
        
        # Split on non-alphanumeric
        alnum_split = re.findall(r'[a-zA-Z0-9]+', text)
        tokens.extend(alnum_split)
        
        # Normalize and filter
        normalized = []
        for token in tokens:
            token = token.lower().strip()
            if len(token) >= 2:  # Filter very short tokens
                normalized.append(token)
        
        return list(set(normalized))  # Remove duplicates
    
    @staticmethod
    def extract_identifiers(text: str) -> List[str]:
        """Extract code identifiers (function names, variables, etc.)"""
        # Match function definitions, variable names, class names
        patterns = [
            r'\bdef\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # Python functions
            r'\bclass\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # Python classes
            r'\bfunction\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # JS functions
            r'\bconst\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # JS constants
            r'\bvar\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # JS variables
            r'\blet\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # JS let
            r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',  # Function calls
        ]
        
        identifiers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            identifiers.extend(matches)
        
        return list(set(identifiers))


class InvertedIndex:
    """
    Fast inverted index for syntactic search using Whoosh-like approach.
    Stores token -> node_id mappings for O(1) lookup.
    """
    
    def __init__(self, index_dir: Path):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory index structures
        self.token_to_nodes: Dict[str, Set[str]] = {}
        self.node_to_tokens: Dict[str, Set[str]] = {}
        self.node_store: Dict[str, CodeNode] = {}
        
        # Persistence
        self.index_file = self.index_dir / "inverted_index.json"
        self.nodes_file = self.index_dir / "nodes.json"
        
        self.logger = logging.getLogger(__name__)
        self._load_index()
    
    def index_nodes(self, nodes: List[CodeNode]):
        """Index multiple code nodes"""
        for node in nodes:
            self._index_node(node)
        self._save_index()
    
    def _index_node(self, node: CodeNode):
        """Index a single code node"""
        node_id = node.id
        
        # Extract searchable text
        searchable_fields = [
            node.name or "",
            node.body,
            node.docstring or "",
            node.comment or "",
            " ".join(node.annotations),
            " ".join(node.decorators),
            " ".join(node.imports),
            " ".join(node.calls)
        ]
        
        # Tokenize all fields
        all_tokens = set()
        for field in searchable_fields:
            tokens = TextTokenizer.tokenize(field)
            all_tokens.update(tokens)
        
        # Add identifier tokens
        for field in searchable_fields:
            identifiers = TextTokenizer.extract_identifiers(field)
            all_tokens.update(identifiers)
        
        # Store node
        self.node_store[node_id] = node
        
        # Update token mappings
        self.node_to_tokens[node_id] = all_tokens
        for token in all_tokens:
            if token not in self.token_to_nodes:
                self.token_to_nodes[token] = set()
            self.token_to_nodes[token].add(node_id)
    
    def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """
        Search using inverted index with token matching.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of search results
        """
        # Tokenize query
        query_tokens = TextTokenizer.tokenize(query)
        
        if not query_tokens:
            return []
        
        # Find nodes containing all tokens (AND operation)
        result_sets = []
        for token in query_tokens:
            if token in self.token_to_nodes:
                result_sets.append(self.token_to_nodes[token])
        
        if not result_sets:
            return []
        
        # Intersection for exact match
        if len(result_sets) > 1:
            matching_node_ids = set.intersection(*result_sets)
        else:
            matching_node_ids = result_sets[0]
        
        # Create results with scoring
        results = []
        for node_id in matching_node_ids:
            node = self.node_store.get(node_id)
            if not node:
                continue
            
            # Calculate score based on token coverage
            node_tokens = self.node_to_tokens.get(node_id, set())
            matched_tokens = set(query_tokens) & node_tokens
            score = len(matched_tokens) / len(query_tokens)
            
            result = SearchResult(
                node=node,
                score=score,
                search_type=SearchType.SYNTACTIC,
                explanation=f"Matched {len(matched_tokens)}/{len(query_tokens)} tokens",
                matched_terms=list(matched_tokens)
            )
            results.append(result)
        
        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]
    
    def remove_node(self, node_id: str):
        """Remove a node from the index"""
        if node_id in self.node_store:
            node = self.node_store[node_id]
            del self.node_store[node_id]
        
        if node_id in self.node_to_tokens:
            tokens = self.node_to_tokens[node_id]
            for token in tokens:
                if token in self.token_to_nodes:
                    self.token_to_nodes[token].discard(node_id)
                    if not self.token_to_nodes[token]:
                        del self.token_to_nodes[token]
            del self.node_to_tokens[node_id]
    
    def clear(self):
        """Clear all index data"""
        self.token_to_nodes.clear()
        self.node_to_tokens.clear()
        self.node_store.clear()
        self._save_index()
    
    def get_size(self) -> Dict[str, int]:
        """Get index statistics"""
        return {
            "total_tokens": len(self.token_to_nodes),
            "total_nodes": len(self.node_store),
            "total_token_mappings": sum(len(nodes) for nodes in self.token_to_nodes.values())
        }
    
    def _save_index(self):
        """Save index to disk"""
        import json
        
        # Convert sets to lists for JSON serialization
        serializable_data = {
            "token_to_nodes": {k: list(v) for k, v in self.token_to_nodes.items()},
            "node_to_tokens": {k: list(v) for k, v in self.node_to_tokens.items()},
            "nodes": {k: v.to_dict() for k, v in self.node_store.items()}
        }
        
        with open(self.index_file, 'w') as f:
            json.dump(serializable_data, f, indent=2)
    
    def _load_index(self):
        """Load index from disk"""
        import json
        
        if not self.index_file.exists():
            return
        
        try:
            with open(self.index_file, 'r') as f:
                data = json.load(f)
            
            # Convert lists back to sets
            self.token_to_nodes = {k: set(v) for k, v in data.get("token_to_nodes", {}).items()}
            self.node_to_tokens = {k: set(v) for k, v in data.get("node_to_tokens", {}).items()}
            
            # Reconstruct nodes
            from ..code_model import CodeNode
            self.node_store = {}
            for node_id, node_data in data.get("nodes", {}).items():
                self.node_store[node_id] = CodeNode.from_dict(node_data)
                
        except Exception as e:
            self.logger.warning(f"Failed to load index: {e}")


class VectorIndex:
    """
    Vector index for semantic search using FAISS-like approach.
    Stores embeddings for similarity search.
    """
    
    def __init__(self, index_dir: Path):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory vector storage
        self.node_embeddings: Dict[str, List[float]] = {}
        self.node_store: Dict[str, CodeNode] = {}
        self.embedding_dim = 384  # Default for sentence-transformers
        
        # Persistence
        self.vectors_file = self.index_dir / "vectors.json"
        self.nodes_file = self.index_dir / "vector_nodes.json"
        
        self.logger = logging.getLogger(__name__)
        self._embedding_model = None
        self._load_index()
    
    def _get_embedding_model(self):
        """Lazy load embedding model"""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.embedding_dim = self._embedding_model.get_sentence_embedding_dimension()
            except ImportError:
                self.logger.warning("sentence-transformers not available, using dummy embeddings")
                self._embedding_model = DummyEmbeddingModel()
        
        return self._embedding_model
    
    def index_nodes(self, nodes: List[CodeNode]):
        """Index multiple code nodes with embeddings"""
        model = self._get_embedding_model()
        
        for node in nodes:
            self._index_node(node, model)
        
        self._save_index()
    
    def _index_node(self, node: CodeNode, model):
        """Index a single code node with embedding"""
        node_id = node.id
        
        # Create text representation for embedding
        text_parts = []
        
        if node.name:
            text_parts.append(node.name)
        
        if node.docstring:
            text_parts.append(node.docstring)
        
        if node.body:
            # Limit body size for embedding
            body_preview = node.body[:500]
            text_parts.append(body_preview)
        
        if node.comment:
            text_parts.append(node.comment)
        
        # Combine for embedding
        full_text = " ".join(text_parts)
        
        # Generate embedding
        embedding = model.encode(full_text)
        
        # Ensure embedding is a list
        if hasattr(embedding, 'tolist'):
            embedding = embedding.tolist()
        elif not isinstance(embedding, list):
            embedding = list(embedding)
        
        # Store
        self.node_embeddings[node_id] = embedding
        self.node_store[node_id] = node
    
    def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """
        Search using vector similarity.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of search results
        """
        if not self.node_embeddings:
            return []
        
        model = self._get_embedding_model()
        
        # Generate query embedding
        query_embedding = model.encode(query)
        
        # Calculate similarities
        results = []
        for node_id, node_embedding in self.node_embeddings.items():
            node = self.node_store.get(node_id)
            if not node:
                continue
            
            # Cosine similarity
            similarity = self._cosine_similarity(query_embedding, node_embedding)
            
            if similarity > 0.1:  # Minimum similarity threshold
                result = SearchResult(
                    node=node,
                    score=similarity,
                    search_type=SearchType.SEMANTIC,
                    explanation=f"Semantic similarity: {similarity:.3f}"
                )
                results.append(result)
        
        # Sort by similarity
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]
    
    def _cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)
    
    def remove_node(self, node_id: str):
        """Remove a node from the vector index"""
        if node_id in self.node_embeddings:
            del self.node_embeddings[node_id]
        if node_id in self.node_store:
            del self.node_store[node_id]
    
    def clear(self):
        """Clear all vector data"""
        self.node_embeddings.clear()
        self.node_store.clear()
        self._save_index()
    
    def get_size(self) -> Dict[str, int]:
        """Get vector index statistics"""
        return {
            "total_nodes": len(self.node_embeddings),
            "embedding_dim": self.embedding_dim,
            "total_embeddings": len(self.node_embeddings)
        }
    
    def _save_index(self):
        """Save vector index to disk"""
        import json
        
        data = {
            "embeddings": self.node_embeddings,
            "nodes": {k: v.to_dict() for k, v in self.node_store.items()},
            "embedding_dim": self.embedding_dim
        }
        
        with open(self.vectors_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_index(self):
        """Load vector index from disk"""
        import json
        
        if not self.vectors_file.exists():
            return
        
        try:
            with open(self.vectors_file, 'r') as f:
                data = json.load(f)
            
            self.node_embeddings = data.get("embeddings", {})
            self.embedding_dim = data.get("embedding_dim", 384)
            
            # Reconstruct nodes
            from ..code_model import CodeNode
            self.node_store = {}
            for node_id, node_data in data.get("nodes", {}).items():
                self.node_store[node_id] = CodeNode.from_dict(node_data)
                
        except Exception as e:
            self.logger.warning(f"Failed to load vector index: {e}")


class DummyEmbeddingModel:
    """Dummy embedding model when sentence-transformers is not available"""
    
    def encode(self, text: str) -> List[float]:
        """Generate dummy embedding based on text hash"""
        import hashlib
        
        # Create deterministic but pseudo-random embedding
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert to float values
        embedding = []
        for i in range(0, len(hash_hex), 2):
            hex_pair = hash_hex[i:i+2]
            val = int(hex_pair, 16) / 255.0  # Normalize to [0, 1]
            embedding.append(val)
        
        # Pad/truncate to desired dimension
        while len(embedding) < 384:
            embedding.extend(embedding[:min(384 - len(embedding), len(embedding))])
        
        return embedding[:384]
    
    def get_sentence_embedding_dimension(self) -> int:
        return 384
