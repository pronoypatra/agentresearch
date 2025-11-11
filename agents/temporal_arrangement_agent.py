"""
Temporal Arrangement Agent (Stage 2)

Arranges Tier 2 papers chronologically and builds citation timeline.
"""

from typing import List, Dict
from datetime import datetime
from agents.stage1_paper_search_agent import PaperMetadata
from knowledge_base.paper_db import PaperDB
from knowledge_base.temporal_graph import TemporalGraph


class TemporalArrangementAgent:
    """
    Arranges papers chronologically and tracks temporal relationships.
    """
    
    def __init__(self, paper_db: PaperDB, temporal_graph: TemporalGraph):
        """
        Initialize temporal arrangement agent.
        
        Args:
            paper_db: Paper database
            temporal_graph: Temporal relationship graph
        """
        self.paper_db = paper_db
        self.temporal_graph = temporal_graph
    
    def arrange_chronologically(self, papers: List[PaperMetadata]) -> List[PaperMetadata]:
        """
        Arrange papers in chronological order.
        
        Args:
            papers: List of papers to arrange
            
        Returns:
            Chronologically sorted papers
        """
        # Separate papers with and without dates
        papers_with_dates = []
        papers_without_dates = []
        
        for paper in papers:
            if paper.publication_date:
                papers_with_dates.append(paper)
            else:
                papers_without_dates.append(paper)
        
        # Sort by publication date
        papers_with_dates.sort(key=lambda p: p.publication_date or datetime.min)
        
        # Papers without dates go at the end
        return papers_with_dates + papers_without_dates
    
    def build_citation_timeline(self, papers: List[PaperMetadata]) -> Dict:
        """
        Build citation timeline from papers.
        
        Args:
            papers: List of papers
            
        Returns:
            Dictionary with timeline information
        """
        timeline = {
            'papers_by_year': {},
            'citations': [],
        }
        
        for paper in papers:
            if paper.publication_date:
                year = paper.publication_date.year
                if year not in timeline['papers_by_year']:
                    timeline['papers_by_year'][year] = []
                timeline['papers_by_year'][year].append({
                    'title': paper.title,
                    'arxiv_id': paper.arxiv_id,
                    'citations': paper.citation_count,
                })
        
        return timeline
    
    def identify_temporal_clusters(self, papers: List[PaperMetadata], 
                                  cluster_size_years: int = 2) -> Dict[int, List[str]]:
        """
        Identify temporal clusters of papers.
        
        Args:
            papers: List of papers
            cluster_size_years: Size of time window for clustering
            
        Returns:
            Dictionary mapping cluster ID to paper IDs
        """
        clusters: Dict[int, List[str]] = {}
        current_cluster = 0
        last_year = None
        
        sorted_papers = self.arrange_chronologically(papers)
        
        for paper in sorted_papers:
            if paper.publication_date:
                year = paper.publication_date.year
                paper_id = paper.arxiv_id or paper.title
                
                if last_year is None or (year - last_year) > cluster_size_years:
                    current_cluster += 1
                    clusters[current_cluster] = []
                
                clusters[current_cluster].append(paper_id)
                last_year = year
        
        return clusters
    
    def get_temporal_metadata(self, papers: List[PaperMetadata]) -> Dict:
        """
        Get temporal metadata for papers.
        
        Args:
            papers: List of papers
            
        Returns:
            Dictionary with temporal metadata
        """
        sorted_papers = self.arrange_chronologically(papers)
        
        metadata = {
            'chronological_order': [p.arxiv_id or p.title for p in sorted_papers],
            'year_range': None,
            'total_years': 0,
            'papers_per_year': {},
        }
        
        years = [p.publication_date.year for p in sorted_papers if p.publication_date]
        
        if years:
            metadata['year_range'] = (min(years), max(years))
            metadata['total_years'] = max(years) - min(years) + 1
            
            for year in years:
                metadata['papers_per_year'][year] = metadata['papers_per_year'].get(year, 0) + 1
        
        return metadata

