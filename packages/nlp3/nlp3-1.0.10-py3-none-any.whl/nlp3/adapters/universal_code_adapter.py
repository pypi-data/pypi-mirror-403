"""
Universal Code Adapter for NLP3

Provides tree navigation and querying capabilities for code repositories
using the universal code model and parser.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass
import logging

from ..core import TreeNode, NodeType, TreeAdapter
from ..code_model import CodeNode, NodeType as CodeNodeType, Language, CodeRepository
from ..universal_parser import UniversalCodeParser, ParseResult
from ..nlp import NLPEngine, IntentType, PredicateType


class CodeTreeNode(TreeNode):
    """Tree node implementation for code structures"""
    
    def __init__(self, code_node: CodeNode):
        self.code_node = code_node
        self._children = []
        
        # Map code node type to tree node type
        type_mapping = {
            CodeNodeType.MODULE: NodeType.LEAF,
            CodeNodeType.CLASS: NodeType.BRANCH,
            CodeNodeType.FUNCTION: NodeType.LEAF,
            CodeNodeType.METHOD: NodeType.LEAF,
            CodeNodeType.INTERFACE: NodeType.BRANCH,
            CodeNodeType.ENUM: NodeType.BRANCH,
            CodeNodeType.NAMESPACE: NodeType.BRANCH,
        }
        
        node_type = type_mapping.get(code_node.node_type, NodeType.LEAF)
        name = code_node.display_name or code_node.name or "unknown"
        
        super().__init__(
            name=name,
            node_type=node_type,
            metadata=CodeNodeMetadata(code_node)
        )
        
        # Build children tree
        self._build_children()
    
    def _build_children(self):
        """Build children tree from code node"""
        for child_code_node in self.code_node.children:
            child_node = CodeTreeNode(child_code_node)
            self._children.append(child_node)
    
    @property
    def children(self) -> List['CodeTreeNode']:
        """Get child nodes"""
        return self._children
    
    def get_children(self) -> List['CodeTreeNode']:
        """Get child nodes (method for compatibility)"""
        return self._children
    
    @property
    def path(self) -> str:
        """Get full path"""
        return self.code_node.full_path
    
    @property
    def value(self) -> Any:
        """Get node value"""
        return self.code_node.body


@dataclass
class CodeNodeMetadata:
    """Metadata for code tree nodes"""
    
    code_node: CodeNode
    
    def __init__(self, code_node: CodeNode):
        self.code_node = code_node
        self.size = len(code_node.body.encode('utf-8')) if code_node.body else 0
        self.modified = None  # Could get from file stats
        self.mime_type = f"text/x-{code_node.language.value}"
        self.language = code_node.language.value
        self.node_type = code_node.node_type.value
        self.complexity = code_node.complexity
        self.lines_of_code = code_node.lines_of_code
        self.signature = str(code_node.signature) if code_node.signature else None
        self.docstring = code_node.docstring
        self.annotations = code_node.annotations
        self.decorators = code_node.decorators
        self.imports = code_node.imports
        self.calls = code_node.calls
        self.tags = code_node.tags


class UniversalCodeAdapter(TreeAdapter):
    """Universal tree adapter for code repositories"""
    
    def __init__(self):
        self.parser = UniversalCodeParser()
        self.nlp_engine = NLPEngine(enable_spell_check=False)
        self.repository: Optional[CodeRepository] = None
        self.root_nodes: List[CodeTreeNode] = []
    
    def supports(self, source: Union[str, Path, CodeRepository]) -> bool:
        """Check if source is supported"""
        if isinstance(source, CodeRepository):
            return True
        elif isinstance(source, (str, Path)):
            path = Path(source)
            return path.is_dir() or (path.is_file() and self._is_code_file(path))
        return False
    
    def _is_code_file(self, path: Path) -> bool:
        """Check if file is a code file"""
        from ..universal_parser import LanguageDetector
        return LanguageDetector.detect_language(str(path)) != Language.UNKNOWN
    
    async def build_tree(self, source: Union[str, Path, CodeRepository], preload: bool = False) -> CodeTreeNode:
        """Build code tree from source"""
        if isinstance(source, CodeRepository):
            self.repository = source
        elif isinstance(source, (str, Path)):
            path = Path(source)
            if path.is_dir():
                self.repository = self.parser.parse_repository(str(path))
            elif path.is_file():
                result = self.parser.parse_file(str(path))
                if result.success:
                    self.repository = CodeRepository(name="single_file", root_path=str(path.parent))
                    for module in result.nodes:
                        self.repository.add_module(module)
                else:
                    # Try fallback parser if tree-sitter fails
                    fallback_result = self.parser.fallback_parser.parse_file(str(path))
                    if fallback_result.success:
                        self.repository = CodeRepository(name="single_file", root_path=str(path.parent))
                        for module in fallback_result.nodes:
                            self.repository.add_module(module)
                    else:
                        raise ValueError(f"Failed to parse file: {fallback_result.errors}")
            else:
                raise ValueError(f"Source not found: {source}")
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")
        
        # Build tree nodes
        self.root_nodes = []
        for module in self.repository.modules:
            root_node = CodeTreeNode(module)
            self.root_nodes.append(root_node)
        
        # Return first root node (or a virtual root)
        if len(self.root_nodes) == 1:
            return self.root_nodes[0]
        else:
            # Create virtual root for multiple files
            virtual_root = CodeNode(
                node_type=CodeNodeType.MODULE,
                name=self.repository.name,
                language=Language.UNKNOWN,
                file_path=self.repository.root_path
            )
            for module in self.repository.modules:
                virtual_root.add_child(module)
            return CodeTreeNode(virtual_root)
    
    def query_code(self, query_text: str) -> List[CodeNode]:
        """Query code using natural language"""
        if not self.repository:
            return []
        
        # Parse NLP query
        parsed_query = self.nlp_engine.parse_query(query_text)
        
        # Execute query on repository
        results = self._execute_query(parsed_query)
        
        return results
    
    def _execute_query(self, parsed_query) -> List[CodeNode]:
        """Execute parsed query on repository"""
        results = []
        
        # Handle different intents
        intent = parsed_query.intent.type
        
        if intent == IntentType.CODE_SEARCH:
            results = self._handle_code_search(parsed_query)
        elif intent == IntentType.FUNCTION_ANALYSIS:
            results = self._handle_function_analysis(parsed_query)
        elif intent == IntentType.SECURITY_SCAN:
            results = self._handle_security_scan(parsed_query)
        elif intent == IntentType.DEPENDENCY_ANALYSIS:
            results = self._handle_dependency_analysis(parsed_query)
        elif intent == IntentType.METRICS:
            results = self._handle_metrics(parsed_query)
        elif intent == IntentType.REFACTOR:
            results = self._handle_refactor(parsed_query)
        elif intent == IntentType.DEBUG:
            results = self._handle_debug(parsed_query)
        else:
            # Default to search
            results = self._handle_general_search(parsed_query)
        
        return results
    
    def _handle_code_search(self, parsed_query) -> List[CodeNode]:
        """Handle code search queries"""
        results = []
        
        for predicate in parsed_query.intent.predicates:
            if predicate.type == PredicateType.FUNCTION:
                # Search for functions by name
                for module in self.repository.modules:
                    results.extend(self._find_functions_by_name(module, predicate.value))
            
            elif predicate.type == PredicateType.CLASS_NAME:
                # Search for classes by name
                for module in self.repository.modules:
                    results.extend(self._find_classes_by_name(module, predicate.value))
            
            elif predicate.type == PredicateType.LANGUAGE:
                # Search by language
                for module in self.repository.modules:
                    if module.language.value == predicate.value:
                        results.append(module)
                        results.extend(module.get_all_functions())
                        results.extend(module.get_all_classes())
            
            elif predicate.type == PredicateType.IMPORT:
                # Search by imports
                for module in self.repository.modules:
                    if predicate.value in module.get_all_imports():
                        results.append(module)
        
        return results
    
    def _handle_function_analysis(self, parsed_query) -> List[CodeNode]:
        """Handle function analysis queries"""
        results = []
        
        for predicate in parsed_query.intent.predicates:
            if predicate.type == PredicateType.FUNCTION:
                # Find specific function and analyze
                for module in self.repository.modules:
                    func = self._find_function_by_name(module, predicate.value)
                    if func:
                        results.append(func)
                        # Add complexity analysis
                        self._analyze_function_complexity(func)
        
        return results
    
    def _handle_security_scan(self, parsed_query) -> List[CodeNode]:
        """Handle security scan queries"""
        results = []
        
        # Look for security patterns
        security_patterns = [
            'eval', 'exec', 'subprocess', 'os.system', 'shell_exec',
            'sql', 'execute', 'query', 'input', 'request'
        ]
        
        for module in self.repository.modules:
            if self._contains_security_patterns(module, security_patterns):
                results.append(module)
        
        return results
    
    def _handle_dependency_analysis(self, parsed_query) -> List[CodeNode]:
        """Handle dependency analysis queries"""
        results = []
        
        for predicate in parsed_query.intent.predicates:
            if predicate.type == PredicateType.IMPORT:
                # Find modules that import specific dependency
                for module in self.repository.modules:
                    if predicate.value in module.get_all_imports():
                        results.append(module)
        
        return results
    
    def _handle_metrics(self, parsed_query) -> List[CodeNode]:
        """Handle metrics queries"""
        results = []
        
        # Return repository statistics
        stats = self.repository.get_statistics()
        
        # Create a virtual node with metrics
        metrics_node = CodeNode(
            node_type=CodeNodeType.MODULE,
            name="repository_metrics",
            language=Language.UNKNOWN,
            file_path="",
            metadata=stats
        )
        
        results.append(metrics_node)
        return results
    
    def _handle_refactor(self, parsed_query) -> List[CodeNode]:
        """Handle refactoring queries"""
        results = []
        
        # Look for code smells
        for module in self.repository.modules:
            # High complexity functions
            for func in module.get_all_functions():
                if func.complexity > 10:
                    results.append(func)
            
            # Long functions
            for func in module.get_all_functions():
                if func.lines_of_code > 50:
                    results.append(func)
        
        return results
    
    def _handle_debug(self, parsed_query) -> List[CodeNode]:
        """Handle debug queries"""
        results = []
        
        # Look for debug patterns
        debug_patterns = ['print', 'console.log', 'debug', 'trace']
        
        for module in self.repository.modules:
            if self._contains_debug_patterns(module, debug_patterns):
                results.append(module)
        
        return results
    
    def _handle_general_search(self, parsed_query) -> List[CodeNode]:
        """Handle general search queries"""
        # Simple text search
        query_text = parsed_query.original.lower()
        results = []
        
        for module in self.repository.modules:
            if self._matches_search_query(module, query_text):
                results.append(module)
        
        return results
    
    def _find_functions_by_name(self, node: CodeNode, name: str) -> List[CodeNode]:
        """Find functions by name (case-insensitive)"""
        results = []
        name_lower = name.lower()
        
        for func in node.get_all_functions():
            if func.name and func.name.lower() == name_lower:
                results.append(func)
        
        return results
    
    def _find_classes_by_name(self, node: CodeNode, name: str) -> List[CodeNode]:
        """Find classes by name (case-insensitive)"""
        results = []
        name_lower = name.lower()
        
        for cls in node.get_all_classes():
            if cls.name and cls.name.lower() == name_lower:
                results.append(cls)
        
        return results
    
    def _find_function_by_name(self, node: CodeNode, name: str) -> Optional[CodeNode]:
        """Find specific function by name"""
        functions = self._find_functions_by_name(node, name)
        return functions[0] if functions else None
    
    def _analyze_function_complexity(self, func: CodeNode):
        """Analyze and set function complexity"""
        # Simple complexity calculation based on patterns
        complexity_patterns = [
            'if', 'elif', 'for', 'while', 'try', 'except', 'with',
            'and', 'or', '&&', '||'
        ]
        
        complexity = 1  # Base complexity
        for pattern in complexity_patterns:
            complexity += func.body.count(pattern)
        
        func.complexity = complexity
        func.cyclomatic_complexity = complexity
    
    def _contains_security_patterns(self, node: CodeNode, patterns: List[str]) -> bool:
        """Check if node contains security patterns"""
        content = (node.body + ' ' + ' '.join(node.calls)).lower()
        return any(pattern in content for pattern in patterns)
    
    def _contains_debug_patterns(self, node: CodeNode, patterns: List[str]) -> bool:
        """Check if node contains debug patterns"""
        content = (node.body + ' ' + ' '.join(node.calls)).lower()
        return any(pattern in content for pattern in patterns)
    
    def _matches_search_query(self, node: CodeNode, query: str) -> bool:
        """Check if node matches search query"""
        searchable_content = [
            node.name or '',
            node.body,
            node.docstring or '',
            ' '.join(node.annotations),
            ' '.join(node.decorators),
            ' '.join(node.imports),
            ' '.join(node.calls)
        ]
        
        content = ' '.join(searchable_content).lower()
        return query in content
    
    def get_repository_stats(self) -> Dict[str, Any]:
        """Get repository statistics"""
        if not self.repository:
            return {}
        
        return self.repository.get_statistics()
    
    def get_supported_languages(self) -> List[str]:
        """Get supported programming languages"""
        return [lang.value for lang in self.parser.get_supported_languages()]


# Register the adapter
from ..core import TreeNavigator

def register_universal_code_adapter(navigator: TreeNavigator):
    """Register universal code adapter with navigator"""
    navigator.register_adapter(UniversalCodeAdapter())
