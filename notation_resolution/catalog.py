"""
Notation Catalog & Ontology

Maintains a comprehensive database of notations and their meanings across papers.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from .extractor import ExtractedNotation, NotationType


@dataclass
class ConceptEntry:
    """Entry for a mathematical concept in the ontology"""
    concept_name: str
    common_symbols: Set[str]
    domain_variants: Dict[str, List[str]] = field(default_factory=dict)
    description: Optional[str] = None


class NotationCatalog:
    """
    Catalog of mathematical notations with ontology and equivalence mappings.
    """
    
    def __init__(self):
        self.notations: Dict[str, ExtractedNotation] = {}
        self.concepts: Dict[str, ConceptEntry] = {}
        self.equivalence_map: Dict[str, Set[str]] = {}
        self._initialize_default_conventions()
    
    def _initialize_default_conventions(self):
        """Initialize with common ML notation conventions"""
        
        # Parameters/Weights
        self.add_concept(
            concept_name="model_parameters",
            common_symbols={"θ", "w", "β", "φ"},
            domain_variants={
                "optimization": ["w", "θ"],
                "statistics": ["β", "θ"],
                "deep_learning": ["W", "θ", "w"],
            },
            description="Model parameters or weights"
        )
        
        # Loss functions
        self.add_concept(
            concept_name="loss_function",
            common_symbols={"L", "ℓ", "J", "R"},
            domain_variants={
                "optimization": ["L", "J"],
                "statistics": ["R", "L"],
                "deep_learning": ["L", "J"],
            },
            description="Loss, cost, or risk function"
        )
        
        # Regularization parameter
        self.add_concept(
            concept_name="regularization_parameter",
            common_symbols={"λ", "α", "μ"},
            domain_variants={
                "optimization": ["λ"],
                "statistics": ["λ", "α"],
                "deep_learning": ["λ", "α"],
            },
            description="Regularization or penalty parameter"
        )
    
    def add_concept(self, concept_name: str, common_symbols: Set[str],
                   domain_variants: Optional[Dict[str, List[str]]] = None,
                   description: Optional[str] = None):
        """Add a concept to the ontology"""
        entry = ConceptEntry(
            concept_name=concept_name,
            common_symbols=common_symbols,
            domain_variants=domain_variants or {},
            description=description
        )
        self.concepts[concept_name] = entry
        
        # Build equivalence map
        for symbol in common_symbols:
            if symbol not in self.equivalence_map:
                self.equivalence_map[symbol] = set()
            self.equivalence_map[symbol].update(common_symbols)
    
    def register_notation(self, notation: ExtractedNotation, paper_id: str):
        """Register a notation from a paper"""
        key = f"{paper_id}:{notation.symbol}"
        self.notations[key] = notation
    
    def find_equivalent(self, symbol: str, domain: Optional[str] = None) -> Set[str]:
        """Find equivalent notations for a given symbol"""
        equivalents = self.equivalence_map.get(symbol, set())
        return equivalents
    
    def get_concept_for_symbol(self, symbol: str) -> Optional[str]:
        """Get the concept name for a symbol"""
        for concept_name, concept in self.concepts.items():
            if symbol in concept.common_symbols:
                return concept_name
        return None

