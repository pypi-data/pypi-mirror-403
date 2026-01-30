"""HTML Adapter for NLP3Tree

Navigates HTML DOM trees using natural language.
"""

from typing import Any, List, Optional
from pathlib import Path
import re
from bs4 import BeautifulSoup, Tag, NavigableString

from ..core import TreeAdapter, BaseTreeNode, NodeType, NodeMetadata


class HTMLTreeNode(BaseTreeNode):
    """HTML DOM tree node"""
    
    def __init__(self, tag: Tag, path: str, parent: Optional['HTMLTreeNode'] = None):
        self._tag = tag
        self._path = path
        
        # Determine node type
        node_type = NodeType.BRANCH if len(tag.contents) > 1 else NodeType.LEAF
        
        # Extract metadata
        metadata = NodeMetadata(
            size=len(str(tag)),
            extra={
                'tag': tag.name,
                'class': tag.get('class', []),
                'id': tag.get('id', ''),
                'attributes': dict(tag.attrs),
                'text': tag.get_text(strip=True)[:100] if tag.get_text(strip=True) else '',
                'children_count': len([c for c in tag.children if isinstance(c, Tag)])
            }
        )
        
        super().__init__(tag.name, path, node_type, metadata)
        self._parent = parent
        self._children: List[HTMLTreeNode] = []
    
    def value(self) -> Any:
        """Get node value"""
        if self._tag.get_text(strip=True):
            return self._tag.get_text(strip=True)
        return self._tag.attrs
    
    def add_child(self, child: 'HTMLTreeNode'):
        """Add child node"""
        child._parent = self
        self._children.append(child)


class HTMLAdapter(TreeAdapter):
    """Adapter for HTML documents"""
    
    def supports(self, source: Any) -> bool:
        """Check if adapter supports this source"""
        if isinstance(source, (str, Path)):
            path = Path(source)
            return path.exists() and path.suffix.lower() in ['.html', '.htm']
        elif isinstance(source, str) and '<' in source and '>' in source:
            # Check if it looks like HTML string
            return bool(re.search(r'<[^>]+>', source))
        return False
    
    async def build_tree(self, source: Any, **kwargs) -> HTMLTreeNode:
        """Build tree from HTML source"""
        if isinstance(source, (str, Path)):
            path = Path(source)
            with open(path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            root_path = str(path)
        else:
            html_content = str(source)
            root_path = "<html_string>"
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find root element (usually html or body)
        root_tag = soup.find('html') or soup.find('body') or soup
        if not root_tag:
            root_tag = soup
        
        # Build tree recursively
        root_node = HTMLTreeNode(root_tag, root_path)
        self._build_children(root_tag, root_node, root_path)
        
        return root_node
    
    def _build_children(self, parent_tag: Tag, parent_node: HTMLTreeNode, base_path: str):
        """Build child nodes recursively"""
        for i, child in enumerate(parent_tag.children):
            if isinstance(child, Tag):
                child_path = f"{parent_node.path}/{child.name}[{i}]"
                child_node = HTMLTreeNode(child, child_path, parent_node)
                parent_node.add_child(child_node)
                
                # Recursively build children
                if len(child.contents) > 1:
                    self._build_children(child, child_node, child_path)
