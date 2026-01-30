"""CSV Output Renderer for NLP3

Generates CSV format output from tree structures.
"""

from typing import List, Optional
from datetime import datetime
import csv
from io import StringIO

from ..core import TreeNode


class CSVRenderer:
    """Render tree structures as CSV"""
    
    @staticmethod
    def render_tree(nodes: List[TreeNode], title: str = "Tree Data") -> str:
        """Render tree structure as CSV"""
        output = StringIO()
        
        # CSV headers
        headers = [
            "name", "type", "path", "size", "modified", 
            "tag", "class", "id", "mime_type", "attributes", "extra_info"
        ]
        
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        
        # Flatten tree and write all nodes
        all_nodes = []
        for node in nodes:
            CSVRenderer._collect_nodes(node, all_nodes)
        
        for node in all_nodes:
            row = CSVRenderer._render_node_csv(node)
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def _collect_nodes(node: TreeNode, nodes_list: List[TreeNode]):
        """Collect all nodes recursively"""
        nodes_list.append(node)
        for child in node.children():
            CSVRenderer._collect_nodes(child, nodes_list)
    
    @staticmethod
    def _render_node_csv(node: TreeNode) -> dict:
        """Render single node as CSV row"""
        row = {
            "name": node.name,
            "type": node.node_type.value,
            "path": node.path,
            "size": "",
            "modified": "",
            "tag": "",
            "class": "",
            "id": "",
            "mime_type": "",
            "attributes": "",
            "extra_info": ""
        }
        
        # Size
        if node.metadata and node.metadata.size:
            size = node.metadata.size
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024**2:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size/1024**2:.1f}MB"
            row["size"] = size_str
        
        # Modified
        if node.metadata.modified:
            import datetime
            row["modified"] = datetime.datetime.fromtimestamp(node.metadata.modified).isoformat()
        
        # Extra metadata
        if node.metadata.extra:
            extra = node.metadata.extra
            
            # HTML specific fields
            if "tag" in extra:
                row["tag"] = extra["tag"]
            
            if "class" in extra:
                classes = extra["class"]
                if isinstance(classes, list):
                    row["class"] = ", ".join(str(c) for c in classes)
                else:
                    row["class"] = str(classes)
            
            if "id" in extra:
                row["id"] = extra["id"]
            
            if "mime_type" in extra:
                row["mime_type"] = extra["mime_type"]
            
            if "attributes" in extra and extra["attributes"]:
                attrs = extra["attributes"]
                if isinstance(attrs, dict):
                    attr_str = "; ".join(f"{k}={v}" for k, v in attrs.items())
                    row["attributes"] = attr_str
            
            # Other extra info
            other_info = []
            for key, value in extra.items():
                if key not in ["tag", "class", "id", "mime_type", "attributes"]:
                    if isinstance(value, (list, dict)):
                        value_str = str(value)
                    else:
                        value_str = str(value)
                    other_info.append(f"{key}={value_str}")
            
            if other_info:
                row["extra_info"] = "; ".join(other_info)
        
        return row
