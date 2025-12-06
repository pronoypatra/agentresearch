"""
State Schema for LangGraph Multi-Agent System

Defines the state structure for the research analysis workflow.
"""

from typing import TypedDict, List, Optional, Dict, Any
from agents.stage1_paper_search_agent import PaperMetadata


class ResearchAnalysisState(TypedDict):
    """
    State schema for the multi-agent research analysis system.
    
    This state is passed between nodes in the LangGraph workflow.
    """
    # User inputs
    query: str
    seed_papers: Optional[List[str]]
    tier2_query: Optional[str]
    
    # Stage 1 results
    tier1_papers: List[PaperMetadata]
    tier1_analysis_results: Dict[str, Any]
    unified_notation_table: Optional[Dict[str, Any]]
    tier1_context: Optional[Dict[str, Any]]
    stage1_complete: bool
    
    # Stage 2 results
    generated_queries: List[str]
    tier2_papers: List[PaperMetadata]
    chronological_papers: List[PaperMetadata]
    temporal_metadata: Optional[Dict[str, Any]]
    gap_candidates: List[Any]
    prioritized_gaps: List[Any]
    gap_report: Optional[str]
    stage2_complete: bool
    
    # Error handling
    error: Optional[str]
    current_step: str
    
    # Metadata
    session_id: Optional[str]

