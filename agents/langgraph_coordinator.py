"""
LangGraph-based Coordinator for Multi-Agent Research Analysis System

Uses LangGraph StateGraph for orchestration with proper state management,
checkpointing, and observability.
"""

from typing import Dict, List, Optional, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
import operator

from .state import ResearchAnalysisState
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


class LangGraphCoordinator:
    """
    LangGraph-based coordinator for the research analysis system.
    
    Features:
    - State machine orchestration with LangGraph
    - LLM-powered analysis with LangChain
    - Checkpointing for resumable workflows
    - Error handling and recovery
    - Observability and debugging
    """
    
    def __init__(self, llm_model: str = "gpt-4o-mini", temperature: float = 0.3):
        """
        Initialize LangGraph coordinator.
        
        Args:
            llm_model: OpenAI model to use (default: gpt-4o-mini for cost efficiency)
            temperature: Temperature for LLM calls
        """
        # Initialize LLM
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)
        
        # Initialize knowledge bases
        self.paper_db = PaperDB()
        self.theorem_db = TheoremDB()
        self.notation_db = NotationDB()
        self.gap_db = GapDB()
        self.temporal_graph = TemporalGraph()
        
        # Initialize agents
        self.paper_search = Stage1PaperSearchAgent(max_results=10)
        self.deep_analysis = DeepAnalysisAgent(self.theorem_db)
        self.context_builder = ContextBuilder(self.theorem_db, self.paper_db)
        self.unified_notation_builder = UnifiedNotationBuilder()
        self.query_generator = QueryGenerationAgent(self.context_builder)
        self.multi_query_search = MultiQuerySearchAgent(self.paper_search, self.paper_db)
        self.temporal_arranger = TemporalArrangementAgent(self.paper_db, self.temporal_graph)
        self.shallow_analysis = ShallowAnalysisAgent(
            self.paper_db, self.theorem_db, self.gap_db, self.temporal_graph
        )
        self.gap_synthesis = GapSynthesisAgent(self.gap_db, self.paper_db, self.theorem_db)
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
        
        # Compile with checkpointing
        self.checkpointer = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph state machine workflow"""
        # Use reducer to merge state updates
        def reducer(left: Dict, right: Dict) -> Dict:
            """Merge state updates"""
            result = left.copy()
            for key, value in right.items():
                if value is not None:
                    result[key] = value
            return result
        
        workflow = StateGraph(ResearchAnalysisState)
        
        # Stage 1 nodes
        workflow.add_node("search_tier1_papers", self._search_tier1_papers)
        workflow.add_node("analyze_tier1_papers", self._analyze_tier1_papers)
        workflow.add_node("build_unified_notation", self._build_unified_notation)
        workflow.add_node("build_context", self._build_context_llm)
        
        # Stage 2 nodes
        workflow.add_node("generate_queries", self._generate_queries_llm)
        workflow.add_node("search_tier2_papers", self._search_tier2_papers)
        workflow.add_node("arrange_temporally", self._arrange_temporally)
        workflow.add_node("analyze_tier2_papers", self._analyze_tier2_papers)
        workflow.add_node("synthesize_gaps", self._synthesize_gaps_llm)
        
        # Set entry point
        workflow.set_entry_point("search_tier1_papers")
        
        # Stage 1 flow
        workflow.add_edge("search_tier1_papers", "analyze_tier1_papers")
        workflow.add_edge("analyze_tier1_papers", "build_unified_notation")
        workflow.add_edge("build_unified_notation", "build_context")
        workflow.add_edge("build_context", END)
        
        # Stage 2 flow (conditional - only if tier2_query is provided)
        workflow.add_conditional_edges(
            "build_context",
            self._should_continue_to_stage2,
            {
                "continue": "generate_queries",
                "end": END
            }
        )
        
        workflow.add_edge("generate_queries", "search_tier2_papers")
        workflow.add_edge("search_tier2_papers", "arrange_temporally")
        workflow.add_edge("arrange_temporally", "analyze_tier2_papers")
        workflow.add_edge("analyze_tier2_papers", "synthesize_gaps")
        workflow.add_edge("synthesize_gaps", END)
        
        return workflow
    
    def _should_continue_to_stage2(self, state: ResearchAnalysisState) -> str:
        """Conditional edge: continue to Stage 2 if tier2_query is provided"""
        if state.get("tier2_query") and state.get("stage1_complete"):
            return "continue"
        return "end"
    
    # Stage 1 Node Functions
    def _search_tier1_papers(self, state: ResearchAnalysisState) -> Dict:
        """Search for Tier 1 papers"""
        try:
            query = state["query"]
            seed_papers = state.get("seed_papers")
            
            print(f"[LangGraph] Searching for Tier 1 papers: {query}")
            tier1_papers = self.paper_search.search(query, seed_papers)
            
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
            
            return {
                "tier1_papers": tier1_papers,
                "current_step": "search_tier1_papers"
            }
        except Exception as e:
            return {"error": str(e), "current_step": "search_tier1_papers"}
    
    def _analyze_tier1_papers(self, state: ResearchAnalysisState) -> Dict:
        """Perform deep analysis of Tier 1 papers"""
        try:
            tier1_papers = state["tier1_papers"]
            analysis_results = {}
            
            print(f"[LangGraph] Analyzing {len(tier1_papers)} Tier 1 papers...")
            
            for paper in tier1_papers:
                paper_id = paper.arxiv_id or paper.title
                content = paper.abstract  # In production, would fetch full content
                analysis = self.deep_analysis.analyze_paper(paper_id, content)
                analysis_results[paper_id] = analysis
                self.paper_db.update_analysis_status(paper_id, "completed")
            
            return {
                "tier1_analysis_results": analysis_results,
                "current_step": "analyze_tier1_papers"
            }
        except Exception as e:
            return {"error": str(e), "current_step": "analyze_tier1_papers"}
    
    def _build_unified_notation(self, state: ResearchAnalysisState) -> Dict:
        """Build unified notation table"""
        try:
            tier1_papers = state["tier1_papers"]
            
            print("[LangGraph] Building unified notation table...")
            
            papers_dict = [p.to_dict() for p in tier1_papers]
            paper_contents = {}  # In production, would fetch full content
            unified_table = self.unified_notation_builder.build_unified_notation(
                papers_dict, paper_contents
            )
            
            self.notation_db.store_unified_table(unified_table)
            
            return {
                "unified_notation_table": unified_table.to_dict() if unified_table else None,
                "current_step": "build_unified_notation"
            }
        except Exception as e:
            return {"error": str(e), "current_step": "build_unified_notation"}
    
    def _build_context_llm(self, state: ResearchAnalysisState) -> Dict:
        """Build research context using LLM-enhanced analysis"""
        try:
            tier1_papers = state["tier1_papers"]
            tier1_analysis = state.get("tier1_analysis_results", {})
            
            print("[LangGraph] Building research context with LLM...")
            
            # Get traditional context
            tier1_paper_ids = [p.arxiv_id or p.title for p in tier1_papers]
            base_context = self.context_builder.build_context(tier1_paper_ids)
            
            # Enhance with LLM
            papers_summary = "\n".join([
                f"- {p.title}: {p.abstract[:200]}..." 
                for p in tier1_papers[:5]
            ])
            
            themes_summary = ", ".join(base_context.get("themes", [])[:5])
            frameworks_summary = ", ".join(base_context.get("frameworks", [])[:3])
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert in theoretical machine learning research analysis.
Analyze the provided research papers and extract:
1. Key research themes and patterns
2. Theoretical frameworks used
3. Important mathematical concepts
4. Research directions and potential extensions
5. Connections between papers

Provide a structured analysis in JSON format."""),
                ("human", """Analyze these Tier 1 research papers:

Papers:
{papers}

Current themes: {themes}
Current frameworks: {frameworks}

Provide enhanced analysis with:
- Refined themes (more specific and insightful)
- Key concepts (mathematical and theoretical)
- Research directions (specific and actionable)
- Frameworks (with brief descriptions)
- Summary (2-3 sentences synthesizing the research landscape)

Format as JSON with keys: themes, concepts, frameworks, research_directions, summary""")
            ])
            
            chain = prompt | self.llm | JsonOutputParser()
            
            try:
                llm_enhanced = chain.invoke({
                    "papers": papers_summary,
                    "themes": themes_summary,
                    "frameworks": frameworks_summary
                })
                
                # Merge LLM insights with base context
                enhanced_context = {
                    **base_context,
                    "themes": llm_enhanced.get("themes", base_context.get("themes", [])),
                    "concepts": llm_enhanced.get("concepts", base_context.get("concepts", [])),
                    "frameworks": llm_enhanced.get("frameworks", base_context.get("frameworks", [])),
                    "research_directions": llm_enhanced.get("research_directions", base_context.get("research_directions", [])),
                    "summary": llm_enhanced.get("summary", base_context.get("summary", ""))
                }
            except Exception as e:
                print(f"[LangGraph] LLM enhancement failed, using base context: {e}")
                enhanced_context = base_context
            
            return {
                "tier1_context": enhanced_context,
                "stage1_complete": True,
                "current_step": "build_context"
            }
        except Exception as e:
            return {"error": str(e), "current_step": "build_context"}
    
    # Stage 2 Node Functions
    def _generate_queries_llm(self, state: ResearchAnalysisState) -> Dict:
        """Generate search queries using LLM"""
        try:
            tier2_query = state.get("tier2_query", "")
            tier1_context = state.get("tier1_context", {})
            
            print("[LangGraph] Generating search queries with LLM...")
            
            # Get base queries from traditional agent
            base_queries = self.query_generator.generate_queries(tier2_query, tier1_context)
            
            # Enhance with LLM
            context_summary = tier1_context.get("summary", "")
            themes = ", ".join(tier1_context.get("themes", [])[:5])
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at generating diverse, effective search queries for academic paper discovery.
Generate queries that will find papers related to the research context but explore different angles:
- Extensions and generalizations
- Applications and use cases
- Alternative approaches
- Historical evolution
- Open problems

Generate 5-7 diverse queries that complement the base queries."""),
                ("human", """Base query: {base_query}

Research context: {context}

Key themes: {themes}

Generate 5-7 diverse search queries (one per line, no numbering) that will help discover related papers from different angles.""")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            
            try:
                llm_queries_text = chain.invoke({
                    "base_query": tier2_query,
                    "context": context_summary,
                    "themes": themes
                })
                
                # Parse LLM queries (one per line)
                llm_queries = [q.strip() for q in llm_queries_text.strip().split("\n") if q.strip()]
                llm_queries = [q for q in llm_queries if not q[0].isdigit()]  # Remove numbering
                
                # Combine and deduplicate
                all_queries = base_queries + llm_queries
                seen = set()
                unique_queries = []
                for q in all_queries:
                    q_lower = q.lower()
                    if q_lower not in seen:
                        seen.add(q_lower)
                        unique_queries.append(q)
                
                # Rank queries
                ranked = self.query_generator.rank_queries(unique_queries, tier1_context)
                top_queries = [q for q, _ in ranked[:7]]  # Top 7 queries
            except Exception as e:
                print(f"[LangGraph] LLM query generation failed, using base queries: {e}")
                ranked = self.query_generator.rank_queries(base_queries, tier1_context)
                top_queries = [q for q, _ in ranked[:5]]
            
            return {
                "generated_queries": top_queries,
                "current_step": "generate_queries"
            }
        except Exception as e:
            return {"error": str(e), "current_step": "generate_queries"}
    
    def _search_tier2_papers(self, state: ResearchAnalysisState) -> Dict:
        """Search for Tier 2 papers"""
        try:
            queries = state.get("generated_queries", [])
            tier1_papers = state.get("tier1_papers", [])
            
            print(f"[LangGraph] Searching for Tier 2 papers with {len(queries)} queries...")
            
            tier1_paper_ids = [p.arxiv_id or p.title for p in tier1_papers]
            tier2_papers = self.multi_query_search.search_and_select(
                queries, target_count=40, tier1_paper_ids=tier1_paper_ids
            )
            
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
            
            return {
                "tier2_papers": tier2_papers,
                "current_step": "search_tier2_papers"
            }
        except Exception as e:
            return {"error": str(e), "current_step": "search_tier2_papers"}
    
    def _arrange_temporally(self, state: ResearchAnalysisState) -> Dict:
        """Arrange papers chronologically"""
        try:
            tier2_papers = state.get("tier2_papers", [])
            
            print("[LangGraph] Arranging papers chronologically...")
            
            chronological_papers = self.temporal_arranger.arrange_chronologically(tier2_papers)
            temporal_metadata = self.temporal_arranger.get_temporal_metadata(chronological_papers)
            
            return {
                "chronological_papers": chronological_papers,
                "temporal_metadata": temporal_metadata,
                "current_step": "arrange_temporally"
            }
        except Exception as e:
            return {"error": str(e), "current_step": "arrange_temporally"}
    
    def _analyze_tier2_papers(self, state: ResearchAnalysisState) -> Dict:
        """Analyze Tier 2 papers for gaps"""
        try:
            chronological_papers = state.get("chronological_papers", [])
            tier1_papers = state.get("tier1_papers", [])
            
            print(f"[LangGraph] Analyzing {len(chronological_papers)} Tier 2 papers...")
            
            tier1_paper_ids = [p.arxiv_id or p.title for p in tier1_papers]
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
            
            return {
                "gap_candidates": all_gap_candidates,
                "current_step": "analyze_tier2_papers"
            }
        except Exception as e:
            return {"error": str(e), "current_step": "analyze_tier2_papers"}
    
    def _synthesize_gaps_llm(self, state: ResearchAnalysisState) -> Dict:
        """Synthesize and prioritize gaps using LLM"""
        try:
            gap_candidates = state.get("gap_candidates", [])
            tier1_papers = state.get("tier1_papers", [])
            
            print(f"[LangGraph] Synthesizing {len(gap_candidates)} gap candidates...")
            
            # Traditional synthesis
            tier1_paper_ids = [p.arxiv_id or p.title for p in tier1_papers]
            prioritized_gaps = self.gap_synthesis.synthesize_gaps(
                gap_candidates, tier1_paper_ids
            )
            
            # Enhance gap descriptions with LLM
            if prioritized_gaps and len(prioritized_gaps) > 0:
                top_gaps_summary = "\n".join([
                    f"{i+1}. {pg.gap.description[:150]}..." 
                    for i, pg in enumerate(prioritized_gaps[:5])
                ])
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are an expert research analyst. Review the identified research gaps and provide:
1. Refined, clearer descriptions
2. Better prioritization reasoning
3. Actionable insights

Maintain the technical accuracy while improving clarity."""),
                    ("human", """Review these research gaps:

{top_gaps}

Provide refined descriptions and insights for the top gaps. Keep descriptions concise (1-2 sentences each).""")
                ])
                
                try:
                    chain = prompt | self.llm | StrOutputParser()
                    llm_insights = chain.invoke({"top_gaps": top_gaps_summary})
                    # Could integrate insights into gap descriptions
                except Exception as e:
                    print(f"[LangGraph] LLM gap enhancement failed: {e}")
            
            # Generate gap report
            gap_report = self.gap_synthesis.generate_gap_report(prioritized_gaps, top_k=10)
            
            return {
                "prioritized_gaps": [
                    {
                        "description": pg.gap.description,
                        "priority": pg.priority_score,
                        "novelty": pg.novelty_score,
                        "feasibility": pg.feasibility_score,
                        "impact": pg.impact_score,
                        "evidence_count": len(pg.gap.evidence),
                        "related_papers": pg.gap.related_papers,
                    }
                    for pg in prioritized_gaps[:10]
                ],
                "gap_report": gap_report,
                "stage2_complete": True,
                "current_step": "synthesize_gaps"
            }
        except Exception as e:
            return {"error": str(e), "current_step": "synthesize_gaps"}
    
    # Public API Methods
    def stage1_search_and_analyze(self, query: str, seed_papers: Optional[List[str]] = None, 
                                 config: Optional[Dict] = None) -> Dict:
        """
        Execute Stage 1: Search and analyze Tier 1 papers.
        
        Args:
            query: Research query
            seed_papers: Optional seed papers
            config: Optional LangGraph config (for checkpointing)
            
        Returns:
            Dictionary with Stage 1 results
        """
        initial_state: ResearchAnalysisState = {
            "query": query,
            "seed_papers": seed_papers,
            "tier2_query": None,
            "tier1_papers": [],
            "tier1_analysis_results": {},
            "unified_notation_table": None,
            "tier1_context": None,
            "stage1_complete": False,
            "generated_queries": [],
            "tier2_papers": [],
            "chronological_papers": [],
            "temporal_metadata": None,
            "gap_candidates": [],
            "prioritized_gaps": [],
            "gap_report": None,
            "stage2_complete": False,
            "error": None,
            "current_step": "start",
            "session_id": config.get("configurable", {}).get("thread_id") if config else None
        }
        
        config = config or {"configurable": {"thread_id": f"session_{id(self)}"}}
        
        # Run workflow and collect final state
        final_state = None
        for state in self.app.stream(initial_state, config=config):
            # State is a dict with node names as keys
            for node_name, node_state in state.items():
                final_state = node_state
                # Check if Stage 1 is complete
                if node_state.get("stage1_complete"):
                    break
        
        if final_state and final_state.get("stage1_complete"):
            return {
                "papers": [p.to_dict() for p in final_state.get("tier1_papers", [])],
                "analysis_results": final_state.get("tier1_analysis_results", {}),
                "unified_notation": final_state.get("unified_notation_table"),
                "context": final_state.get("tier1_context"),
            }
        
        return {"error": "Workflow execution failed or incomplete"}
    
    def stage2_search_and_analyze(self, tier2_query: str, config: Optional[Dict] = None) -> Dict:
        """
        Execute Stage 2: Search and analyze Tier 2 papers.
        
        Args:
            tier2_query: Additional query for Tier 2 papers
            config: Optional LangGraph config (should use same thread_id as Stage 1)
            
        Returns:
            Dictionary with Stage 2 results
        """
        config = config or {"configurable": {"thread_id": f"session_{id(self)}"}}
        
        # Continue workflow with tier2_query
        # The workflow will pick up from checkpoint if available
        initial_state = {
            "tier2_query": tier2_query,
        }
        
        final_state = None
        for state in self.app.stream(initial_state, config=config):
            for node_name, node_state in state.items():
                final_state = node_state
                if node_state.get("stage2_complete"):
                    break
        
        if final_state and final_state.get("stage2_complete"):
            return {
                "papers": [p.to_dict() for p in final_state.get("chronological_papers", [])],
                "temporal_metadata": final_state.get("temporal_metadata"),
                "gap_candidates_count": len(final_state.get("gap_candidates", [])),
                "prioritized_gaps": final_state.get("prioritized_gaps", []),
                "gap_report": final_state.get("gap_report"),
            }
        
        return {"error": "Stage 2 execution failed or Stage 1 not complete"}
    
    def is_stage1_complete(self, config: Optional[Dict] = None) -> bool:
        """Check if Stage 1 is complete by reading checkpoint state"""
        # Simplified implementation - in production would read from checkpoint
        return False

