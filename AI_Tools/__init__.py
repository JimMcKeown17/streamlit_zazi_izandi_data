"""
AI Tools Package

This package contains all AI-related analysis tools and utilities for the project.

Modules:
- ai_tools: Core data analysis toolkit with statistical functions
- openai_analysis: Context-only OpenAI analysis utilities  
- openai_tools_analysis: Tool-enabled OpenAI analysis with dynamic data exploration
- debug_ai_analysis: Diagnostic and debugging tools for AI analysis
"""

# Make imports available at package level
from .ai_tools import DataAnalysisToolkit
from .openai_analysis import analyze_data_with_openai, prepare_data_summary
from .openai_tools_analysis import analyze_with_tools
from .debug_ai_analysis import run_comprehensive_diagnostics

__version__ = "1.0.0"
__all__ = [
    "DataAnalysisToolkit",
    "analyze_data_with_openai", 
    "prepare_data_summary",
    "analyze_with_tools",
    "run_comprehensive_diagnostics"
] 