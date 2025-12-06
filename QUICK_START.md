# Quick Start Guide

Get started with the LangGraph-powered Multi-Agent Research Analysis System in 5 minutes!

## Prerequisites

- Python 3.10 or 3.11
- OpenAI API key

## Setup

1. **Clone and install:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Set your API key:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. **Run the interface:**
```bash
python interface/gradio_app_langgraph.py
```

4. **Open your browser:**
Navigate to `http://localhost:7860`

## Usage

### Stage 1: Context Building

1. Enter a research query (e.g., "generalization bounds for deep learning")
2. Optionally add seed papers (arXiv IDs separated by commas)
3. Click "Search & Analyze Tier 1 Papers"
4. **Save the Session ID** that appears in the status message

### Stage 2: Gap Discovery

1. Enter an additional query for Tier 2 papers (e.g., "extensions and applications")
2. **Paste the Session ID from Stage 1**
3. Click "Search & Analyze Tier 2 Papers"
4. Review the prioritized research gaps!

## What You Get

- **Tier 1 Papers**: Top 10 most relevant papers with deep analysis
- **Unified Notation Table**: Resolved notation conflicts across papers
- **LLM-Enhanced Context**: Intelligent synthesis of themes, frameworks, and concepts
- **Tier 2 Papers**: 40 related papers arranged chronologically
- **Prioritized Gaps**: Research gaps scored by novelty, feasibility, and impact

## Tips

- Use specific queries for better results
- The Session ID enables checkpointing - use it to resume workflows
- LLM calls add latency but improve quality
- Check the "Full Gap Report" for detailed analysis

## Troubleshooting

**"OpenAI API key not found"**
→ Set `OPENAI_API_KEY` environment variable

**"Stage 1 not complete" in Stage 2**
→ Make sure you're using the Session ID from Stage 1

**Slow responses**
→ LLM calls take time. The system shows progress messages.

## Next Steps

- Read the full [README.md](README.md) for architecture details
- Check [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) if migrating from old coordinator
- Explore the code in `agents/langgraph_coordinator.py`

Happy researching! 🚀

