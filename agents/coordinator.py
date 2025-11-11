"""
Coordinator Agent

Orchestrates the two-stage workflow of the research analysis system.
"""

from typing import Dict, List, Optional
from .stage1_paper_search_agent import Stage1PaperSearchAgent, PaperMetadata
from .deep_analysis_agent import DeepAnalysisAgent
from .context_builder import ContextBuilder
from .query_generation_agent import QueryGenerationAgent
from .multi_query_search_agent import MultiQuerySearchAgent
from .temporal_arrangement_agent import TemporalArrangementAgent
from .shallow_analysis_agent import ShallowAnalysisAgent
from .gap_synthesis_agent import GapSynthesisAgent
from notation_resolution.unified_notation_builder import UnifiedNotationBuilder
from knowledge_base.paper_db import PaperDB, PaperRecord
from knowledge_base.theorem_db import TheoremDB
from knowledge_base.notation_db import NotationDB
from knowledge_base.gap_db import GapDB
from knowledge_base.temporal_graph import TemporalGraph


class Coordinator:
    """
    Main coordinator for the research analysis system.
    """
    
    def __init__(self):
        """Initialize coordinator with all necessary components"""
        # Knowledge bases
        self.paper_db = PaperDB()
        self.theorem_db = TheoremDB()
        self.notation_db = NotationDB()
        self.gap_db = GapDB()
        self.temporal_graph = TemporalGraph()
        
        # Stage 1 Agents
        self.paper_search = Stage1PaperSearchAgent(max_results=10)
        self.deep_analysis = DeepAnalysisAgent(self.theorem_db)
        self.context_builder = ContextBuilder(self.theorem_db, self.paper_db)
        self.unified_notation_builder = UnifiedNotationBuilder()
        
        # Stage 2 Agents
        self.query_generator = QueryGenerationAgent(self.context_builder)
        self.multi_query_search = MultiQuerySearchAgent(self.paper_search, self.paper_db)
        self.temporal_arranger = TemporalArrangementAgent(self.paper_db, self.temporal_graph)
        self.shallow_analysis = ShallowAnalysisAgent(
            self.paper_db, self.theorem_db, self.gap_db, self.temporal_graph
        )
        self.gap_synthesis = GapSynthesisAgent(self.gap_db, self.paper_db, self.theorem_db)
        
        # State
        self.stage1_complete = False
        self.stage2_complete = False
        self.tier1_papers: List[PaperMetadata] = []
        self.tier2_papers: List[PaperMetadata] = []
        self.tier1_context: Optional[Dict] = None
        self.unified_notation_table = None
        self.prioritized_gaps = []
    
    def stage1_search_and_analyze(self, query: str, seed_papers: Optional[List[str]] = None) -> Dict:
        """
        Stage 1: Search for Tier 1 papers and perform deep analysis.
        
        Args:
            query: Research query
            seed_papers: Optional seed papers
            
        Returns:
            Dictionary with Stage 1 results
        """
        # Search for papers
        print("Searching for Tier 1 papers...")
        tier1_papers = self.paper_search.search(query, seed_papers)
        self.tier1_papers = tier1_papers
        
        # Store papers in database
        for paper in tier1_papers:
            paper_id = paper.arxiv_id or paper.title
            paper_record = PaperRecord(
                paper_id=paper_id,
                title=paper.title,
                authors=paper.authors,
                abstract=paper.abstract,
                arxiv_id=paper.arxiv_id,
                publication_date=paper.publication_date.isoformat() if paper.publication_date else None,
                citation_count=paper.citation_count,
                url=paper.url,
                source=paper.source,
                tier=1,
                analysis_status="analyzing"
            )
            self.paper_db.add_paper(paper_record)
        
        # Perform deep analysis (simplified - would need actual paper content)
        print("Performing deep analysis...")
        paper_contents = {}  # In real implementation, would fetch PDF/LaTeX content
        analysis_results = {}
        
        for paper in tier1_papers:
            paper_id = paper.arxiv_id or paper.title
            content = paper_contents.get(paper_id, paper.abstract)  # Fallback to abstract
            analysis = self.deep_analysis.analyze_paper(paper_id, content)
            analysis_results[paper_id] = analysis
            self.paper_db.update_analysis_status(paper_id, "completed")
        
        # Build unified notation
        print("Building unified notation...")
        papers_dict = [p.to_dict() for p in tier1_papers]
        unified_table = self.unified_notation_builder.build_unified_notation(
            papers_dict, paper_contents
        )
        self.unified_notation_table = unified_table
        self.notation_db.store_unified_table(unified_table)
        
        # Build context
        print("Building research context...")
        tier1_paper_ids = [p.arxiv_id or p.title for p in tier1_papers]
        context = self.context_builder.build_context(tier1_paper_ids)
        self.tier1_context = context
        
        self.stage1_complete = True
        
        return {
            'papers': [p.to_dict() for p in tier1_papers],
            'analysis_results': analysis_results,
            'unified_notation': unified_table.to_dict(),
            'context': context,
        }
    
    def get_stage1_results(self) -> Dict:
        """Get Stage 1 results"""
        if not self.stage1_complete:
            return {'status': 'not_complete'}
        
        return {
            'papers': [p.to_dict() for p in self.tier1_papers],
            'unified_notation': self.unified_notation_table.to_dict() if self.unified_notation_table else None,
            'context': self.tier1_context,
        }
    
    def is_stage1_complete(self) -> bool:
        """Check if Stage 1 is complete"""
        return self.stage1_complete
    
    def stage2_search_and_analyze(self, tier2_query: str) -> Dict:
        """
        Stage 2: Search for Tier 2 papers and perform gap analysis.
        
        Args:
            tier2_query: Additional query for Tier 2 papers
            
        Returns:
            Dictionary with Stage 2 results
        """
        if not self.stage1_complete:
            return {'error': 'Stage 1 must be completed first'}
        
        # Generate multiple queries
        print("Generating search queries...")
        queries = self.query_generator.generate_queries(tier2_query, self.tier1_context)
        ranked_queries = self.query_generator.rank_queries(queries, self.tier1_context)
        top_queries = [q for q, _ in ranked_queries[:5]]  # Top 5 queries
        
        # Search with multiple queries
        print("Searching for Tier 2 papers...")
        tier1_paper_ids = [p.arxiv_id or p.title for p in self.tier1_papers]
        tier2_papers = self.multi_query_search.search_and_select(
            top_queries, target_count=40, tier1_paper_ids=tier1_paper_ids
        )
        self.tier2_papers = tier2_papers
        
        # Store Tier 2 papers
        for paper in tier2_papers:
            paper_id = paper.arxiv_id or paper.title
            paper_record = PaperRecord(
                paper_id=paper_id,
                title=paper.title,
                authors=paper.authors,
                abstract=paper.abstract,
                arxiv_id=paper.arxiv_id,
                publication_date=paper.publication_date.isoformat() if paper.publication_date else None,
                citation_count=paper.citation_count,
                url=paper.url,
                source=paper.source,
                tier=2,
                analysis_status="analyzing"
            )
            self.paper_db.add_paper(paper_record)
        
        # Arrange chronologically
        print("Arranging papers chronologically...")
        chronological_papers = self.temporal_arranger.arrange_chronologically(tier2_papers)
        temporal_metadata = self.temporal_arranger.get_temporal_metadata(chronological_papers)
        
        # Perform shallow analysis (chronologically)
        print("Performing shallow gap analysis...")
        all_gap_candidates = []
        processed_paper_ids = []
        
        for paper in chronological_papers:
            paper_id = paper.arxiv_id or paper.title
            gaps = self.shallow_analysis.analyze_paper_chronologically(
                paper_id, tier1_paper_ids, processed_paper_ids
            )
            all_gap_candidates.extend(gaps)
            processed_paper_ids.append(paper_id)
            self.paper_db.update_analysis_status(paper_id, "completed")
        
        # Synthesize gaps
        print("Synthesizing research gaps...")
        prioritized_gaps = self.gap_synthesis.synthesize_gaps(
            all_gap_candidates, tier1_paper_ids
        )
        self.prioritized_gaps = prioritized_gaps
        
        # Generate gap report
        gap_report = self.gap_synthesis.generate_gap_report(prioritized_gaps, top_k=10)
        
        self.stage2_complete = True
        
        return {
            'papers': [p.to_dict() for p in chronological_papers],
            'temporal_metadata': temporal_metadata,
            'gap_candidates_count': len(all_gap_candidates),
            'prioritized_gaps': [
                {
                    'description': pg.gap.description,
                    'priority': pg.priority_score,
                    'novelty': pg.novelty_score,
                    'feasibility': pg.feasibility_score,
                    'impact': pg.impact_score,
                    'evidence_count': len(pg.gap.evidence),
                    'related_papers': pg.gap.related_papers,
                }
                for pg in prioritized_gaps[:10]
            ],
            'gap_report': gap_report,
        }

