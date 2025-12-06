"""
Gradio Interface for Multi-Agent Research Analysis System (LangGraph Version)

Enhanced interface using LangGraph coordinator with LLM-powered analysis.
"""

import gradio as gr
import sys
import os
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.langgraph_coordinator import LangGraphCoordinator
from typing import List, Optional


# Global coordinator instance
coordinator = LangGraphCoordinator()


def stage1_analysis(query: str, seed_papers: str) -> tuple:
    """
    Stage 1: Search and analyze Tier 1 papers using LangGraph.
    
    Args:
        query: Research query
        seed_papers: Comma-separated list of seed papers (arXiv IDs or URLs)
        
    Returns:
        Tuple of outputs for Gradio interface
    """
    seed_list = [s.strip() for s in seed_papers.split(',') if s.strip()] if seed_papers else None
    
    try:
        # Create unique session ID for checkpointing
        session_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": session_id}}
        
        results = coordinator.stage1_search_and_analyze(query, seed_list, config=config)
        
        if "error" in results:
            error_msg = f"Error in Stage 1: {results['error']}"
            return error_msg, "", "", error_msg
        
        # Format papers for display
        papers_text = "## Tier 1 Papers Found:\n\n"
        for i, paper in enumerate(results.get('papers', []), 1):
            papers_text += f"{i}. **{paper['title']}**\n"
            papers_text += f"   Authors: {', '.join(paper.get('authors', [])[:3])}\n"
            papers_text += f"   arXiv ID: {paper.get('arxiv_id', 'N/A')}\n"
            papers_text += f"   Citations: {paper.get('citation_count', 0)}\n\n"
        
        # Format unified notation table
        notation_text = "## Unified Notation Table:\n\n"
        if results.get('unified_notation'):
            notation_data = results['unified_notation']
            entries = notation_data.get('entries', []) if isinstance(notation_data, dict) else []
            for entry in entries[:20]:  # Show first 20
                notation_text += f"**{entry.get('unified_symbol', 'N/A')}** ({entry.get('concept', 'N/A')})\n"
                definition = entry.get('definition', '')
                notation_text += f"  Definition: {definition[:100]}...\n" if definition else "  Definition: N/A\n"
                notation_text += f"  Confidence: {entry.get('confidence', 0):.2f}\n"
                mappings = entry.get('paper_mappings', {})
                if isinstance(mappings, dict):
                    notation_text += f"  Paper mappings: {', '.join(list(mappings.keys())[:3])}\n\n"
        else:
            notation_text += "Notation table being built...\n"
        
        # Format context
        context_text = "## Research Context (LLM-Enhanced):\n\n"
        if results.get('context'):
            ctx = results['context']
            context_text += f"**Themes:** {', '.join(ctx.get('themes', []))}\n\n"
            context_text += f"**Frameworks:** {', '.join(ctx.get('frameworks', []))}\n\n"
            context_text += f"**Concepts:** {', '.join(ctx.get('concepts', [])[:10])}\n\n"
            context_text += f"**Summary:** {ctx.get('summary', 'N/A')}\n"
        else:
            context_text += "Context building in progress...\n"
        
        status = f"Stage 1 Complete! Ready for Stage 2. (Session ID: {session_id[:8]})"
        return papers_text, notation_text, context_text, status
        
    except Exception as e:
        error_msg = f"Error in Stage 1: {str(e)}"
        import traceback
        traceback.print_exc()
        return error_msg, "", "", error_msg


def stage2_analysis(tier2_query: str, session_id: str) -> tuple:
    """
    Stage 2: Search and analyze Tier 2 papers using LangGraph.
    
    Args:
        tier2_query: Additional query for Tier 2 papers
        session_id: Session ID from Stage 1 (for checkpointing)
        
    Returns:
        Tuple of outputs for Gradio interface
    """
    if not tier2_query.strip():
        return "Please enter a query for Tier 2 papers!", "", "", "", "Status: No query provided"
    
    try:
        # Use provided session ID or default
        config = {"configurable": {"thread_id": session_id or f"session_{id(coordinator)}"}}
        
        results = coordinator.stage2_search_and_analyze(tier2_query, config=config)
        
        if 'error' in results:
            return results['error'], "", "", "", f"Error: {results['error']}"
        
        # Format Tier 2 papers
        papers_text = "## Tier 2 Papers Found (Chronologically Ordered):\n\n"
        for i, paper in enumerate(results.get('papers', []), 1):
            papers_text += f"{i}. **{paper['title']}**\n"
            papers_text += f"   Authors: {', '.join(paper.get('authors', [])[:3])}\n"
            papers_text += f"   arXiv ID: {paper.get('arxiv_id', 'N/A')}\n"
            if paper.get('publication_date'):
                papers_text += f"   Date: {paper['publication_date'][:10]}\n"
            papers_text += f"   Citations: {paper.get('citation_count', 0)}\n\n"
        
        # Format temporal metadata
        temporal_info = "## Temporal Analysis:\n\n"
        if results.get('temporal_metadata'):
            tm = results['temporal_metadata']
            if tm.get('year_range'):
                temporal_info += f"**Year Range:** {tm['year_range'][0]} - {tm['year_range'][1]}\n"
                temporal_info += f"**Total Years:** {tm.get('total_years', 'N/A')}\n"
                temporal_info += f"**Total Papers:** {len(results.get('papers', []))}\n\n"
        
        # Format prioritized gaps summary
        gaps_text = "## Prioritized Research Gaps Summary (LLM-Enhanced):\n\n"
        if results.get('prioritized_gaps'):
            gaps_text += f"**Total Gaps Found:** {len(results['prioritized_gaps'])}\n\n"
            gaps_text += "**Top 5 Gaps:**\n\n"
            for i, gap in enumerate(results['prioritized_gaps'][:5], 1):
                gaps_text += f"{i}. {gap.get('description', 'N/A')[:100]}...\n"
                gaps_text += f"   Priority Score: {gap.get('priority', 0):.2f}\n\n"
        else:
            gaps_text += "No gaps identified.\n"
        
        # Full gap report
        gap_report = results.get('gap_report', 'Gap report generation in progress...')
        
        status = f"Stage 2 Complete! Found {len(results.get('papers', []))} papers and {results.get('gap_candidates_count', 0)} gap candidates."
        
        return papers_text, temporal_info, gaps_text, gap_report, status
        
    except Exception as e:
        error_msg = f"Error in Stage 2: {str(e)}"
        import traceback
        traceback.print_exc()
        return error_msg, "", "", "", error_msg


# Create Gradio interface
with gr.Blocks(title="Multi-Agent Research Analysis System (LangGraph)") as demo:
    gr.Markdown("# Multi-Agent Research Analysis System")
    gr.Markdown("**Powered by LangGraph & LangChain** - Analyze theoretical ML papers with deep mathematical understanding and LLM-enhanced analysis")
    
    with gr.Tabs():
        with gr.Tab("Stage 1: Context Building"):
            with gr.Row():
                with gr.Column():
                    stage1_query = gr.Textbox(
                        label="Research Query",
                        placeholder="Enter your research topic (e.g., 'generalization bounds for deep learning')",
                        lines=2
                    )
                    seed_papers_input = gr.Textbox(
                        label="Seed Papers (Optional)",
                        placeholder="Comma-separated arXiv IDs or URLs (e.g., '1234.5678, 2345.6789')",
                        lines=1
                    )
                    stage1_button = gr.Button("Search & Analyze Tier 1 Papers", variant="primary")
                    session_id_output = gr.Textbox(
                        label="Session ID (save this for Stage 2)",
                        interactive=False,
                        visible=True
                    )
                
            with gr.Row():
                with gr.Column():
                    papers_output = gr.Markdown(label="Tier 1 Papers")
                with gr.Column():
                    notation_output = gr.Markdown(label="Unified Notation Table")
            
            with gr.Row():
                context_output = gr.Markdown(label="Research Context (LLM-Enhanced)")
            
            stage1_status = gr.Textbox(label="Status", interactive=False)
            
            def stage1_with_session(query, seed_papers):
                session_id = str(uuid.uuid4())
                results = stage1_analysis(query, seed_papers)
                return (*results, session_id)
            
            stage1_button.click(
                fn=stage1_with_session,
                inputs=[stage1_query, seed_papers_input],
                outputs=[papers_output, notation_output, context_output, stage1_status, session_id_output]
            )
        
        with gr.Tab("Stage 2: Gap Discovery"):
            with gr.Row():
                with gr.Column():
                    stage2_query = gr.Textbox(
                        label="Additional Query for Tier 2 Papers",
                        placeholder="Enter query for related papers (e.g., 'extensions and applications')",
                        lines=2
                    )
                    stage2_session_id = gr.Textbox(
                        label="Session ID from Stage 1",
                        placeholder="Paste the Session ID from Stage 1",
                        lines=1
                    )
                    stage2_button = gr.Button("Search & Analyze Tier 2 Papers", variant="primary")
            
            with gr.Row():
                with gr.Column():
                    stage2_papers_output = gr.Markdown(label="Tier 2 Papers (Chronological)")
                with gr.Column():
                    stage2_temporal_output = gr.Markdown(label="Temporal Analysis")
            
            with gr.Row():
                stage2_gaps_output = gr.Markdown(label="Prioritized Research Gaps (LLM-Enhanced)")
            
            with gr.Row():
                stage2_report_output = gr.Markdown(label="Full Gap Report")
            
            stage2_status = gr.Textbox(label="Status", interactive=False)
            
            stage2_button.click(
                fn=stage2_analysis,
                inputs=[stage2_query, stage2_session_id],
                outputs=[stage2_papers_output, stage2_temporal_output, stage2_gaps_output, 
                        stage2_report_output, stage2_status]
            )


if __name__ == "__main__":
    demo.launch(share=False)

