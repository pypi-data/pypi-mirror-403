"""Natural Language Processing Engine for NLP2Tree"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re
from .spell_check import NLP3SpellChecker, SpellSuggestion


class IntentType(Enum):
    """Types of navigation intents"""
    # Code-specific intents (higher priority)
    CODE_SEARCH = "code_search"
    FUNCTION_ANALYSIS = "function_analysis"
    SECURITY_SCAN = "security_scan"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    METRICS = "metrics"
    REFACTOR = "refactor"
    DEBUG = "debug"
    # General intents (lower priority)
    FIND = "find"
    LIST = "list"
    FILTER = "filter"
    COUNT = "count"
    PATH = "path"
    TREE = "tree"


class PredicateType(Enum):
    """Types of predicates"""
    SIZE = "size"
    NAME = "name"
    TYPE = "type"
    CONTAINS = "contains"
    MODIFIED = "modified"
    EXTENSION = "extension"
    MIME_TYPE = "mime_type"
    TAG = "tag"
    CLASS = "class"
    ID = "id"
    ATTRIBUTE = "attribute"
    STATUS = "status"
    XPATH = "xpath"
    # Code-specific predicates
    LANGUAGE = "language"
    FUNCTION = "function"
    CLASS_NAME = "class_name"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"
    DECORATOR = "decorator"
    CALL = "call"
    ASYNC = "async"
    TEST = "test"
    DOCUMENTATION = "documentation"
    COMMENT = "comment"
    PATTERN = "pattern"
    COMPLEXITY = "complexity"
    DEPENDENCY = "dependency"


@dataclass
class Intent:
    """Parsed navigation intent"""
    type: IntentType
    confidence: float
    target: Optional[str] = None
    predicates: List['Predicate'] = None
    
    def __post_init__(self):
        if self.predicates is None:
            self.predicates = []


@dataclass
class Predicate:
    """Parsed predicate"""
    type: PredicateType
    operator: str  # >, <, =, contains, regex
    value: Any
    confidence: float


@dataclass
class QueryParse:
    """Parsed natural language query"""
    original: str
    intent: Intent
    tokens: List[str]
    entities: Dict[str, Any]


class NLPEngine:
    """Natural Language Processing Engine"""
    
    def __init__(self, enable_spell_check: bool = True):
        self.enable_spell_check = enable_spell_check
        self.spell_checker = NLP3SpellChecker() if enable_spell_check else None
        
        self._intent_patterns = {
            IntentType.FIND: [
                r"(znajdź|wyszukaj|pokaż|where is|find|search|show)(?!\s+funkcja|funkcji|kod|code)",
            ],
            IntentType.LIST: [
                r"(wylistuj|pokaż wszystkie|list|show all)",
                r".*(wylistuj|list|pokaż wszystkie|show all).+",
            ],
            IntentType.FILTER: [
                r"(filtruj|tylko|where|with|filter|only)",
                r".*(filtruj|filter|tylko|only|where|with).+",
            ],
            IntentType.COUNT: [
                r"(ile|policz|count|how many)",
                r".*(ile|policz|count|how many).+",
            ],
            IntentType.PATH: [
                r"(ścieżka do|path to|jak dojść|how to get to)",
                r".*(ścieżka|path|jak dojść|how to get to).+",
            ],
            IntentType.TREE: [
                r"(drzewo|struktura|tree|structure)",
                r".*(drzewo|tree|struktura|structure).+",
            ],
            # Code-specific intent patterns
            IntentType.CODE_SEARCH: [
                r"(znajdź funkcję|znajdź funkcji|wyszukaj kod|search code|pokaż funkcje|show functions)",
                r".*(funkcja|funkcję|funkcji|function|kod|code).*(znajdź|wyszukaj|pokaż|find|search|show).+",
                r".*(znajdź|wyszukaj|pokaż|find|search|show).*(funkcja|funkcję|funkcji|function|kod|code).+",
            ],
            IntentType.FUNCTION_ANALYSIS: [
                r"(analizuj funkcję|analyze function|co robi|what does|jak działa|how does)",
                r".*(analiza|analysis|działanie|behavior|logika|logic).+(funkcji|function).+",
            ],
            IntentType.SECURITY_SCAN: [
                r"(bezpieczeństwo|security|eval|exec|wyciek|leak|atak|attack)",
                r".*(bezpieczeństwo|security|vulnerability|zagrożenie|threat).+",
            ],
            IntentType.DEPENDENCY_ANALYSIS: [
                r"(zależności|dependencies|importy|imports|wywołania|calls)",
                r".*(zależności|dependencies|importy|imports).+",
            ],
            IntentType.METRICS: [
                r"(metryki|metrics|statystyki|statistics|liczba|count)",
                r".*(metryki|metrics|statystyki|statistics).+",
            ],
            IntentType.REFACTOR: [
                r"(refaktoryzacja|refactor|przenieś|move|zmień|change)",
                r".*(refaktoryzacja|refactor|popraw|improve).+",
            ],
            IntentType.DEBUG: [
                r"(debug|debugowanie|błąd|error|problem|issue)",
                r".*(debug|błąd|error|problem|issue).+",
            ],
        }
        
        self._predicate_patterns = {
            PredicateType.SIZE: [
                r"(większe niż|larger than|>)(\s+)(\d+(?:\.\d+)?)(\s*(KB|MB|GB|TB|b|kb|mb|gb|tb))?",
                r"(mniejsze niż|smaller than|<)(\s+)(\d+(?:\.\d+)?)(\s*(KB|MB|GB|TB|b|kb|mb|gb|tb))?",
                r"(o rozmiarze|of size|=)(\s+)(\d+(?:\.\d+)?)(\s*(KB|MB|GB|TB|b|kb|mb|gb|tb))?",
                r"(między|between)\s+(\d+(?:\.\d+)?)(\s*(KB|MB|GB|TB|b|kb|mb|gb|tb))?\s+(a|and)\s+(\d+(?:\.\d+)?)(\s*(KB|MB|GB|TB|b|kb|mb|gb|tb))?",
                r"(od|from)\s+(\d+(?:\.\d+)?)(\s*(KB|MB|GB|TB|b|kb|mb|gb|tb))?\s+(do|to)\s+(\d+(?:\.\d+)?)(\s*(KB|MB|GB|TB|b|kb|mb|gb|tb))?",
            ],
            PredicateType.NAME: [
                r"(nazwane|o nazwie|named|called)(\s+)([\"']?[^\"'\s]+[\"']?)",
                r".*([\"']?[^\"'\s]+[\"']?)(\s+)(w nazwie|in name)",
            ],
            PredicateType.TYPE: [
                r"(typu|kind of|type)(\s+)(\w+)",
                r".*(\w+)(\s+)(type|typu)",
            ],
            PredicateType.CONTAINS: [
                r"(zawierające|z|containing|with)(\s+)([\"']?[^\"'\s]+[\"']?)",
                r".*([\"']?[^\"'\s]+[\"']?)(\s+)(zawiera|contains)",
            ],
            PredicateType.MODIFIED: [
                r"(zmodyfikowane|changed|modified)(\s+)(w|in)(\s+)(ostatnim|last)(\s+)(\d+)(\s+)(dni|days|tygodniach|weeks|miesiącach|months)",
                r".*(ostatnich|last)(\s+)(\d+)(\s+)(dni|days|tygodniach|weeks|miesiącach|months)",
            ],
            PredicateType.EXTENSION: [
                r"(\.)(\w+)(\s+)(pliki|files)",
                r"(pliki|files)(\s+)(\.)(\w+)",
                r".*\.(\w+)(\s+)?$",
                r"(pliki|files)(\s+)(\w+)(\s+)?$",
            ],
            PredicateType.TAG: [
                r"(tag|znacznik)(\s+)(\w+)",
                r".*<(\w+)>",
                r".*(tag|znacznik)(\s+)(\w+)",
            ],
            PredicateType.CLASS: [
                r"(class|klasa)(\s+)([\"']?[\w\-]+[\"']?)",
                r".*class=['\"]([^'\"]+)['\"]",
            ],
            PredicateType.ID: [
                r"(id)(\s+)([\"']?[\w\-]+[\"']?)",
                r".*id=['\"]([^'\"]+)['\"]",
            ],
            PredicateType.ATTRIBUTE: [
                r"(atrybut|attribute)(\s+)(\w+)(\s+)([\"']?[^\"'\s]+[\"']?)",
                r".*(\w+)=['\"]([^'\"]+)['\"]",
            ],
            PredicateType.STATUS: [
                r"(status)(\s+)(\d+)",
                r".*(status)(\s+)(\d+)",
            ],
            # Code-specific predicate patterns
            PredicateType.LANGUAGE: [
                r"(język|language)(\s+)(python|java|javascript|go|js|ts)",
                r".*(python|java|javascript|go|js|ts)(\s+)(kod|code)?",
            ],
            PredicateType.FUNCTION: [
                r"(funkcja|funkcję|funkcji|function)(\s+)([\"']?[\w\-]+[\"']?)",
                r".*(def|function)(\s+)([\w\-]+)",
            ],
            PredicateType.CLASS_NAME: [
                r"(klasa|class)(\s+)([\"']?[\w\-]+[\"']?)",
                r".*(class)(\s+)([\w\-]+)",
            ],
            PredicateType.METHOD: [
                r"(metoda|method)(\s+)([\"']?[\w\-]+[\"']?)",
                r".*(method)(\s+)([\w\-]+)",
            ],
            PredicateType.IMPORT: [
                r"(import|from)(\s+)([\"']?[\w\.\-]+[\"']?)",
                r".*(import|from)(\s+)([\w\.\-]+)",
            ],
            PredicateType.DECORATOR: [
                r"(dekorator|decorator)(\s+)(@[\w\.\-]+)",
                r".*@([\w\.\-]+)",
            ],
            PredicateType.CALL: [
                r"(wywołanie|call)(\s+)([\"']?[\w\-]+[\"']?)",
                r".*(wywołuje|calls)(\s+)([\w\-]+)",
            ],
            PredicateType.ASYNC: [
                r"(asynchroniczny|async|await)",
                r".*(async|await).+",
            ],
            PredicateType.TEST: [
                r"(test|testy|tests)",
                r".*(test|tests).+",
            ],
            PredicateType.DOCUMENTATION: [
                r"(dokumentacja|documentation|docstring|komentarz|comment)",
                r".*(doc|documentation|comment).+",
            ],
            PredicateType.PATTERN: [
                r"(wzorzec|pattern)(\s+)([\"']?[^\"'\s]+[\"']?)",
                r".*(regex|pattern).+",
            ],
            PredicateType.COMPLEXITY: [
                r"(złożoność|complexity)(\s+)(wysoka|niska|high|low)",
                r".*(complexity).+",
            ],
            PredicateType.DEPENDENCY: [
                r"(zależność|dependency)(\s+)([\"']?[\w\.\-]+[\"']?)",
                r".*(dependency|dependencies).+",
            ],
        }
    
    def parse_query(self, query: str) -> QueryParse:
        """Parse natural language query"""
        # Tokenize
        tokens = self._tokenize(query)
        
        # Extract intent
        intent = self._extract_intent(query)
        
        # Extract entities
        entities = self._extract_entities(query)
        
        return QueryParse(
            original=query,
            intent=intent,
            tokens=tokens,
            entities=entities
        )
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        # Convert to lowercase and split on whitespace
        tokens = text.lower().split()
        # Remove punctuation
        tokens = [re.sub(r'[^\w\.]', '', token) for token in tokens if token]
        return tokens
    
    def _extract_intent(self, query: str) -> Intent:
        """Extract navigation intent"""
        query_lower = query.lower()
        
        best_intent = None
        best_confidence = 0.0
        
        for intent_type, patterns in self._intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query_lower)
                if match:
                    confidence = len(match.group(0)) / len(query_lower)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = Intent(type=intent_type, confidence=confidence)
        
        if best_intent is None:
            # Default to FIND intent
            best_intent = Intent(type=IntentType.FIND, confidence=0.5)
        
        # Extract predicates
        best_intent.predicates = self._extract_predicates(query)
        
        return best_intent
    
    def _extract_predicates(self, query: str) -> List[Predicate]:
        """Extract predicates from query"""
        predicates = []
        query_lower = query.lower()
        
        for pred_type, patterns in self._predicate_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, query_lower)
                for match in matches:
                    predicate = self._parse_predicate_match(pred_type, match, query)
                    if predicate:
                        predicates.append(predicate)
        
        # Deduplicate predicates (same type, operator, and value)
        unique_predicates = []
        seen = set()
        for pred in predicates:
            key = (pred.type.value, pred.operator, str(pred.value))
            if key not in seen:
                seen.add(key)
                unique_predicates.append(pred)
        
        return unique_predicates
    
    def _parse_predicate_match(self, pred_type: PredicateType, match: re.Match, original_query: str) -> Optional[Predicate]:
        """Parse individual predicate match"""
        groups = match.groups()
        
        if pred_type == PredicateType.SIZE:
            if len(groups) >= 3:
                # Check for range predicates (między X a Y, od X do Y)
                if "między" in match.group(0) or "between" in match.group(0) and len(groups) >= 7:
                    # Range predicate: między X a Y
                    value1 = float(groups[1])
                    unit1 = groups[3] if len(groups) > 3 and groups[3] else "B"
                    value2 = float(groups[5]) if len(groups) > 5 else 0
                    unit2 = groups[7] if len(groups) > 7 and groups[7] else unit1
                    
                    # Convert to bytes
                    multiplier = {"B": 1, "b": 1, "KB": 1024, "kb": 1024, "MB": 1024**2, "mb": 1024**2, "GB": 1024**3, "gb": 1024**3, "TB": 1024**4, "tb": 1024**4}
                    value1_bytes = value1 * multiplier.get(unit1.upper(), 1)
                    value2_bytes = value2 * multiplier.get(unit2.upper(), 1)
                    
                    # Create range predicate
                    return Predicate(type=pred_type, operator="range", value=(value1_bytes, value2_bytes), confidence=0.8)
                
                elif ("od" in match.group(0) or "from" in match.group(0)) and len(groups) >= 7:
                    # Range predicate: od X do Y
                    value1 = float(groups[1])
                    unit1 = groups[3] if len(groups) > 3 and groups[3] else "B"
                    value2 = float(groups[5]) if len(groups) > 5 else 0
                    unit2 = groups[7] if len(groups) > 7 and groups[7] else unit1
                    
                    # Convert to bytes
                    multiplier = {"B": 1, "b": 1, "KB": 1024, "kb": 1024, "MB": 1024**2, "mb": 1024**2, "GB": 1024**3, "gb": 1024**3, "TB": 1024**4, "tb": 1024**4}
                    value1_bytes = value1 * multiplier.get(unit1.upper(), 1)
                    value2_bytes = value2 * multiplier.get(unit2.upper(), 1)
                    
                    # Create range predicate
                    return Predicate(type=pred_type, operator="range", value=(value1_bytes, value2_bytes), confidence=0.8)
                
                else:
                    # Single value predicate
                    operator = ">" if "większe" in match.group(0) or "larger" in match.group(0) else "<" if "mniejsze" in match.group(0) or "smaller" in match.group(0) else "="
                    value = float(groups[2])
                    unit = groups[3] if len(groups) > 3 and groups[3] else "B"
                    
                    # Convert to bytes
                    multiplier = {"B": 1, "b": 1, "KB": 1024, "kb": 1024, "MB": 1024**2, "mb": 1024**2, "GB": 1024**3, "gb": 1024**3, "TB": 1024**4, "tb": 1024**4}
                    value_bytes = value * multiplier.get(unit.upper(), 1)
                    
                    return Predicate(type=pred_type, operator=operator, value=value_bytes, confidence=0.8)
        
        elif pred_type == PredicateType.NAME:
            if len(groups) >= 3:
                name = groups[2].strip('\'"')
                return Predicate(type=pred_type, operator="=", value=name, confidence=0.7)
        
        elif pred_type == PredicateType.TYPE:
            if len(groups) >= 3:
                type_value = groups[2]
                return Predicate(type=pred_type, operator="=", value=type_value, confidence=0.7)
        
        elif pred_type == PredicateType.CONTAINS:
            if len(groups) >= 3:
                contains_value = groups[2].strip('\'"')
                return Predicate(type=pred_type, operator="contains", value=contains_value, confidence=0.7)
        
        elif pred_type == PredicateType.FUNCTION:
            if len(groups) >= 3:
                function_name = groups[2].strip('\'"')
                return Predicate(type=pred_type, operator="=", value=function_name, confidence=0.8)
        
        elif pred_type == PredicateType.CLASS_NAME:
            if len(groups) >= 3:
                class_name = groups[2].strip('\'"')
                return Predicate(type=pred_type, operator="=", value=class_name, confidence=0.8)
        
        elif pred_type == PredicateType.METHOD:
            if len(groups) >= 3:
                method_name = groups[2].strip('\'"')
                return Predicate(type=pred_type, operator="=", value=method_name, confidence=0.8)
        
        elif pred_type == PredicateType.IMPORT:
            if len(groups) >= 3:
                import_name = groups[2].strip('\'"')
                return Predicate(type=pred_type, operator="=", value=import_name, confidence=0.8)
        
        elif pred_type == PredicateType.LANGUAGE:
            if len(groups) >= 3:
                language = groups[2]
                return Predicate(type=pred_type, operator="=", value=language, confidence=0.8)
        
        elif pred_type == PredicateType.MODIFIED:
            if len(groups) >= 9:
                time_value = int(groups[6])
                time_unit = groups[8]
                # Convert to days
                multiplier = {"dni": 1, "days": 1, "tygodniach": 7, "weeks": 7, "miesiącach": 30, "months": 30}
                days = time_value * multiplier.get(time_unit.lower(), 1)
                return Predicate(type=pred_type, operator="<", value=days, confidence=0.6)
        
        elif pred_type == PredicateType.EXTENSION:
            if len(groups) >= 1:
                # Try different group positions based on pattern
                ext = None
                if groups[0] == '.' and len(groups) >= 2 and groups[1]:  # First pattern group (\.)(\w+)
                    ext = groups[1]
                elif len(groups) >= 4 and groups[3]:  # Second pattern group (pliki .(\w+))
                    ext = groups[3]
                elif len(groups) >= 3 and groups[2]:  # Fourth pattern group (pliki (\w+))
                    ext = groups[2]
                elif groups[0] and groups[0] != '.':  # Third pattern group (.*\.(\w+))
                    ext = groups[0]
                
                if ext and ext not in ['pliki', 'files']:
                    return Predicate(type=pred_type, operator="=", value=f".{ext}", confidence=0.8)
        
        elif pred_type == PredicateType.TAG:
            if len(groups) >= 3:
                tag_name = groups[2]
                return Predicate(type=pred_type, operator="=", value=tag_name, confidence=0.7)
        
        elif pred_type == PredicateType.CLASS:
            if len(groups) >= 3:
                class_name = groups[2].strip('\'"')
                return Predicate(type=pred_type, operator="contains", value=class_name, confidence=0.7)
        
        elif pred_type == PredicateType.ID:
            if len(groups) >= 3:
                id_value = groups[2].strip('\'"')
                return Predicate(type=pred_type, operator="=", value=id_value, confidence=0.7)
        
        elif pred_type == PredicateType.ATTRIBUTE:
            if len(groups) >= 5:
                attr_name = groups[2]
                attr_value = groups[4].strip('\'"')
                return Predicate(type=pred_type, operator="=", value=f"{attr_name}={attr_value}", confidence=0.7)
        
        elif pred_type == PredicateType.STATUS:
            if len(groups) >= 3:
                status_code = int(groups[2])
                return Predicate(type=pred_type, operator="=", value=status_code, confidence=0.7)
        
        return None
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract named entities"""
        entities = {}
        
        # Extract file extensions
        ext_matches = re.findall(r'\.(\w+)', query)
        if ext_matches:
            entities['extensions'] = ext_matches
        
        # Extract numbers with units
        size_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(KB|MB|GB|TB|B)', query, re.IGNORECASE)
        if size_matches:
            entities['sizes'] = [(float(value), unit.upper()) for value, unit in size_matches]
        
        # Extract quoted strings
        quoted_matches = re.findall(r'["\']([^"\']+)["\']', query)
        if quoted_matches:
            entities['quoted_strings'] = quoted_matches
        
        return entities
    
    def parse(self, query: str) -> QueryParse:
        """Parse natural language query"""
        original_query = query
        
        # Apply spell checking if enabled
        if self.enable_spell_check and self.spell_checker:
            corrected_query, spell_suggestions = self.spell_checker.correct_query(query)
            if corrected_query != query:
                query = corrected_query
        else:
            spell_suggestions = []
        
        # Tokenize
        tokens = self._tokenize(query)
        
        # Extract intent
        intent = self._extract_intent(query)
        
        # Extract predicates
        intent.predicates = self._extract_predicates(query)
        
        # Extract entities
        entities = self._extract_entities(query)
        
        # Add spell suggestions to entities for debugging
        if spell_suggestions:
            entities['spell_suggestions'] = spell_suggestions
        
        return QueryParse(
            original=original_query,
            intent=intent,
            tokens=tokens,
            entities=entities
        )
