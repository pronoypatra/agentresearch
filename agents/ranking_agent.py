"""
Adaptive Ranking Agent

Handles initial and refined ranking of papers with notation compatibility
and theoretical framework alignment.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from agents.stage1_paper_search_agent import PaperMetadata
from knowledge_base.paper_db import PaperDB
from knowledge_base.theorem_db import TheoremDB
from notation_resolution.unified_notation_builder import UnifiedNotationTable


@dataclass
class RankingScore:
    """Represents a ranking score for a paper"""
    paper_id: str
    initial_score: float
    refined_score: float
    notation_compatibility: float
    framework_alignment: float
    citation_score: float
    relevance_score: float
    total_score: float


class AdaptiveRankingAgent:
    """
    Adaptively ranks papers with initial and refined scoring.
    """
    
    def __init__(self, paper_db: PaperDB, theorem_db: TheoremDB):
        """
        Initialize ranking agent.
        
        Args:
            paper_db: Paper database
            theorem_db: Theorem database
        """
        self.paper_db = paper_db
        self.theorem_db = theorem_db
    
    def initial_ranking(self, papers: List[PaperMetadata], query: str) -> List[PaperMetadata]:
        """
        Perform initial ranking based on relevance, citations, and recency.
        
        Args:
            papers: List of papers to rank
            query: Research query
            
        Returns:
            Ranked list of papers
        """
        scored_papers = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for paper in papers:
            score = 0.0
            
            # Relevance score (keyword matching)
            title_lower = paper.title.lower()
            abstract_lower = paper.abstract.lower()
            
            title_matches = sum(1 for word in query_words if word in title_lower)
            abstract_matches = sum(1 for word in query_words if word in abstract_lower)
            
            relevance_score = (title_matches * 2 + abstract_matches) / max(len(query_words), 1)
            score += relevance_score * 0.4
            
            # Citation score (normalized)
            citation_score = min(paper.citation_count / 100.0, 1.0)
            score += citation_score * 0.3
            
            # Recency score
            if paper.publication_date:
                from datetime import datetime
                years_ago = (datetime.now() - paper.publication_date.replace(tzinfo=None)).days / 365.0
                recency_score = max(0, 1.0 - years_ago / 10.0)
                score += recency_score * 0.3
            else:
                score += 0.1
            
            scored_papers.append((score, paper))
        
        # Sort by score
        scored_papers.sort(key=lambda x: x[0], reverse=True)
        return [paper for _, paper in scored_papers]
    
    def refined_ranking(self, papers: List[PaperMetadata], 
                       tier1_paper_ids: List[str],
                       unified_notation: Optional[UnifiedNotationTable] = None) -> List[RankingScore]:
        """
        Perform refined ranking using Tier 1 context.
        
        Args:
            papers: Papers to rank
            tier1_paper_ids: List of Tier 1 paper IDs for context
            unified_notation: Unified notation table
            
        Returns:
            List of ranking scores
        """
        # Get Tier 1 context
        tier1_papers = [self.paper_db.get_paper(pid) for pid in tier1_paper_ids if self.paper_db.get_paper(pid)]
        tier1_themes = self._extract_themes_from_papers(tier1_papers)
        tier1_frameworks = self._extract_frameworks_from_papers(tier1_papers)
        
        ranking_scores = []
        
        for paper in papers:
            paper_id = paper.arxiv_id or paper.title
            
            # Initial score (from initial ranking)
            initial_score = 0.5  # Placeholder - would use actual initial score
            
            # Notation compatibility
            notation_compat = self._compute_notation_compatibility(
                paper_id, unified_notation
            ) if unified_notation else 0.5
            
            # Framework alignment
            framework_align = self._compute_framework_alignment(
                paper, tier1_frameworks
            )
            
            # Citation network analysis
            citation_score = self._compute_citation_score(paper, tier1_paper_ids)
            
            # Relevance to Tier 1 themes
            relevance_score = self._compute_relevance_to_tier1(
                paper, tier1_themes, tier1_frameworks
            )
            
            # Refined score (weighted combination)
            refined_score = (
                initial_score * 0.2 +
                notation_compat * 0.2 +
                framework_align * 0.25 +
                citation_score * 0.15 +
                relevance_score * 0.2
            )
            
            ranking_score = RankingScore(
                paper_id=paper_id,
                initial_score=initial_score,
                refined_score=refined_score,
                notation_compatibility=notation_compat,
                framework_alignment=framework_align,
                citation_score=citation_score,
                relevance_score=relevance_score,
                total_score=refined_score
            )
            ranking_scores.append(ranking_score)
        
        # Sort by total score
        ranking_scores.sort(key=lambda x: x.total_score, reverse=True)
        return ranking_scores
    
    def _extract_themes_from_papers(self, papers: List) -> List[str]:
        """Extract themes from Tier 1 papers"""
        themes = set()
        for paper in papers:
            if paper and paper.content:
                content_lower = paper.content.lower()
                theme_keywords = {
                    'generalization': ['generalization', 'generalize'],
                    'optimization': ['optimization', 'gradient'],
                    'complexity': ['complexity', 'sample complexity'],
                    'convergence': ['convergence', 'rate'],
                }
                for theme, keywords in theme_keywords.items():
                    if any(kw in content_lower for kw in keywords):
                        themes.add(theme)
        return list(themes)
    
    def _extract_frameworks_from_papers(self, papers: List) -> List[str]:
        """Extract frameworks from Tier 1 papers"""
        frameworks = set()
        for paper in papers:
            if paper and paper.content:
                content_lower = paper.content.lower()
                framework_keywords = {
                    'VC Theory': ['VC dimension', 'VC theory'],
                    'Rademacher Complexity': ['Rademacher'],
                    'PAC Learning': ['PAC'],
                }
                for framework, keywords in framework_keywords.items():
                    if any(kw in content_lower for kw in keywords):
                        frameworks.add(framework)
        return list(frameworks)
    
    def _compute_notation_compatibility(self, paper_id: str, 
                                       unified_notation: UnifiedNotationTable) -> float:
        """Compute notation compatibility score"""
        # Simplified: check if paper uses similar notation
        # In full implementation, would extract notations from paper and compare
        return 0.7  # Placeholder
    
    def _compute_framework_alignment(self, paper: PaperMetadata, 
                                    tier1_frameworks: List[str]) -> float:
        """Compute framework alignment score"""
        if not tier1_frameworks:
            return 0.5
        
        paper_text = (paper.title + " " + paper.abstract).lower()
        matches = sum(1 for fw in tier1_frameworks if fw.lower() in paper_text)
        return min(1.0, matches / len(tier1_frameworks))
    
    def _compute_citation_score(self, paper: PaperMetadata, 
                               tier1_paper_ids: List[str]) -> float:
        """Compute citation network score"""
        # Simplified: would check if paper cites Tier 1 papers
        # For now, use citation count as proxy
        return min(1.0, paper.citation_count / 50.0)
    
    def _compute_relevance_to_tier1(self, paper: PaperMetadata,
                                   tier1_themes: List[str],
                                   tier1_frameworks: List[str]) -> float:
        """Compute relevance to Tier 1 context"""
        paper_text = (paper.title + " " + paper.abstract).lower()
        
        theme_matches = sum(1 for theme in tier1_themes if theme.lower() in paper_text)
        framework_matches = sum(1 for fw in tier1_frameworks if fw.lower() in paper_text)
        
        total_matches = theme_matches + framework_matches
        max_possible = len(tier1_themes) + len(tier1_frameworks)
        
        if max_possible == 0:
            return 0.5
        
        return min(1.0, total_matches / max_possible)
    
    def assign_tiers(self, papers: List[PaperMetadata], 
                    tier1_count: int = 10) -> tuple:
        """
        Assign papers to Tier 1 and Tier 2.
        
        Args:
            papers: List of papers
            tier1_count: Number of Tier 1 papers
            
        Returns:
            Tuple of (tier1_papers, tier2_papers)
        """
        if len(papers) <= tier1_count:
            return papers, []
        
        tier1 = papers[:tier1_count]
        tier2 = papers[tier1_count:]
        
        return tier1, tier2

