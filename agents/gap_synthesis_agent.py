"""
Gap Synthesis Agent

Aggregates, validates, and prioritizes research gaps from Tier 2 analysis.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from knowledge_base.gap_db import GapDB, ResearchGap
from knowledge_base.paper_db import PaperDB
from knowledge_base.theorem_db import TheoremDB
from agents.shallow_analysis_agent import GapCandidate
import uuid


@dataclass
class PrioritizedGap:
    """Represents a prioritized research gap"""
    gap: ResearchGap
    priority_score: float
    novelty_score: float
    feasibility_score: float
    impact_score: float
    evidence_strength: float


class GapSynthesisAgent:
    """
    Synthesizes and prioritizes research gaps.
    """
    
    def __init__(self, gap_db: GapDB, paper_db: PaperDB, theorem_db: TheoremDB):
        """
        Initialize gap synthesis agent.
        
        Args:
            gap_db: Gap database
            paper_db: Paper database
            theorem_db: Theorem database
        """
        self.gap_db = gap_db
        self.paper_db = paper_db
        self.theorem_db = theorem_db
    
    def synthesize_gaps(self, gap_candidates: List[GapCandidate],
                       tier1_paper_ids: List[str]) -> List[PrioritizedGap]:
        """
        Synthesize and prioritize gaps from candidates.
        
        Args:
            gap_candidates: List of gap candidates from shallow analysis
            tier1_paper_ids: List of Tier 1 paper IDs for validation
            
        Returns:
            List of prioritized gaps
        """
        # Aggregate similar gaps
        aggregated_gaps = self._aggregate_gaps(gap_candidates)
        
        # Validate against Tier 1
        validated_gaps = self._validate_gaps(aggregated_gaps, tier1_paper_ids)
        
        # Compute scores
        scored_gaps = []
        for gap_data in validated_gaps:
            gap = self._create_research_gap(gap_data)
            
            # Compute scores
            novelty = self._compute_novelty_score(gap, tier1_paper_ids)
            feasibility = self._compute_feasibility_score(gap)
            impact = self._compute_impact_score(gap)
            evidence = self._compute_evidence_strength(gap)
            
            # Priority score (weighted combination)
            priority = (
                novelty * 0.3 +
                feasibility * 0.2 +
                impact * 0.3 +
                evidence * 0.2
            )
            
            gap.priority = priority
            gap.novelty_score = novelty
            gap.feasibility_score = feasibility
            gap.impact_score = impact
            
            # Store in database
            self.gap_db.add_gap(gap)
            
            prioritized = PrioritizedGap(
                gap=gap,
                priority_score=priority,
                novelty_score=novelty,
                feasibility_score=feasibility,
                impact_score=impact,
                evidence_strength=evidence
            )
            scored_gaps.append(prioritized)
        
        # Sort by priority
        scored_gaps.sort(key=lambda x: x.priority_score, reverse=True)
        
        return scored_gaps
    
    def _aggregate_gaps(self, candidates: List[GapCandidate]) -> List[Dict]:
        """Aggregate similar gap candidates"""
        aggregated = []
        processed = set()
        
        for candidate in candidates:
            # Check if similar gap already exists
            is_duplicate = False
            for existing in aggregated:
                if self._are_similar(candidate, existing):
                    # Merge evidence
                    existing['evidence'].extend(candidate.evidence)
                    existing['related_papers'].extend(candidate.related_papers)
                    existing['confidence'] = max(existing['confidence'], candidate.confidence)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                aggregated.append({
                    'gap_type': candidate.gap_type,
                    'description': candidate.description,
                    'evidence': candidate.evidence,
                    'related_papers': list(set(candidate.related_papers)),
                    'confidence': candidate.confidence,
                    'temporal_context': candidate.temporal_context,
                })
        
        return aggregated
    
    def _are_similar(self, gap1: GapCandidate, gap2: Dict) -> bool:
        """Check if two gaps are similar"""
        # Simple similarity: same type and similar description
        if gap1.gap_type != gap2['gap_type']:
            return False
        
        # Check description similarity (simple word overlap)
        desc1_words = set(gap1.description.lower().split())
        desc2_words = set(gap2['description'].lower().split())
        overlap = len(desc1_words.intersection(desc2_words))
        similarity = overlap / max(len(desc1_words), len(desc2_words), 1)
        
        return similarity > 0.5
    
    def _validate_gaps(self, gaps: List[Dict], tier1_paper_ids: List[str]) -> List[Dict]:
        """Validate gaps against Tier 1 analysis"""
        validated = []
        
        # Get Tier 1 theorems and concepts
        tier1_theorems = []
        for tid in tier1_paper_ids:
            tier1_theorems.extend(self.theorem_db.get_paper_theorems(tid))
        
        for gap in gaps:
            # Check if gap is already addressed in Tier 1
            is_addressed = False
            gap_desc_lower = gap['description'].lower()
            
            for theorem in tier1_theorems:
                if any(word in gap_desc_lower for word in theorem.statement.lower().split()[:10]):
                    # Potential overlap - lower confidence
                    gap['confidence'] *= 0.7
                    is_addressed = True
            
            if not is_addressed or gap['confidence'] > 0.5:
                validated.append(gap)
        
        return validated
    
    def _create_research_gap(self, gap_data: Dict) -> ResearchGap:
        """Create a ResearchGap from gap data"""
        gap_id = str(uuid.uuid4())[:8]
        
        return ResearchGap(
            gap_id=gap_id,
            description=gap_data['description'],
            evidence=gap_data['evidence'],
            priority=0.0,  # Will be computed
            novelty_score=0.0,
            feasibility_score=0.0,
            impact_score=0.0,
            related_papers=gap_data['related_papers'],
            temporal_context=gap_data.get('temporal_context'),
        )
    
    def _compute_novelty_score(self, gap: ResearchGap, tier1_paper_ids: List[str]) -> float:
        """Compute novelty score (distance from Tier 1 content)"""
        # Simplified: check if concepts in gap are new
        gap_words = set(gap.description.lower().split())
        
        # Get all Tier 1 content
        tier1_content = ""
        for tid in tier1_paper_ids:
            paper = self.paper_db.get_paper(tid)
            if paper:
                tier1_content += (paper.title + " " + paper.abstract).lower()
        
        tier1_words = set(tier1_content.split())
        
        # Novelty = proportion of gap words not in Tier 1
        novel_words = gap_words - tier1_words
        if len(gap_words) == 0:
            return 0.5
        
        novelty = len(novel_words) / len(gap_words)
        return min(1.0, novelty * 1.2)  # Slight boost
    
    def _compute_feasibility_score(self, gap: ResearchGap) -> float:
        """Compute feasibility score (theoretically tractable)"""
        # Simplified: check for feasibility indicators
        gap_lower = gap.description.lower()
        
        feasibility_keywords = {
            'positive': ['straightforward', 'direct', 'simple', 'clear'],
            'negative': ['challenging', 'difficult', 'open', 'unknown'],
        }
        
        score = 0.5  # Base score
        
        for keyword in feasibility_keywords['positive']:
            if keyword in gap_lower:
                score += 0.1
        
        for keyword in feasibility_keywords['negative']:
            if keyword in gap_lower:
                score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _compute_impact_score(self, gap: ResearchGap) -> float:
        """Compute impact score (addresses important questions)"""
        gap_lower = gap.description.lower()
        
        impact_keywords = {
            'high': ['fundamental', 'important', 'significant', 'major', 'key'],
            'medium': ['useful', 'relevant', 'applicable'],
        }
        
        score = 0.5  # Base score
        
        for keyword in impact_keywords['high']:
            if keyword in gap_lower:
                score += 0.15
        
        for keyword in impact_keywords['medium']:
            if keyword in gap_lower:
                score += 0.1
        
        # Boost if multiple papers related
        if len(gap.related_papers) > 1:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _compute_evidence_strength(self, gap: ResearchGap) -> float:
        """Compute strength of evidence"""
        # Based on number of evidence items and related papers
        evidence_score = min(1.0, len(gap.evidence) / 3.0)
        paper_score = min(1.0, len(gap.related_papers) / 2.0)
        
        return (evidence_score + paper_score) / 2.0
    
    def generate_gap_report(self, prioritized_gaps: List[PrioritizedGap], 
                           top_k: int = 10) -> str:
        """
        Generate a detailed formatted report of prioritized gaps.
        
        Args:
            prioritized_gaps: List of prioritized gaps
            top_k: Number of top gaps to include
            
        Returns:
            Formatted detailed report string
        """
        lines = []
        lines.append("## DETAILED RESEARCH GAP ANALYSIS REPORT")
        lines.append("")
        lines.append(f"**Total Gaps Analyzed:** {len(prioritized_gaps)}")
        lines.append(f"**Top {min(top_k, len(prioritized_gaps))} Prioritized Gaps:**")
        lines.append("")
        
        top_gaps = prioritized_gaps[:top_k]
        
        for i, pgap in enumerate(top_gaps, 1):
            gap = pgap.gap
            lines.append(f"### Gap #{i}")
            lines.append("")
            lines.append(f"**Description:** {gap.description}")
            lines.append("")
            lines.append("**Scores:**")
            lines.append(f"- Priority Score: {pgap.priority_score:.3f}")
            lines.append(f"- Novelty: {pgap.novelty_score:.3f}")
            lines.append(f"- Feasibility: {pgap.feasibility_score:.3f}")
            lines.append(f"- Impact: {pgap.impact_score:.3f}")
            lines.append(f"- Evidence Strength: {pgap.evidence_strength:.3f}")
            lines.append("")
            lines.append(f"**Evidence Items** ({len(gap.evidence)}):")
            for j, evidence in enumerate(gap.evidence[:5], 1):  # Show first 5 evidence items
                lines.append(f"  {j}. {evidence}")
            if len(gap.evidence) > 5:
                lines.append(f"  ... and {len(gap.evidence) - 5} more")
            lines.append("")
            lines.append(f"**Related Papers** ({len(gap.related_papers)}):")
            for paper_id in gap.related_papers[:5]:  # Show first 5 papers
                lines.append(f"  - {paper_id}")
            if len(gap.related_papers) > 5:
                lines.append(f"  ... and {len(gap.related_papers) - 5} more")
            if gap.temporal_context:
                lines.append("")
                lines.append(f"**Temporal Context:** {gap.temporal_context}")
            lines.append("")
        
        return "\n".join(lines)

