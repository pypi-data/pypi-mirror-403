"""XML Output Renderer for NLP3

Generates XML format output from tree structures.
"""

from typing import List, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

from ..core import TreeNode


class XMLRenderer:
    """Render tree structures as XML"""
    
    @staticmethod
    def render_tree(nodes: List[TreeNode], title: str = "TreeData") -> str:
        """Render tree structure as XML"""
        # Create root element
        root = ET.Element("nlp3tree")
        root.set("title", title)
        root.set("generated_at", datetime.now().isoformat())
        root.set("total_nodes", str(XMLRenderer._count_all_nodes(nodes)))
        root.set("root_nodes", str(len(nodes)))
        
        # Add metadata
        metadata = ET.SubElement(root, "metadata")
        ET.SubElement(metadata, "title").text = title
        ET.SubElement(metadata, "generated_at").text = datetime.now().isoformat()
        ET.SubElement(metadata, "total_nodes").text = str(XMLRenderer._count_all_nodes(nodes))
        ET.SubElement(metadata, "root_nodes").text = str(len(nodes))
        
        # Add nodes
        nodes_elem = ET.SubElement(root, "nodes")
        for node in nodes:
            node_elem = XMLRenderer._render_node_xml(node)
            nodes_elem.append(node_elem)
        
        # Pretty print XML
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    @staticmethod
    def _render_node_xml(node: TreeNode) -> ET.Element:
        """Render single node as XML element"""
        # Create node element
        node_elem = ET.Element("node")
        node_elem.set("name", node.name)
        node_elem.set("type", node.node_type.value)
        node_elem.set("path", node.path)
        
        # Add metadata
        metadata_elem = ET.SubElement(node_elem, "metadata")
        
        # Size
        if node.metadata.size:
            size = node.metadata.size
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024**2:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size/1024**2:.1f}MB"
            ET.SubElement(metadata_elem, "size").text = size_str
        
        # Modified
        if node.metadata.modified:
            import datetime
            modified_str = datetime.datetime.fromtimestamp(node.metadata.modified).isoformat()
            ET.SubElement(metadata_elem, "modified").text = modified_str
        
        # Extra metadata
        if node.metadata.extra:
            extra_elem = ET.SubElement(metadata_elem, "extra")
            for key, value in node.metadata.extra.items():
                if value is not None:
                    elem = ET.SubElement(extra_elem, key)
                    if isinstance(value, (list, dict)):
                        elem.text = str(value)
                    else:
                        elem.text = str(value)
        
        # Add children
        children = list(node.children())
        if children:
            children_elem = ET.SubElement(node_elem, "children")
            for child in children:
                child_elem = XMLRenderer._render_node_xml(child)
                children_elem.append(child_elem)
        
        return node_elem
    
    @staticmethod
    def _count_all_nodes(nodes: List[TreeNode]) -> int:
        """Count all nodes recursively"""
        count = 0
        for node in nodes:
            count += 1
            children = list(node.children())
            if children:
                count += XMLRenderer._count_all_nodes(children)
        return count
