# AI Tools Package

This package contains all AI-related analysis tools and utilities for the ZZ Data Site project.

## Package Structure

```
AI_Tools/
├── __init__.py                 # Package initialization with exposed imports
├── ai_tools.py                 # Core data analysis toolkit with statistical functions
├── openai_analysis.py          # Context-only OpenAI analysis utilities
├── openai_tools_analysis.py    # Tool-enabled OpenAI analysis with dynamic data exploration
├── debug_ai_analysis.py        # Diagnostic and debugging tools for AI analysis
├── OPENAI_SETUP.md            # OpenAI setup and configuration documentation
└── README.md                   # This file
```

## Usage

### From the main application files:

```python
# Import the entire package
from AI_Tools import DataAnalysisToolkit, analyze_data_with_openai, analyze_with_tools

# Or import specific modules
from AI_Tools.openai_analysis import analyze_data_with_openai
from AI_Tools.debug_ai_analysis import run_comprehensive_diagnostics
```

### From within the package:

```python
# Use relative imports
from .ai_tools import DataAnalysisToolkit
from .openai_analysis import analyze_data_with_openai
```

## Modules Overview

### `ai_tools.py`
Core data analysis toolkit providing statistical functions and utilities for analyzing educational assessment data.

### `openai_analysis.py`
Context-only OpenAI analysis that sends pre-calculated summary statistics to the AI for analysis. Faster and uses fewer API calls.

### `openai_tools_analysis.py`
Tool-enabled OpenAI analysis that allows the AI to dynamically explore data using function calls. More powerful but uses more API calls.

### `debug_ai_analysis.py`
Diagnostic tools for troubleshooting AI analysis issues, including API connectivity tests and data validation.

## Migration Notes

This package was created by refactoring AI-related files from the project root into a dedicated package structure. All imports in the main application files have been updated to use the new package structure.

## Requirements

- OpenAI API key configured in environment variables
- All dependencies listed in the main project's requirements.txt 