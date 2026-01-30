"""Code Adapter for NLP3Tree - Multi-language code analysis"""

import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator, Set
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..core import TreeNode, NodeType, NodeMetadata


@dataclass(frozen=True)
class CodeElement:
    """Represents a code element (function, class, etc.)"""
    name: str
    type: str  # function, class, method, variable, import
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    signature: Optional[str] = None
    decorators: List[str] = None
    imports: List[str] = None
    calls: List[str] = None
    parent: Optional[str] = None
    
    def __post_init__(self):
        if self.decorators is None:
            object.__setattr__(self, 'decorators', [])
        if self.imports is None:
            object.__setattr__(self, 'imports', [])
        if self.calls is None:
            object.__setattr__(self, 'calls', [])
    
    def __hash__(self):
        return hash((self.name, self.type, self.line_start, self.line_end))


class LanguageParser(ABC):
    """Abstract base class for language-specific parsers"""
    
    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the file"""
        pass
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> List[CodeElement]:
        """Parse file and extract code elements"""
        pass
    
    @abstractmethod
    def extract_imports(self, content: str) -> List[str]:
        """Extract import statements"""
        pass
    
    @abstractmethod
    def extract_functions(self, content: str) -> List[CodeElement]:
        """Extract function definitions"""
        pass
    
    @abstractmethod
    def extract_classes(self, content: str) -> List[CodeElement]:
        """Extract class definitions"""
        pass


class PythonParser(LanguageParser):
    """Python code parser using AST"""
    
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix in ['.py', '.pyi']
    
    def parse_file(self, file_path: Path) -> List[CodeElement]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        elements = []
        elements.extend(self.extract_imports(content))
        elements.extend(self.extract_functions(content))
        elements.extend(self.extract_classes(content))
        return elements
    
    def extract_imports(self, content: str) -> List[CodeElement]:
        """Extract import statements"""
        imports = []
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_element = CodeElement(
                        name=alias.name,
                        type="import",
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        signature=f"import {alias.name}"
                    )
                    imports.append(import_element)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    import_element = CodeElement(
                        name=f"{module}.{alias.name}",
                        type="import",
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        signature=f"from {module} import {alias.name}"
                    )
                    imports.append(import_element)
        
        return imports
    
    def extract_functions(self, content: str) -> List[CodeElement]:
        """Extract function definitions"""
        functions = []
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Extract decorators
                decorators = []
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        decorators.append(decorator.id)
                    elif isinstance(decorator, ast.Attribute):
                        decorators.append(ast.unparse(decorator))
                
                # Extract docstring
                docstring = ast.get_docstring(node)
                
                # Extract signature
                signature = f"def {node.name}(...)"
                
                # Extract function calls
                calls = []
                for sub_node in ast.walk(node):
                    if isinstance(sub_node, ast.Call):
                        if isinstance(sub_node.func, ast.Name):
                            calls.append(sub_node.func.id)
                        elif isinstance(sub_node.func, ast.Attribute):
                            calls.append(ast.unparse(sub_node.func))
                
                func_element = CodeElement(
                    name=node.name,
                    type="function",
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    docstring=docstring,
                    signature=signature,
                    decorators=decorators,
                    calls=calls
                )
                functions.append(func_element)
        
        return functions
    
    def extract_classes(self, content: str) -> List[CodeElement]:
        """Extract class definitions"""
        classes = []
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Extract decorators
                decorators = []
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        decorators.append(decorator.id)
                    elif isinstance(decorator, ast.Attribute):
                        decorators.append(ast.unparse(decorator))
                
                # Extract docstring
                docstring = ast.get_docstring(node)
                
                # Extract methods
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)
                
                class_element = CodeElement(
                    name=node.name,
                    type="class",
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    docstring=docstring,
                    signature=f"class {node.name}:",
                    decorators=decorators,
                    calls=methods
                )
                classes.append(class_element)
        
        return classes


class JavaScriptParser(LanguageParser):
    """JavaScript/TypeScript code parser"""
    
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix in ['.js', '.jsx', '.ts', '.tsx', '.mjs']
    
    def parse_file(self, file_path: Path) -> List[CodeElement]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        elements = []
        elements.extend(self.extract_imports(content))
        elements.extend(self.extract_functions(content))
        elements.extend(self.extract_classes(content))
        return elements
    
    def extract_imports(self, content: str) -> List[CodeElement]:
        """Extract import statements using regex"""
        imports = []
        
        # ES6 imports
        import_patterns = [
            (r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]', "import"),
            (r'import\s+[\'"]([^\'"]+)[\'"]', "import"),
            (r'require\([\'"]([^\'"]+)[\'"]\)', "require")
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, import_type in import_patterns:
                match = re.search(pattern, line)
                if match:
                    import_element = CodeElement(
                        name=match.group(1),
                        type="import",
                        line_start=i,
                        line_end=i,
                        signature=line.strip()
                    )
                    imports.append(import_element)
        
        return imports
    
    def extract_functions(self, content: str) -> List[CodeElement]:
        """Extract function definitions"""
        functions = []
        
        # Function patterns
        patterns = [
            (r'function\s+(\w+)\s*\(', 'function'),
            (r'const\s+(\w+)\s*=\s*\(', 'arrow_function'),
            (r'(\w+)\s*:\s*function\s*\(', 'method'),
            (r'async\s+function\s+(\w+)\s*\(', 'async_function'),
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, func_type in patterns:
                match = re.search(pattern, line)
                if match:
                    func_element = CodeElement(
                        name=match.group(1),
                        type=func_type,
                        line_start=i,
                        line_end=i,
                        signature=line.strip()
                    )
                    functions.append(func_element)
        
        return functions
    
    def extract_classes(self, content: str) -> List[CodeElement]:
        """Extract class definitions"""
        classes = []
        
        # Class patterns
        patterns = [
            r'class\s+(\w+)',
            r'export\s+class\s+(\w+)',
            r'export\s+default\s+class\s+(\w+)',
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    class_element = CodeElement(
                        name=match.group(1),
                        type="class",
                        line_start=i,
                        line_end=i,
                        signature=line.strip()
                    )
                    classes.append(class_element)
        
        return classes


class GoParser(LanguageParser):
    """Go code parser"""
    
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix == '.go'
    
    def parse_file(self, file_path: Path) -> List[CodeElement]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        elements = []
        elements.extend(self.extract_imports(content))
        elements.extend(self.extract_functions(content))
        return elements
    
    def extract_imports(self, content: str) -> List[CodeElement]:
        """Extract import statements"""
        imports = []
        
        # Go import patterns
        patterns = [
            (r'import\s+[\'"]([^\'"]+)[\'"]', "import"),
            (r'import\s*\(\s*([^)]+)\s*\)', "import_block"),
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, import_type in patterns:
                match = re.search(pattern, line, re.MULTILINE | re.DOTALL)
                if match:
                    if import_type == "import_block":
                        # Multi-line import block
                        block_content = match.group(1)
                        block_lines = block_content.strip().split('\n')
                        for block_line in block_lines:
                            block_line = block_line.strip().strip('"\'')
                            if block_line:
                                import_element = CodeElement(
                                    name=block_line,
                                    type="import",
                                    line_start=i,
                                    line_end=i,
                                    signature=f"import {block_line}"
                                )
                                imports.append(import_element)
                    else:
                        import_element = CodeElement(
                            name=match.group(1).strip('"\''),
                            type="import",
                            line_start=i,
                            line_end=i,
                            signature=line.strip()
                        )
                        imports.append(import_element)
        
        return imports
    
    def extract_functions(self, content: str) -> List[CodeElement]:
        """Extract function definitions"""
        functions = []
        
        # Go function patterns
        patterns = [
            r'func\s+(\w+)\s*\(',
            r'func\s*\([^)]+\)\s*(\w+)\s*\(',  # Method with receiver
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    func_element = CodeElement(
                        name=match.group(1),
                        type="function",
                        line_start=i,
                        line_end=i,
                        signature=line.strip()
                    )
                    functions.append(func_element)
        
        return functions
    
    def extract_classes(self, content: str) -> List[CodeElement]:
        """Go doesn't have classes, but has structs"""
        structs = []
        
        pattern = r'type\s+(\w+)\s+struct\s*\{'
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            match = re.search(pattern, line)
            if match:
                struct_element = CodeElement(
                    name=match.group(1),
                    type="struct",
                    line_start=i,
                    line_end=i,
                    signature=line.strip()
                )
                structs.append(struct_element)
        
        return structs


class JavaParser(LanguageParser):
    """Java code parser"""
    
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix == '.java'
    
    def parse_file(self, file_path: Path) -> List[CodeElement]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        elements = []
        elements.extend(self.extract_imports(content))
        elements.extend(self.extract_functions(content))
        elements.extend(self.extract_classes(content))
        return elements
    
    def extract_imports(self, content: str) -> List[CodeElement]:
        """Extract import statements"""
        imports = []
        pattern = r'import\s+([^;]+);'
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            match = re.search(pattern, line)
            if match:
                import_element = CodeElement(
                    name=match.group(1).strip(),
                    type="import",
                    line_start=i,
                    line_end=i,
                    signature=line.strip()
                )
                imports.append(import_element)
        
        return imports
    
    def extract_functions(self, content: str) -> List[CodeElement]:
        """Extract method definitions"""
        methods = []
        
        # Java method patterns
        patterns = [
            r'(?:public|private|protected|static|final|native|synchronized|abstract|transient|strictfp)?\s+'
            r'(?:(?:\w+\.)*\w+)\s+'  # Return type
            r'(\w+)\s*\(',  # Method name
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            match = re.search(pattern, line)
            if match:
                method_element = CodeElement(
                    name=match.group(1),
                    type="method",
                    line_start=i,
                    line_end=i,
                    signature=line.strip()
                )
                methods.append(method_element)
        
        return methods
    
    def extract_classes(self, content: str) -> List[CodeElement]:
        """Extract class definitions"""
        classes = []
        
        # Java class patterns
        patterns = [
            r'(?:public|private|protected)?\s+'
            r'(?:abstract|final)?\s+'
            r'class\s+(\w+)',
            r'(?:public|private|protected)?\s+'
            r'(?:abstract|final)?\s+'
            r'interface\s+(\w+)',
            r'(?:public|private|protected)?\s+'
            r'enum\s+(\w+)',
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    class_element = CodeElement(
                        name=match.group(1),
                        type="class",
                        line_start=i,
                        line_end=i,
                        signature=line.strip()
                    )
                    classes.append(class_element)
        
        return classes


class CodeAdapter:
    """Main adapter for code analysis"""
    
    def __init__(self):
        self.parsers = [
            PythonParser(),
            JavaScriptParser(),
            GoParser(),
            JavaParser(),
        ]
    
    def get_parser(self, file_path: Path) -> Optional[LanguageParser]:
        """Get appropriate parser for file"""
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser
        return None
    
    def analyze_file(self, file_path: Path) -> List[CodeElement]:
        """Analyze a single file"""
        parser = self.get_parser(file_path)
        if not parser:
            return []
        
        return parser.parse_file(file_path)
    
    def analyze_directory(self, dir_path: Path) -> Dict[str, List[CodeElement]]:
        """Analyze all files in directory"""
        results = {}
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                elements = self.analyze_file(file_path)
                if elements:
                    results[str(file_path)] = elements
        
        return results
    
    def search_elements(self, elements: List[CodeElement], query: str) -> List[CodeElement]:
        """Search elements by name, type, or content"""
        results = []
        query_lower = query.lower()
        
        for element in elements:
            # Search in name
            if query_lower in element.name.lower():
                results.append(element)
                continue
            
            # Search in docstring
            if element.docstring and query_lower in element.docstring.lower():
                results.append(element)
                continue
            
            # Search in signature
            if element.signature and query_lower in element.signature.lower():
                results.append(element)
                continue
            
            # Search in calls
            for call in element.calls:
                if query_lower in call.lower():
                    results.append(element)
                    break
        
        return results
