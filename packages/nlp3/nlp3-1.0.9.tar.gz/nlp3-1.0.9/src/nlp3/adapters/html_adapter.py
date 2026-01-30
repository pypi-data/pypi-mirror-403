"""
HTML Adapter for NLP2Tree
Parses HTML files into DOM tree structure using BeautifulSoup
"""

from bs4 import BeautifulSoup, Tag
from pathlib import Path
from typing import Optional, List, Iterator
import logging

from ..core import TreeAdapter, NodeType, BaseTreeNode, NodeMetadata

logger = logging.getLogger(__name__)


class HtmlElementNode(BaseTreeNode):
    """TreeNode representing HTML DOM element"""
    
    def __init__(self, tag: Tag, parent_path: str = ""):
        # Create metadata with HTML attributes
        metadata = NodeMetadata()
        metadata.attributes = dict(tag.attrs) if tag.attrs else {}
        
        # Extract common attributes for easier access
        if 'id' in tag.attrs:
            metadata.attributes['id'] = tag.attrs['id']
        if 'class' in tag.attrs:
            metadata.attributes['class'] = tag.attrs['class']
        
        # Determine node type based on content
        has_children = any(isinstance(child, Tag) for child in tag.contents)
        node_type = NodeType.BRANCH if has_children else NodeType.LEAF
        
        # Create unique path for this element
        element_path = f"{parent_path}/{tag.name}"
        if 'id' in tag.attrs:
            element_path += f"#{tag.attrs['id']}"
        elif 'class' in tag.attrs:
            classes = tag.attrs['class']
            if isinstance(classes, list):
                element_path += f".{'.'.join(classes[:2])}"  # First 2 classes
            else:
                element_path += f".{classes}"
        
        super().__init__(
            name=tag.name,
            path=element_path,
            node_type=node_type,
            metadata=metadata
        )
        
        self._tag = tag
        self._children_loaded = False
        self._parent_path = parent_path
    
    def children(self) -> Iterator['HtmlElementNode']:
        """Get child elements with lazy loading"""
        if not self._children_loaded:
            self._load_children()
        return super().children()
    
    def _load_children(self):
        """Load child elements from DOM"""
        if self._children_loaded:
            return
        
        try:
            for child in self._tag.children:
                if isinstance(child, Tag):
                    child_node = HtmlElementNode(child, self.path)
                    self.add_child(child_node)
        except Exception as e:
            logger.warning(f"Error loading children for {self.name}: {e}")
        
        self._children_loaded = True
    
    def value(self) -> Optional[str]:
        """Get text content of this element"""
        try:
            return self._tag.get_text(strip=True)
        except Exception:
            return None
    
    def inner_html(self) -> Optional[str]:
        """Get inner HTML of this element"""
        try:
            return str(self._tag)
        except Exception:
            return None
    
    def outer_html(self) -> Optional[str]:
        """Get outer HTML (same as inner_html for BeautifulSoup)"""
        return self.inner_html()
    
    def get_attribute(self, name: str) -> Optional[str]:
        """Get specific attribute value"""
        return self._tag.get(name)
    
    def has_class(self, class_name: str) -> bool:
        """Check if element has specific class"""
        classes = self._tag.get('class', [])
        if isinstance(classes, list):
            return class_name in classes
        return class_name in str(classes).split()
    
    def get_css_selector(self) -> str:
        """Generate CSS selector for this element"""
        selector = self.name
        
        # Add ID if present
        element_id = self._tag.get('id')
        if element_id:
            selector += f"#{element_id}"
        
        # Add first class if present
        classes = self._tag.get('class', [])
        if classes:
            if isinstance(classes, list):
                selector += f".{classes[0]}"
            else:
                selector += f".{classes}"
        
        return selector


class HtmlAdapter(TreeAdapter):
    """Adapter for HTML file navigation and DOM parsing"""
    
    def supports(self, source) -> bool:
        """Check if source is supported (HTML file)"""
        if isinstance(source, (str, Path)):
            path = Path(source)
            return path.suffix.lower() in ['.html', '.htm']
        return False
    
    async def build_tree(self, source, **kwargs) -> HtmlElementNode:
        """Build DOM tree from HTML file"""
        path = Path(source)
        
        if not path.exists():
            raise FileNotFoundError(f"HTML file not found: {path}")
        
        try:
            # Read HTML content
            html_content = path.read_text(encoding='utf-8', errors='ignore')
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Use html tag as root, or fallback to soup itself
            root_tag = soup.find('html') or soup
            root_node = HtmlElementNode(root_tag)
            
            logger.info(f"Built HTML tree from {path} with {len(list(root_node.children()))} top-level elements")
            return root_node
            
        except Exception as e:
            logger.error(f"Error parsing HTML file {path}: {e}")
            raise
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return ['.html', '.htm']
    
    def get_description(self) -> str:
        """Get adapter description"""
        return "HTML DOM parser using BeautifulSoup for web page structure navigation"
