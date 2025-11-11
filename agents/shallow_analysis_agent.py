"""
Shallow Gap Analysis Agent (Stage 2)

Performs quick gap detection in Tier 2 papers processed chronologically.
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from knowledge_base.paper_db import PaperDB
from knowledge_base.theorem_db import TheoremDB
from knowledge_base.gap_db import GapDB, ResearchGap
from knowledge_base.temporal_graph import TemporalGraph


@dataclass
class GapCandidate:
    """Represents a potential research gap"""
    gap_type: str  # "missing_connection", "contradiction", "extension", "open_problem"
    description: str
    evidence: List[str]
    related_papers: List[str]
    confidence: float
    temporal_context: Optional[str] = None


class ShallowAnalysisAgent:
    """
    Performs shallow analysis for gap detection in Tier 2 papers.
    """
    
    def __init__(self, paper_db: PaperDB, theorem_db: TheoremDB, 
                 gap_db: GapDB, temporal_graph: TemporalGraph):
        """
        Initialize shallow analysis agent.
        
        Args:
            paper_db: Paper database
            theorem_db: Theorem database
            gap_db: Gap database
            temporal_graph: Temporal relationship graph
        """
        self.paper_db = paper_db
        self.theorem_db = theorem_db
        self.gap_db = gap_db
        self.temporal_graph = temporal_graph
        self.processed_papers: List[str] = []
    
    def analyze_paper_chronologically(self, paper_id: str, 
                                     tier1_paper_ids: List[str],
                                     previous_tier2_papers: List[str]) -> List[GapCandidate]:
        """
        Analyze a Tier 2 paper in chronological order.
        
        Args:
            paper_id: ID of paper to analyze
            tier1_paper_ids: List of Tier 1 paper IDs
            previous_tier2_papers: List of previously processed Tier 2 papers
            
        Returns:
            List of gap candidates
        """
        paper = self.paper_db.get_paper(paper_id)
        if not paper:
            return []
        
        content = paper.content or paper.abstract
        gap_candidates = []
        
        # Quick extraction: abstract, intro, conclusion, key theorems
        abstract = paper.abstract
        intro_section = self._extract_section(content, "introduction")
        conclusion_section = self._extract_section(content, "conclusion")
        key_theorems = self._extract_key_theorems(content)
        
        # Compare against Tier 1 findings
        tier1_theorems = []
        for tid in tier1_paper_ids:
            tier1_theorems.extend(self.theorem_db.get_paper_theorems(tid))
        
        # Compare against previous Tier 2 papers
        previous_theorems = []
        for pid in previous_tier2_papers:
            previous_theorems.extend(self.theorem_db.get_paper_theorems(pid))
        
        # Detect gaps
        gap_candidates.extend(
            self._detect_missing_connections(paper_id, content, tier1_paper_ids, previous_tier2_papers)
        )
        gap_candidates.extend(
            self._detect_contradictions(paper_id, content, tier1_theorems, previous_theorems)
        )
        gap_candidates.extend(
            self._detect_extensions(paper_id, content, tier1_theorems)
        )
        gap_candidates.extend(
            self._detect_open_problems(paper_id, content)
        )
        gap_candidates.extend(
            self._detect_under_explored_areas(paper_id, content, tier1_paper_ids)
        )
        
        # Track evolution
        self._track_evolution(paper_id, paper, previous_tier2_papers)
        
        # Mark as processed
        self.processed_papers.append(paper_id)
        
        return gap_candidates
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a section from paper content"""
        patterns = [
            rf'\\section\*?\{{.*?{section_name}.*?\}}(.*?)(?=\\section|$)',
            rf'\\subsection\*?\{{.*?{section_name}.*?\}}(.*?)(?=\\section|\\subsection|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()[:1000]  # Limit length
        
        return ""
    
    def _extract_key_theorems(self, content: str) -> List[str]:
        """Extract key theorem statements"""
        theorems = []
        theorem_pattern = r'\\textbf\{Theorem.*?\}:(.*?)(?=\\textbf|\\begin|$)'
        matches = re.finditer(theorem_pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            theorems.append(match.group(1).strip()[:200])
        return theorems[:5]  # Top 5
    
    def _detect_missing_connections(self, paper_id: str, content: str,
                                   tier1_paper_ids: List[str],
                                   previous_tier2: List[str]) -> List[GapCandidate]:
        """Detect missing connections between papers"""
        gaps = []
        
        # Check if paper should cite Tier 1 papers but doesn't
        content_lower = content.lower()
        for tier1_id in tier1_paper_ids:
            tier1_paper = self.paper_db.get_paper(tier1_id)
            if tier1_paper:
                # Check if concepts from Tier 1 appear but paper isn't cited
                tier1_title_words = set(tier1_paper.title.lower().split())
                content_words = set(content_lower.split())
                overlap = tier1_title_words.intersection(content_words)
                
                # If significant overlap but no citation mention
                if len(overlap) >= 2 and tier1_id not in content:
                    gaps.append(GapCandidate(
                        gap_type="missing_connection",
                        description=f"Paper may be related to {tier1_paper.title} but doesn't cite it",
                        evidence=[f"Shared concepts: {', '.join(list(overlap)[:3])}"],
                        related_papers=[paper_id, tier1_id],
                        confidence=0.6,
                    ))
        
        return gaps
    
    def _detect_contradictions(self, paper_id: str, content: str,
                              tier1_theorems: List, previous_theorems: List) -> List[GapCandidate]:
        """Detect contradictions with existing results"""
        gaps = []
        
        # Look for contradiction keywords
        contradiction_keywords = ['contradict', 'inconsistent', 'disagree', 'conflict']
        content_lower = content.lower()
        
        for keyword in contradiction_keywords:
            if keyword in content_lower:
                # Find context
                pattern = rf'{keyword}.*?(?:with|to|from).*?(?:result|theorem|paper|work)'
                match = re.search(pattern, content_lower)
                if match:
                    gaps.append(GapCandidate(
                        gap_type="contradiction",
                        description=f"Potential contradiction detected: {match.group(0)[:100]}",
                        evidence=[f"Found keyword: {keyword}"],
                        related_papers=[paper_id],
                        confidence=0.7,
                    ))
        
        return gaps
    
    def _detect_extensions(self, paper_id: str, content: str,
                          tier1_theorems: List) -> List[GapCandidate]:
        """Detect natural extensions not explored"""
        gaps = []
        
        # Look for extension keywords
        extension_keywords = ['extend', 'generalize', 'improve', 'relax']
        content_lower = content.lower()
        
        for keyword in extension_keywords:
            if keyword in content_lower:
                # Find what is being extended
                pattern = rf'{keyword}.*?(?:to|by|with).*?(?:\.|,)'
                match = re.search(pattern, content_lower)
                if match:
                    gaps.append(GapCandidate(
                        gap_type="extension",
                        description=f"Extension identified: {match.group(0)[:100]}",
                        evidence=[f"Extension keyword: {keyword}"],
                        related_papers=[paper_id],
                        confidence=0.6,
                    ))
        
        return gaps
    
    def _detect_open_problems(self, paper_id: str, content: str) -> List[GapCandidate]:
        """Detect explicitly stated open problems"""
        gaps = []
        
        # Look for open problem sections
        open_problem_patterns = [
            r'open problem[^.]*:(.*?)(?=\\.|$)',
            r'future work[^.]*:(.*?)(?=\\.|$)',
            r'open question[^.]*:(.*?)(?=\\.|$)',
        ]
        
        for pattern in open_problem_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                problem_text = match.group(1).strip()[:200]
                gaps.append(GapCandidate(
                    gap_type="open_problem",
                    description=f"Open problem: {problem_text}",
                    evidence=[f"Found in {match.group(0)[:50]}"],
                    related_papers=[paper_id],
                    confidence=0.8,
                ))
        
        return gaps
    
    def _detect_under_explored_areas(self, paper_id: str, content: str,
                                   tier1_paper_ids: List[str]) -> List[GapCandidate]:
        """Detect under-explored research areas"""
        gaps = []
        
        # Look for "limited", "few", "under-explored" keywords
        under_explored_patterns = [
            r'limited.*?research.*?on',
            r'few.*?studies.*?on',
            r'under.*?explored',
            r'little.*?attention.*?to',
        ]
        
        content_lower = content.lower()
        for pattern in under_explored_patterns:
            matches = re.finditer(pattern, content_lower, re.IGNORECASE)
            for match in matches:
                # Extract the area
                context = content_lower[max(0, match.start()-50):match.end()+50]
                gaps.append(GapCandidate(
                    gap_type="under_explored",
                    description=f"Under-explored area: {context[:150]}",
                    evidence=[f"Pattern: {pattern}"],
                    related_papers=[paper_id],
                    confidence=0.65,
                ))
        
        return gaps
    
    def _track_evolution(self, paper_id: str, paper, previous_tier2: List[str]):
        """Track how concepts evolve over time"""
        # Add to temporal graph
        if paper.publication_date:
            try:
                timestamp = datetime.fromisoformat(paper.publication_date.replace('Z', '+00:00'))
                self.temporal_graph.add_paper(paper_id, timestamp)
            except:
                pass
        
        # Add edges to previous papers
        for prev_id in previous_tier2:
            # Check if current paper cites previous
            if paper.content and prev_id in paper.content:
                self.temporal_graph.add_edge(prev_id, paper_id, "cites")
            else:
                # Add temporal edge anyway
                self.temporal_graph.add_edge(prev_id, paper_id, "temporal")

