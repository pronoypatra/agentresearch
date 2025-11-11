"""
Multi-Query Search Agent (Stage 2)

Executes multiple search queries and selects optimal set of Tier 2 papers.
"""

from typing import List, Dict, Set
from agents.stage1_paper_search_agent import Stage1PaperSearchAgent, PaperMetadata
from agents.query_generation_agent import QueryGenerationAgent
from knowledge_base.paper_db import PaperDB


class MultiQuerySearchAgent:
    """
    Executes multiple queries and selects optimal papers.
    """
    
    def __init__(self, paper_search: Stage1PaperSearchAgent, paper_db: PaperDB):
        """
        Initialize multi-query search agent.
        
        Args:
            paper_search: Paper search agent
            paper_db: Paper database
        """
        self.paper_search = paper_search
        self.paper_db = paper_db
    
    def search_and_select(self, queries: List[str], target_count: int = 40,
                        tier1_paper_ids: List[str] = None) -> List[PaperMetadata]:
        """
        Execute multiple queries and select optimal papers.
        
        Args:
            queries: List of search queries
            target_count: Target number of papers to select
            tier1_paper_ids: List of Tier 1 paper IDs to exclude
            
        Returns:
            List of selected papers
        """
        all_candidates = []
        tier1_ids_set = set(tier1_paper_ids or [])
        
        # Execute each query
        for query in queries:
            try:
                results = self.paper_search.search(query, seed_papers=None)
                # Filter out Tier 1 papers
                filtered = [p for p in results if (p.arxiv_id or p.title) not in tier1_ids_set]
                all_candidates.extend(filtered)
            except Exception as e:
                print(f"Error searching with query '{query}': {e}")
                continue
        
        # Deduplicate
        unique_papers = self._deduplicate(all_candidates)
        
        # Score and select optimal set
        scored_papers = self._score_papers(unique_papers, queries)
        
        # Select diverse set
        selected = self._select_diverse_set(scored_papers, target_count)
        
        return selected
    
    def _deduplicate(self, papers: List[PaperMetadata]) -> List[PaperMetadata]:
        """Remove duplicate papers"""
        seen = set()
        unique = []
        
        for paper in papers:
            key = paper.arxiv_id if paper.arxiv_id else paper.title.lower()
            if key and key not in seen:
                seen.add(key)
                unique.append(paper)
        
        return unique
    
    def _score_papers(self, papers: List[PaperMetadata], queries: List[str]) -> List[tuple]:
        """Score papers by relevance and diversity"""
        scored = []
        
        for paper in papers:
            score = 0.0
            
            # Relevance to queries
            paper_text = (paper.title + " " + paper.abstract).lower()
            query_matches = 0
            for query in queries:
                query_words = set(query.lower().split())
                paper_words = set(paper_text.split())
                overlap = len(query_words.intersection(paper_words))
                if overlap > 0:
                    query_matches += overlap / len(query_words)
            
            score += query_matches / len(queries) * 0.4
            
            # Citation score
            citation_score = min(paper.citation_count / 50.0, 1.0)
            score += citation_score * 0.3
            
            # Recency score
            if paper.publication_date:
                from datetime import datetime
                years_ago = (datetime.now() - paper.publication_date.replace(tzinfo=None)).days / 365.0
                recency = max(0, 1.0 - years_ago / 10.0)
                score += recency * 0.3
            else:
                score += 0.1
            
            scored.append((score, paper))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored
    
    def _select_diverse_set(self, scored_papers: List[tuple], target_count: int) -> List[PaperMetadata]:
        """Select diverse set of papers"""
        selected = []
        selected_texts = set()
        
        for score, paper in scored_papers:
            if len(selected) >= target_count:
                break
            
            # Check diversity (simple: check if very similar to already selected)
            paper_text = (paper.title + " " + paper.abstract).lower()
            paper_words = set(paper_text.split())
            
            is_diverse = True
            for selected_text in selected_texts:
                selected_words = set(selected_text.split())
                overlap = len(paper_words.intersection(selected_words))
                similarity = overlap / max(len(paper_words), len(selected_words), 1)
                if similarity > 0.7:  # Too similar
                    is_diverse = False
                    break
            
            if is_diverse:
                selected.append(paper)
                selected_texts.add(paper_text)
        
        return selected

