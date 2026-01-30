"""Tests for Code Analysis Components"""

import pytest
import tempfile
import shutil
from pathlib import Path

from nlp3.adapters.code_adapter import CodeAdapter, CodeElement
from nlp3.adapters.code_intelligence import CodeIntelligenceEngine
from nlp3.adapters.semantic_search import SemanticSearchEngine
from nlp3.adapters.code_use_cases import CodeAnalysisUseCases


class TestCodeAdapter:
    """Test CodeAdapter functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.code_adapter = CodeAdapter()
        
        # Create test files
        self.create_test_files()
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def create_test_files(self):
        """Create test code files"""
        # Python test file
        py_content = '''
import json
import requests
from typing import Dict

def parse_json(data: str) -> Dict:
    """Parse JSON string to dictionary"""
    return json.loads(data)

class Logger:
    """Simple logging class"""
    
    def __init__(self):
        self.logs = []
    
    def log(self, message: str):
        """Log a message"""
        self.logs.append(message)
        print(f"LOG: {message}")

def main():
    """Main entry point"""
    logger = Logger()
    logger.log("Application started")
    
    # TODO: Add error handling
    data = '{"key": "value"}'
    parsed = parse_json(data)
    logger.log(f"Parsed: {parsed}")

if __name__ == "__main__":
    main()
'''
        
        py_file = self.temp_dir / "test.py"
        py_file.write_text(py_content)
        
        # JavaScript test file
        js_content = '''
const express = require('express');
const axios = require('axios');

function parseJSON(data) {
    return JSON.parse(data);
}

class Logger {
    constructor() {
        this.logs = [];
    }
    
    log(message) {
        this.logs.push(message);
        console.log(`LOG: ${message}`);
    }
}

const app = express();

app.get('/users', async (req, res) => {
    try {
        // FIXME: Add authentication
        const response = await axios.get('https://api.example.com/users');
        res.json(response.data);
    } catch (error) {
        res.status(500).json({error: error.message});
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
'''
        
        js_file = self.temp_dir / "test.js"
        js_file.write_text(js_content)
    
    def test_python_parser(self):
        """Test Python code parsing"""
        py_file = self.temp_dir / "test.py"
        parser = self.code_adapter.get_parser(py_file)
        
        assert parser is not None
        assert parser.can_parse(py_file)
        
        elements = parser.parse_file(py_file)
        assert len(elements) > 0
        
        # Check for specific elements
        functions = [e for e in elements if e.type == "function"]
        assert len(functions) >= 2  # parse_json, main
        
        classes = [e for e in elements if e.type == "class"]
        assert len(classes) == 1  # Logger
        
        imports = [e for e in elements if e.type == "import"]
        assert len(imports) >= 2  # json, requests
    
    def test_javascript_parser(self):
        """Test JavaScript code parsing"""
        js_file = self.temp_dir / "test.js"
        parser = self.code_adapter.get_parser(js_file)
        
        assert parser is not None
        assert parser.can_parse(js_file)
        
        elements = parser.parse_file(js_file)
        assert len(elements) > 0
        
        # Check for specific elements
        functions = [e for e in elements if e.type in ["function", "arrow_function"]]
        assert len(functions) >= 2  # parseJSON, app.listen callback
    
        classes = [e for e in elements if e.type == "class"]
        assert len(classes) == 1  # Logger
    
    def test_analyze_directory(self):
        """Test directory analysis"""
        results = self.code_adapter.analyze_directory(self.temp_dir)
        
        assert len(results) == 2  # test.py and test.js
        assert str(self.temp_dir / "test.py") in results
        assert str(self.temp_dir / "test.js") in results
        
        # Check elements in Python file
        py_elements = results[str(self.temp_dir / "test.py")]
        assert len(py_elements) > 0
    
    def test_search_elements(self):
        """Test element search"""
        py_file = self.temp_dir / "test.py"
        elements = self.code_adapter.analyze_file(py_file)
        
        # Search for "parse"
        results = self.code_adapter.search_elements(elements, "parse")
        assert len(results) > 0
        
        # Search for "log"
        results = self.code_adapter.search_elements(elements, "log")
        assert len(results) > 0


class TestCodeIntelligenceEngine:
    """Test CodeIntelligenceEngine functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.engine = CodeIntelligenceEngine()
        
        # Create test files
        self.create_test_files()
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def create_test_files(self):
        """Create test code files"""
        # Create files with various patterns
        content1 = '''
import os
import json

def parse_data(data):
    return json.loads(data)

def unused_function():
    pass

def main():
    data = '{"test": "value"}'
    result = parse_data(data)
    print(result)
'''
        
        content2 = '''
import logging

class Logger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def log_info(self, message):
        self.logger.info(message)
    
    def log_error(self, message):
        self.logger.error(message)

def process_data():
    logger = Logger()
    logger.log_info("Processing started")
    # TODO: Add error handling
    logger.log_error("An error occurred")
'''
        
        (self.temp_dir / "file1.py").write_text(content1)
        (self.temp_dir / "file2.py").write_text(content2)
    
    def test_build_index(self):
        """Test index building"""
        index = self.engine.build_index(self.temp_dir)
        
        assert index is not None
        assert len(index.file_to_elements) == 2
        assert len(index.token_to_files) > 0
        assert len(index.token_to_elements) > 0
    
    def test_search(self):
        """Test code search"""
        self.engine.build_index(self.temp_dir)
        
        results = self.engine.search("parse")
        assert len(results) > 0
        
        results = self.engine.search("logger")
        assert len(results) > 0
    
    def test_find_unused_functions(self):
        """Test unused function detection"""
        self.engine.build_index(self.temp_dir)
        
        unused = self.engine.find_unused_functions()
        # Should find unused_function
        assert len(unused) >= 1
        assert any("unused_function" in elem.name for elem in unused)
    
    def test_find_todo_comments(self):
        """Test TODO comment detection"""
        todos = self.engine.find_todo_comments(self.temp_dir)
        assert len(todos) >= 1
        assert any("TODO" in todo[2] for todo in todos)
    
    def test_find_entry_points(self):
        """Test entry point detection"""
        self.engine.build_index(self.temp_dir)
        
        entry_points = self.engine.find_entry_points()
        # Should find main function
        assert len(entry_points) >= 1
        assert any(elem.name == "main" for elem in entry_points)


class TestCodeAnalysisUseCases:
    """Test 30 use cases implementation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create comprehensive test files
        self.create_test_files()
        self.use_cases = CodeAnalysisUseCases(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def create_test_files(self):
        """Create comprehensive test files"""
        # Python file with various patterns
        py_content = '''
import json
import pandas as pd
import logging
from typing import Dict, List
import asyncio
import multiprocessing

# TODO: Add error handling
# FIXME: This is inefficient

class Logger:
    """Logger class for application logging"""
    
    def __init__(self):
        self.logs = []
    
    def log(self, message: str):
        """Log a message"""
        self.logs.append(message)
        print(f"LOG: {message}")

async def parse_json_async(data: str) -> Dict:
    """Parse JSON asynchronously"""
    return json.loads(data)

def validate_input(data: Dict) -> bool:
    """Validate input data"""
    return isinstance(data, dict) and "key" in data

def process_data_with_retry(data: str, max_retries: int = 3):
    """Process data with retry logic"""
    for attempt in range(max_retries):
        try:
            return json.loads(data)
        except Exception:
            if attempt == max_retries - 1:
                raise

def database_operation():
    """Simulate database operation"""
    # INSERT operation
    pass

def generate_html_report():
    """Generate HTML report"""
    return "<html><body>Report</body></html>"

def create_chart():
    """Create a chart"""
    # matplotlib code would go here
    pass

def serialize_data(data):
    """Serialize data to JSON"""
    return json.dumps(data)

def main():
    """Main entry point"""
    logger = Logger()
    logger.log("Starting application")
    
    # Feature flag check
    if FEATURE_ENABLED:
        logger.log("Feature is enabled")

if __name__ == "__main__":
    main()
'''
        
        (self.temp_dir / "app.py").write_text(py_content)
        
        # Test file
        test_content = '''
import pytest
from app import parse_json_async, validate_input

def test_parse_json():
    """Test JSON parsing"""
    data = '{"key": "value"}'
    result = parse_json_async(data)
    assert result["key"] == "value"

def test_validate_input():
    """Test input validation"""
    data = {"key": "value"}
    assert validate_input(data) is True
'''
        
        (self.temp_dir / "test_app.py").write_text(test_content)
        
        # Config file
        config_content = '''
{
    "database": {
        "url": "sqlite:///app.db"
    },
    "feature_flags": {
        "new_feature": true
    }
}
'''
        
        (self.temp_dir / "config.json").write_text(config_content)
    
    def test_find_functions_by_name(self):
        """Test use case 1: Find functions by name"""
        results = self.use_cases.find_functions_by_name()
        assert len(results) > 0
    
    def test_find_logging_classes(self):
        """Test use case 2: Find logging classes"""
        results = self.use_cases.find_logging_classes()
        assert len(results) > 0
        assert any("log" in elem.name.lower() for elem in results)
    
    def test_find_todo_comments(self):
        """Test use case 7: Find TODO comments"""
        results = self.use_cases.find_todo_comments()
        assert len(results) >= 2  # TODO and FIXME
    
    def test_find_async_code(self):
        """Test use case 28: Find async code"""
        results = self.use_cases.find_async_code()
        assert len(results) > 0
        assert any("async" in elem.name.lower() or 
                  (elem.signature and "async" in elem.signature.lower()) 
                  for elem in results)
    
    def test_find_heavy_imports(self):
        """Test use case 15: Find heavy imports"""
        results = self.use_cases.find_heavy_imports()
        assert len(results) > 0
        # Should find pandas import
    
    def test_find_json_serialization(self):
        """Test use case 24: Find JSON serialization"""
        results = self.use_cases.find_json_serialization()
        assert len(results) > 0
        assert any("json" in elem.name.lower() or 
                  (elem.signature and "json" in elem.signature.lower()) 
                  for elem in results)


if __name__ == "__main__":
    pytest.main([__file__])
