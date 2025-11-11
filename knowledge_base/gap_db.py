"""
Gap Database

Stores identified research gaps.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import json


@dataclass
class ResearchGap:
    """Represents a research gap"""
    gap_id: str
    description: str
    evidence: List[str] = field(default_factory=list)
    priority: float = 0.0
    novelty_score: float = 0.0
    feasibility_score: float = 0.0
    impact_score: float = 0.0
    related_papers: List[str] = field(default_factory=list)
    temporal_context: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class GapDB:
    """
    Database for storing research gaps.
    """
    
    def __init__(self, db_path: str = "knowledge_base/gaps.json"):
        """
        Initialize gap database.
        
        Args:
            db_path: Path to JSON file for storage
        """
        self.db_path = db_path
        self.gaps: Dict[str, ResearchGap] = {}
        self._load()
    
    def _load(self):
        """Load gaps from disk"""
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                for gid, gdata in data.items():
                    self.gaps[gid] = ResearchGap(**gdata)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading gap database: {e}")
    
    def _save(self):
        """Save gaps to disk"""
        try:
            data = {gid: gap.to_dict() for gid, gap in self.gaps.items()}
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving gap database: {e}")
    
    def add_gap(self, gap: ResearchGap):
        """Add a research gap"""
        self.gaps[gap.gap_id] = gap
        self._save()
    
    def get_all_gaps(self) -> List[ResearchGap]:
        """Get all gaps"""
        return list(self.gaps.values())
    
    def get_prioritized_gaps(self, top_k: int = 10) -> List[ResearchGap]:
        """Get top K prioritized gaps"""
        sorted_gaps = sorted(self.gaps.values(), key=lambda g: g.priority, reverse=True)
        return sorted_gaps[:top_k]

