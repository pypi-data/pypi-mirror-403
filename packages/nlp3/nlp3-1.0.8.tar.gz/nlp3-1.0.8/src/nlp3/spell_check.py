"""Spell checking and typo correction for NLP3"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re
from collections import defaultdict
import json


class SpellCheckAlgorithm(Enum):
    """Available spell checking algorithms"""
    LEVENSHTEIN = "levenshtein"
    DAMERAU_LEVENSHTEIN = "damerau_levenshtein"
    JARO_WINKLER = "jaro_winkler"
    NGRAM = "ngram"
    SYMSPELL = "symspell"


@dataclass
class SpellSuggestion:
    """Spell correction suggestion"""
    word: str
    original: str
    confidence: float
    algorithm: SpellCheckAlgorithm
    distance: Optional[int] = None


class LevenshteinSpellChecker:
    """Levenshtein distance based spell checker"""
    
    def __init__(self, vocabulary: List[str], max_distance: int = 2):
        self.vocabulary = vocabulary
        self.max_distance = max_distance
        self.cache = {}
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def suggest(self, word: str) -> List[SpellSuggestion]:
        """Get spelling suggestions for a word"""
        if word in self.cache:
            return self.cache[word]
        
        suggestions = []
        word_lower = word.lower()
        
        for vocab_word in self.vocabulary:
            vocab_lower = vocab_word.lower()
            distance = self._levenshtein_distance(word_lower, vocab_lower)
            
            if 0 < distance <= self.max_distance:
                confidence = 1.0 - (distance / max(len(word), len(vocab_word)))
                suggestions.append(SpellSuggestion(
                    word=vocab_word,
                    original=word,
                    confidence=confidence,
                    algorithm=SpellCheckAlgorithm.LEVENSHTEIN,
                    distance=distance
                ))
        
        # Sort by distance, then by confidence
        suggestions.sort(key=lambda x: (x.distance, -x.confidence))
        self.cache[word] = suggestions[:5]  # Top 5 suggestions
        
        return suggestions


class NGramSpellChecker:
    """N-gram based spell checker"""
    
    def __init__(self, vocabulary: List[str], n_min: int = 2, n_max: int = 3):
        self.vocabulary = vocabulary
        self.n_min = n_min
        self.n_max = n_max
        self.ngram_index = self._build_ngram_index()
    
    def _build_ngram_index(self) -> Dict[str, List[str]]:
        """Build n-gram index for vocabulary"""
        index = defaultdict(list)
        
        for word in self.vocabulary:
            word_lower = word.lower()
            for n in range(self.n_min, min(self.n_max + 1, len(word_lower) + 1)):
                for i in range(len(word_lower) - n + 1):
                    ngram = word_lower[i:i+n]
                    index[ngram].append(word)
        
        return index
    
    def _get_ngrams(self, word: str) -> List[str]:
        """Get all n-grams for a word"""
        word_lower = word.lower()
        ngrams = []
        
        for n in range(self.n_min, min(self.n_max + 1, len(word_lower) + 1)):
            for i in range(len(word_lower) - n + 1):
                ngrams.append(word_lower[i:i+n])
        
        return ngrams
    
    def suggest(self, word: str) -> List[SpellSuggestion]:
        """Get spelling suggestions using n-grams"""
        suggestions = defaultdict(float)
        word_ngrams = self._get_ngrams(word)
        
        if not word_ngrams:
            return []
        
        for ngram in word_ngrams:
            if ngram in self.ngram_index:
                for vocab_word in self.ngram_index[ngram]:
                    suggestions[vocab_word] += 1
        
        # Calculate confidence based on n-gram overlap
        max_overlap = max(suggestions.values()) if suggestions else 1
        result = []
        
        for vocab_word, overlap in suggestions.items():
            confidence = overlap / max_overlap
            if confidence >= 0.3:  # Minimum 30% overlap
                result.append(SpellSuggestion(
                    word=vocab_word,
                    original=word,
                    confidence=confidence,
                    algorithm=SpellCheckAlgorithm.NGRAM
                ))
        
        result.sort(key=lambda x: -x.confidence)
        return result[:5]


class JaroWinklerSpellChecker:
    """Jaro-Winkler similarity based spell checker"""
    
    def __init__(self, vocabulary: List[str], min_similarity: float = 0.8):
        self.vocabulary = vocabulary
        self.min_similarity = min_similarity
    
    def _jaro_similarity(self, s1: str, s2: str) -> float:
        """Calculate Jaro similarity"""
        if s1 == s2:
            return 1.0
        
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0
        
        match_distance = max(len1, len2) // 2 - 1
        s1_matches = [False] * len1
        s2_matches = [False] * len2
        
        matches = 0
        transpositions = 0
        
        # Find matches
        for i in range(len1):
            start = max(0, i - match_distance)
            end = min(i + match_distance + 1, len2)
            
            for j in range(start, end):
                if s2_matches[j] or s1[i] != s2[j]:
                    continue
                s1_matches[i] = s2_matches[j] = True
                matches += 1
                break
        
        if matches == 0:
            return 0.0
        
        # Find transpositions
        s1_matched = []
        s2_matched = []
        
        for i in range(len1):
            if s1_matches[i]:
                s1_matched.append(s1[i])
        
        for j in range(len2):
            if s2_matches[j]:
                s2_matched.append(s2[j])
        
        transpositions = sum(1 for a, b in zip(s1_matched, s2_matched) if a != b) // 2
        
        # Calculate Jaro similarity
        jaro = (
            (matches / len1) +
            (matches / len2) +
            ((matches - transpositions) / matches)
        ) / 3
        
        return jaro
    
    def _jaro_winkler_similarity(self, s1: str, s2: str) -> float:
        """Calculate Jaro-Winkler similarity"""
        jaro = self._jaro_similarity(s1, s2)
        
        # Winkler prefix scaling
        prefix_length = 0
        max_prefix = min(4, len(s1), len(s2))
        
        for i in range(max_prefix):
            if s1[i].lower() == s2[i].lower():
                prefix_length += 1
            else:
                break
        
        return jaro + (0.1 * prefix_length * (1 - jaro))
    
    def suggest(self, word: str) -> List[SpellSuggestion]:
        """Get spelling suggestions using Jaro-Winkler similarity"""
        suggestions = []
        word_lower = word.lower()
        
        for vocab_word in self.vocabulary:
            vocab_lower = vocab_word.lower()
            similarity = self._jaro_winkler_similarity(word_lower, vocab_lower)
            
            if similarity >= self.min_similarity and similarity < 1.0:
                suggestions.append(SpellSuggestion(
                    word=vocab_word,
                    original=word,
                    confidence=similarity,
                    algorithm=SpellCheckAlgorithm.JARO_WINKLER
                ))
        
        suggestions.sort(key=lambda x: -x.confidence)
        return suggestions[:5]


class SymSpellChecker:
    """SymSpell-like fast spell checker"""
    
    def __init__(self, vocabulary: List[str], max_distance: int = 2):
        self.vocabulary = vocabulary
        self.max_distance = max_distance
        self.deletes_index = self._build_deletes_index()
    
    def _build_deletes_index(self) -> Dict[str, List[str]]:
        """Build delete index for fast lookup"""
        index = defaultdict(list)
        
        for word in self.vocabulary:
            word_lower = word.lower()
            index[word_lower].append(word)  # Add exact word
            
            # Generate deletes
            for i in range(len(word_lower)):
                deleted = word_lower[:i] + word_lower[i+1:]
                index[deleted].append(word)
        
        return index
    
    def _generate_deletes(self, word: str) -> List[str]:
        """Generate all possible deletes for a word"""
        deletes = []
        word_lower = word.lower()
        
        for i in range(len(word_lower)):
            deleted = word_lower[:i] + word_lower[i+1:]
            deletes.append(deleted)
        
        return deletes
    
    def suggest(self, word: str) -> List[SpellSuggestion]:
        """Get spelling suggestions using SymSpell algorithm"""
        suggestions = defaultdict(list)
        word_lower = word.lower()
        
        # Check exact match first
        if word_lower in [v.lower() for v in self.vocabulary]:
            return []
        
        # Generate deletes and lookup
        deletes = self._generate_deletes(word_lower)
        
        for deleted in deletes:
            if deleted in self.deletes_index:
                for vocab_word in self.deletes_index[deleted]:
                    distance = self._calculate_distance(word_lower, vocab_word.lower())
                    if distance <= self.max_distance:
                        confidence = 1.0 - (distance / max(len(word), len(vocab_word)))
                        suggestions[distance].append(SpellSuggestion(
                            word=vocab_word,
                            original=word,
                            confidence=confidence,
                            algorithm=SpellCheckAlgorithm.SYMSPELL,
                            distance=distance
                        ))
        
        # Flatten and sort suggestions
        result = []
        for distance in sorted(suggestions.keys()):
            result.extend(suggestions[distance])
        
        return result[:5]
    
    def _calculate_distance(self, s1: str, s2: str) -> int:
        """Simple distance calculation"""
        if s1 == s2:
            return 0
        
        # Simple Levenshtein for short words
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]


class NLP3SpellChecker:
    """Main spell checker for NLP3 combining multiple algorithms"""
    
    def __init__(self):
        # NLP3 vocabulary
        self.commands = [
            "query", "explore", "parse", "inspect", "find", 
            "list", "count", "show", "search", "filter"
        ]
        
        self.keywords = [
            "znajdź", "wszystkie", "pliki", "katalogu", "pokaż", 
            "moduły", "zmodyfikowane", "tygodniu", "status", 
            "tag", "class", "id", "attribute", "extension"
        ]
        
        self.vocabulary = self.commands + self.keywords
        
        # Initialize spell checkers
        self.levenshtein_checker = LevenshteinSpellChecker(self.vocabulary)
        self.ngram_checker = NGramSpellChecker(self.vocabulary)
        self.jaro_winkler_checker = JaroWinklerSpellChecker(self.vocabulary)
        self.symspell_checker = SymSpellChecker(self.vocabulary)
        
        # Cache for corrections
        self.correction_cache = {}
    
    def correct_word(self, word: str) -> str:
        """Correct a single word"""
        if word.lower() in [v.lower() for v in self.vocabulary]:
            return word
        
        if word in self.correction_cache:
            return self.correction_cache[word]
        
        # Try different algorithms in order of preference
        suggestions = []
        
        # 1. Levenshtein (most accurate for small typos)
        suggestions.extend(self.levenshtein_checker.suggest(word))
        
        # 2. SymSpell (fast, good for production)
        suggestions.extend(self.symspell_checker.suggest(word))
        
        # 3. Jaro-Winkler (good for similar words)
        suggestions.extend(self.jaro_winkler_checker.suggest(word))
        
        # 4. N-grams (for larger typos)
        suggestions.extend(self.ngram_checker.suggest(word))
        
        # Remove duplicates and sort by confidence
        unique_suggestions = {}
        for suggestion in suggestions:
            key = suggestion.word.lower()
            if key not in unique_suggestions or suggestion.confidence > unique_suggestions[key].confidence:
                unique_suggestions[key] = suggestion
        
        # Get best suggestion
        if unique_suggestions:
            best_suggestion = max(unique_suggestions.values(), key=lambda x: x.confidence)
            if best_suggestion.confidence >= 0.7:  # 70% confidence threshold
                self.correction_cache[word] = best_suggestion.word
                return best_suggestion.word
        
        # No good suggestion found
        self.correction_cache[word] = word
        return word
    
    def correct_query(self, query: str) -> Tuple[str, List[SpellSuggestion]]:
        """Correct an entire query and return suggestions"""
        words = query.split()
        corrected_words = []
        all_suggestions = []
        
        for word in words:
            # Skip very short words and common words
            if len(word) <= 2 or word.lower() in ['w', 'z', 'na', 'do', 'i', 'oraz', 'the', 'a', 'an', 'of', 'in', 'to']:
                corrected_words.append(word)
                continue
            
            corrected = self.correct_word(word)
            corrected_words.append(corrected)
            
            # Collect suggestions for debugging
            if corrected != word:
                suggestions = self.levenshtein_checker.suggest(word)[:3]
                all_suggestions.extend(suggestions)
        
        corrected_query = " ".join(corrected_words)
        return corrected_query, all_suggestions
    
    def get_suggestions(self, word: str, max_suggestions: int = 5) -> List[SpellSuggestion]:
        """Get spelling suggestions for a word"""
        all_suggestions = []
        
        # Get suggestions from all algorithms
        all_suggestions.extend(self.levenshtein_checker.suggest(word))
        all_suggestions.extend(self.symspell_checker.suggest(word))
        all_suggestions.extend(self.jaro_winkler_checker.suggest(word))
        all_suggestions.extend(self.ngram_checker.suggest(word))
        
        # Remove duplicates and sort
        unique_suggestions = {}
        for suggestion in all_suggestions:
            key = suggestion.word.lower()
            if key not in unique_suggestions or suggestion.confidence > unique_suggestions[key].confidence:
                unique_suggestions[key] = suggestion
        
        # Sort by confidence and return top suggestions
        sorted_suggestions = sorted(unique_suggestions.values(), key=lambda x: -x.confidence)
        return sorted_suggestions[:max_suggestions]


# Example usage and testing
if __name__ == "__main__":
    # Initialize spell checker
    spell_checker = NLP3SpellChecker()
    
    # Test examples
    test_words = [
        "queri",      # Should be "query"
        "expolre",    # Should be "explore"
        "pars",       # Should be "parse"
        "inspekt",    # Should be "inspect"
        "znajdz",     # Should be "znajdź"
        "pliki",      # Should be "pliki" (correct)
        "moduly",     # Should be "moduły"
    ]
    
    print("=== NLP3 Spell Checker Test ===")
    for word in test_words:
        corrected = spell_checker.correct_word(word)
        suggestions = spell_checker.get_suggestions(word, 3)
        
        print(f"\nOriginal: {word}")
        print(f"Corrected: {corrected}")
        print("Suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion.word} ({suggestion.confidence:.2f}) - {suggestion.algorithm.value}")
    
    # Test full query correction
    test_queries = [
        "queri pliki .py",
        "expolre ./src --depth 2",
        "pars znajdz pliki",
        "inspekt ./docs/index.html"
    ]
    
    print("\n=== Query Correction Test ===")
    for query in test_queries:
        corrected, suggestions = spell_checker.correct_query(query)
        print(f"\nOriginal: {query}")
        print(f"Corrected: {corrected}")
        if suggestions:
            print("Changes made:")
            for suggestion in suggestions[:3]:
                print(f"  - {suggestion.original} → {suggestion.word}")
