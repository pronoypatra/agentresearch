"""
Notation Mapping & Translation
"""

from typing import Dict, List, Optional, Set, Tuple
from .extractor import ExtractedNotation
from .catalog import NotationCatalog
from .disambiguator import NotationDisambiguator


class NotationMapper:
    """Maps and translates notations between papers."""
    
    def __init__(self, catalog: NotationCatalog, disambiguator: NotationDisambiguator):
        self.catalog = catalog
        self.disambiguator = disambiguator
        self.translation_cache: Dict[Tuple[str, str], Dict[str, str]] = {}
    
    def translate_notation(self, source_symbol: str, source_context: str,
                          target_paper_id: str, source_paper_id: str) -> Optional[str]:
        """Translate a notation from source paper to target paper's notation"""
        cache_key = (source_paper_id, target_paper_id)
        if cache_key in self.translation_cache:
            if source_symbol in self.translation_cache[cache_key]:
                return self.translation_cache[cache_key][source_symbol]
        
        concept = self.catalog.get_concept_for_symbol(source_symbol)
        if not concept:
            return None
        
        target_notations = self._get_paper_notations(target_paper_id)
        for notation in target_notations:
            target_concept = self.catalog.get_concept_for_symbol(notation.symbol)
            if target_concept == concept:
                if cache_key not in self.translation_cache:
                    self.translation_cache[cache_key] = {}
                self.translation_cache[cache_key][source_symbol] = notation.symbol
                return notation.symbol
        
        return None
    
    def _get_paper_notations(self, paper_id: str) -> List[ExtractedNotation]:
        """Get all notations for a paper"""
        notations = []
        for key, notation in self.catalog.notations.items():
            if key.startswith(f"{paper_id}:"):
                notations.append(notation)
        return notations

