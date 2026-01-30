"""Semantic Search Engine for Code Analysis"""

import re
import hashlib
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import numpy as np
from collections import defaultdict

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not available. Semantic search will be disabled.")

from .code_adapter import CodeElement
from .code_intelligence import CodeIntelligenceEngine


@dataclass
class SemanticIndex:
    """Semantic search index for code elements"""
    embeddings: Dict[str, np.ndarray]  # element_id -> embedding
    element_texts: Dict[str, str]      # element_id -> combined text
    element_metadata: Dict[str, CodeElement]  # element_id -> CodeElement
    model_name: str


class SemanticSearchEngine:
    """Semantic search engine for code analysis"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.semantic_index: Optional[SemanticIndex] = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                print(f"Loaded semantic model: {model_name}")
            except Exception as e:
                print(f"Error loading semantic model: {e}")
                self.model = None
    
    def build_semantic_index(self, code_engine: CodeIntelligenceEngine, root_path: Path) -> SemanticIndex:
        """Build semantic index for code elements"""
        if not self.model:
            raise RuntimeError("Semantic model not available. Install sentence-transformers.")
        
        print("Building semantic index...")
        
        # Ensure code index is built
        if not code_engine.index:
            code_engine.build_index(root_path)
        
        # Prepare texts for embedding
        element_texts = {}
        element_metadata = {}
        
        element_id = 0
        for file_path, elements in code_engine.index.file_to_elements.items():
            for element in elements:
                # Create combined text for semantic search
                combined_text = self._create_element_text(element)
                
                elem_id = f"elem_{element_id}"
                element_texts[elem_id] = combined_text
                element_metadata[elem_id] = element
                element_id += 1
        
        # Generate embeddings
        print(f"Generating embeddings for {len(element_texts)} elements...")
        texts = list(element_texts.values())
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Create index
        embeddings_dict = {}
        for i, (elem_id, text) in enumerate(element_texts.items()):
            embeddings_dict[elem_id] = embeddings[i]
        
        self.semantic_index = SemanticIndex(
            embeddings=embeddings_dict,
            element_texts=element_texts,
            element_metadata=element_metadata,
            model_name=self.model_name
        )
        
        print(f"Semantic index built with {len(embeddings_dict)} elements")
        return self.semantic_index
    
    def _create_element_text(self, element: CodeElement) -> str:
        """Create combined text for semantic embedding"""
        parts = []
        
        # Name and type
        parts.append(f"{element.type} {element.name}")
        
        # Signature
        if element.signature:
            parts.append(f"signature: {element.signature}")
        
        # Docstring
        if element.docstring:
            parts.append(f"documentation: {element.docstring}")
        
        # Decorators
        if element.decorators:
            parts.append(f"decorators: {', '.join(element.decorators)}")
        
        # Function calls
        if element.calls:
            parts.append(f"calls: {', '.join(element.calls[:10])}")  # Limit to first 10
        
        # Imports
        if element.imports:
            parts.append(f"imports: {', '.join(element.imports[:10])}")  # Limit to first 10
        
        return " ".join(parts)
    
    def semantic_search(self, query: str, limit: int = 20) -> List[Tuple[CodeElement, float]]:
        """Perform semantic search"""
        if not self.semantic_index or not self.model:
            raise RuntimeError("Semantic index not built or model not available")
        
        # Generate query embedding
        query_embedding = self.model.encode([query])
        
        # Calculate similarities
        similarities = []
        for elem_id, embedding in self.semantic_index.embeddings.items():
            similarity = cosine_similarity(query_embedding, embedding.reshape(1, -1))[0][0]
            element = self.semantic_index.element_metadata[elem_id]
            similarities.append((element, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:limit]
    
    def find_similar_functions(self, target_function: str, limit: int = 10) -> List[Tuple[CodeElement, float]]:
        """Find functions similar to a target function"""
        if not self.semantic_index:
            raise RuntimeError("Semantic index not built")
        
        # Find target function
        target_elem = None
        target_embedding = None
        
        for elem_id, element in self.semantic_index.element_metadata.items():
            if element.name == target_function:
                target_elem = element
                target_embedding = self.semantic_index.embeddings[elem_id]
                break
        
        if not target_elem:
            raise ValueError(f"Function '{target_function}' not found")
        
        # Find similar functions
        similarities = []
        for elem_id, embedding in self.semantic_index.embeddings.items():
            element = self.semantic_index.element_metadata[elem_id]
            
            # Skip self
            if element.name == target_function:
                continue
            
            # Only compare with same type
            if element.type != target_elem.type:
                continue
            
            similarity = cosine_similarity(
                target_embedding.reshape(1, -1), 
                embedding.reshape(1, -1)
            )[0][0]
            
            similarities.append((element, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:limit]
    
    def search_by_intent(self, intent: str, context: str = "", limit: int = 20) -> List[Tuple[CodeElement, float]]:
        """Search by programming intent"""
        # Intent-specific query enhancement
        intent_queries = {
            "parse": f"parse data input format validation extract transform",
            "validate": f"validate check verify input data format schema rules",
            "authenticate": f"auth login user password token session security",
            "database": f"database sql query insert update delete save store",
            "api": f"api http request response endpoint service client server",
            "cache": f"cache memory store temporary fast storage redis",
            "log": f"log logging debug info error trace message output",
            "test": f"test unit testing assert mock verify check",
            "config": f"config configuration settings options parameters load",
            "async": f"async await promise future callback concurrent parallel",
            "error": f"error exception handling try catch throw raise",
            "file": f"file read write save load path directory",
            "network": f"network socket connection client server protocol",
            "security": f"security encryption hash password token protect",
            "performance": f"performance optimize fast efficient memory cpu",
        }
        
        # Enhanced query
        base_query = intent_queries.get(intent.lower(), intent)
        enhanced_query = f"{base_query} {context}"
        
        return self.semantic_search(enhanced_query, limit)
    
    def find_functions_by_description(self, description: str, limit: int = 20) -> List[Tuple[CodeElement, float]]:
        """Find functions by natural language description"""
        return self.semantic_search(description, limit)
    
    def code_similarity_analysis(self, file_path1: str, file_path2: str) -> Dict[str, Any]:
        """Analyze similarity between two files"""
        if not self.semantic_index:
            raise RuntimeError("Semantic index not built")
        
        # Get elements for each file
        file1_elements = []
        file2_elements = []
        
        for elem_id, element in self.semantic_index.element_metadata.items():
            # Extract file path from element (this would need to be stored in element)
            # For now, we'll use a simplified approach
            if hasattr(element, 'file_path'):
                if element.file_path == file_path1:
                    file1_elements.append((elem_id, element))
                elif element.file_path == file_path2:
                    file2_elements.append((elem_id, element))
        
        if not file1_elements or not file2_elements:
            return {"error": "One or both files not found in index"}
        
        # Calculate average similarities
        similarities = []
        for elem1_id, elem1 in file1_elements:
            for elem2_id, elem2 in file2_elements:
                if elem1.type == elem2.type:  # Only compare same types
                    emb1 = self.semantic_index.embeddings[elem1_id]
                    emb2 = self.semantic_index.embeddings[elem2_id]
                    similarity = cosine_similarity(
                        emb1.reshape(1, -1), 
                        emb2.reshape(1, -1)
                    )[0][0]
                    similarities.append(similarity)
        
        return {
            "file1": file_path1,
            "file2": file_path2,
            "avg_similarity": np.mean(similarities) if similarities else 0,
            "max_similarity": max(similarities) if similarities else 0,
            "comparisons": len(similarities),
            "file1_elements": len(file1_elements),
            "file2_elements": len(file2_elements)
        }
    
    def get_embedding_statistics(self) -> Dict[str, Any]:
        """Get statistics about embeddings"""
        if not self.semantic_index:
            return {"error": "Semantic index not built"}
        
        embeddings = list(self.semantic_index.embeddings.values())
        embeddings_array = np.array(embeddings)
        
        return {
            "total_embeddings": len(embeddings),
            "embedding_dimension": embeddings_array.shape[1],
            "model_name": self.semantic_index.model_name,
            "avg_embedding_norm": np.mean(np.linalg.norm(embeddings_array, axis=1)),
            "embedding_stats": {
                "mean": np.mean(embeddings_array),
                "std": np.std(embeddings_array),
                "min": np.min(embeddings_array),
                "max": np.max(embeddings_array)
            }
        }


class CodeSearchEngine:
    """Unified search engine combining keyword and semantic search"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.code_engine = CodeIntelligenceEngine()
        self.semantic_engine = SemanticSearchEngine()
        
        # Build indexes
        print("Building code index...")
        self.code_engine.build_index(root_path)
        
        print("Building semantic index...")
        try:
            self.semantic_engine.build_semantic_index(self.code_engine, root_path)
            self.semantic_available = True
        except RuntimeError:
            print("Semantic search not available")
            self.semantic_available = False
    
    def search(self, query: str, search_type: str = "hybrid", limit: int = 20) -> List[Dict[str, Any]]:
        """Unified search interface"""
        results = []
        
        if search_type in ["keyword", "hybrid"]:
            # Keyword search
            keyword_results = self.code_engine.search(query, limit)
            for element, file_path in keyword_results:
                results.append({
                    "element": element,
                    "file_path": file_path,
                    "score": 1.0,  # Keyword search gets perfect score
                    "type": "keyword"
                })
        
        if search_type in ["semantic", "hybrid"] and self.semantic_available:
            # Semantic search
            semantic_results = self.semantic_engine.semantic_search(query, limit)
            for element, similarity in semantic_results:
                results.append({
                    "element": element,
                    "file_path": "unknown",  # Would need to be tracked
                    "score": similarity,
                    "type": "semantic"
                })
        
        # Remove duplicates and sort
        seen = set()
        unique_results = []
        for result in results:
            element_id = id(result["element"])
            if element_id not in seen:
                seen.add(element_id)
                unique_results.append(result)
        
        # Sort by score
        unique_results.sort(key=lambda x: x["score"], reverse=True)
        
        return unique_results[:limit]
    
    def get_code_summary(self) -> Dict[str, Any]:
        """Get comprehensive code summary"""
        metrics = self.code_engine.calculate_metrics(self.root_path)
        
        summary = {
            "metrics": metrics,
            "semantic_available": self.semantic_available,
        }
        
        if self.semantic_available:
            summary["semantic_stats"] = self.semantic_engine.get_embedding_statistics()
        
        return summary
