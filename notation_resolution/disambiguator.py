"""
Context-Aware Notation Disambiguation
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .extractor import ExtractedNotation, NotationContext
from .catalog import NotationCatalog


@dataclass
class DisambiguationResult:
    """Result of notation disambiguation"""
    symbol: str
    resolved_meaning: str
    confidence: float
    evidence: List[str]


class NotationDisambiguator:
    """Disambiguates notations using contextual information."""
    
    CONTEXT_PATTERNS = {
        'λ': {
            'regularization': [r'regulariz', r'penalty', r'L\(.*\)\s*\+\s*λ'],
            'eigenvalue': [r'eigenvalue', r'eigenvector', r'A.*=.*λ'],
        },
    }
    
    def __init__(self, catalog: NotationCatalog):
        self.catalog = catalog
    
    def disambiguate(self, symbol: str, context: NotationContext) -> DisambiguationResult:
        """Disambiguate a symbol using its context"""
        import re
        
        context_text = self._get_context_text(context)
        
        if symbol in self.CONTEXT_PATTERNS:
            meanings = self._match_context_patterns(symbol, context_text)
        else:
            meanings = self._infer_from_catalog(symbol, context)
        
        if not meanings:
            return DisambiguationResult(
                symbol=symbol,
                resolved_meaning="unknown",
                confidence=0.0,
                evidence=[]
            )
        
        meanings.sort(key=lambda x: x[1], reverse=True)
        best_meaning, best_confidence = meanings[0]
        evidence = self._collect_evidence(symbol, best_meaning, context_text)
        
        return DisambiguationResult(
            symbol=symbol,
            resolved_meaning=best_meaning,
            confidence=best_confidence,
            evidence=evidence
        )
    
    def _get_context_text(self, context: NotationContext) -> str:
        """Extract all context text"""
        texts = []
        if context.definition_text:
            texts.append(context.definition_text)
        if context.surrounding_text:
            texts.append(context.surrounding_text)
        return ' '.join(texts).lower()
    
    def _match_context_patterns(self, symbol: str, context_text: str) -> List[Tuple[str, float]]:
        """Match context against known patterns"""
        import re
        meanings = []
        patterns = self.CONTEXT_PATTERNS.get(symbol, {})
        
        for meaning, pattern_list in patterns.items():
            matches = sum(1 for pattern in pattern_list if re.search(pattern, context_text, re.IGNORECASE))
            if matches > 0:
                confidence = min(0.9, 0.5 + matches * 0.1)
                meanings.append((meaning, confidence))
        
        return meanings
    
    def _infer_from_catalog(self, symbol: str, context: NotationContext) -> List[Tuple[str, float]]:
        """Infer meaning from catalog"""
        meanings = []
        concept = self.catalog.get_concept_for_symbol(symbol)
        if concept:
            meanings.append((concept, 0.7))
        return meanings
    
    def _collect_evidence(self, symbol: str, meaning: str, context_text: str) -> List[str]:
        """Collect evidence for the disambiguation"""
        evidence = []
        if meaning in context_text:
            evidence.append(f"Explicit mention: '{meaning}'")
        return evidence

