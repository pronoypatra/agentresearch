# Multi-Agent Research Analysis System

An interactive multi-agent system for analyzing theoretical ML papers with deep mathematical understanding, unified notation resolution, and research gap identification. Enhanced with LLM-powered analysis for superior results.

## Features

- **Two-Stage Analysis**: Deep analysis of top papers (Tier 1) followed by gap discovery in related papers (Tier 2)
- **Unified Notation Resolution**: Automatically resolves notation conflicts across papers
- **Mathematical Analysis**: Extracts theorems, proofs, definitions, and bounds
- **Temporal Evolution Tracking**: Analyzes how research evolves over time chronologically
- **Research Gap Identification**: Finds missing connections, contradictions, extensions, and open problems
- **Interactive Gradio Interface**: User-friendly web interface for both stages
- **Multi-Query Search**: Generates diverse queries and finds optimal paper sets
- **Gap Prioritization**: Scores gaps by novelty, feasibility, impact, and evidence strength

## Architecture

### Stage 1: Context Building
1. **Paper Search**: Searches arXiv and Semantic Scholar for top 10 relevant papers
2. **Deep Analysis**: Complete mathematical analysis of each paper (theorems, definitions, bounds, assumptions)
3. **Unified Notation**: Builds canonical notation from all Tier 1 papers with user-displayable table
4. **Context Building**: Synthesizes research themes, frameworks, and concepts

### Stage 2: Gap Discovery
1. **Query Generation**: Uses Tier 1 context to generate diverse search queries (themes, frameworks, extensions)
2. **Multi-Query Search**: Executes multiple queries and finds optimal set of 40 Tier 2 papers
3. **Temporal Arrangement**: Orders papers chronologically and builds citation timeline
4. **Shallow Analysis**: Quick gap detection in Tier 2 papers (processed chronologically)
5. **Gap Synthesis**: Aggregates, validates, and prioritizes research gaps with scoring

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key (required for LLM features)
export OPENAI_API_KEY="your-api-key-here"
# Or create .env file with: OPENAI_API_KEY=your-api-key-here
```

**Note**: The system uses LangGraph for orchestration and LangChain for LLM-powered analysis. Make sure to set your OpenAI API key.

## Usage

### Running the Gradio Interface

**LangGraph Version (Recommended):**
```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the LangGraph-powered interface
python interface/gradio_app_langgraph.py
```

**Legacy Version:**
```bash
python interface/gradio_app.py
```

The interface will launch at `http://localhost:7860`

**Key Features of LangGraph Version:**
- LLM-enhanced context building and gap analysis
- Session-based checkpointing
- Better error handling
- Improved query generation

**Workflow:**
1. **Stage 1 Tab**: Enter research query and optional seed papers
   - System searches for top 10 Tier 1 papers
   - Performs deep mathematical analysis
   - Builds unified notation table
   - Synthesizes research context
2. **Stage 2 Tab**: Enter additional query for Tier 2 papers
   - System generates multiple search queries
   - Finds optimal 40 Tier 2 papers
   - Arranges chronologically
   - Performs gap analysis
   - Displays prioritized research gaps

### Using the API

**LangGraph Coordinator (Recommended):**
```python
from agents.langgraph_coordinator import LangGraphCoordinator

coordinator = LangGraphCoordinator(llm_model="gpt-4o-mini")
config = {"configurable": {"thread_id": "my_session"}}

# Stage 1: Search and analyze Tier 1 papers
results = coordinator.stage1_search_and_analyze(
    query="generalization bounds for deep learning",
    seed_papers=["1234.5678", "2345.6789"],  # Optional
    config=config
)

# Access Stage 1 results
papers = results['papers']
unified_notation = results['unified_notation']
context = results['context']

# Stage 2: Search and analyze Tier 2 papers (use same config)
stage2_results = coordinator.stage2_search_and_analyze(
    tier2_query="extensions and applications",
    config=config  # Same thread_id for checkpointing
)
```

**Legacy Coordinator:**
```python
from agents.coordinator import Coordinator

coordinator = Coordinator()
results = coordinator.stage1_search_and_analyze(
    query="generalization bounds for deep learning",
    seed_papers=["1234.5678", "2345.6789"]
)

# Access Stage 2 results
tier2_papers = stage2_results['papers']
prioritized_gaps = stage2_results['prioritized_gaps']
gap_report = stage2_results['gap_report']
temporal_metadata = stage2_results['temporal_metadata']
```

## Project Structure

```
.
├── agents/                      # Agent implementations
│   ├── coordinator.py          # Main orchestrator (Stage 1 & 2)
│   ├── stage1_paper_search_agent.py  # Tier 1 paper search
│   ├── deep_analysis_agent.py       # Tier 1 deep analysis
│   ├── context_builder.py            # Research context synthesis
│   ├── ranking_agent.py              # Adaptive ranking
│   ├── query_generation_agent.py    # Stage 2 query generation
│   ├── multi_query_search_agent.py   # Stage 2 multi-query search
│   ├── temporal_arrangement_agent.py # Chronological arrangement
│   ├── shallow_analysis_agent.py     # Tier 2 gap detection
│   └── gap_synthesis_agent.py        # Gap prioritization
├── knowledge_base/             # Data storage
│   ├── paper_db.py            # Paper metadata storage
│   ├── theorem_db.py          # Theorems and definitions
│   ├── notation_db.py         # Unified notation storage
│   ├── gap_db.py              # Research gaps storage
│   └── temporal_graph.py      # Temporal relationships
├── notation_resolution/         # Notation system
│   ├── extractor.py           # Notation extraction
│   ├── catalog.py             # Notation catalog & ontology
│   ├── disambiguator.py       # Context-aware disambiguation
│   ├── mapper.py             # Cross-paper notation mapping
│   └── unified_notation_builder.py  # Unified notation creation
├── interface/                   # User interface
│   └── gradio_app.py         # Gradio web interface
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## Components

### Stage 1 Agents

**Paper Search Agent**
- Multi-source search (arXiv, Semantic Scholar)
- Seed paper support
- Relevance ranking with citations and recency

**Deep Analysis Agent**
- Theorem extraction from LaTeX
- Definition extraction
- Complexity bound identification
- Assumption extraction
- Dependency graph building
- Contribution and theme extraction

**Unified Notation Builder**
- Extracts notations from all Tier 1 papers
- Resolves conflicts and ambiguities
- Creates canonical notation table
- Generates user-friendly notation mapping for display

**Context Builder**
- Synthesizes insights from Tier 1 analysis
- Extracts research themes and frameworks
- Identifies key concepts and research directions

### Stage 2 Agents

**Query Generation Agent**
- Generates diverse search queries from Tier 1 context
- Creates variations based on themes, frameworks, concepts
- Ranks queries by importance and diversity

**Multi-Query Search Agent**
- Executes multiple search queries
- Selects optimal set of 40 Tier 2 papers
- Ensures diversity and relevance
- Excludes Tier 1 papers

**Temporal Arrangement Agent**
- Arranges papers chronologically
- Builds citation timeline
- Identifies temporal clusters
- Provides temporal metadata

**Shallow Analysis Agent**
- Quick parsing of Tier 2 papers (abstract, intro, conclusion)
- Gap detection: missing connections, contradictions, extensions
- Open problem identification
- Under-explored area detection
- Processes papers chronologically

**Gap Synthesis Agent**
- Aggregates similar gaps
- Validates gaps against Tier 1 analysis
- Computes novelty, feasibility, impact scores
- Prioritizes gaps
- Generates formatted gap reports

### Knowledge Base
- **Paper Database**: Metadata and content storage
- **Theorem Database**: Mathematical components storage
- **Notation Database**: Unified notation storage
- **Gap Database**: Research gaps storage
- **Temporal Graph**: Evolution and citation relationships

## Current Status

**LangGraph Version:**
- LangGraph state machine orchestration with checkpointing
- LangChain LLM integration for enhanced analysis
- LLM-powered context building and query generation
- Session-based state persistence
- Enhanced error handling and observability
- Stage 1: Paper search, deep analysis, unified notation, LLM-enhanced context building
- Stage 2: LLM-enhanced query generation, multi-query search, temporal arrangement, shallow analysis, gap synthesis
- Knowledge base: All storage components
- Gradio interface: Both Stage 1 and Stage 2 with LangGraph support

**Legacy Implementation:**
- Stage 1: Paper search, deep analysis, unified notation, context building
- Stage 2: Query generation, multi-query search, temporal arrangement, shallow analysis, gap synthesis
- Knowledge base: All storage components
- Gradio interface: Both Stage 1 and Stage 2

**Future Enhancements:**
- Mathematical Relation Graph (MRG) with embeddings
- Evaluation framework with quantitative metrics
- Enhanced theorem/proof extraction
- Interactive visualization of knowledge graphs
- Learning from user feedback
- Database-backed checkpointing for production
- LangSmith integration for observability

## Key Features in Detail

### Unified Notation System
- Automatically extracts mathematical notations from LaTeX papers
- Resolves ambiguities (e.g., λ for regularization vs eigenvalue)
- Maps equivalent notations across papers (e.g., w ↔ β for parameters)
- Creates canonical notation table for user review
- Prevents confusion when comparing papers with different notation conventions

### Gap Detection Types
1. **Missing Connections**: Papers that should cite each other but don't
2. **Contradictions**: Conflicting theoretical results
3. **Extensions**: Natural generalizations not explored
4. **Open Problems**: Explicitly stated unsolved questions
5. **Under-explored Areas**: Promising directions not pursued

### Gap Prioritization
Gaps are scored on multiple dimensions:
- **Novelty**: Distance from existing Tier 1/Tier 2 content
- **Feasibility**: Theoretical tractability
- **Impact**: Importance of questions addressed
- **Evidence Strength**: Number of evidence items and related papers

### Temporal Evolution
- Papers processed in chronological order
- Citation timeline construction
- Temporal cluster identification
- Evolution pattern detection

## Future Enhancements

1. **Mathematical Relation Graph (MRG)**: Embedding-based relationship detection using MathBERT/TangentCFT
2. **Evaluation Framework**: Quantitative metrics (relevance, diversity, novelty, temporal coherence)
3. **Enhanced Analysis**: More sophisticated theorem and proof extraction with formal verification
4. **Visualization**: Interactive knowledge graphs and evolution timelines
5. **Learning**: Improve from user feedback and corrections
6. **PDF Processing**: Direct PDF parsing for full paper content
7. **LLM Integration**: Enhanced query generation and analysis using large language models

## Technical Notes

- The system currently works with abstracts and basic content. For full functionality, PDF/LaTeX parsing would enhance results.
- Some components use simplified algorithms (e.g., regex-based theorem extraction); full implementation would use more sophisticated NLP.
- The system is designed to be extensible - new agents and analysis methods can be easily added.

## Contributing

This is an active research project. Contributions welcome!


