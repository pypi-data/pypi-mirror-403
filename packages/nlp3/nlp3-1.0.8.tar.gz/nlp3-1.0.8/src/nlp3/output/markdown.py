"""Markdown Output Renderer for NLP3

Generates Markdown format output from tree structures.
"""

from typing import List, Optional
from datetime import datetime

from ..core import TreeNode


class MarkdownRenderer:
    """Render tree structures as Markdown"""
    
    @staticmethod
    def render_tree(nodes: List[TreeNode], title: str = "Tree Data") -> str:
        """Render tree structure as Markdown"""
        md = []
        
        # Header
        md.append(f"# {title}")
        md.append("")
        md.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        md.append("")
        
        # Summary
        total_nodes = MarkdownRenderer._count_all_nodes(nodes)
        md.append(f"## Summary")
        md.append("")
        md.append(f"- **Total Nodes:** {total_nodes}")
        md.append(f"- **Root Nodes:** {len(nodes)}")
        md.append("")
        
        # Table of contents
        md.append("## Table of Contents")
        md.append("")
        for i, node in enumerate(nodes, 1):
            md.append(f"{i}. [{node.name}](#{node.name.lower().replace(' ', '-').replace('.', '').replace('/', '-')})")
        md.append("")
        
        # Tree structure
        md.append("## Tree Structure")
        md.append("")
        for node in nodes:
            MarkdownRenderer._render_node_markdown(node, md, 0)
        
        # Detailed table
        md.append("## Detailed Information")
        md.append("")
        md.append("| Name | Type | Size | Modified | Path |")
        md.append("|------|------|------|----------|------|")
        
        all_nodes = []
        for node in nodes:
            MarkdownRenderer._collect_nodes(node, all_nodes)
        
        for node in all_nodes:
            name = node.name
            node_type = node.node_type.value
            size_str = ""
            modified_str = ""
            path = node.path
            
            # Size
            if node.metadata.size:
                size = node.metadata.size
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024**2:
                    size_str = f"{size/1024:.1f}KB"
                else:
                    size_str = f"{size/1024**2:.1f}MB"
            
            # Modified
            if node.metadata.modified:
                modified_str = datetime.fromtimestamp(node.metadata.modified).strftime("%Y-%m-%d %H:%M")
            
            # Escape pipe characters in name
            name = name.replace("|", "\\|")
            path = path.replace("|", "\\|")
            
            md.append(f"| {name} | {node_type} | {size_str} | {modified_str} | {path} |")
        
        return "\n".join(md)
    
    @staticmethod
    def _render_node_markdown(node: TreeNode, md: List[str], depth: int):
        """Render single node as Markdown"""
        indent = "  " * depth
        bullet = "-" if depth > 0 else ""
        
        # Node header
        node_info = f"{node.name} ({node.node_type.value})"
        
        # Size
        if node.metadata.size:
            size = node.metadata.size
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024**2:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size/1024**2:.1f}MB"
            node_info += f" - *{size_str}*"
        
        md.append(f"{indent}{bullet} **{node_info}**")
        
        # Extra metadata
        if node.metadata.extra:
            extra_lines = []
            for key, value in node.metadata.extra.items():
                if key in ['tag', 'type', 'class', 'id', 'mime_type'] and value:
                    if isinstance(value, list):
                        value = ', '.join(str(v) for v in value)
                    extra_lines.append(f"{indent}  - *{key}*: {value}")
            
            for line in extra_lines:
                md.append(line)
        
        md.append("")
        
        # Children
        children = list(node.children())
        if children:
            for child in children:
                MarkdownRenderer._render_node_markdown(child, md, depth + 1)
    
    @staticmethod
    def _collect_nodes(node: TreeNode, nodes_list: List[TreeNode]):
        """Collect all nodes recursively"""
        nodes_list.append(node)
        for child in node.children():
            MarkdownRenderer._collect_nodes(child, nodes_list)
    
    @staticmethod
    def _count_all_nodes(nodes: List[TreeNode]) -> int:
        """Count all nodes recursively"""
        count = 0
        for node in nodes:
            count += 1
            children = list(node.children())
            if children:
                count += MarkdownRenderer._count_all_nodes(children)
        return count
