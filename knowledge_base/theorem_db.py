"""
Theorem Database

Stores extracted theorems, proofs, and mathematical components.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
import json


@dataclass
class Theorem:
    """Represents a theorem or mathematical result"""
    theorem_id: str
    paper_id: str
    statement: str
    assumptions: List[str]
    conclusion: str
    proof_technique: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)  # IDs of dependent theorems
    bounds: Optional[str] = None
    complexity: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Definition:
    """Represents a mathematical definition"""
    definition_id: str
    paper_id: str
    concept: str
    definition_text: str
    notation: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class TheoremDB:
    """
    Database for storing theorems and mathematical components.
    """
    
    def __init__(self, db_path: str = "knowledge_base/theorems.json"):
        """
        Initialize theorem database.
        
        Args:
            db_path: Path to JSON file for storage
        """
        self.db_path = db_path
        self.theorems: Dict[str, Theorem] = {}
        self.definitions: Dict[str, Definition] = {}
        self._load()
    
    def _load(self):
        """Load theorems from disk"""
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                theorems_data = data.get('theorems', {})
                definitions_data = data.get('definitions', {})
                
                for tid, tdata in theorems_data.items():
                    self.theorems[tid] = Theorem(**tdata)
                
                for did, ddata in definitions_data.items():
                    self.definitions[did] = Definition(**ddata)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading theorem database: {e}")
    
    def _save(self):
        """Save theorems to disk"""
        try:
            data = {
                'theorems': {tid: t.to_dict() for tid, t in self.theorems.items()},
                'definitions': {did: d.to_dict() for did, d in self.definitions.items()},
            }
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving theorem database: {e}")
    
    def add_theorem(self, theorem: Theorem):
        """Add a theorem"""
        self.theorems[theorem.theorem_id] = theorem
        self._save()
    
    def add_definition(self, definition: Definition):
        """Add a definition"""
        self.definitions[definition.definition_id] = definition
        self._save()
    
    def get_paper_theorems(self, paper_id: str) -> List[Theorem]:
        """Get all theorems for a paper"""
        return [t for t in self.theorems.values() if t.paper_id == paper_id]
    
    def get_paper_definitions(self, paper_id: str) -> List[Definition]:
        """Get all definitions for a paper"""
        return [d for d in self.definitions.values() if d.paper_id == paper_id]

