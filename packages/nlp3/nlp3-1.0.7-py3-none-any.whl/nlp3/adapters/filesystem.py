"""Filesystem Adapter for NLP2Tree"""

import os
import asyncio
from pathlib import Path as PathlibPath  # Explicit import
from typing import Any, Iterator, Optional
from datetime import datetime
import stat

from ..core import TreeAdapter, TreeNode, NodeType, BaseTreeNode, NodeMetadata


class FilesystemNode(BaseTreeNode):
    """Filesystem tree node implementation"""
    
    def __init__(self, path):
        # Ensure we always have a Path object - use explicit PathlibPath
        if isinstance(path, str):
            self._path = PathlibPath(path)
        elif isinstance(path, PathlibPath):
            self._path = path
        else:
            self._path = PathlibPath(str(path))
        self._stat = self._path.stat() if self._path.exists() else None
        
        # Determine node type
        node_type = NodeType.BRANCH if self._path.is_dir() else NodeType.LEAF
        
        # Create metadata
        metadata = NodeMetadata()
        if self._stat:
            metadata.size = self._stat.st_size
            metadata.modified = self._stat.st_mtime
            metadata.permissions = oct(self._stat.st_mode)[-3:]
            
            # Try to determine MIME type for files
            if self._path.is_file():
                metadata.mime_type = self._guess_mime_type(self._path)
        
        # Store both Path object and string path
        self._path_obj = self._path  # Keep Path object for operations
        
        super().__init__(
            name=self._path.name,
            path=str(self._path),  # BaseTreeNode needs string
            node_type=node_type,
            metadata=metadata
        )
        
        # Load children for directories (lazy loading)
        self._children_loaded = False
    
    def _guess_mime_type(self, path):
        """Simple MIME type guess based on extension"""
        ext = path.suffix.lower()
        mime_types = {
            '.txt': 'text/plain',
            '.py': 'text/x-python',
            '.js': 'text/javascript',
            '.html': 'text/html',
            '.css': 'text/css',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.yaml': 'application/x-yaml',
            '.yml': 'application/x-yaml',
            '.md': 'text/markdown',
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.zip': 'application/zip',
            '.tar': 'application/x-tar',
            '.gz': 'application/gzip',
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def children(self):
        """Get child nodes with lazy loading"""
        if not self._children_loaded and self._path_obj.is_dir():
            self._load_children()
        return super().children()
    
    def _load_children(self):
        """Load children from filesystem"""
        if self._children_loaded or not self._path_obj.is_dir():
            return
        
        try:
            for child_path in sorted(self._path_obj.iterdir()):
                child_node = FilesystemNode(child_path)
                self.add_child(child_node)
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass
        
        self._children_loaded = True
    
    def value(self):
        """Get value for leaf nodes (file content)"""
        if self._path_obj.is_file():
            # Check if this is an HTML file - delegate to HTML adapter
            if self._path_obj.suffix.lower() in ['.html', '.htm']:
                return None  # HTML files should use HTML adapter
            try:
                return self._path_obj.read_text(encoding='utf-8')
            except (UnicodeDecodeError, PermissionError, OSError):
                # For binary files or unreadable files, return None
                return None
        return None


class FilesystemAdapter(TreeAdapter):
    """Adapter for filesystem navigation"""
    
    def supports(self, source):
        """Check if source is a filesystem path"""
        if isinstance(source, (str, PathlibPath)):
            path = PathlibPath(source)
            return path.exists() and (path.is_file() or path.is_dir())
        return False
    
    async def build_tree(self, source, **kwargs):
        """Build tree from filesystem path"""
        if isinstance(source, str):
            source = PathlibPath(source)
        
        if not isinstance(source, PathlibPath):
            raise ValueError(f"Expected Path or string, got {type(source)}")
        
        if not source.exists():
            raise FileNotFoundError(f"Path does not exist: {source}")
        
        # Create root node
        root_node = FilesystemNode(source)
        
        # Preload children if requested
        if kwargs.get('preload', False):
            if isinstance(root_node, FilesystemNode):
                root_node._load_children()
        
        return root_node
