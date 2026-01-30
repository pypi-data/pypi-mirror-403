"""Code Adapter Integration for NLP3Tree"""

from pathlib import Path
from typing import Any, List, Optional
import asyncio

from ..core import TreeNode, NodeType, NodeMetadata, TreeNavigator, TreeAdapter
from ..adapters.code_adapter import CodeAdapter as CodeAnalyzer, CodeElement
from ..adapters.code_intelligence import CodeIntelligenceEngine
from ..adapters.semantic_search import SemanticSearchEngine
from ..adapters.code_use_cases import CodeAnalysisUseCases


class CodeNode(TreeNode):
    """Tree node for code elements"""
    
    def __init__(self, element: CodeElement, file_path: str):
        self._element = element
        self._file_path = file_path
        self._children = []
    
    @property
    def name(self) -> str:
        return self._element.name
    
    @property
    def path(self) -> str:
        return f"{self._file_path}:{self._element.line_start}"
    
    @property
    def node_type(self) -> NodeType:
        return NodeType.LEAF
    
    @property
    def metadata(self) -> NodeMetadata:
        extra = {
            "type": self._element.type,
            "line_start": self._element.line_start,
            "line_end": self._element.line_end,
            "docstring": self._element.docstring,
            "signature": self._element.signature,
            "decorators": self._element.decorators,
            "imports": self._element.imports,
            "calls": self._element.calls,
            "file_path": self._file_path,
        }
        return NodeMetadata(extra=extra)
    
    def children(self) -> List['TreeNode']:
        return self._children


class CodeFileNode(TreeNode):
    """Tree node for code files"""
    
    def __init__(self, file_path: Path, elements: List[CodeElement]):
        self._file_path = file_path
        self._elements = elements
        self._children = []
        
        # Create child nodes for each element
        for element in elements:
            child_node = CodeNode(element, str(file_path))
            self._children.append(child_node)
    
    @property
    def name(self) -> str:
        return self._file_path.name
    
    @property
    def path(self) -> str:
        return str(self._file_path)
    
    @property
    def node_type(self) -> NodeType:
        return NodeType.BRANCH
    
    @property
    def metadata(self) -> NodeMetadata:
        try:
            size = self._file_path.stat().st_size
            modified = self._file_path.stat().st_mtime
        except (OSError, FileNotFoundError):
            size = None
            modified = None
        
        extra = {
            "file_type": "code",
            "elements_count": len(self._elements),
            "functions": len([e for e in self._elements if e.type in ["function", "method"]]),
            "classes": len([e for e in self._elements if e.type == "class"]),
            "imports": len(set().union(*[e.imports for e in self._elements if e.imports])),
        }
        
        return NodeMetadata(size=size, modified=modified, extra=extra)
    
    def children(self) -> List['TreeNode']:
        return self._children


class CodeDirectoryNode(TreeNode):
    """Tree node for code directories"""
    
    def __init__(self, dir_path: Path, code_engine: CodeIntelligenceEngine):
        self._dir_path = dir_path
        self._code_engine = code_engine
        self._children = []
        self._build_children()
    
    def _build_children(self):
        """Build child nodes"""
        # Analyze directory
        all_elements = self._code_engine.code_adapter.analyze_directory(self._dir_path)
        
        # Group by file
        file_elements = {}
        for file_path, elements in all_elements.items():
            path_obj = Path(file_path)
            if path_obj.parent == self._dir_path:
                file_elements[path_obj] = elements
        
        # Create file nodes
        for file_path, elements in file_elements.items():
            file_node = CodeFileNode(file_path, elements)
            self._children.append(file_node)
        
        # Add subdirectories
        for sub_dir in self._dir_path.iterdir():
            if sub_dir.is_dir() and not sub_dir.name.startswith('.'):
                # Check if directory contains code files
                has_code = any(
                    f.suffix in ['.py', '.js', '.ts', '.go', '.java']
                    for f in sub_dir.rglob('*')
                    if f.is_file()
                )
                if has_code:
                    dir_node = CodeDirectoryNode(sub_dir, self._code_engine)
                    self._children.append(dir_node)
    
    @property
    def name(self) -> str:
        return self._dir_path.name
    
    @property
    def path(self) -> str:
        return str(self._dir_path)
    
    @property
    def node_type(self) -> NodeType:
        return NodeType.BRANCH
    
    @property
    def metadata(self) -> NodeMetadata:
        try:
            size = sum(f.stat().st_size for f in self._dir_path.rglob('*') if f.is_file())
            modified = max(f.stat().st_mtime for f in self._dir_path.rglob('*') if f.is_file())
        except (OSError, FileNotFoundError, ValueError):
            size = None
            modified = None
        
        # Count code elements
        all_elements = self._code_engine.code_adapter.analyze_directory(self._dir_path)
        total_elements = sum(len(elements) for elements in all_elements.values())
        
        extra = {
            "directory_type": "code",
            "total_elements": total_elements,
            "files_count": len(all_elements),
        }
        
        return NodeMetadata(size=size, modified=modified, extra=extra)
    
    def children(self) -> List['TreeNode']:
        return self._children


class CodeAdapter(TreeAdapter):
    """Main adapter for integrating code analysis with NLP3Tree"""
    
    def __init__(self):
        self.code_adapter = CodeAnalyzer()
        self.code_engine = CodeIntelligenceEngine()
        self.semantic_engine = SemanticSearchEngine()
        self.use_cases = None
    
    def supports(self, source: Any) -> bool:
        """Check if adapter supports this source type"""
        # Only support for explicit code analysis, not general file browsing
        # This allows FilesystemAdapter to handle basic file operations
        return False  # Disable for now to let FilesystemAdapter handle .py files
    
    async def build_tree(self, source: Any, preload: bool = False) -> TreeNode:
        """Build tree from code source"""
        if isinstance(source, (str, Path)):
            path = Path(source)
            
            if path.is_file():
                # Single file
                elements = self.code_adapter.analyze_file(path)
                return CodeFileNode(path, elements)
            
            elif path.is_dir():
                # Directory
                if not self.code_engine.index:
                    self.code_engine.build_index(path)
                
                return CodeDirectoryNode(path, self.code_engine)
        
        raise ValueError(f"Unsupported source type: {type(source)}")
    
    async def query(self, query_text: str, source: Any, preload: bool = False) -> List[TreeNode]:
        """Query code using natural language"""
        # Build tree first
        tree = await self.build_tree(source, preload)
        
        # Initialize use cases if needed
        if not self.use_cases:
            self.use_cases = CodeAnalysisUseCases(Path(source) if isinstance(source, (str, Path)) else Path("."))
        
        # Parse query and execute appropriate use case
        query_lower = query_text.lower()
        
        # Map queries to use cases
        if "funkcja" in query_lower or "function" in query_lower:
            if "json" in query_lower or "parse" in query_lower:
                results = self.use_cases.find_functions_by_name()
            elif "test" in query_lower:
                results = self.use_cases.find_tests_for_function()
            else:
                results = self.code_engine.search(query_lower)
        
        elif "log" in query_lower or "logger" in query_lower:
            results = self.use_cases.find_logging_classes()
        
        elif "todo" in query_lower or "fixme" in query_lower:
            results = self.use_cases.find_todo_comments()
        
        elif "security" in query_lower or "eval" in query_lower:
            results = self.use_cases.find_security_hotspots()
        
        elif "async" in query_lower or "await" in query_lower:
            results = self.use_cases.find_async_code()
        
        elif "database" in query_lower or "db" in query_lower:
            results = self.use_cases.find_database_operations()
        
        elif "api" in query_lower or "endpoint" in query_lower:
            results = self.use_cases.find_api_endpoints()
        
        elif "retry" in query_lower:
            results = self.use_cases.find_retry_logic()
        
        elif "cache" in query_lower:
            results = self.use_cases.find_caching_logic()
        
        elif "import" in query_lower and "pandas" in query_lower:
            results = self.use_cases.find_heavy_imports()
        
        elif "unused" in query_lower or "dead" in query_lower:
            results = self.use_cases.find_unused_functions()
        
        elif "upload" in query_lower or "file" in query_lower:
            results = self.use_cases.find_file_upload()
        
        elif "chart" in query_lower or "plot" in query_lower:
            results = self.use_cases.find_chart_generation()
        
        elif "json" in query_lower and "serial" in query_lower:
            results = self.use_cases.find_json_serialization()
        
        elif "cli" in query_lower or "command" in query_lower:
            results = self.use_cases.find_cli_code()
        
        elif "config" in query_lower or "settings" in query_lower:
            results = self.use_cases.find_config_loading()
        
        elif "socket" in query_lower or "network" in query_lower:
            results = self.use_cases.find_socket_usage()
        
        elif "multiprocess" in query_lower or "thread" in query_lower:
            results = self.use_cases.find_multiprocessing()
        
        elif "feature" in query_lower or "flag" in query_lower:
            results = self.use_cases.find_feature_flags()
        
        else:
            # General search
            results = self.code_engine.search(query_lower)
        
        # Convert results to tree nodes
        nodes = []
        for result in results:
            if isinstance(result, CodeElement):
                # Create a dummy file path for the element
                node = CodeNode(result, "unknown")
                nodes.append(node)
            elif isinstance(result, tuple) and len(result) >= 2:
                if isinstance(result[0], CodeElement):
                    file_path = result[1] if isinstance(result[1], str) else "unknown"
                    node = CodeNode(result[0], file_path)
                    nodes.append(node)
        
        return nodes
    
    def can_handle(self, source: Any) -> bool:
        """Check if this adapter can handle the source"""
        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.exists():
                if path.is_file():
                    return path.suffix in ['.py', '.js', '.ts', '.jsx', '.go', '.java']
                elif path.is_dir():
                    # Check if directory contains code files
                    return any(
                        f.suffix in ['.py', '.js', '.ts', '.jsx', '.go', '.java']
                        for f in path.rglob('*')
                        if f.is_file()
                    )
        return False
