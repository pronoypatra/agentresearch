"""
Paper Database

Stores paper metadata and content.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class PaperRecord:
    """Record for a paper in the database"""
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    arxiv_id: Optional[str]
    publication_date: Optional[str]
    citation_count: int
    url: Optional[str]
    source: str
    content: Optional[str] = None  # LaTeX or text content
    tier: Optional[int] = None  # 1 for Tier 1, 2 for Tier 2
    analysis_status: str = "pending"  # pending, analyzing, completed
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class PaperDB:
    """
    Database for storing paper metadata and content.
    """
    
    def __init__(self, db_path: str = "knowledge_base/papers.json"):
        """
        Initialize paper database.
        
        Args:
            db_path: Path to JSON file for storage
        """
        self.db_path = db_path
        self.papers: Dict[str, PaperRecord] = {}
        self._load()
    
    def _load(self):
        """Load papers from disk"""
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                for paper_id, paper_data in data.items():
                    self.papers[paper_id] = PaperRecord(**paper_data)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading paper database: {e}")
    
    def _save(self):
        """Save papers to disk"""
        try:
            data = {pid: paper.to_dict() for pid, paper in self.papers.items()}
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving paper database: {e}")
    
    def add_paper(self, paper: PaperRecord):
        """Add or update a paper"""
        self.papers[paper.paper_id] = paper
        self._save()
    
    def get_paper(self, paper_id: str) -> Optional[PaperRecord]:
        """Get a paper by ID"""
        return self.papers.get(paper_id)
    
    def get_tier_papers(self, tier: int) -> List[PaperRecord]:
        """Get all papers in a tier"""
        return [p for p in self.papers.values() if p.tier == tier]
    
    def update_analysis_status(self, paper_id: str, status: str):
        """Update analysis status of a paper"""
        if paper_id in self.papers:
            self.papers[paper_id].analysis_status = status
            self._save()
    
    def set_paper_content(self, paper_id: str, content: str):
        """Set paper content"""
        if paper_id in self.papers:
            self.papers[paper_id].content = content
            self._save()
    
    def get_all_papers(self) -> List[PaperRecord]:
        """Get all papers"""
        return list(self.papers.values())

