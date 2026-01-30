"""
Universal Code Parser using Tree-sitter

Provides unified parsing interface for multiple programming languages
using tree-sitter grammars. Converts language-specific ASTs to
universal CodeNode model.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import logging

try:
    import tree_sitter
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logging.warning("tree-sitter not available. Install with: pip install tree-sitter")

from .code_model import CodeNode, NodeType, Language, CodeRange, CodePosition, CodeSignature, CodeRepository


@dataclass
class ParseResult:
    """Result of parsing operation"""
    success: bool
    nodes: List[CodeNode]
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class LanguageDetector:
    """Detect programming language from file extension and content"""
    
    EXTENSION_MAP = {
        '.py': Language.PYTHON,
        '.js': Language.JAVASCRIPT,
        '.jsx': Language.JAVASCRIPT,
        '.ts': Language.TYPESCRIPT,
        '.tsx': Language.TYPESCRIPT,
        '.go': Language.GO,
        '.java': Language.JAVA,
        '.cs': Language.CSHARP,
        '.rs': Language.RUST,
        '.cpp': Language.CPP,
        '.cxx': Language.CPP,
        '.cc': Language.CPP,
        '.c': Language.CPP,
        '.h': Language.CPP,
        '.hpp': Language.CPP,
        '.rb': Language.RUBY,
        '.php': Language.PHP,
        '.kt': Language.KOTLIN,
        '.swift': Language.SWIFT,
    }
    
    SHEBANG_MAP = {
        'python': Language.PYTHON,
        'node': Language.JAVASCRIPT,
        'bash': Language.UNKNOWN,  # Could add shell support
    }
    
    @classmethod
    def detect_language(cls, file_path: str, content: str = None) -> Language:
        """Detect language from file path and optionally content"""
        path = Path(file_path)
        
        # Check extension
        ext = path.suffix.lower()
        if ext in cls.EXTENSION_MAP:
            return cls.EXTENSION_MAP[ext]
        
        # Check shebang if content provided
        if content and content.startswith('#!'):
            first_line = content.split('\n')[0]
            for shebang, lang in cls.SHEBANG_MAP.items():
                if shebang in first_line:
                    return lang
        
        return Language.UNKNOWN


class TreeSitterParser:
    """Tree-sitter based parser for multiple languages"""
    
    def __init__(self):
        self.parsers = {}
        self._init_parsers()
    
    def _init_parsers(self):
        """Initialize tree-sitter parsers for supported languages"""
        if not TREE_SITTER_AVAILABLE:
            return
        
        # Language parser mappings
        try:
            # Python
            import tree_sitter_python
            self.parsers[Language.PYTHON] = tree_sitter_python.language()
        except ImportError:
            logging.warning("tree-sitter-python not available")
        
        try:
            # JavaScript
            import tree_sitter_javascript
            self.parsers[Language.JAVASCRIPT] = tree_sitter_javascript.language()
        except ImportError:
            logging.warning("tree-sitter-javascript not available")
        
        try:
            # TypeScript
            import tree_sitter_typescript
            self.parsers[Language.TYPESCRIPT] = tree_sitter_typescript.language_typescript()
        except ImportError:
            logging.warning("tree-sitter-typescript not available")
        
        try:
            # Go
            import tree_sitter_go
            self.parsers[Language.GO] = tree_sitter_go.language()
        except ImportError:
            logging.warning("tree-sitter-go not available")
        
        try:
            # Java
            import tree_sitter_java
            self.parsers[Language.JAVA] = tree_sitter_java.language()
        except ImportError:
            logging.warning("tree-sitter-java not available")
        
        try:
            # C#
            import tree_sitter_c_sharp
            self.parsers[Language.CSHARP] = tree_sitter_c_sharp.language()
        except ImportError:
            logging.warning("tree-sitter-c-sharp not available")
        
        try:
            # Rust
            import tree_sitter_rust
            self.parsers[Language.RUST] = tree_sitter_rust.language()
        except ImportError:
            logging.warning("tree-sitter-rust not available")
    
    def is_supported(self, language: Language) -> bool:
        """Check if language is supported"""
        return language in self.parsers
    
    def parse_file(self, file_path: str, content: str = None) -> ParseResult:
        """Parse a single file"""
        if content is None:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                return ParseResult(False, [], [f"Failed to read file: {e}"])
        
        # Detect language
        language = LanguageDetector.detect_language(file_path, content)
        if language == Language.UNKNOWN:
            return ParseResult(False, [], [f"Unknown language for file: {file_path}"])
        
        if not self.is_supported(language):
            return ParseResult(False, [], [f"Language not supported: {language.value}"])
        
        # Parse with tree-sitter
        try:
            parser = tree_sitter.Parser()
            language_parser = self.parsers[language]
            
            # Create parser with language (new API)
            parser = tree_sitter.Parser(language_parser)
            
            tree = parser.parse(bytes(content, "utf-8"))
            
            # Convert to CodeNode
            converter = ASTToCodeNodeConverter(language, file_path, content)
            root_node = converter.convert(tree.root_node)
            
            return ParseResult(True, [root_node])
            
        except Exception as e:
            return ParseResult(False, [], [f"Parse error: {e}"])


class ASTToCodeNodeConverter:
    """Convert tree-sitter AST nodes to universal CodeNode model"""
    
    def __init__(self, language: Language, file_path: str, source_code: str):
        self.language = language
        self.file_path = file_path
        self.source_code = source_code
        self.lines = source_code.split('\n')
    
    def convert(self, ts_node) -> CodeNode:
        """Convert tree-sitter node to CodeNode"""
        # Create root module node
        root_node = CodeNode(
            node_type=NodeType.MODULE,
            name=Path(self.file_path).stem,
            language=self.language,
            file_path=self.file_path,
            body=self.source_code
        )
        
        # Process children
        for child in ts_node.children:
            converted = self._convert_node(child)
            if converted:
                root_node.add_child(converted)
        
        return root_node
    
    def _convert_node(self, ts_node) -> Optional[CodeNode]:
        """Convert individual tree-sitter node"""
        node_type = self._map_node_type(ts_node.type)
        if not node_type:
            return None
        
        # Extract node information
        name = self._extract_name(ts_node)
        signature = self._extract_signature(ts_node)
        body = self._extract_body(ts_node)
        docstring = self._extract_docstring(ts_node)
        
        # Get position
        start_pos = CodePosition(ts_node.start_point[0] + 1, ts_node.start_point[1] + 1)
        end_pos = CodePosition(ts_node.end_point[0] + 1, ts_node.end_point[1] + 1)
        code_range = CodeRange(start_pos, end_pos)
        
        # Create CodeNode
        code_node = CodeNode(
            node_type=node_type,
            name=name,
            signature=signature,
            language=self.language,
            file_path=self.file_path,
            range=code_range,
            body=body,
            docstring=docstring
        )
        
        # Add language-specific metadata
        self._add_language_metadata(code_node, ts_node)
        
        # Process children
        for child in ts_node.children:
            converted = self._convert_node(child)
            if converted:
                code_node.add_child(converted)
        
        return code_node
    
    def _map_node_type(self, ts_type: str) -> Optional[NodeType]:
        """Map tree-sitter node type to universal NodeType"""
        type_mappings = {
            # Python
            'function_definition': NodeType.FUNCTION,
            'async_function_definition': NodeType.FUNCTION,
            'class_definition': NodeType.CLASS,
            'import_statement': NodeType.IMPORT,
            'import_from_statement': NodeType.IMPORT,
            'decorated_definition': NodeType.FUNCTION,
            'decorator': NodeType.DECORATOR,
            'call': NodeType.CALL,
            'assignment': NodeType.VARIABLE,
            
            # JavaScript/TypeScript
            'function_declaration': NodeType.FUNCTION,
            'function_expression': NodeType.FUNCTION,
            'arrow_function': NodeType.FUNCTION,
            'class_declaration': NodeType.CLASS,
            'class_expression': NodeType.CLASS,
            'import_statement': NodeType.IMPORT,
            'export_statement': NodeType.IMPORT,
            'call_expression': NodeType.CALL,
            'variable_declaration': NodeType.VARIABLE,
            'method_definition': NodeType.METHOD,
            
            # Go
            'function_declaration': NodeType.FUNCTION,
            'method_declaration': NodeType.FUNCTION,
            'type_declaration': NodeType.CLASS,
            'struct_type': NodeType.CLASS,
            'interface_type': NodeType.INTERFACE,
            'import_spec': NodeType.IMPORT,
            'call_expression': NodeType.CALL,
            
            # Java
            'method_declaration': NodeType.METHOD,
            'constructor_declaration': NodeType.METHOD,
            'class_declaration': NodeType.CLASS,
            'interface_declaration': NodeType.INTERFACE,
            'enum_declaration': NodeType.ENUM,
            'import_declaration': NodeType.IMPORT,
            'method_invocation': NodeType.CALL,
            'field_declaration': NodeType.VARIABLE,
            
            # C#
            'method_declaration': NodeType.METHOD,
            'constructor_declaration': NodeType.METHOD,
            'class_declaration': NodeType.CLASS,
            'interface_declaration': NodeType.INTERFACE,
            'enum_declaration': NodeType.ENUM,
            'using_directive': NodeType.IMPORT,
            'invocation_expression': NodeType.CALL,
            'field_declaration': NodeType.VARIABLE,
        }
        
        return type_mappings.get(ts_type)
    
    def _extract_name(self, ts_node) -> Optional[str]:
        """Extract node name from tree-sitter node"""
        # Try different field names for name
        name_fields = ['name', 'identifier', 'class_name', 'function_name']
        
        for field in name_fields:
            child = ts_node.child_by_field_name(field)
            if child:
                return self._get_node_text(child)
        
        # Try to find identifier child
        for child in ts_node.children:
            if child.type == 'identifier':
                return self._get_node_text(child)
        
        return None
    
    def _extract_signature(self, ts_node) -> Optional[CodeSignature]:
        """Extract function/method signature"""
        if ts_node.type not in ['function_definition', 'function_declaration', 'method_declaration']:
            return None
        
        # Extract name
        name = self._extract_name(ts_node) or "unknown"
        
        # Extract parameters
        parameters = []
        params_node = ts_node.child_by_field_name('parameters')
        if params_node:
            parameters = self._extract_parameters(params_node)
        
        # Extract return type
        return_type = None
        return_type_node = ts_node.child_by_field_name('return_type')
        if return_type_node:
            return_type = self._get_node_text(return_type_node)
        
        return CodeSignature(name=name, parameters=parameters, return_type=return_type)
    
    def _extract_parameters(self, params_node) -> List[Dict[str, Any]]:
        """Extract function parameters"""
        parameters = []
        
        for child in params_node.children:
            if child.type == 'identifier':
                param_name = self._get_node_text(child)
                parameters.append({"name": param_name, "type": "unknown"})
            elif child.type == 'typed_parameter':
                # Try to extract type and name
                name_node = child.child_by_field_name('name')
                type_node = child.child_by_field_name('type')
                
                param_name = self._get_node_text(name_node) if name_node else "unknown"
                param_type = self._get_node_text(type_node) if type_node else "unknown"
                
                parameters.append({"name": param_name, "type": param_type})
        
        return parameters
    
    def _extract_body(self, ts_node) -> str:
        """Extract node body text"""
        body_node = ts_node.child_by_field_name('body')
        if body_node:
            return self._get_node_text(body_node)
        return ""
    
    def _extract_docstring(self, ts_node) -> Optional[str]:
        """Extract docstring/comment"""
        # Look for string literal or comment nodes
        for child in ts_node.children:
            if child.type in ['string_literal', 'comment', 'block_comment']:
                text = self._get_node_text(child)
                # Clean up docstring
                text = text.strip('\'"')
                if text.startswith('"""') or text.startswith("'''"):
                    text = text[3:-3].strip()
                return text
        return None
    
    def _get_node_text(self, ts_node) -> str:
        """Get text content of tree-sitter node"""
        start_byte = ts_node.start_byte
        end_byte = ts_node.end_byte
        return self.source_code.encode('utf-8')[start_byte:end_byte].decode('utf-8')
    
    def _add_language_metadata(self, code_node: CodeNode, ts_node):
        """Add language-specific metadata"""
        if self.language == Language.PYTHON:
            self._add_python_metadata(code_node, ts_node)
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            self._add_javascript_metadata(code_node, ts_node)
        elif self.language == Language.GO:
            self._add_go_metadata(code_node, ts_node)
        elif self.language == Language.JAVA:
            self._add_java_metadata(code_node, ts_node)
    
    def _add_python_metadata(self, code_node: CodeNode, ts_node):
        """Add Python-specific metadata"""
        # Extract decorators
        decorators = []
        if ts_node.type == 'decorated_definition':
            for child in ts_node.children:
                if child.type == 'decorator':
                    decorator_text = self._get_node_text(child)
                    decorators.append(decorator_text.strip('@'))
        
        code_node.decorators = decorators
        
        # Extract imports
        if ts_node.type == 'import_statement':
            for child in ts_node.children:
                if child.type == 'dotted_name':
                    import_name = self._get_node_text(child)
                    code_node.imports.append(import_name)
        
        # Extract function calls
        calls = []
        for child in ts_node.children:
            if child.type == 'call':
                call_name = self._extract_call_name(child)
                if call_name:
                    calls.append(call_name)
        
        code_node.calls = calls
    
    def _add_javascript_metadata(self, code_node: CodeNode, ts_node):
        """Add JavaScript/TypeScript-specific metadata"""
        # Extract imports/exports
        if ts_node.type == 'import_statement':
            for child in ts_node.children:
                if child.type == 'identifier':
                    import_name = self._get_node_text(child)
                    code_node.imports.append(import_name)
    
    def _add_go_metadata(self, code_node: CodeNode, ts_node):
        """Add Go-specific metadata"""
        # Extract imports
        if ts_node.type == 'import_spec':
            import_path = self._get_node_text(ts_node)
            code_node.imports.append(import_path.strip('"'))
    
    def _add_java_metadata(self, code_node: CodeNode, ts_node):
        """Add Java-specific metadata"""
        # Extract annotations
        annotations = []
        for child in ts_node.children:
            if child.type == 'marker_annotation':
                annotation_text = self._get_node_text(child)
                annotations.append(annotation_text.strip('@'))
        
        code_node.annotations = annotations
    
    def _extract_call_name(self, call_node) -> Optional[str]:
        """Extract function call name"""
        function_node = call_node.child_by_field_name('function')
        if function_node:
            if function_node.type == 'identifier':
                return self._get_node_text(function_node)
            elif function_node.type == 'attribute':
                # Handle method calls like obj.method()
                for child in function_node.children:
                    if child.type == 'identifier':
                        return self._get_node_text(child)
        return None


class UniversalCodeParser:
    """Universal code parser supporting multiple languages"""
    
    def __init__(self):
        self.tree_sitter_parser = TreeSitterParser()
        self.fallback_parser = FallbackParser()
    
    def parse_repository(self, repo_path: str, **kwargs) -> CodeRepository:
        """Parse entire repository"""
        repo_path = Path(repo_path).resolve()
        repo_name = repo_path.name
        
        repository = CodeRepository(name=repo_name, root_path=str(repo_path))
        
        # Find all code files
        code_files = self._find_code_files(repo_path)
        
        for file_path in code_files:
            result = self.parse_file(str(file_path))
            if result.success:
                for module in result.nodes:
                    repository.add_module(module)
            else:
                logging.warning(f"Failed to parse {file_path}: {result.errors}")
        
        return repository
    
    def parse_file(self, file_path: str, content: str = None) -> ParseResult:
        """Parse single file"""
        # Try tree-sitter first
        if self.tree_sitter_parser.is_supported(LanguageDetector.detect_language(file_path, content)):
            return self.tree_sitter_parser.parse_file(file_path, content)
        
        # Fallback to simple parser
        return self.fallback_parser.parse_file(file_path, content)
    
    def _find_code_files(self, repo_path: Path) -> List[Path]:
        """Find all code files in repository"""
        code_files = []
        
        # Common ignore patterns
        ignore_patterns = {
            '.git', '__pycache__', 'node_modules', '.vscode', '.idea',
            'target', 'build', 'dist', '.pytest_cache', '.coverage'
        }
        
        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                # Skip ignored directories
                if any(pattern in file_path.parts for pattern in ignore_patterns):
                    continue
                
                # Check if it's a code file
                if LanguageDetector.detect_language(str(file_path)) != Language.UNKNOWN:
                    code_files.append(file_path)
        
        return sorted(code_files)
    
    def get_supported_languages(self) -> List[Language]:
        """Get list of supported languages"""
        return [lang for lang in Language if lang != Language.UNKNOWN]


class FallbackParser:
    """Simple fallback parser for unsupported languages"""
    
    def parse_file(self, file_path: str, content: str = None) -> ParseResult:
        """Simple parsing based on regex patterns"""
        if content is None:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                return ParseResult(False, [], [f"Failed to read file: {e}"])
        
        language = LanguageDetector.detect_language(file_path, content)
        
        # Create basic module node
        module_node = CodeNode(
            node_type=NodeType.MODULE,
            name=Path(file_path).stem,
            language=language,
            file_path=file_path,
            body=content
        )
        
        # Try basic regex extraction
        self._extract_with_regex(module_node, content, language)
        
        return ParseResult(True, [module_node])
    
    def _extract_with_regex(self, module_node: CodeNode, content: str, language: Language):
        """Extract basic information using regex"""
        if language == Language.PYTHON:
            self._extract_python_regex(module_node, content)
        elif language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            self._extract_javascript_regex(module_node, content)
    
    def _extract_python_regex(self, module_node: CodeNode, content: str):
        """Extract Python patterns with regex"""
        # Function definitions
        func_pattern = r'def\s+(\w+)\s*\([^)]*\):'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1)
            func_node = CodeNode(
                node_type=NodeType.FUNCTION,
                name=func_name,
                language=module_node.language,
                file_path=module_node.file_path
            )
            module_node.add_child(func_node)
        
        # Class definitions
        class_pattern = r'class\s+(\w+)(?:\([^)]*\))?:'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            class_node = CodeNode(
                node_type=NodeType.CLASS,
                name=class_name,
                language=module_node.language,
                file_path=module_node.file_path
            )
            module_node.add_child(class_node)
        
        # Imports
        import_pattern = r'import\s+(\w+(?:\.\w+)*)'
        for match in re.finditer(import_pattern, content):
            import_name = match.group(1)
            module_node.imports.append(import_name)
    
    def _extract_javascript_regex(self, module_node: CodeNode, content: str):
        """Extract JavaScript patterns with regex"""
        # Function declarations
        func_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*{'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1)
            func_node = CodeNode(
                node_type=NodeType.FUNCTION,
                name=func_name,
                language=module_node.language,
                file_path=module_node.file_path
            )
            module_node.add_child(func_node)
        
        # Class declarations
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+\w+)?\s*{'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            class_node = CodeNode(
                node_type=NodeType.CLASS,
                name=class_name,
                language=module_node.language,
                file_path=module_node.file_path
            )
            module_node.add_child(class_node)
