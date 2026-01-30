"""
Code Query Engine

Advanced query engine for code repositories with semantic and structural search capabilities.
"""

import re
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .code_model import CodeNode, NodeType as CodeNodeType, Language
from .universal_parser import UniversalCodeParser
from .nlp import NLPEngine, IntentType, PredicateType


class QueryType(Enum):
    """Types of code queries"""
    STRUCTURAL = "structural"  # Based on AST structure
    SEMANTIC = "semantic"      # Based on embeddings/similarity
    TEXTUAL = "textual"        # Based on text search
    METRIC = "metric"          # Based on code metrics
    DEPENDENCY = "dependency"  # Based on call/import graphs


@dataclass
class QueryResult:
    """Result of a code query"""
    nodes: List[CodeNode]
    query_type: QueryType
    confidence: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CodeIndex:
    """Inverted index for fast code search"""
    
    # Text indices
    token_to_nodes: Dict[str, Set[str]] = None
    name_to_nodes: Dict[str, Set[str]] = None
    
    # Structural indices
    function_to_calls: Dict[str, Set[str]] = None
    class_to_methods: Dict[str, Set[str]] = None
    import_to_modules: Dict[str, Set[str]] = None
    
    # Language indices
    language_to_nodes: Dict[str, Set[str]] = None
    
    # Node lookup
    nodes: Dict[str, CodeNode] = None
    
    def __post_init__(self):
        if self.token_to_nodes is None:
            self.token_to_nodes = {}
        if self.name_to_nodes is None:
            self.name_to_nodes = {}
        if self.function_to_calls is None:
            self.function_to_calls = {}
        if self.class_to_methods is None:
            self.class_to_methods = {}
        if self.import_to_modules is None:
            self.import_to_modules = {}
        if self.language_to_nodes is None:
            self.language_to_nodes = {}
        if self.nodes is None:
            self.nodes = {}


class CodeQueryEngine:
    """Advanced code query engine"""
    
    def __init__(self):
        self.parser = UniversalCodeParser()
        self.nlp_engine = NLPEngine(enable_spell_check=False)
        self.index = CodeIndex()
        self.repository = None
    
    def index_repository(self, repository):
        """Build search index for repository"""
        self.repository = repository
        self._build_index()
    
    def _build_index(self):
        """Build inverted indices"""
        self.index = CodeIndex()
        
        for module in self.repository.modules:
            self._index_node(module)
    
    def _index_node(self, node: CodeNode):
        """Index a single node and its children"""
        node_id = node.id
        self.index.nodes[node_id] = node
        
        # Language index
        lang = node.language.value
        if lang not in self.index.language_to_nodes:
            self.index.language_to_nodes[lang] = set()
        self.index.language_to_nodes[lang].add(node_id)
        
        # Name index
        if node.name:
            name_lower = node.name.lower()
            if name_lower not in self.index.name_to_nodes:
                self.index.name_to_nodes[name_lower] = set()
            self.index.name_to_nodes[name_lower].add(node_id)
        
        # Token index (from body, docstring, etc.)
        tokens = self._extract_tokens(node)
        for token in tokens:
            if token not in self.index.token_to_nodes:
                self.index.token_to_nodes[token] = set()
            self.index.token_to_nodes[token].add(node_id)
        
        # Structural indices
        if node.node_type == CodeNodeType.FUNCTION:
            self.index.function_to_calls[node_id] = set(node.calls)
        elif node.node_type == CodeNodeType.CLASS:
            self.index.class_to_methods[node_id] = set(
                child.id for child in node.children 
                if child.node_type == CodeNodeType.METHOD
            )
        
        # Import index
        for import_name in node.imports:
            if import_name not in self.index.import_to_modules:
                self.index.import_to_modules[import_name] = set()
            self.index.import_to_modules[import_name].add(node_id)
        
        # Index children
        for child in node.children:
            self._index_node(child)
    
    def _extract_tokens(self, node: CodeNode) -> Set[str]:
        """Extract searchable tokens from node"""
        tokens = set()
        
        # From name
        if node.name:
            tokens.update(self._tokenize(node.name))
        
        # From body
        if node.body:
            tokens.update(self._tokenize(node.body))
        
        # From docstring
        if node.docstring:
            tokens.update(self._tokenize(node.docstring))
        
        # From annotations/decorators
        for annotation in node.annotations:
            tokens.update(self._tokenize(annotation))
        
        for decorator in node.decorators:
            tokens.update(self._tokenize(decorator))
        
        return tokens
    
    def _tokenize(self, text: str) -> Set[str]:
        """Tokenize text for indexing"""
        # Split on common delimiters and normalize
        tokens = re.split(r'[\W_]+', text.lower())
        return {token for token in tokens if token and len(token) > 2}
    
    def query(self, query_text: str, query_type: QueryType = QueryType.TEXTUAL) -> QueryResult:
        """Execute query on indexed repository"""
        if not self.repository:
            return QueryResult([], query_type, 0.0)
        
        # Parse natural language query
        parsed_query = self.nlp_engine.parse_query(query_text)
        
        # Route to appropriate query handler
        if query_type == QueryType.STRUCTURAL:
            return self._structural_query(parsed_query)
        elif query_type == QueryType.SEMANTIC:
            return self._semantic_query(parsed_query)
        elif query_type == QueryType.DEPENDENCY:
            return self._dependency_query(parsed_query)
        elif query_type == QueryType.METRIC:
            return self._metric_query(parsed_query)
        else:
            return self._textual_query(parsed_query)
    
    def _textual_query(self, parsed_query) -> QueryResult:
        """Text-based search query"""
        results = []
        query_tokens = self._tokenize(parsed_query.original)
        
        # Find nodes matching tokens
        candidate_nodes = set()
        for token in query_tokens:
            if token in self.index.token_to_nodes:
                candidate_nodes.update(self.index.token_to_nodes[token])
        
        # Rank by relevance (number of matching tokens)
        scored_nodes = []
        for node_id in candidate_nodes:
            node = self.index.nodes[node_id]
            node_tokens = self._extract_tokens(node)
            score = len(query_tokens.intersection(node_tokens)) / len(query_tokens)
            scored_nodes.append((node, score))
        
        # Sort by score
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        
        results = [node for node, score in scored_nodes if score > 0.1]
        confidence = scored_nodes[0][1] if scored_nodes else 0.0
        
        return QueryResult(results, QueryType.TEXTUAL, confidence)
    
    def _structural_query(self, parsed_query) -> QueryResult:
        """Structure-based query"""
        results = []
        
        for predicate in parsed_query.intent.predicates:
            if predicate.type == PredicateType.FUNCTION:
                # Find functions by name
                name_lower = predicate.value.lower()
                if name_lower in self.index.name_to_nodes:
                    for node_id in self.index.name_to_nodes[name_lower]:
                        node = self.index.nodes[node_id]
                        if node.node_type == CodeNodeType.FUNCTION:
                            results.append(node)
            
            elif predicate.type == PredicateType.CLASS_NAME:
                # Find classes by name
                name_lower = predicate.value.lower()
                if name_lower in self.index.name_to_nodes:
                    for node_id in self.index.name_to_nodes[name_lower]:
                        node = self.index.nodes[node_id]
                        if node.node_type == CodeNodeType.CLASS:
                            results.append(node)
            
            elif predicate.type == PredicateType.LANGUAGE:
                # Find nodes by language
                lang = predicate.value
                if lang in self.index.language_to_nodes:
                    for node_id in self.index.language_to_nodes[lang]:
                        results.append(self.index.nodes[node_id])
            
            elif predicate.type == PredicateType.IMPORT:
                # Find modules that import specific dependency
                import_name = predicate.value
                if import_name in self.index.import_to_modules:
                    for node_id in self.index.import_to_modules[import_name]:
                        results.append(self.index.nodes[node_id])
        
        confidence = 1.0 if results else 0.0
        return QueryResult(results, QueryType.STRUCTURAL, confidence)
    
    def _semantic_query(self, parsed_query) -> QueryResult:
        """Semantic similarity query (placeholder for future embedding support)"""
        # For now, fall back to textual search
        # TODO: Implement embeddings and cosine similarity
        return self._textual_query(parsed_query)
    
    def _dependency_query(self, parsed_query) -> QueryResult:
        """Dependency graph query"""
        results = []
        
        for predicate in parsed_query.intent.predicates:
            if predicate.type == PredicateType.FUNCTION:
                # Find functions that call this function
                func_name = predicate.value
                for node_id, calls in self.index.function_to_calls.items():
                    if func_name in calls:
                        results.append(self.index.nodes[node_id])
            
            elif predicate.type == PredicateType.IMPORT:
                # Find modules that import this dependency
                import_name = predicate.value
                if import_name in self.index.import_to_modules:
                    for node_id in self.index.import_to_modules[import_name]:
                        results.append(self.index.nodes[node_id])
        
        confidence = 1.0 if results else 0.0
        return QueryResult(results, QueryType.DEPENDENCY, confidence)
    
    def _metric_query(self, parsed_query) -> QueryResult:
        """Metric-based query"""
        results = []
        
        # Find nodes by metrics
        for node in self.index.nodes.values():
            # High complexity
            if node.complexity > 10:
                node.tags.append("high_complexity")
                results.append(node)
            
            # Long functions
            if node.node_type == CodeNodeType.FUNCTION and node.lines_of_code > 50:
                node.tags.append("long_function")
                results.append(node)
            
            # Functions without docstrings
            if node.node_type == CodeNodeType.FUNCTION and not node.docstring:
                node.tags.append("no_docstring")
                results.append(node)
        
        confidence = 1.0 if results else 0.0
        return QueryResult(results, QueryType.METRIC, confidence)
    
    def find_similar_functions(self, function_name: str, limit: int = 10) -> List[CodeNode]:
        """Find functions with similar names or patterns"""
        name_lower = function_name.lower()
        candidates = []
        
        for node in self.index.nodes.values():
            if node.node_type == CodeNodeType.FUNCTION and node.name:
                # Simple similarity based on name
                node_name_lower = node.name.lower()
                similarity = self._name_similarity(name_lower, node_name_lower)
                if similarity > 0.3:  # Threshold
                    candidates.append((node, similarity))
        
        # Sort by similarity
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        return [node for node, similarity in candidates[:limit]]
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """Simple name similarity calculation"""
        # Check for common prefixes/suffixes
        if name1.startswith(name2) or name2.startswith(name1):
            return 0.8
        
        # Check for common substrings
        common_words = {'get', 'set', 'create', 'update', 'delete', 'find', 'list', 'handle', 'process'}
        words1 = set(name1.split('_'))
        words2 = set(name2.split('_'))
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def get_call_graph(self, function_name: str) -> Dict[str, List[str]]:
        """Get call graph for a function"""
        call_graph = {"calls": [], "called_by": []}
        
        # Find the function
        func_node = None
        for node in self.index.nodes.values():
            if node.node_type == CodeNodeType.FUNCTION and node.name == function_name:
                func_node = node
                break
        
        if not func_node:
            return call_graph
        
        # Get functions this function calls
        call_graph["calls"] = list(func_node.calls)
        
        # Get functions that call this function
        func_id = func_node.id
        for node_id, calls in self.index.function_to_calls.items():
            if func_name in calls:
                caller = self.index.nodes[node_id]
                call_graph["called_by"].append(caller.name)
        
        return call_graph
    
    def get_repository_overview(self) -> Dict[str, Any]:
        """Get repository overview statistics"""
        if not self.repository:
            return {}
        
        stats = self.repository.get_statistics()
        
        # Add index statistics
        stats["index_stats"] = {
            "total_nodes": len(self.index.nodes),
            "total_tokens": len(self.index.token_to_nodes),
            "total_functions": len([n for n in self.index.nodes.values() if n.node_type == CodeNodeType.FUNCTION]),
            "total_classes": len([n for n in self.index.nodes.values() if n.node_type == CodeNodeType.CLASS]),
            "total_imports": len(self.index.import_to_modules),
        }
        
        return stats
    
    def suggest_refactoring(self) -> List[Dict[str, Any]]:
        """Suggest refactoring opportunities"""
        suggestions = []
        
        for node in self.index.nodes.values():
            if node.node_type == CodeNodeType.FUNCTION:
                # Long function
                if node.lines_of_code > 50:
                    suggestions.append({
                        "type": "long_function",
                        "node": node.name,
                        "file": node.file_path,
                        "lines": node.lines_of_code,
                        "suggestion": f"Consider breaking down {node.name} into smaller functions"
                    })
                
                # High complexity
                if node.complexity > 10:
                    suggestions.append({
                        "type": "high_complexity",
                        "node": node.name,
                        "file": node.file_path,
                        "complexity": node.complexity,
                        "suggestion": f"Consider simplifying {node.name} to reduce complexity"
                    })
                
                # No docstring
                if not node.docstring:
                    suggestions.append({
                        "type": "missing_docstring",
                        "node": node.name,
                        "file": node.file_path,
                        "suggestion": f"Add docstring to {node.name}"
                    })
        
        return suggestions
