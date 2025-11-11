"""
Gradio Interface for Multi-Agent Research Analysis System
"""

import gradio as gr
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.coordinator import Coordinator
from typing import List, Optional


# Global coordinator instance
coordinator = Coordinator()


def stage1_analysis(query: str, seed_papers: str) -> tuple:
    """
    Stage 1: Search and analyze Tier 1 papers.
    
    Args:
        query: Research query
        seed_papers: Comma-separated list of seed papers (arXiv IDs or URLs)
        
    Returns:
        Tuple of outputs for Gradio interface
    """
    seed_list = [s.strip() for s in seed_papers.split(',') if s.strip()] if seed_papers else None
    
    try:
        results = coordinator.stage1_search_and_analyze(query, seed_list)
        
        # Format papers for display
        papers_text = "## Tier 1 Papers Found:\n\n"
        for i, paper in enumerate(results['papers'], 1):
            papers_text += f"{i}. **{paper['title']}**\n"
            papers_text += f"   Authors: {', '.join(paper['authors'][:3])}\n"
            papers_text += f"   arXiv ID: {paper.get('arxiv_id', 'N/A')}\n"
            papers_text += f"   Citations: {paper.get('citation_count', 0)}\n\n"
        
        # Format unified notation table
        notation_text = "## Unified Notation Table:\n\n"
        if results.get('unified_notation'):
            notation_data = results['unified_notation']
            for entry in notation_data.get('entries', [])[:20]:  # Show first 20
                notation_text += f"**{entry['unified_symbol']}** ({entry['concept']})\n"
                notation_text += f"  Definition: {entry['definition'][:100]}...\n"
                notation_text += f"  Confidence: {entry['confidence']:.2f}\n"
                notation_text += f"  Paper mappings: {', '.join(entry['paper_mappings'].keys())}\n\n"
        else:
            notation_text += "Notation table being built...\n"
        
        # Format context
        context_text = "## Research Context:\n\n"
        if results.get('context'):
            ctx = results['context']
            context_text += f"**Themes:** {', '.join(ctx.get('themes', []))}\n\n"
            context_text += f"**Frameworks:** {', '.join(ctx.get('frameworks', []))}\n\n"
            context_text += f"**Concepts:** {', '.join(ctx.get('concepts', [])[:10])}\n\n"
            context_text += f"**Summary:** {ctx.get('summary', 'N/A')}\n"
        else:
            context_text += "Context building in progress...\n"
        
        return papers_text, notation_text, context_text, "Stage 1 Complete! Ready for Stage 2."
        
    except Exception as e:
        error_msg = f"Error in Stage 1: {str(e)}"
        return error_msg, "", "", error_msg


def stage2_analysis(tier2_query: str) -> tuple:
    """
    Stage 2: Search and analyze Tier 2 papers.
    
    Args:
        tier2_query: Additional query for Tier 2 papers
        
    Returns:
        Tuple of outputs for Gradio interface
    """
    if not coordinator.is_stage1_complete():
        return "Please complete Stage 1 first!", "", "", "", "Status: Stage 1 not complete"
    
    try:
        results = coordinator.stage2_search_and_analyze(tier2_query)
        
        if 'error' in results:
            return results['error'], "", "", "", f"Error: {results['error']}"
        
        # Format Tier 2 papers
        papers_text = "## Tier 2 Papers Found (Chronologically Ordered):\n\n"
        for i, paper in enumerate(results['papers'], 1):
            papers_text += f"{i}. **{paper['title']}**\n"
            papers_text += f"   Authors: {', '.join(paper['authors'][:3])}\n"
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
                temporal_info += f"**Total Years:** {tm['total_years']}\n"
                temporal_info += f"**Total Papers:** {len(results['papers'])}\n\n"
        
        # Format prioritized gaps summary (brief overview)
        gaps_text = "## Prioritized Research Gaps Summary:\n\n"
        if results.get('prioritized_gaps'):
            gaps_text += f"**Total Gaps Found:** {len(results['prioritized_gaps'])}\n\n"
            gaps_text += "**Top 5 Gaps:**\n\n"
            for i, gap in enumerate(results['prioritized_gaps'][:5], 1):
                gaps_text += f"{i}. {gap['description'][:100]}...\n"
                gaps_text += f"   Priority Score: {gap['priority']:.2f}\n\n"
        else:
            gaps_text += "No gaps identified.\n"
        
        # Full gap report (detailed)
        gap_report = results.get('gap_report', 'Gap report generation in progress...')
        
        status = f"Stage 2 Complete! Found {len(results['papers'])} papers and {results.get('gap_candidates_count', 0)} gap candidates."
        
        return papers_text, temporal_info, gaps_text, gap_report, status
        
    except Exception as e:
        error_msg = f"Error in Stage 2: {str(e)}"
        import traceback
        traceback.print_exc()
        return error_msg, "", "", "", error_msg


# Create Gradio interface
with gr.Blocks(title="Multi-Agent Research Analysis System") as demo:
    gr.Markdown("# Multi-Agent Research Analysis System")
    gr.Markdown("Analyze theoretical ML papers with deep mathematical understanding")
    
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
                
            with gr.Row():
                with gr.Column():
                    papers_output = gr.Markdown(label="Tier 1 Papers")
                with gr.Column():
                    notation_output = gr.Markdown(label="Unified Notation Table")
            
            with gr.Row():
                context_output = gr.Markdown(label="Research Context")
            
            stage1_status = gr.Textbox(label="Status", interactive=False)
            
            stage1_button.click(
                fn=stage1_analysis,
                inputs=[stage1_query, seed_papers_input],
                outputs=[papers_output, notation_output, context_output, stage1_status]
            )
        
        with gr.Tab("Stage 2: Gap Discovery"):
            with gr.Row():
                with gr.Column():
                    stage2_query = gr.Textbox(
                        label="Additional Query for Tier 2 Papers",
                        placeholder="Enter query for related papers (e.g., 'extensions and applications')",
                        lines=2
                    )
                    stage2_button = gr.Button("Search & Analyze Tier 2 Papers", variant="primary")
            
            with gr.Row():
                with gr.Column():
                    stage2_papers_output = gr.Markdown(label="Tier 2 Papers (Chronological)")
                with gr.Column():
                    stage2_temporal_output = gr.Markdown(label="Temporal Analysis")
            
            with gr.Row():
                stage2_gaps_output = gr.Markdown(label="Prioritized Research Gaps")
            
            with gr.Row():
                stage2_report_output = gr.Markdown(label="Full Gap Report")
            
            stage2_status = gr.Textbox(label="Status", interactive=False)
            
            stage2_button.click(
                fn=stage2_analysis,
                inputs=[stage2_query],
                outputs=[stage2_papers_output, stage2_temporal_output, stage2_gaps_output, 
                        stage2_report_output, stage2_status]
            )


if __name__ == "__main__":
    demo.launch(share=False)

