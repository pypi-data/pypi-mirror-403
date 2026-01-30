"""NLP3 - Universal Context Navigator

Navigate any data structure using natural language.
Files, APIs, Databases, Documents, and more.
"""

__version__ = "1.0.10"
__author__ = "WronAI"

from .core import TreeNavigator, TreeNode
from .nlp import NLPEngine

__all__ = ["TreeNavigator", "TreeNode", "NLPEngine"]
