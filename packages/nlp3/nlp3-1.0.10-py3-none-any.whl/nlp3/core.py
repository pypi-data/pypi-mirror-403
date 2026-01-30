"""Core NLP2Tree Components"""

from enum import Enum
from typing import Protocol, Iterator, Optional, Any, Dict, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncio
import os
import time
import logging
from pathlib import Path


class NodeType(Enum):
    """Type of tree node"""
    BRANCH = "branch"  # Has children
    LEAF = "leaf"      # No children, has value


@dataclass
class NodeMetadata:
    """Metadata for tree nodes"""
    size: Optional[int] = None
    modified: Optional[float] = None
    mime_type: Optional[str] = None
    permissions: Optional[str] = None
    extra: Dict[str, Any] = None


class TreeNode(Protocol):
    """Universal tree node protocol"""
    
    @property
    def name(self) -> str:
        """Node name"""
        ...
    
    @property
    def path(self) -> str:
        """Full path from root"""
        ...
    
    @property
    def node_type(self) -> NodeType:
        """BRANCH or LEAF"""
        ...
    
    @property
    def metadata(self) -> NodeMetadata:
        """Node metadata"""
        ...
    
    def children(self) -> Iterator['TreeNode']:
        """Get child nodes"""
        ...
    
    def parent(self) -> Optional['TreeNode']:
        """Get parent node"""
        ...
    
    def value(self) -> Any:
        """Get value for leaf nodes"""
        ...


class BaseTreeNode(ABC):
    """Base implementation of TreeNode"""
    
    def __init__(self, name: str, path: str, node_type: NodeType, 
                 metadata: Optional[NodeMetadata] = None):
        self._name = name
        self._path = path
        self._node_type = node_type
        self._metadata = metadata or NodeMetadata()
        self._parent: Optional['BaseTreeNode'] = None
        self._children: List['BaseTreeNode'] = []
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def path(self) -> str:
        return self._path
    
    @property
    def node_type(self) -> NodeType:
        return self._node_type
    
    @property
    def metadata(self) -> NodeMetadata:
        return self._metadata
    
    def children(self) -> Iterator['TreeNode']:
        return iter(self._children)
    
    def parent(self) -> Optional['TreeNode']:
        return self._parent
    
    def add_child(self, child: 'BaseTreeNode'):
        """Add child node"""
        child._parent = self
        self._children.append(child)
    
    @abstractmethod
    def value(self) -> Any:
        """Get value for leaf nodes"""
        pass


class TreeAdapter(ABC):
    """Base adapter for different data sources"""
    
    @abstractmethod
    async def build_tree(self, source: Any, **kwargs) -> TreeNode:
        """Build tree from data source"""
        pass
    
    @abstractmethod
    def supports(self, source: Any) -> bool:
        """Check if adapter supports this source type"""
        pass


class TreeNavigator:
    """Main navigator class"""
    
    def __init__(self):
        self._adapters: List[TreeAdapter] = []
        # Import NLP engine here to avoid circular imports
        from .nlp import NLPEngine
        self._nlp_engine = NLPEngine()
    
    def register_adapter(self, adapter: TreeAdapter):
        """Register a new adapter"""
        self._adapters.append(adapter)
    
    async def query(self, query_text: str, source: Any, **kwargs) -> List[TreeNode]:
        """Execute natural language query on data source"""
        # Find appropriate adapter
        adapter = self._find_adapter(source)
        if not adapter:
            raise ValueError(f"No adapter found for source: {type(source)}")
        
        # Build tree
        tree = await adapter.build_tree(source, **kwargs)
        
        # Parse query with NLP engine
        parsed_query = self._nlp_engine.parse_query(query_text)
        
        # Process query with parsed intent
        return self._process_query(parsed_query, tree)
    
    def _find_adapter(self, source: Any) -> Optional[TreeAdapter]:
        """Find adapter that supports the source"""
        for adapter in self._adapters:
            if adapter.supports(source):
                return adapter
        return None
    
    def _process_query(self, parsed_query, tree: TreeNode) -> List[TreeNode]:
        """Process natural language query using parsed intent"""
        from .nlp import IntentType, PredicateType
        
        results = []
        
        # Check if we're dealing with code and route appropriately
        is_code_tree = hasattr(tree, 'code_node') or (
            hasattr(tree, 'metadata') and 
            hasattr(tree.metadata, 'language') and 
            tree.metadata.language != 'unknown'
        )
        
        # For code trees with generic FIND/LIST intents, upgrade to CODE_SEARCH
        if is_code_tree and parsed_query.intent.type in [IntentType.FIND, IntentType.LIST]:
            # Extract search terms from query for code search
            query_text = parsed_query.original.lower()
            
            # Create function predicate if "funkcje" or "functions" is mentioned
            if 'funkcje' in query_text or 'function' in query_text:
                from .nlp import Intent, Predicate
                # Create CODE_SEARCH intent with function predicate
                code_intent = Intent(
                    type=IntentType.CODE_SEARCH,
                    confidence=0.8,
                    target='code_search',
                    predicates=[
                        Predicate(
                            type=PredicateType.FUNCTION,
                            value='',  # Empty means all functions
                            operator='contains',
                            confidence=0.8
                        )
                    ]
                )
                parsed_query.intent = code_intent
        
        # Handle code-specific intents
        if parsed_query.intent.type == IntentType.SECURITY_SCAN:
            results = self._handle_security_scan(tree, parsed_query.intent.predicates)
        elif parsed_query.intent.type == IntentType.DEPENDENCY_ANALYSIS:
            results = self._handle_dependency_analysis(tree, parsed_query.intent.predicates)
        elif parsed_query.intent.type == IntentType.CODE_SEARCH:
            results = self._handle_code_search(tree, parsed_query.intent.predicates)
        elif parsed_query.intent.type == IntentType.FUNCTION_ANALYSIS:
            results = self._handle_function_analysis(tree, parsed_query.intent.predicates)
        elif parsed_query.intent.type == IntentType.METRICS:
            results = self._handle_metrics(tree, parsed_query.intent.predicates)
        elif parsed_query.intent.type == IntentType.REFACTOR:
            results = self._handle_refactor(tree, parsed_query.intent.predicates)
        elif parsed_query.intent.type == IntentType.DEBUG:
            results = self._handle_debug(tree, parsed_query.intent.predicates)
        
        # If it's a FIND or LIST intent, search the tree
        elif parsed_query.intent.type in [IntentType.FIND, IntentType.LIST]:
            results = self._search_tree(tree, parsed_query.intent.predicates)
        
        # If it's a TREE intent, return the root
        elif parsed_query.intent.type == IntentType.TREE:
            results = [tree]
        
        # If no predicates, return direct children
        elif not parsed_query.intent.predicates:
            results = list(tree.children())
        
        return results
    
    def _handle_security_scan(self, tree: TreeNode, predicates: List) -> List[TreeNode]:
        """Handle security scan queries"""
        results = []
        
        # Security patterns to look for
        security_patterns = [
            'eval', 'exec', 'subprocess', 'os.system', 'shell_exec',
            'sql', 'execute', 'query', 'input', 'request', 'pickle',
            'marshal', 'compile', '__import__'
        ]
        
        for node in self._flatten_tree(tree):
            # Check node content for security patterns
            content = self._get_node_content(node).lower()
            if any(pattern in content for pattern in security_patterns):
                results.append(node)
        
        return results
    
    def _handle_dependency_analysis(self, tree: TreeNode, predicates: List) -> List[TreeNode]:
        """Handle dependency analysis queries"""
        results = []
        
        for predicate in predicates:
            if predicate.type == PredicateType.IMPORT:
                # Find nodes that import specific dependency
                for node in self._flatten_tree(tree):
                    content = self._get_node_content(node)
                    if predicate.value.lower() in content.lower():
                        results.append(node)
        
        return results
    
    def _handle_code_search(self, tree: TreeNode, predicates: List) -> List[TreeNode]:
        """Handle code search queries"""
        from .nlp import PredicateType
        results = []
        
        for predicate in predicates:
            if predicate.type == PredicateType.FUNCTION:
                # Find functions by name or all functions if empty
                for node in self._flatten_tree(tree):
                    if self._is_function_node(node):
                        # If predicate value is empty, return all functions
                        if not predicate.value or predicate.value == '':
                            results.append(node)
                        # Otherwise match by name
                        elif node.name and node.name.lower() == predicate.value.lower():
                            results.append(node)
            
            elif predicate.type == PredicateType.CLASS_NAME:
                # Find classes by name
                for node in self._flatten_tree(tree):
                    if self._is_class_node(node) and node.name and node.name.lower() == predicate.value.lower():
                        results.append(node)
        
        return results
    
    def _handle_function_analysis(self, tree: TreeNode, predicates: List) -> List[TreeNode]:
        """Handle function analysis queries"""
        results = []
        
        for predicate in predicates:
            if predicate.type == PredicateType.FUNCTION:
                # Find specific function for analysis
                for node in self._flatten_tree(tree):
                    if self._is_function_node(node) and node.name and node.name.lower() == predicate.value.lower():
                        results.append(node)
        
        return results
    
    def _handle_metrics(self, tree: TreeNode, predicates: List) -> List[TreeNode]:
        """Handle metrics queries"""
        # Return all nodes for metrics analysis
        return self._flatten_tree(tree)
    
    def _handle_refactor(self, tree: TreeNode, predicates: List) -> List[TreeNode]:
        """Handle refactoring queries"""
        results = []
        
        # Look for code smells
        for node in self._flatten_tree(tree):
            content = self._get_node_content(node)
            
            # Long functions/classes
            if len(content.split('\n')) > 50:
                results.append(node)
            
            # High complexity (simple heuristic)
            complexity_indicators = ['if ', 'for ', 'while ', 'try:', 'except', 'with ']
            complexity = sum(content.count(indicator) for indicator in complexity_indicators)
            if complexity > 10:
                results.append(node)
        
        return results
    
    def _handle_debug(self, tree: TreeNode, predicates: List) -> List[TreeNode]:
        """Handle debug queries"""
        results = []
        
        # Look for debug patterns
        debug_patterns = ['print(', 'console.log', 'debug', 'trace', 'logging']
        
        for node in self._flatten_tree(tree):
            content = self._get_node_content(node).lower()
            if any(pattern in content for pattern in debug_patterns):
                results.append(node)
        
        return results
    
    def _flatten_tree(self, tree: TreeNode) -> List[TreeNode]:
        """Flatten tree to list of all nodes"""
        nodes = [tree]
        # Handle both property and method access
        if hasattr(tree, 'children'):
            if callable(tree.children):
                children = tree.children()
            else:
                children = tree.children  # Property access
            for child in children:
                nodes.extend(self._flatten_tree(child))
        return nodes
    
    def _get_node_content(self, node: TreeNode) -> str:
        """Get searchable content from node"""
        content_parts = []
        
        # Add name
        if node.name:
            content_parts.append(node.name)
        
        # Add value/content (this should get the source code from CodeTreeNode)
        if hasattr(node, 'value') and node.value:
            if isinstance(node.value, str):
                content_parts.append(node.value)
        
        # Add body/source code (for CodeNode)
        if hasattr(node, 'body') and node.body:
            if isinstance(node.body, str):
                content_parts.append(node.body)
        
        # Add docstring
        if hasattr(node, 'docstring') and node.docstring:
            if isinstance(node.docstring, str):
                content_parts.append(node.docstring)
        
        # Add signature
        if hasattr(node, 'signature') and node.signature:
            if hasattr(node.signature, 'text') and node.signature.text:
                content_parts.append(node.signature.text)
        
        # Add metadata
        if hasattr(node, 'metadata') and node.metadata:
            # Handle NodeMetadata object
            metadata_dict = {}
            if hasattr(node.metadata, '__dict__'):
                metadata_dict = node.metadata.__dict__
            elif isinstance(node.metadata, dict):
                metadata_dict = node.metadata
            
            for key, value in metadata_dict.items():
                if isinstance(value, str):
                    content_parts.append(value)
        
        return ' '.join(content_parts)
    
    def _is_function_node(self, node: TreeNode) -> bool:
        """Check if node represents a function"""
        # Check multiple ways to determine if it's a function
        
        # 1. Check node_type directly
        if hasattr(node, 'node_type'):
            if hasattr(node.node_type, 'value'):
                if node.node_type.value == 'function' or node.node_type.value == 'method':
                    return True
            elif str(node.node_type) in ['function', 'method']:
                return True
        
        # 2. Check metadata
        if hasattr(node, 'metadata') and node.metadata:
            if hasattr(node.metadata, 'node_type'):
                if node.metadata.node_type in ['function', 'method']:
                    return True
            # Check if metadata is a dict
            if isinstance(node.metadata, dict):
                if node.metadata.get('node_type') in ['function', 'method']:
                    return True
        
        # 3. Check code_node for UniversalCodeAdapter
        if hasattr(node, 'code_node'):
            if hasattr(node.code_node, 'node_type'):
                try:
                    from nlp3.code_model import NodeType as CodeNodeType
                    return node.code_node.node_type in [CodeNodeType.FUNCTION, CodeNodeType.METHOD]
                except ImportError:
                    # Fallback if import fails
                    return str(node.code_node.node_type) in ['function', 'method']
        
        return False
    
    def _is_class_node(self, node: TreeNode) -> bool:
        """Check if node represents a class"""
        # Check multiple ways to determine if it's a class
        
        # 1. Check node_type directly
        if hasattr(node, 'node_type'):
            if hasattr(node.node_type, 'value'):
                if node.node_type.value == 'class':
                    return True
            elif str(node.node_type) == 'class':
                return True
        
        # 2. Check metadata
        if hasattr(node, 'metadata') and node.metadata:
            if hasattr(node.metadata, 'node_type'):
                if node.metadata.node_type == 'class':
                    return True
            # Check if metadata is a dict
            if isinstance(node.metadata, dict):
                if node.metadata.get('node_type') == 'class':
                    return True
        
        # 3. Check code_node for UniversalCodeAdapter
        if hasattr(node, 'code_node'):
            if hasattr(node.code_node, 'node_type'):
                try:
                    from nlp3.code_model import NodeType as CodeNodeType
                    return node.code_node.node_type in [CodeNodeType.CLASS, CodeNodeType.INTERFACE, CodeNodeType.ENUM]
                except ImportError:
                    # Fallback if import fails
                    return str(node.code_node.node_type) in ['class', 'interface', 'enum']
        
        return False
    
    def _search_tree(self, node: TreeNode, predicates: List, results: List[TreeNode] = None) -> List[TreeNode]:
        """Recursively search tree for nodes matching predicates"""
        if results is None:
            results = []
        
        # Check if current node matches predicates
        if self._matches_predicates(node, predicates):
            results.append(node)
        
        # Recursively search children
        if hasattr(node, 'children'):
            if callable(node.children):
                children = node.children()
            else:
                children = node.children  # Property access
            for child in children:
                self._search_tree(child, predicates, results)
        
        return results
    
    def _matches_predicates(self, node: TreeNode, predicates: List) -> bool:
        """Check if node matches all predicates"""
        from .nlp import PredicateType
        
        if not predicates:
            return True
        
        for predicate in predicates:
            # Handle None predicate values
            if predicate is None or predicate.value is None:
                continue
                
            if predicate.type == PredicateType.EXTENSION:
                # Check file extension
                if not node.name or not node.name.endswith(predicate.value):
                    return False
            
            elif predicate.type == PredicateType.NAME:
                # Check name contains or equals
                if predicate.operator == "contains":
                    if predicate.value.lower() not in node.name.lower():
                        return False
                elif predicate.operator == "=":
                    if node.name != predicate.value:
                        return False
            
            elif predicate.type == PredicateType.SIZE:
                # Check file size
                if not node.metadata or not node.metadata.size:
                    return False
                
                if predicate.operator == ">":
                    if node.metadata.size <= predicate.value:
                        return False
                elif predicate.operator == "<":
                    if node.metadata.size >= predicate.value:
                        return False
                elif predicate.operator == "=":
                    if node.metadata.size != predicate.value:
                        return False
                elif predicate.operator == "range":
                    # Check if size is within range
                    min_size, max_size = predicate.value
                    if not (min_size <= node.metadata.size <= max_size):
                        return False
            
            elif predicate.type == PredicateType.MODIFIED:
                # Check modification time
                if not node.metadata.modified:
                    return False
                
                # Convert days to seconds
                days_ago = time.time() - (predicate.value * 24 * 3600)
                if predicate.operator == "<":
                    if node.metadata.modified < days_ago:
                        return False
            
            elif predicate.type == PredicateType.TAG:
                # Check HTML tag
                if not node.metadata.extra or 'tag' not in node.metadata.extra:
                    return False
                if node.metadata.extra['tag'] != predicate.value:
                    return False
            
            elif predicate.type == PredicateType.CLASS:
                # Check HTML class
                if not node.metadata.extra or 'class' not in node.metadata.extra:
                    return False
                classes = node.metadata.extra['class']
                if isinstance(classes, list):
                    if predicate.value not in classes:
                        return False
                elif isinstance(classes, str):
                    if predicate.value not in classes.split():
                        return False
            
            elif predicate.type == PredicateType.ID:
                # Check HTML ID
                if not node.metadata.extra or 'id' not in node.metadata.extra:
                    return False
                if node.metadata.extra['id'] != predicate.value:
                    return False
            
            elif predicate.type == PredicateType.ATTRIBUTE:
                # Check HTML attribute
                if not node.metadata.extra or 'attributes' not in node.metadata.extra:
                    return False
                
                # Parse attribute value (format: "name=value")
                if '=' in predicate.value:
                    attr_name, attr_value = predicate.value.split('=', 1)
                    attrs = node.metadata.extra['attributes']
                    if attr_name not in attrs or attrs[attr_name] != attr_value:
                        return False
        
        return True
