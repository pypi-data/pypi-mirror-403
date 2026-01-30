"""Code Intelligence Engine - Advanced code analysis capabilities"""

import re
import ast
import json
from typing import Dict, List, Set, Any, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from pathlib import Path
import hashlib

from .code_adapter import CodeElement, CodeAdapter


@dataclass
class CodeIndex:
    """Inverted index for code search"""
    token_to_files: Dict[str, Set[str]]
    token_to_elements: Dict[str, List[CodeElement]]
    file_to_elements: Dict[str, List[CodeElement]]
    function_calls: Dict[str, List[str]]  # function -> list of called functions
    call_graph: Dict[str, Set[str]]  # function -> set of functions that call it


@dataclass
class CodeMetrics:
    """Code metrics and statistics"""
    total_files: int
    total_functions: int
    total_classes: int
    total_lines: int
    language_distribution: Dict[str, int]
    complexity_metrics: Dict[str, Any]


class CodeIntelligenceEngine:
    """Advanced code analysis engine"""
    
    def __init__(self):
        self.code_adapter = CodeAdapter()
        self.index: Optional[CodeIndex] = None
        self.metrics: Optional[CodeMetrics] = None
    
    def build_index(self, root_path: Path) -> CodeIndex:
        """Build inverted index for code search"""
        print(f"Building index for {root_path}...")
        
        # Analyze all files
        all_elements = self.code_adapter.analyze_directory(root_path)
        
        # Initialize index structures
        token_to_files = defaultdict(set)
        token_to_elements = defaultdict(list)
        file_to_elements = {}
        function_calls = defaultdict(list)
        call_graph = defaultdict(set)
        
        # Process each file
        for file_path, elements in all_elements.items():
            file_to_elements[file_path] = elements
            
            for element in elements:
                # Tokenize element
                tokens = self._tokenize_element(element)
                
                # Add to index
                for token in tokens:
                    token_to_files[token].add(file_path)
                    token_to_elements[token].append(element)
                
                # Build call graph
                if element.type in ['function', 'method']:
                    function_calls[element.name] = element.calls
                    for called_func in element.calls:
                        call_graph[called_func].add(element.name)
        
        self.index = CodeIndex(
            token_to_files=dict(token_to_files),
            token_to_elements=dict(token_to_elements),
            file_to_elements=file_to_elements,
            function_calls=dict(function_calls),
            call_graph=dict(call_graph)
        )
        
        print(f"Index built: {len(all_elements)} files, {sum(len(e) for e in all_elements.values())} elements")
        return self.index
    
    def _tokenize_element(self, element: CodeElement) -> List[str]:
        """Extract searchable tokens from code element"""
        tokens = []
        
        # Name tokens
        name_tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', element.name)
        tokens.extend(name_tokens)
        
        # Docstring tokens
        if element.docstring:
            doc_tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', element.docstring.lower())
            tokens.extend(doc_tokens)
        
        # Signature tokens
        if element.signature:
            sig_tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', element.signature)
            tokens.extend(sig_tokens)
        
        # Call tokens
        for call in element.calls:
            call_tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', call)
            tokens.extend(call_tokens)
        
        # Type tokens
        tokens.append(element.type)
        
        return [token.lower() for token in tokens]
    
    def search(self, query: str, limit: int = 50) -> List[Tuple[CodeElement, str]]:
        """Search code using inverted index"""
        if not self.index:
            raise RuntimeError("Index not built. Call build_index() first.")
        
        # Tokenize query
        query_tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', query.lower())
        
        # Score elements
        element_scores = defaultdict(int)
        element_files = {}
        
        for token in query_tokens:
            if token in self.index.token_to_elements:
                for element in self.index.token_to_elements[token]:
                    element_scores[element] += 1
                    # Find which file this element belongs to
                    if element not in element_files:
                        for file_path, elements in self.index.file_to_elements.items():
                            if element in elements:
                                element_files[element] = file_path
                                break
        
        # Sort by score
        results = []
        for element, score in sorted(element_scores.items(), key=lambda x: x[1], reverse=True):
            if len(results) >= limit:
                break
            file_path = element_files.get(element, "unknown")
            results.append((element, file_path))
        
        return results
    
    def find_functions_by_pattern(self, pattern: str) -> List[CodeElement]:
        """Find functions matching regex pattern"""
        results = []
        regex = re.compile(pattern, re.IGNORECASE)
        
        for file_path, elements in self.index.file_to_elements.items():
            for element in elements:
                if element.type in ['function', 'method']:
                    if regex.search(element.name) or \
                       (element.docstring and regex.search(element.docstring)):
                        results.append(element)
        
        return results
    
    def find_unused_functions(self) -> List[CodeElement]:
        """Find functions that are never called"""
        unused = []
        
        for file_path, elements in self.index.file_to_elements.items():
            for element in elements:
                if element.type in ['function', 'method']:
                    # Skip special functions
                    if element.name.startswith('_') or element.name in ['main', 'init']:
                        continue
                    
                    # Check if function is called
                    if element.name not in self.index.call_graph:
                        unused.append(element)
        
        return unused
    
    def find_entry_points(self) -> List[CodeElement]:
        """Find potential entry points"""
        entry_points = []
        
        for file_path, elements in self.index.file_to_elements.items():
            for element in elements:
                # Python entry points
                if element.name == 'main' or element.name == '__main__':
                    entry_points.append(element)
                
                # Go entry points
                if element.name == 'main' and 'go' in file_path:
                    entry_points.append(element)
                
                # Java entry points
                if element.name == 'main' and 'java' in file_path:
                    entry_points.append(element)
                
                # Express/Node.js entry points
                if element.name in ['app', 'server', 'listen'] and ('js' in file_path or 'ts' in file_path):
                    entry_points.append(element)
        
        return entry_points
    
    def find_security_hotspots(self) -> List[CodeElement]:
        """Find potential security issues"""
        security_patterns = [
            (r'eval\s*\(', 'Use of eval() function'),
            (r'exec\s*\(', 'Use of exec() function'),
            (r'shell_exec\s*\(', 'Use of shell_exec() function'),
            (r'system\s*\(', 'Use of system() function'),
            (r'subprocess\.call\s*\(', 'Use of subprocess.call()'),
            (r'os\.system\s*\(', 'Use of os.system()'),
            (r'pickle\.loads?\s*\(', 'Use of pickle (unsafe)'),
            (r'marshal\.loads?\s*\(', 'Use of marshal (unsafe)'),
            (r'input\s*\(', 'User input without validation'),
            (r'raw_input\s*\(', 'User input without validation'),
        ]
        
        results = []
        
        for file_path, elements in self.index.file_to_elements.items():
            for element in elements:
                for pattern, description in security_patterns:
                    if re.search(pattern, element.signature or '', re.IGNORECASE):
                        # Create a new element with security info
                        security_element = CodeElement(
                            name=element.name,
                            type=element.type,
                            line_start=element.line_start,
                            line_end=element.line_end,
                            docstring=f"SECURITY: {description}",
                            signature=element.signature,
                            decorators=element.decorators,
                            imports=element.imports,
                            calls=element.calls,
                            parent=element.parent
                        )
                        results.append(security_element)
        
        return results
    
    def find_todo_comments(self, root_path: Path) -> List[Tuple[str, int, str]]:
        """Find TODO, FIXME, and similar comments"""
        todo_patterns = [
            r'(TODO|FIXME|HACK|XXX|NOTE|BUG)\s*[:\-]?\s*(.*)',
            r'#\s*(TODO|FIXME|HACK|XXX)\s*[:\-]?\s*(.*)',
            r'//\s*(TODO|FIXME|HACK|XXX)\s*[:\-]?\s*(.*)',
            r'/\*\s*(TODO|FIXME|HACK|XXX)\s*[:\-]?\s*(.*)\*/',
        ]
        
        results = []
        
        for file_path in root_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    for pattern in todo_patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            todo_type = match.group(1)
                            todo_text = match.group(2) if len(match.groups()) > 1 else ""
                            results.append((str(file_path), line_num, f"{todo_type}: {todo_text}"))
            
            except (UnicodeDecodeError, PermissionError):
                continue
        
        return results
    
    def find_database_operations(self) -> List[CodeElement]:
        """Find database-related operations"""
        db_patterns = [
            r'\.save\s*\(',
            r'\.create\s*\(',
            r'\.update\s*\(',
            r'\.delete\s*\(',
            r'\.insert\s*\(',
            r'\.commit\s*\(',
            r'\.execute\s*\(',
            r'SELECT\s+',
            r'INSERT\s+',
            r'UPDATE\s+',
            r'DELETE\s+',
            r'CREATE\s+TABLE',
            r'DROP\s+TABLE',
        ]
        
        results = []
        
        for file_path, elements in self.index.file_to_elements.items():
            for element in elements:
                for pattern in db_patterns:
                    if re.search(pattern, element.signature or '', re.IGNORECASE):
                        results.append(element)
                        break
        
        return results
    
    def find_async_functions(self) -> List[CodeElement]:
        """Find async/await functions"""
        async_patterns = [
            r'async\s+def\s+',
            r'async\s+function\s+',
            r'await\s+',
            r'Promise\.',
            r'then\s*\(',
            r'catch\s*\(',
            r'go\s+func\s+',
            r'goroutine',
        ]
        
        results = []
        
        for file_path, elements in self.index.file_to_elements.items():
            for element in elements:
                if element.type in ['function', 'method', 'async_function']:
                    results.append(element)
                    continue
                
                # Check for async patterns in signature
                if element.signature:
                    for pattern in async_patterns:
                        if re.search(pattern, element.signature, re.IGNORECASE):
                            results.append(element)
                            break
        
        return results
    
    def calculate_metrics(self, root_path: Path) -> CodeMetrics:
        """Calculate code metrics"""
        if not self.index:
            self.build_index(root_path)
        
        total_files = len(self.index.file_to_elements)
        total_functions = sum(1 for elements in self.index.file_to_elements.values() 
                             for e in elements if e.type in ['function', 'method'])
        total_classes = sum(1 for elements in self.index.file_to_elements.values() 
                           for e in elements if e.type == 'class')
        
        # Count lines
        total_lines = 0
        language_distribution = defaultdict(int)
        
        for file_path in root_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                    total_lines += lines
                
                # Language distribution
                suffix = file_path.suffix.lower()
                if suffix in ['.py', '.pyi']:
                    language_distribution['Python'] += 1
                elif suffix in ['.js', '.jsx', '.ts', '.tsx', '.mjs']:
                    language_distribution['JavaScript'] += 1
                elif suffix == '.go':
                    language_distribution['Go'] += 1
                elif suffix == '.java':
                    language_distribution['Java'] += 1
                elif suffix in ['.c', '.cpp', '.cc', '.cxx']:
                    language_distribution['C/C++'] += 1
                else:
                    language_distribution['Other'] += 1
            
            except (UnicodeDecodeError, PermissionError):
                continue
        
        self.metrics = CodeMetrics(
            total_files=total_files,
            total_functions=total_functions,
            total_classes=total_classes,
            total_lines=total_lines,
            language_distribution=dict(language_distribution),
            complexity_metrics={}
        )
        
        return self.metrics
    
    def get_call_graph(self, function_name: str) -> Dict[str, Any]:
        """Get call graph for a specific function"""
        if not self.index:
            raise RuntimeError("Index not built. Call build_index() first.")
        
        # Functions called by this function
        called = self.index.function_calls.get(function_name, [])
        
        # Functions that call this function
        callers = list(self.index.call_graph.get(function_name, set()))
        
        return {
            'function': function_name,
            'calls': called,
            'called_by': callers,
            'call_depth': self._calculate_call_depth(function_name)
        }
    
    def _calculate_call_depth(self, function_name: str, visited: Set[str] = None) -> int:
        """Calculate maximum call depth for a function"""
        if visited is None:
            visited = set()
        
        if function_name in visited:
            return 0  # Prevent infinite recursion
        
        visited.add(function_name)
        called = self.index.function_calls.get(function_name, [])
        
        if not called:
            visited.remove(function_name)
            return 0
        
        max_depth = 0
        for called_func in called:
            depth = self._calculate_call_depth(called_func, visited.copy())
            max_depth = max(max_depth, depth + 1)
        
        visited.remove(function_name)
        return max_depth
