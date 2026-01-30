"""Tests for NLP2Tree core components"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import os

from src.nlp3.core import TreeNavigator, NodeType, NodeMetadata
from src.nlp3.adapters import FilesystemAdapter, JsonAdapter
from src.nlp3.nlp import NLPEngine, IntentType, PredicateType


@pytest.fixture
def temp_dir():
    """Create temporary directory with test files"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create test files
        (tmp_path / "test.py").write_text("print('hello')")
        (tmp_path / "data.json").write_text('{"key": "value"}')
        (tmp_path / "readme.md").write_text("# Test")
        
        # Create subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested content")
        
        yield tmp_path


class TestNLPEngine:
    """Test NLP engine functionality"""
    
    def test_parse_find_intent(self):
        """Test parsing find intent"""
        nlp = NLPEngine()
        
        queries = [
            "znajdź pliki .py",
            "find files larger than 100MB",
            "pokaż wszystkie pliki",
            "wyszukaj dokumenty",
        ]
        
        for query in queries:
            parsed = nlp.parse_query(query)
            assert parsed.intent.type == IntentType.FIND
            assert parsed.intent.confidence > 0.5
            assert parsed.original == query
    
    def test_parse_size_predicate(self):
        """Test parsing size predicates"""
        nlp = NLPEngine()
        
        queries = [
            "znajdź pliki większe niż 100MB",
            "find files smaller than 1GB",
            "pokaż pliki o rozmiarze 50KB",
        ]
        
        for query in queries:
            parsed = nlp.parse_query(query)
            size_predicates = [p for p in parsed.intent.predicates if p.type == PredicateType.SIZE]
            assert len(size_predicates) >= 1
            assert size_predicates[0].operator in [">", "<", "="]
            assert isinstance(size_predicates[0].value, (int, float))
    
    def test_parse_name_predicate(self):
        """Test parsing name predicates"""
        nlp = NLPEngine()
        
        queries = [
            "znajdź pliki nazwane 'test'",
            "find files called 'example'",
            "pokaż pliki o nazwie main",
        ]
        
        for query in queries:
            parsed = nlp.parse_query(query)
            name_predicates = [p for p in parsed.intent.predicates if p.type == PredicateType.NAME]
            assert len(name_predicates) >= 1
            assert name_predicates[0].operator == "="
    
    def test_parse_extension_predicate(self):
        """Test parsing extension predicates"""
        nlp = NLPEngine()
        
        queries = [
            "znajdź pliki .py",
            "find .txt files",
            "pokaż pliki json",
        ]
        
        for query in queries:
            parsed = nlp.parse_query(query)
            ext_predicates = [p for p in parsed.intent.predicates if p.type == PredicateType.EXTENSION]
            assert len(ext_predicates) >= 1
            assert ext_predicates[0].value.startswith('.')


class TestFilesystemAdapter:
    """Test filesystem adapter"""
    
    def test_adapter_supports_path(self, temp_dir):
        """Test adapter supports filesystem paths"""
        adapter = FilesystemAdapter()
        
        assert adapter.supports(temp_dir) is True
        assert adapter.supports(temp_dir / "test.py") is True
        assert adapter.supports("/nonexistent/path") is False
        assert adapter.supports({"not": "a path"}) is False
    
    @pytest.mark.asyncio
    async def test_build_tree_from_directory(self, temp_dir):
        """Test building tree from directory"""
        adapter = FilesystemAdapter()
        
        tree = await adapter.build_tree(temp_dir)
        
        assert tree.name == temp_dir.name
        assert tree.node_type == NodeType.BRANCH
        assert tree.metadata.size is not None
        
        # Check children
        children = list(tree.children())
        child_names = [child.name for child in children]
        assert "test.py" in child_names
        assert "data.json" in child_names
        assert "readme.md" in child_names
        assert "subdir" in child_names
    
    @pytest.mark.asyncio
    async def test_build_tree_from_file(self, temp_dir):
        """Test building tree from file"""
        adapter = FilesystemAdapter()
        file_path = temp_dir / "test.py"
        
        tree = await adapter.build_tree(file_path)
        
        assert tree.name == "test.py"
        assert tree.node_type == NodeType.LEAF
        assert tree.metadata.size == len("print('hello')")
        assert tree.metadata.mime_type == "text/x-python"
        assert tree.value() == "print('hello')"


class TestJsonAdapter:
    """Test JSON adapter"""
    
    def test_adapter_supports_json_data(self):
        """Test adapter supports JSON data"""
        adapter = JsonAdapter()
        
        # Test dict
        assert adapter.supports({"key": "value"}) is True
        
        # Test list
        assert adapter.supports([1, 2, 3]) is True
        
        # Test JSON string
        assert adapter.supports('{"key": "value"}') is True
        
        # Test non-JSON
        assert adapter.supports("not json") is False
        assert adapter.supports(123) is False
    
    @pytest.mark.asyncio
    async def test_build_tree_from_dict(self):
        """Test building tree from dictionary"""
        adapter = JsonAdapter()
        data = {
            "users": [
                {"name": "Jan", "city": "Warszawa"},
                {"name": "Anna", "city": "Kraków"}
            ],
            "count": 2
        }
        
        tree = await adapter.build_tree(data)
        
        assert tree.name == "root"
        assert tree.node_type == NodeType.BRANCH
        
        # Check children
        children = list(tree.children())
        child_names = [child.name for child in children]
        assert "users" in child_names
        assert "count" in child_names
    
    @pytest.mark.asyncio
    async def test_build_tree_from_list(self):
        """Test building tree from list"""
        adapter = JsonAdapter()
        data = ["item1", "item2", {"nested": "value"}]
        
        tree = await adapter.build_tree(data)
        
        assert tree.name == "root"
        assert tree.node_type == NodeType.BRANCH
        
        # Check children
        children = list(tree.children())
        assert len(children) == 3
        assert children[0].name == "0"
        assert children[1].name == "1"
        assert children[2].name == "2"


class TestTreeNavigator:
    """Test tree navigator"""
    
    @pytest.fixture
    def navigator(self):
        """Create navigator with adapters"""
        nav = TreeNavigator()
        nav.register_adapter(FilesystemAdapter())
        nav.register_adapter(JsonAdapter())
        return nav
    
    @pytest.mark.asyncio
    async def test_query_filesystem(self, navigator, temp_dir):
        """Test querying filesystem"""
        results = await navigator.query("znajdź pliki", temp_dir)
        
        assert len(results) >= 1
        assert results[0].name == temp_dir.name
    
    @pytest.mark.asyncio
    async def test_query_json(self, navigator):
        """Test querying JSON data"""
        data = {"users": [{"name": "Jan"}, {"name": "Anna"}]}
        
        results = await navigator.query("pokaż użytkowników", data)
        
        assert len(results) >= 1
        assert results[0].name == "root"


if __name__ == "__main__":
    pytest.main([__file__])
