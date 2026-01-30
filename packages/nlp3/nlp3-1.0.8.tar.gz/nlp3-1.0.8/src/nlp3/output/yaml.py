"""YAML Output Renderer for NLP3

Generates YAML format output from tree structures.
"""

from typing import List, Optional, Any
from datetime import datetime
import yaml

from ..core import TreeNode


class YAMLRenderer:
    """Render tree structures as YAML"""
    
    @staticmethod
    def render_tree(nodes: List[TreeNode], title: str = "Tree Data") -> str:
        """Render tree structure as YAML"""
        data = {
            "metadata": {
                "title": title,
                "generated_at": datetime.now().isoformat(),
                "total_nodes": YAMLRenderer._count_all_nodes(nodes),
                "root_nodes": len(nodes)
            },
            "nodes": []
        }
        
        for node in nodes:
            node_data = YAMLRenderer._render_node_yaml(node)
            data["nodes"].append(node_data)
        
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    @staticmethod
    def _render_node_yaml(node: TreeNode, depth: int = 0, max_depth: int = 10) -> dict:
        """Render single node as YAML structure"""
        node_data = {
            "name": node.name,
            "type": node.node_type.value,
            "path": node.path
        }
        
        # Add metadata
        metadata = {}
        if node.metadata.size:
            size = node.metadata.size
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024**2:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size/1024**2:.1f}MB"
            metadata["size"] = size_str
        
        if node.metadata.modified:
            import datetime
            metadata["modified"] = datetime.datetime.fromtimestamp(node.metadata.modified).isoformat()
        
        if node.metadata.extra:
            # Filter important extra fields
            important_keys = ['tag', 'type', 'class', 'id', 'mime_type', 'attributes']
            for key in important_keys:
                if key in node.metadata.extra and node.metadata.extra[key]:
                    value = node.metadata.extra[key]
                    if isinstance(value, list) and value:
                        metadata[key] = value
                    elif isinstance(value, dict) and value:
                        metadata[key] = value
                    elif value:
                        metadata[key] = value
        
        if metadata:
            node_data["metadata"] = metadata
        
        # Add children with depth limiting
        if depth < max_depth:
            children = list(node.children())
            if children:
                node_data["children"] = []
                for child in children:
                    child_data = YAMLRenderer._render_node_yaml(child, depth + 1, max_depth)
                    node_data["children"].append(child_data)
        elif depth == max_depth:
            # Add placeholder for deeper levels
            children = list(node.children())
            if children:
                node_data["children"] = f"[{len(children)} children truncated at depth {max_depth}]"
        
        return node_data
    
    @staticmethod
    def _count_all_nodes(nodes: List[TreeNode], max_depth: int = 50, depth: int = 0) -> int:
        """Count all nodes recursively with depth limiting"""
        if depth >= max_depth:
            return 0  # Stop counting at max depth to prevent infinite recursion
        
        count = 0
        for node in nodes:
            count += 1
            children = list(node.children())
            if children and depth < max_depth:
                count += YAMLRenderer._count_all_nodes(children, max_depth, depth + 1)
        return count
