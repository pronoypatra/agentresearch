"""
Unified Notation Builder

Creates a canonical unified notation from Tier 1 papers and generates
a notation table for user display.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from .extractor import NotationExtractor, ExtractedNotation
from .catalog import NotationCatalog
from .disambiguator import NotationDisambiguator
from .mapper import NotationMapper


@dataclass
class UnifiedNotationEntry:
    """Entry in the unified notation table"""
    unified_symbol: str
    concept: str
    definition: str
    paper_mappings: Dict[str, str]  # paper_id -> original_symbol
    confidence: float
    domain: Optional[str] = None


@dataclass
class UnifiedNotationTable:
    """Complete unified notation table"""
    entries: List[UnifiedNotationEntry]
    paper_ids: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for display"""
        return {
            'entries': [
                {
                    'unified_symbol': entry.unified_symbol,
                    'concept': entry.concept,
                    'definition': entry.definition,
                    'paper_mappings': entry.paper_mappings,
                    'confidence': entry.confidence,
                    'domain': entry.domain,
                }
                for entry in self.entries
            ],
            'paper_ids': self.paper_ids,
        }


class UnifiedNotationBuilder:
    """
    Builds unified notation from Tier 1 papers.
    """
    
    def __init__(self):
        self.extractor = NotationExtractor()
        self.catalog = NotationCatalog()
        self.disambiguator = NotationDisambiguator(self.catalog)
        self.mapper = NotationMapper(self.catalog, self.disambiguator)
    
    def build_unified_notation(self, papers: List[Dict], paper_contents: Dict[str, str]) -> UnifiedNotationTable:
        """
        Build unified notation from Tier 1 papers.
        
        Args:
            papers: List of paper metadata dictionaries
            paper_contents: Dictionary mapping paper_id -> LaTeX content
            
        Returns:
            Unified notation table
        """
        paper_ids = []
        all_extracted_notations = {}
        
        # Extract notations from all papers
        for paper in papers:
            paper_id = paper.get('arxiv_id', paper.get('title', 'unknown'))
            paper_ids.append(paper_id)
            
            content = paper_contents.get(paper_id, '')
            if not content:
                continue
            
            # Extract notations
            notations = self.extractor.extract_from_latex(content, paper_id=paper_id)
            
            # Register in catalog
            for notation in notations:
                self.catalog.register_notation(notation, paper_id)
                key = f"{paper_id}:{notation.symbol}"
                all_extracted_notations[key] = notation
        
        # Build unified notation entries
        unified_entries = self._build_unified_entries(paper_ids, all_extracted_notations)
        
        return UnifiedNotationTable(
            entries=unified_entries,
            paper_ids=paper_ids
        )
    
    def _build_unified_entries(self, paper_ids: List[str], 
                               all_notations: Dict[str, ExtractedNotation]) -> List[UnifiedNotationEntry]:
        """Build unified notation entries by grouping equivalent notations"""
        entries = []
        
        # Group notations by concept
        concept_groups: Dict[str, Dict[str, ExtractedNotation]] = {}
        
        for key, notation in all_notations.items():
            paper_id = key.split(':')[0]
            concept = self.catalog.get_concept_for_symbol(notation.symbol)
            
            if not concept:
                # Create new concept for this symbol
                concept = f"concept_{notation.symbol}"
            
            if concept not in concept_groups:
                concept_groups[concept] = {}
            
            concept_groups[concept][key] = notation
        
        # Create unified entries
        for concept, notations in concept_groups.items():
            # Choose unified symbol (prefer most common or first)
            symbols = [n.symbol for n in notations.values()]
            unified_symbol = self._choose_unified_symbol(symbols, concept)
            
            # Build paper mappings
            paper_mappings = {}
            for key, notation in notations.items():
                paper_id = key.split(':')[0]
                paper_mappings[paper_id] = notation.symbol
            
            # Get definition (from first notation with definition)
            definition = ""
            for notation in notations.values():
                if notation.context.definition_text:
                    definition = notation.context.definition_text[:200]  # Truncate
                    break
            if not definition:
                definition = f"{concept} from {len(paper_mappings)} papers"
            
            # Calculate confidence (based on agreement across papers)
            confidence = min(1.0, len(paper_mappings) / len(paper_ids))
            
            # Get domain
            domain = None
            for notation in notations.values():
                if notation.context.domain_keywords:
                    domain = notation.context.domain_keywords[0]
                    break
            
            entry = UnifiedNotationEntry(
                unified_symbol=unified_symbol,
                concept=concept,
                definition=definition,
                paper_mappings=paper_mappings,
                confidence=confidence,
                domain=domain
            )
            entries.append(entry)
        
        return entries
    
    def _choose_unified_symbol(self, symbols: List[str], concept: str) -> str:
        """Choose the best unified symbol from a list"""
        # Prefer symbols that match concept's common symbols
        concept_entry = self.catalog.concepts.get(concept)
        if concept_entry:
            for common_symbol in concept_entry.common_symbols:
                if common_symbol in symbols:
                    return common_symbol
        
        # Otherwise, use most frequent or first
        from collections import Counter
        if symbols:
            counter = Counter(symbols)
            return counter.most_common(1)[0][0]
        
        return symbols[0] if symbols else "unknown"
    
    def get_notation_table_for_display(self, table: UnifiedNotationTable) -> str:
        """
        Generate a formatted string representation of the notation table.
        
        Args:
            table: Unified notation table
            
        Returns:
            Formatted string for display
        """
        lines = []
        lines.append("=" * 80)
        lines.append("UNIFIED NOTATION TABLE")
        lines.append("=" * 80)
        lines.append("")
        
        for entry in table.entries:
            lines.append(f"Unified Symbol: {entry.unified_symbol}")
            lines.append(f"  Concept: {entry.concept}")
            lines.append(f"  Definition: {entry.definition[:100]}...")
            lines.append(f"  Confidence: {entry.confidence:.2f}")
            if entry.domain:
                lines.append(f"  Domain: {entry.domain}")
            lines.append(f"  Paper Mappings:")
            for paper_id, symbol in entry.paper_mappings.items():
                lines.append(f"    {paper_id}: {symbol}")
            lines.append("")
        
        return "\n".join(lines)

