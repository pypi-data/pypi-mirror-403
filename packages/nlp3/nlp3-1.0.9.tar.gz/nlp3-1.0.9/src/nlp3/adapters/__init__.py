"""Adapters package for NLP3Tree"""

from .filesystem import FilesystemAdapter, FilesystemNode
from .json_adapter import JsonAdapter, JsonNode, YamlAdapter
from .html import HTMLAdapter, HTMLTreeNode
from .api.rest import RESTAdapter, RESTTreeNode
from .code_tree_adapter import CodeAdapter as CodeTreeAdapter
from .code_adapter import CodeAdapter, CodeElement
from .code_intelligence import CodeIntelligenceEngine, CodeIndex, CodeMetrics
from .semantic_search import SemanticSearchEngine, CodeSearchEngine
from .code_use_cases import CodeAnalysisUseCases

__all__ = [
    "FilesystemAdapter", "FilesystemNode", 
    "JsonAdapter", "JsonNode", "YamlAdapter", 
    "HTMLAdapter", "HTMLTreeNode",
    "RESTAdapter", "RESTTreeNode",
    "CodeTreeAdapter",
    "CodeAdapter",
    "CodeElement",
    "CodeIntelligenceEngine",
    "CodeIndex",
    "CodeMetrics",
    "SemanticSearchEngine",
    "CodeSearchEngine",
    "CodeAnalysisUseCases",
]
