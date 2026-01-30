"""REST API Adapter for NLP3Tree

Navigates HTTP API responses as tree structures.
"""

import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import aiohttp
from datetime import datetime

from ...core import TreeAdapter, BaseTreeNode, NodeType, NodeMetadata


class RESTTreeNode(BaseTreeNode):
    """REST API response tree node"""
    
    def __init__(self, name: str, path: str, value: Any = None, 
                 node_type: NodeType = NodeType.LEAF, parent: Optional['RESTTreeNode'] = None):
        metadata = self._create_metadata(value)
        super().__init__(name, path, node_type, metadata)
        self._value = value
        self._parent = parent
        self._children: List[RESTTreeNode] = []
    
    def _create_metadata(self, value: Any) -> NodeMetadata:
        """Create metadata from API response value"""
        metadata = NodeMetadata()
        
        if isinstance(value, dict):
            metadata.size = len(str(value))
            metadata.extra = {
                'keys': list(value.keys())[:10],  # First 10 keys
                'type': 'object',
                'keys_count': len(value)
            }
        elif isinstance(value, list):
            metadata.size = len(str(value))
            metadata.extra = {
                'type': 'array',
                'length': len(value),
                'first_item_type': type(value[0]).__name__ if value else None
            }
        elif isinstance(value, (str, int, float, bool)):
            metadata.size = len(str(value))
            metadata.extra = {
                'type': type(value).__name__,
                'value': str(value)[:100] if isinstance(value, str) else value
            }
        else:
            metadata.size = len(str(value))
            metadata.extra = {
                'type': type(value).__name__
            }
        
        return metadata
    
    def value(self) -> Any:
        """Get node value"""
        return self._value
    
    def add_child(self, child: 'RESTTreeNode'):
        """Add child node"""
        child._parent = self
        self._children.append(child)


class RESTAdapter(TreeAdapter):
    """Adapter for REST API responses"""
    
    def __init__(self, timeout: int = 30, headers: Optional[Dict[str, str]] = None):
        self.timeout = timeout
        self.headers = headers or {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    def supports(self, source: Any) -> bool:
        """Check if adapter supports this source"""
        if isinstance(source, str):
            # Check if it's a URL
            parsed = urlparse(source)
            return parsed.scheme in ['http', 'https']
        elif isinstance(source, dict):
            # Check if it looks like an API response
            return any(key in source for key in ['data', 'results', 'items', 'response'])
        return False
    
    async def build_tree(self, source: Any, **kwargs) -> RESTTreeNode:
        """Build tree from REST API source"""
        if isinstance(source, str):
            # It's a URL - fetch the data
            response_data = await self._fetch_api(source, **kwargs)
            root_name = f"API: {source}"
        else:
            # It's already data
            response_data = source
            root_name = "API Response"
        
        # Create root node with response structure
        root_node = RESTTreeNode(root_name, "/", response_data, NodeType.BRANCH)
        
        # Build tree from response data
        self._build_data_tree(response_data, root_node, root_name)
        
        return root_node
    
    async def _fetch_api(self, url: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Fetch data from REST API"""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        
        # Filter out NLP3Tree specific kwargs
        api_kwargs = {k: v for k, v in kwargs.items() if k not in ['preload']}
        
        async with self.session.request(
            method=method,
            url=url,
            headers=self.headers,
            **api_kwargs
        ) as response:
            response.raise_for_status()
            
            # Try to parse as JSON
            try:
                data = await response.json()
            except:
                # If not JSON, get text
                text = await response.text()
                data = {"response": text}
            
            # Add response metadata
            return {
                "status": response.status,
                "headers": dict(response.headers),
                "url": str(response.url),
                "data": data
            }
    
    def _build_data_tree(self, data: Any, parent_node: RESTTreeNode, parent_path: str):
        """Build tree from API response data"""
        if isinstance(data, dict):
            for key, value in data.items():
                child_path = f"{parent_path}/{key}"
                child_type = NodeType.BRANCH if isinstance(value, (dict, list)) and value else NodeType.LEAF
                child_node = RESTTreeNode(key, child_path, value, child_type, parent_node)
                parent_node.add_child(child_node)
                
                # Recursively build children
                if isinstance(value, (dict, list)) and value:
                    self._build_data_tree(value, child_node, child_path)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                item_name = f"[{i}]"
                child_path = f"{parent_path}/{item_name}"
                child_type = NodeType.BRANCH if isinstance(item, (dict, list)) and item else NodeType.LEAF
                child_node = RESTTreeNode(item_name, child_path, item, child_type, parent_node)
                parent_node.add_child(child_node)
                
                # Recursively build children
                if isinstance(item, (dict, list)) and item:
                    self._build_data_tree(item, child_node, child_path)
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
