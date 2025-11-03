# AgentV2 Tools

This directory contains modular tools for the Zazi iZandi AI Assistant (Agent V2).

## Structure

Each tool is in its own file for better maintainability and testing. Tools use the `@function_tool` decorator from the `agents` library.

## Files

### Utility Files
- **`utils.py`** - Shared utility functions like `clean_nan_values()` for JSON serialization
- **`data_loader_2024.py`** - Shared data loader for 2024 programme data

### 2023 Tools
- **`children_count_2023.py`** - Get number of children in 2023 programme

### 2024 Tools
- **`children_count_2024.py`** - Get number of children in 2024 programme
- **`percentage_at_benchmark_2024.py`** - Calculate percentage of children meeting grade level benchmarks
  - Supports Grade R (20+ EGRA) and Grade 1 (40+ EGRA)
  - Can analyze Baseline, Midline, or Endline assessments
  - Supports school-level and programme-wide analysis
  - Can return top N performing schools
  
- **`improvement_scores_2024.py`** - Calculate improvement scores for EGRA or Letters Known
  - Shows baseline to midline or endline improvement
  - Supports both EGRA and Letters metrics
  - Note: Letters improvement at Endline uses Midline Letters as baseline
  
- **`total_scores_2024.py`** - Get score statistics (average, median, max, min)
  - Works with both EGRA and Letters assessments
  - Can analyze Baseline, Midline, or Endline assessments
  - Supports school-level and programme-wide analysis

### 2025 Tools
- **`children_count_2025.py`** - Get number of children in 2025 programme

## Usage in Agents

Tools are automatically decorated with `@function_tool` when imported. Example:

```python
from .tools import (
    percentage_at_benchmark_2024,
    improvement_scores_2024,
    total_scores_2024
)

# Pass to agent
agent = Agent(
    name="My Agent",
    tools=[percentage_at_benchmark_2024, improvement_scores_2024]
)
```

## Data Notes

### 2024 Data Structure
- **Baseline**: Has 'EGRA Baseline' and 'Baseline Letters Known'
- **Midline**: Has both baseline and midline columns for comparison
- **Endline**: Has 'EGRA Baseline', 'EGRA Endline', 'Letters Known', 'Midline Letters Known'
  - Note: Endline dataset does NOT have 'Baseline Letters Known'
  - Letters improvement at endline compares Endline to Midline

### Known Limitations
1. Letters improvement for Endline assessment uses Midline as baseline (not initial baseline)
2. Some grade/school combinations may return empty results if data is not available
3. All NaN and Inf values are cleaned to None for JSON serialization

## Testing

Tools have been tested with real 2024 data and confirmed to work correctly:
- ✅ Percentage at benchmark calculations
- ✅ EGRA improvement scores
- ✅ Letters improvement scores (with data limitations noted)
- ✅ Total score statistics
- ✅ Top N school rankings
- ✅ School-specific and programme-wide analysis

## Adding New Tools

To add a new tool:

1. Create a new file in this directory (e.g., `my_new_tool.py`)
2. Import required dependencies and data loaders
3. Define your function with proper docstrings
4. Decorate with `@function_tool` or create decorated version
5. Export both raw function (prefixed with `_`) and decorated version
6. Add to `__init__.py` exports
7. Update this README

Example:
```python
from agents import function_tool
from .utils import clean_nan_values

def _my_tool(param1: str, param2: int = 10):
    """
    Tool description here.
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        Dictionary with results
    """
    # Implementation
    return clean_nan_values(result)

# Export decorated version
my_tool = function_tool(_my_tool)
```

