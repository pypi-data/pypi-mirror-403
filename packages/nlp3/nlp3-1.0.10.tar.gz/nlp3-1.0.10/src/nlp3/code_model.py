"""
Universal Code Node Model

Common abstraction for code elements across all programming languages.
Provides unified interface for AST nodes from different parsers.
"""

from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import ast
import json


class NodeType(Enum):
    """Universal node types across all languages"""
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"
    CALL = "call"
    DECORATOR = "decorator"
    ANNOTATION = "annotation"
    COMMENT = "comment"
    DOCSTRING = "docstring"
    CONSTANT = "constant"
    INTERFACE = "interface"
    ENUM = "enum"
    NAMESPACE = "namespace"
    ENDPOINT = "endpoint"
    MIDDLEWARE = "middleware"
    TEST = "test"
    CONFIG = "config"


class Language(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    CSHARP = "csharp"
    RUST = "rust"
    CPP = "cpp"
    RUBY = "ruby"
    PHP = "php"
    KOTLIN = "kotlin"
    SWIFT = "swift"
    UNKNOWN = "unknown"


@dataclass
class CodePosition:
    """Position information in source code"""
    line: int
    column: int
    
    def __str__(self) -> str:
        return f"{self.line}:{self.column}"


@dataclass
class CodeRange:
    """Range in source code"""
    start: CodePosition
    end: CodePosition
    
    def __str__(self) -> str:
        return f"{self.start}-{self.end}"
    
    @property
    def line_count(self) -> int:
        return self.end.line - self.start.line + 1


@dataclass
class CodeSignature:
    """Function/method signature information"""
    name: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    modifiers: List[str] = field(default_factory=list)
    generics: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        params = ", ".join([f"{p.get('name', '')}: {p.get('type', '')}" for p in self.parameters])
        return f"{self.name}({params}) -> {self.return_type or 'void'}"


@dataclass
class CodeNode:
    """Universal code node abstraction"""
    
    # Core identification
    node_type: NodeType
    name: Optional[str] = None
    signature: Optional[CodeSignature] = None
    language: Language = Language.UNKNOWN
    
    # Location information
    file_path: str = ""
    range: Optional[CodeRange] = None
    
    # Content
    body: str = ""
    docstring: Optional[str] = None
    comment: Optional[str] = None
    
    # Metadata
    annotations: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)
    
    # Relationships
    parent: Optional['CodeNode'] = None
    children: List['CodeNode'] = field(default_factory=list)
    
    # Metrics
    complexity: int = 0
    lines_of_code: int = 0
    cyclomatic_complexity: int = 0
    
    # Semantic information
    embedding: Optional[List[float]] = None
    tags: List[str] = field(default_factory=list)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate derived properties"""
        if self.range:
            self.lines_of_code = self.range.line_count
        if self.signature and not self.name:
            self.name = self.signature.name
    
    @property
    def id(self) -> str:
        """Unique identifier for this node"""
        parts = [self.language.value, self.node_type.value]
        if self.name:
            parts.append(self.name)
        if self.file_path:
            parts.append(self.file_path)
        return ":".join(parts)
    
    @property
    def display_name(self) -> str:
        """Human-readable display name"""
        if self.name:
            return self.name
        elif self.signature:
            return str(self.signature)
        else:
            return f"{self.node_type.value} ({self.file_path}:{self.range.start.line if self.range else '?'})"
    
    @property
    def full_path(self) -> str:
        """Full path including parent hierarchy"""
        if self.parent:
            return f"{self.parent.full_path}.{self.name}" if self.name else self.parent.full_path
        return self.name or self.node_type.value
    
    def add_child(self, child: 'CodeNode'):
        """Add a child node"""
        child.parent = self
        self.children.append(child)
    
    def find_children(self, node_type: NodeType, recursive: bool = True) -> List['CodeNode']:
        """Find children of specific type"""
        results = []
        for child in self.children:
            if child.node_type == node_type:
                results.append(child)
            if recursive:
                results.extend(child.find_children(node_type, recursive))
        return results
    
    def find_by_name(self, name: str, recursive: bool = True) -> Optional['CodeNode']:
        """Find child by name"""
        for child in self.children:
            if child.name == name:
                return child
            if recursive:
                found = child.find_by_name(name, recursive)
                if found:
                    return found
        return None
    
    def get_all_functions(self, recursive: bool = True) -> List['CodeNode']:
        """Get all function/method nodes"""
        return self.find_children(NodeType.FUNCTION, recursive) + self.find_children(NodeType.METHOD, recursive)
    
    def get_all_classes(self, recursive: bool = True) -> List['CodeNode']:
        """Get all class/interface nodes"""
        return self.find_children(NodeType.CLASS, recursive) + self.find_children(NodeType.INTERFACE, recursive)
    
    def get_all_imports(self, recursive: bool = True) -> List[str]:
        """Get all imports from this node and children"""
        imports = set(self.imports)
        if recursive:
            for child in self.children:
                imports.update(child.get_all_imports(recursive))
        return list(imports)
    
    def get_all_calls(self, recursive: bool = True) -> List[str]:
        """Get all function calls from this node and children"""
        calls = set(self.calls)
        if recursive:
            for child in self.children:
                calls.update(child.get_all_calls(recursive))
        return list(calls)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "type": self.node_type.value,
            "name": self.name,
            "signature": str(self.signature) if self.signature else None,
            "language": self.language.value,
            "file_path": self.file_path,
            "range": {
                "start": {"line": self.range.start.line, "column": self.range.start.column},
                "end": {"line": self.range.end.line, "column": self.range.end.column}
            } if self.range else None,
            "body": self.body,
            "docstring": self.docstring,
            "comment": self.comment,
            "annotations": self.annotations,
            "decorators": self.decorators,
            "imports": self.imports,
            "calls": self.calls,
            "complexity": self.complexity,
            "lines_of_code": self.lines_of_code,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "tags": self.tags,
            "metadata": self.metadata,
            "children": [child.to_dict() for child in self.children]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeNode':
        """Create from dictionary"""
        # Handle range
        range_data = data.get("range")
        code_range = None
        if range_data:
            code_range = CodeRange(
                start=CodePosition(range_data["start"]["line"], range_data["start"]["column"]),
                end=CodePosition(range_data["end"]["line"], range_data["end"]["column"])
            )
        
        # Handle signature
        signature_data = data.get("signature")
        signature = None
        if signature_data:
            # Parse signature string back to CodeSignature (simplified)
            signature = CodeSignature(name=signature_data.split('(')[0].strip())
        
        node = cls(
            node_type=NodeType(data["type"]),
            name=data.get("name"),
            signature=signature,
            language=Language(data.get("language", "unknown")),
            file_path=data.get("file_path", ""),
            range=code_range,
            body=data.get("body", ""),
            docstring=data.get("docstring"),
            comment=data.get("comment"),
            annotations=data.get("annotations", []),
            decorators=data.get("decorators", []),
            imports=data.get("imports", []),
            calls=data.get("calls", []),
            complexity=data.get("complexity", 0),
            lines_of_code=data.get("lines_of_code", 0),
            cyclomatic_complexity=data.get("cyclomatic_complexity", 0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )
        
        # Recursively add children
        for child_data in data.get("children", []):
            child = cls.from_dict(child_data)
            node.add_child(child)
        
        return node
    
    def __str__(self) -> str:
        """String representation"""
        parts = [f"{self.node_type.value}"]
        if self.name:
            parts.append(self.name)
        if self.file_path:
            parts.append(f"({self.file_path}:{self.range.start.line if self.range else '?'})")
        return " ".join(parts)
    
    def __repr__(self) -> str:
        """Detailed representation"""
        return f"CodeNode(type={self.node_type.value}, name={self.name}, language={self.language.value})"


@dataclass
class CodeRepository:
    """Repository-level container for code nodes"""
    
    name: str
    root_path: str
    language_distribution: Dict[str, int] = field(default_factory=dict)
    total_files: int = 0
    total_nodes: int = 0
    modules: List[CodeNode] = field(default_factory=list)
    
    def add_module(self, module: CodeNode):
        """Add a module (file) to the repository"""
        self.modules.append(module)
        self.total_nodes += self._count_nodes(module)
        self.total_files += 1
        
        # Update language distribution
        lang = module.language.value
        self.language_distribution[lang] = self.language_distribution.get(lang, 0) + 1
    
    def _count_nodes(self, node: CodeNode) -> int:
        """Count all nodes in subtree"""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count
    
    def find_by_path(self, path: str) -> Optional[CodeNode]:
        """Find node by full path"""
        for module in self.modules:
            if module.file_path == path:
                return module
            # Search within module
            found = self._find_by_path_recursive(module, path)
            if found:
                return found
        return None
    
    def _find_by_path_recursive(self, node: CodeNode, path: str) -> Optional[CodeNode]:
        """Recursive path search"""
        if node.full_path == path:
            return node
        for child in node.children:
            found = self._find_by_path_recursive(child, path)
            if found:
                return found
        return None
    
    def search(self, query: str) -> List[CodeNode]:
        """Simple text search across all nodes"""
        results = []
        query_lower = query.lower()
        
        for module in self.modules:
            results.extend(self._search_recursive(module, query_lower))
        
        return results
    
    def _search_recursive(self, node: CodeNode, query: str) -> List[CodeNode]:
        """Recursive search"""
        results = []
        
        # Search in current node
        searchable_text = [
            node.name or "",
            node.body,
            node.docstring or "",
            node.comment or "",
            " ".join(node.annotations),
            " ".join(node.decorators)
        ]
        
        if any(query in text.lower() for text in searchable_text):
            results.append(node)
        
        # Search in children
        for child in node.children:
            results.extend(self._search_recursive(child, query))
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics"""
        stats = {
            "name": self.name,
            "root_path": self.root_path,
            "total_files": self.total_files,
            "total_nodes": self.total_nodes,
            "language_distribution": self.language_distribution,
            "node_types": {},
            "complexity_stats": {
                "total_complexity": 0,
                "avg_complexity": 0,
                "max_complexity": 0
            }
        }
        
        # Count node types and complexity
        total_complexity = 0
        node_count = 0
        max_complexity = 0
        
        for module in self.modules:
            for node in self._flatten_nodes(module):
                node_type = node.node_type.value
                stats["node_types"][node_type] = stats["node_types"].get(node_type, 0) + 1
                
                if node.complexity > 0:
                    total_complexity += node.complexity
                    node_count += 1
                    max_complexity = max(max_complexity, node.complexity)
        
        stats["complexity_stats"]["total_complexity"] = total_complexity
        stats["complexity_stats"]["max_complexity"] = max_complexity
        stats["complexity_stats"]["avg_complexity"] = total_complexity / node_count if node_count > 0 else 0
        
        return stats
    
    def _flatten_nodes(self, node: CodeNode) -> List[CodeNode]:
        """Flatten tree to list"""
        nodes = [node]
        for child in node.children:
            nodes.extend(self._flatten_nodes(child))
        return nodes
