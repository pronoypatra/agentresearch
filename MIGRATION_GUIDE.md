# Migration Guide: LangGraph & LangChain Integration

This guide explains the new LangGraph-based architecture and how to migrate from the old coordinator.

## What's New

### 1. **LangGraph State Machine Orchestration**
- **Before**: Manual coordinator with simple state tracking
- **After**: LangGraph StateGraph with proper state management, checkpointing, and visualization

### 2. **LLM-Powered Analysis**
- **Before**: Rule-based analysis only
- **After**: LangChain integration for enhanced:
  - Context building (themes, frameworks, concepts)
  - Query generation (diverse, intelligent queries)
  - Gap synthesis (refined descriptions and insights)

### 3. **Checkpointing & Resumability**
- **Before**: No state persistence
- **After**: Memory-based checkpointing allows resuming workflows

### 4. **Better Error Handling**
- **Before**: Basic error handling
- **After**: Structured error handling with state tracking

## Architecture Changes

### Old Architecture
```
Coordinator (Python class)
├── Manual state management
├── Sequential method calls
└── No persistence
```

### New Architecture
```
LangGraphCoordinator
├── LangGraph StateGraph
│   ├── State nodes (search, analyze, synthesize)
│   ├── Conditional edges
│   └── Checkpointing
├── LangChain LLM integration
│   ├── Enhanced context building
│   ├── Intelligent query generation
│   └── Gap refinement
└── Memory checkpointing
```

## Migration Steps

### 1. Update Dependencies

```bash
pip install -r requirements.txt
```

The requirements have been updated with:
- `langchain>=0.3.0`
- `langchain-openai>=0.2.0`
- `langchain-core>=0.3.0`
- `langgraph>=0.2.0`

### 2. Update Your Code

#### Old Way:
```python
from agents.coordinator import Coordinator

coordinator = Coordinator()
results = coordinator.stage1_search_and_analyze(query, seed_papers)
```

#### New Way:
```python
from agents.langgraph_coordinator import LangGraphCoordinator

coordinator = LangGraphCoordinator(llm_model="gpt-4o-mini")
config = {"configurable": {"thread_id": "my_session"}}
results = coordinator.stage1_search_and_analyze(query, seed_papers, config=config)
```

### 3. Using the New Gradio Interface

Run the new LangGraph-powered interface:

```bash
python interface/gradio_app_langgraph.py
```

**Key differences:**
- Session ID tracking for checkpointing
- LLM-enhanced outputs
- Better error messages

### 4. Environment Variables

Make sure you have your OpenAI API key set:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```
OPENAI_API_KEY=your-api-key-here
```

## API Changes

### Stage 1 Method

**Old:**
```python
results = coordinator.stage1_search_and_analyze(query, seed_papers)
```

**New:**
```python
config = {"configurable": {"thread_id": "unique_session_id"}}
results = coordinator.stage1_search_and_analyze(query, seed_papers, config=config)
```

### Stage 2 Method

**Old:**
```python
results = coordinator.stage2_search_and_analyze(tier2_query)
```

**New:**
```python
# Use same config/thread_id from Stage 1
results = coordinator.stage2_search_and_analyze(tier2_query, config=config)
```

## Benefits

1. **Better Analysis Quality**: LLM enhancement improves context understanding and gap identification
2. **Resumable Workflows**: Checkpointing allows resuming interrupted analyses
3. **Observability**: LangGraph provides visualization and debugging tools
4. **Scalability**: State machine architecture is easier to extend
5. **Error Recovery**: Better error handling and state tracking

## Backward Compatibility

The old `Coordinator` class is still available for backward compatibility:

```python
from agents.coordinator import Coordinator  # Old coordinator
from agents.langgraph_coordinator import LangGraphCoordinator  # New coordinator
```

## Performance Considerations

- **LLM Calls**: The new system makes LLM calls which add latency and cost
- **Model Choice**: Default is `gpt-4o-mini` for cost efficiency. You can use `gpt-4o` for better quality
- **Caching**: Consider implementing LLM response caching for repeated queries

## Troubleshooting

### Issue: "OpenAI API key not found"
**Solution**: Set `OPENAI_API_KEY` environment variable

### Issue: "State not found" in Stage 2
**Solution**: Make sure to use the same `thread_id` from Stage 1

### Issue: LLM calls failing
**Solution**: Check your API key, rate limits, and internet connection. The system falls back to rule-based analysis if LLM fails.

## Next Steps

1. Test the new interface: `python interface/gradio_app_langgraph.py`
2. Compare results with old coordinator
3. Adjust LLM model/temperature if needed
4. Implement custom checkpointing (e.g., database) for production

## Questions?

Check the main README.md for more details on the system architecture.

