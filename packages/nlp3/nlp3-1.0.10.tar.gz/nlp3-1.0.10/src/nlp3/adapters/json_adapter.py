"""JSON/YAML Adapter for NLP2Tree"""

import json
import yaml
from typing import Any, Iterator, Union
from pathlib import Path

from ..core import TreeAdapter, TreeNode, NodeType, BaseTreeNode, NodeMetadata


class JsonNode(BaseTreeNode):
    """JSON/YAML tree node implementation"""
    
    def __init__(self, key: str, value: Any, parent_path: str = ""):
        self._value = value
        self._parent_path = parent_path
        
        # Determine node type
        if isinstance(value, (dict, list)):
            node_type = NodeType.BRANCH
        else:
            node_type = NodeType.LEAF
        
        # Create path
        path = f"{parent_path}.{key}" if parent_path else key
        
        # Create metadata
        metadata = NodeMetadata()
        if isinstance(value, str):
            metadata.size = len(value.encode('utf-8'))
            metadata.mime_type = 'text/plain'
        elif isinstance(value, (int, float)):
            metadata.size = 8  # Rough estimate
            metadata.mime_type = 'application/number'
        elif isinstance(value, bool):
            metadata.size = 1
            metadata.mime_type = 'application/boolean'
        elif isinstance(value, dict):
            metadata.size = len(str(value))
            metadata.mime_type = 'application/json'
        elif isinstance(value, list):
            metadata.size = len(value)
            metadata.mime_type = 'application/json-array'
        else:
            metadata.size = 0  # Fallback for None or other types
            metadata.mime_type = 'application/unknown'
        
        super().__init__(
            name=str(key),
            path=path,
            node_type=node_type,
            metadata=metadata
        )
        
        # Pre-load children for objects and arrays
        if node_type == NodeType.BRANCH:
            self._load_children()
    
    def _load_children(self):
        """Load children from JSON structure"""
        if isinstance(self._value, dict):
            for key, value in sorted(self._value.items()):
                child_node = JsonNode(key, value, self._path)
                self.add_child(child_node)
        elif isinstance(self._value, list):
            for index, value in enumerate(self._value):
                child_node = JsonNode(str(index), value, self._path)
                self.add_child(child_node)
    
    def value(self) -> Any:
        """Get value for leaf nodes"""
        return self._value if self._node_type == NodeType.LEAF else None


class JsonAdapter(TreeAdapter):
    """Adapter for JSON/YAML data structures"""
    
    def supports(self, source: Any) -> bool:
        """Check if source is JSON/YAML data"""
        # Check for dict/list
        if isinstance(source, (dict, list)):
            return True
        
        # Check for file paths
        if isinstance(source, (str, Path)):
            path = Path(source) if isinstance(source, str) else source
            if path.exists() and path.is_file():
                ext = path.suffix.lower()
                return ext in ['.json', '.yaml', '.yml']
        
        # Check for JSON strings
        if isinstance(source, str):
            try:
                json.loads(source)
                return True
            except (json.JSONDecodeError, TypeError):
                pass
        
        return False
    
    async def build_tree(self, source: Any, **kwargs) -> TreeNode:
        """Build tree from JSON/YAML source"""
        data = await self._parse_source(source)
        
        # Create root node
        root_key = kwargs.get('root_key', 'root')
        return JsonNode(root_key, data)
    
    async def _parse_source(self, source: Any) -> Any:
        """Parse source into Python data structure"""
        # Handle dict/list directly
        if isinstance(source, (dict, list)):
            return source
        
        # Handle file paths
        if isinstance(source, (str, Path)):
            path = Path(source) if isinstance(source, str) else source
            
            if not path.exists():
                raise FileNotFoundError(f"File does not exist: {path}")
            
            content = path.read_text(encoding='utf-8')
            
            if path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(content)
            else:  # JSON
                return json.loads(content)
        
        # Handle JSON strings
        if isinstance(source, str):
            return json.loads(source)
        
        raise ValueError(f"Unsupported source type: {type(source)}")


class YamlAdapter(JsonAdapter):
    """Specialized YAML adapter"""
    
    def supports(self, source: Any) -> bool:
        """Check if source is YAML data"""
        if isinstance(source, (str, Path)):
            path = Path(source) if isinstance(source, str) else source
            if path.exists() and path.is_file():
                ext = path.suffix.lower()
                return ext in ['.yaml', '.yml']
        
        # Try to parse as YAML
        if isinstance(source, str):
            try:
                yaml.safe_load(source)
                return True
            except yaml.YAMLError:
                pass
        
        return False
    
    async def _parse_source(self, source: Any) -> Any:
        """Parse YAML source"""
        # Handle file paths
        if isinstance(source, (str, Path)):
            path = Path(source) if isinstance(source, str) else source
            
            if not path.exists():
                raise FileNotFoundError(f"File does not exist: {path}")
            
            content = path.read_text(encoding='utf-8')
            return yaml.safe_load(content)
        
        # Handle YAML strings
        if isinstance(source, str):
            return yaml.safe_load(source)
        
        raise ValueError(f"Unsupported source type: {type(source)}")
