"""
Incremental parsing system with tree-sitter for multi-language support.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
import logging
import hashlib
import json
import time
from datetime import datetime

from ..code_model import CodeNode, CodeRepository, NodeType, Language, CodePosition, CodeRange, CodeSignature


@dataclass
class FileMetadata:
    """Metadata for parsed files"""
    file_path: str
    file_hash: str
    last_modified: float
    parsed_at: datetime
    language: Language
    node_count: int


class IncrementalParser:
    """
    Incremental parser that only reparses changed files.
    Uses tree-sitter for multi-language AST parsing.
    """
    
    def __init__(self, repository_path: str):
        self.repository_path = Path(repository_path)
        self.logger = logging.getLogger(__name__)
        
        # File tracking
        self.metadata_file = self.repository_path / ".nlp3" / "file_metadata.json"
        self.metadata_file.parent.mkdir(exist_ok=True)
        self.file_metadata: Dict[str, FileMetadata] = {}
        
        # Tree-sitter parsers (lazy loaded)
        self._parsers: Dict[Language, Any] = {}
        self._languages: Dict[str, Language] = {}
        
        # Language detection
        self._setup_language_mapping()
        self._load_metadata()
    
    def _setup_language_mapping(self):
        """Setup file extension to language mapping"""
        self._languages = {
            '.py': Language.PYTHON,
            '.js': Language.JAVASCRIPT,
            '.ts': Language.TYPESCRIPT,
            '.jsx': Language.JAVASCRIPT,
            '.tsx': Language.TYPESCRIPT,
            '.go': Language.GO,
            '.java': Language.JAVA,
            '.cs': Language.CSHARP,
            '.rs': Language.RUST,
            '.cpp': Language.CPP,
            '.cc': Language.CPP,
            '.cxx': Language.CPP,
            '.c': Language.CPP,
            '.h': Language.CPP,
            '.hpp': Language.CPP,
            '.rb': Language.RUBY,
            '.php': Language.PHP,
            '.kt': Language.KOTLIN,
            '.swift': Language.SWIFT
        }
    
    def _get_tree_sitter_parser(self, language: Language):
        """Get or create tree-sitter parser for language"""
        if language in self._parsers:
            return self._parsers[language]
        
        # For now, disable tree-sitter and use fallback parsing
        self.logger.debug(f"Tree-sitter disabled for {language.value}, using fallback")
        self._parsers[language] = None
        return None
    
    def parse_repository(self, force_reparse: bool = False) -> CodeRepository:
        """
        Parse entire repository with incremental updates.
        
        Args:
            force_reparse: Force reparsing all files
            
        Returns:
            Parsed repository
        """
        start_time = time.time()
        
        repository = CodeRepository(
            name=self.repository_path.name,
            root_path=str(self.repository_path)
        )
        
        # Find all code files
        code_files = self._find_code_files()
        
        if force_reparse:
            self.logger.info("Force reparsing all files")
            self.file_metadata.clear()
        
        # Parse files incrementally
        parsed_files = 0
        skipped_files = 0
        
        for file_path in code_files:
            if self._should_parse_file(file_path):
                nodes = self.parse_file(file_path)
                if nodes:
                    for node in nodes:
                        repository.add_module(node)
                    parsed_files += 1
            else:
                skipped_files += 1
        
        parse_time = time.time() - start_time
        
        self.logger.info(
            f"Parsed repository: {parsed_files} files, {skipped_files} skipped, "
            f"{repository.total_nodes} nodes in {parse_time:.2f}s"
        )
        
        self._save_metadata()
        return repository
    
    def _find_code_files(self) -> List[Path]:
        """Find all code files in repository"""
        code_files = []
        
        for file_path in self.repository_path.rglob('*'):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                suffix = file_path.suffix.lower()
                if suffix in self._languages:
                    code_files.append(file_path)
        
        return code_files
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        ignore_patterns = [
            '.git', '__pycache__', 'node_modules', '.vscode', '.idea',
            'build', 'dist', 'target', 'vendor', '.venv', 'venv'
        ]
        
        return any(pattern in str(file_path) for pattern in ignore_patterns)
    
    def _should_parse_file(self, file_path: Path) -> bool:
        """Check if file needs parsing (changed or new)"""
        file_path_str = str(file_path)
        
        # Check if file exists in metadata
        if file_path_str not in self.file_metadata:
            return True
        
        # Check if file was modified
        metadata = self.file_metadata[file_path_str]
        current_mtime = file_path.stat().st_mtime
        current_hash = self._calculate_file_hash(file_path)
        
        return (current_mtime != metadata.last_modified or 
                current_hash != metadata.file_hash)
    
    def parse_file(self, file_path: Path) -> List[CodeNode]:
        """
        Parse a single file into CodeNodes.
        
        Args:
            file_path: Path to file
            
        Returns:
            List of parsed CodeNodes
        """
        try:
            # Detect language
            language = self._detect_language(file_path)
            if language == Language.UNKNOWN:
                return []
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse with tree-sitter or fallback
            nodes = self._parse_with_tree_sitter(content, file_path, language)
            if not nodes:
                nodes = self._parse_fallback(content, file_path, language)
            
            # Update metadata
            self._update_file_metadata(file_path, language, nodes)
            
            return nodes
            
        except Exception as e:
            self.logger.error(f"Failed to parse {file_path}: {e}")
            return []
    
    def _detect_language(self, file_path: Path) -> Language:
        """Detect language from file extension"""
        suffix = file_path.suffix.lower()
        return self._languages.get(suffix, Language.UNKNOWN)
    
    def _parse_with_tree_sitter(self, content: str, file_path: Path, language: Language) -> List[CodeNode]:
        """Parse using tree-sitter if available"""
        parser = self._get_tree_sitter_parser(language)
        if not parser:
            return []
        
        try:
            import tree_sitter
            
            # Parse AST
            tree = parser.parse(bytes(content, 'utf-8'))
            
            # Convert to CodeNodes
            nodes = []
            root_node = self._tree_sitter_to_code_node(
                tree.root_node, content, str(file_path), language
            )
            if root_node:
                nodes.append(root_node)
            
            return nodes
            
        except Exception as e:
            self.logger.warning(f"Tree-sitter parsing failed for {file_path}: {e}")
            return []
    
    def _tree_sitter_to_code_node(self, ts_node, content: str, file_path: str, language: Language) -> Optional[CodeNode]:
        """Convert tree-sitter node to CodeNode"""
        try:
            import tree_sitter
            
            # Get node type
            node_type = self._map_tree_sitter_type(ts_node.type, language)
            if node_type == NodeType.MODULE:
                node_type = NodeType.MODULE
            
            # Get node text
            start_byte = ts_node.start_byte
            end_byte = ts_node.end_byte
            node_text = content[start_byte:end_byte]
            
            # Get position
            start_pos = CodePosition(ts_node.start_point[0] + 1, ts_node.start_point[1] + 1)
            end_pos = CodePosition(ts_node.end_point[0] + 1, ts_node.end_point[1] + 1)
            code_range = CodeRange(start_pos, end_pos)
            
            # Extract name and other properties
            name = self._extract_node_name(ts_node, content)
            docstring = self._extract_docstring(ts_node, content)
            body = self._extract_body(ts_node, content)
            
            # Create CodeNode
            code_node = CodeNode(
                node_type=node_type,
                name=name,
                language=language,
                file_path=file_path,
                range=code_range,
                body=body,
                docstring=docstring,
                metadata={"tree_sitter_type": ts_node.type}
            )
            
            # Process children
            for child in ts_node.children:
                child_node = self._tree_sitter_to_code_node(child, content, file_path, language)
                if child_node:
                    code_node.add_child(child_node)
            
            return code_node
            
        except Exception as e:
            self.logger.warning(f"Failed to convert tree-sitter node: {e}")
            return None
    
    def _map_tree_sitter_type(self, ts_type: str, language: Language) -> NodeType:
        """Map tree-sitter node type to universal NodeType"""
        type_mapping = {
            # Python
            'function_definition': NodeType.FUNCTION,
            'class_definition': NodeType.CLASS,
            'module': NodeType.MODULE,
            'import_statement': NodeType.IMPORT,
            'import_from_statement': NodeType.IMPORT,
            'call': NodeType.CALL,
            'comment': NodeType.COMMENT,
            'string': NodeType.DOCSTRING,  # Heuristic
            
            # JavaScript/TypeScript
            'function_declaration': NodeType.FUNCTION,
            'class_declaration': NodeType.CLASS,
            'method_definition': NodeType.METHOD,
            'import_statement': NodeType.IMPORT,
            'call_expression': NodeType.CALL,
            'export_statement': NodeType.MODULE,
            
            # Go
            'function_declaration': NodeType.FUNCTION,
            'type_declaration': NodeType.CLASS,
            'import_declaration': NodeType.IMPORT,
            'call_expression': NodeType.CALL,
            
            # Java
            'method_declaration': NodeType.METHOD,
            'class_declaration': NodeType.CLASS,
            'interface_declaration': NodeType.INTERFACE,
            'import_declaration': NodeType.IMPORT,
            
            # Common
            'identifier': NodeType.VARIABLE,
            'string_literal': NodeType.CONSTANT,
            'number_literal': NodeType.CONSTANT,
        }
        
        return type_mapping.get(ts_type, NodeType.MODULE)
    
    def _extract_node_name(self, ts_node, content: str) -> Optional[str]:
        """Extract node name from tree-sitter node"""
        # Look for identifier child
        for child in ts_node.children:
            if child.type == 'identifier':
                start_byte = child.start_byte
                end_byte = child.end_byte
                return content[start_byte:end_byte]
        return None
    
    def _extract_docstring(self, ts_node, content: str) -> Optional[str]:
        """Extract docstring from tree-sitter node"""
        # Look for string literal child (heuristic for docstrings)
        for child in ts_node.children:
            if child.type in ['string', 'string_literal']:
                start_byte = child.start_byte
                end_byte = child.end_byte
                return content[start_byte:end_byte].strip('\'"')
        return None
    
    def _extract_body(self, ts_node, content: str) -> str:
        """Extract body content from tree-sitter node"""
        start_byte = ts_node.start_byte
        end_byte = ts_node.end_byte
        return content[start_byte:end_byte]
    
    def _parse_fallback(self, content: str, file_path: Path, language: Language) -> List[CodeNode]:
        """Fallback parsing using regex and simple heuristics"""
        nodes = []
        
        if language == Language.PYTHON:
            nodes = self._parse_python_fallback(content, str(file_path))
        elif language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            nodes = self._parse_javascript_fallback(content, str(file_path))
        else:
            # Generic fallback - create module node
            node = CodeNode(
                node_type=NodeType.MODULE,
                name=file_path.stem,
                language=language,
                file_path=str(file_path),
                body=content
            )
            nodes.append(node)
        
        return nodes
    
    def _parse_python_fallback(self, content: str, file_path: str) -> List[CodeNode]:
        """Fallback Python parsing using regex"""
        import re
        import ast
        
        nodes = []
        
        try:
            # Try to parse with AST first
            tree = ast.parse(content)
            
            # Create module node
            module_node = CodeNode(
                node_type=NodeType.MODULE,
                name=Path(file_path).stem,
                language=Language.PYTHON,
                file_path=file_path,
                body=content
            )
            
            # Process AST nodes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_node = CodeNode(
                        node_type=NodeType.FUNCTION,
                        name=node.name,
                        language=Language.PYTHON,
                        file_path=file_path,
                        range=CodeRange(
                            CodePosition(node.lineno, node.col_offset + 1),
                            CodePosition(node.end_lineno, node.end_col_offset + 1) if hasattr(node, 'end_lineno') else CodePosition(node.lineno, 1)
                        ),
                        body=ast.get_source_segment(content, node) or "",
                        docstring=ast.get_docstring(node)
                    )
                    module_node.add_child(func_node)
                
                elif isinstance(node, ast.ClassDef):
                    class_node = CodeNode(
                        node_type=NodeType.CLASS,
                        name=node.name,
                        language=Language.PYTHON,
                        file_path=file_path,
                        range=CodeRange(
                            CodePosition(node.lineno, node.col_offset + 1),
                            CodePosition(node.end_lineno, node.end_col_offset + 1) if hasattr(node, 'end_lineno') else CodePosition(node.lineno, 1)
                        ),
                        body=ast.get_source_segment(content, node) or "",
                        docstring=ast.get_docstring(node)
                    )
                    module_node.add_child(class_node)
            
            nodes.append(module_node)
            
        except SyntaxError:
            # If AST parsing fails, create simple module
            module_node = CodeNode(
                node_type=NodeType.MODULE,
                name=Path(file_path).stem,
                language=Language.PYTHON,
                file_path=file_path,
                body=content
            )
            nodes.append(module_node)
        
        return nodes
    
    def _parse_javascript_fallback(self, content: str, file_path: str) -> List[CodeNode]:
        """Fallback JavaScript parsing using regex"""
        import re
        
        nodes = []
        
        # Create module node
        module_node = CodeNode(
            node_type=NodeType.MODULE,
            name=Path(file_path).stem,
            language=Language.JAVASCRIPT,
            file_path=file_path,
            body=content
        )
        
        # Extract functions using regex
        func_pattern = r'(?:function\s+(\w+)|(\w+)\s*=\s*function|const\s+(\w+)\s*=\s*\([^)]*\)\s*=>)'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1) or match.group(2) or match.group(3)
            if func_name:
                func_node = CodeNode(
                    node_type=NodeType.FUNCTION,
                    name=func_name,
                    language=Language.JAVASCRIPT,
                    file_path=file_path,
                    body=match.group(0)
                )
                module_node.add_child(func_node)
        
        nodes.append(module_node)
        return nodes
    
    def get_changed_files(self) -> List[str]:
        """Get list of files that have changed since last parsing"""
        changed_files = []
        
        for file_path in self._find_code_files():
            if self._should_parse_file(file_path):
                changed_files.append(str(file_path))
        
        return changed_files
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _update_file_metadata(self, file_path: Path, language: Language, nodes: List[CodeNode]):
        """Update metadata for parsed file"""
        file_path_str = str(file_path)
        
        metadata = FileMetadata(
            file_path=file_path_str,
            file_hash=self._calculate_file_hash(file_path),
            last_modified=file_path.stat().st_mtime,
            parsed_at=datetime.now(),
            language=language,
            node_count=len(nodes)
        )
        
        self.file_metadata[file_path_str] = metadata
    
    def _load_metadata(self):
        """Load file metadata from disk"""
        if not self.metadata_file.exists():
            return
        
        try:
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
            
            self.file_metadata = {}
            for file_path, metadata_dict in data.items():
                # Convert parsed_at back to datetime
                metadata_dict['parsed_at'] = datetime.fromisoformat(metadata_dict['parsed_at'])
                metadata_dict['language'] = Language(metadata_dict['language'])
                
                self.file_metadata[file_path] = FileMetadata(**metadata_dict)
                
        except Exception as e:
            self.logger.warning(f"Failed to load metadata: {e}")
            self.file_metadata = {}
    
    def _save_metadata(self):
        """Save file metadata to disk"""
        try:
            data = {}
            for file_path, metadata in self.file_metadata.items():
                data[file_path] = {
                    'file_path': metadata.file_path,
                    'file_hash': metadata.file_hash,
                    'last_modified': metadata.last_modified,
                    'parsed_at': metadata.parsed_at.isoformat(),
                    'language': metadata.language.value,
                    'node_count': metadata.node_count
                }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {e}")
