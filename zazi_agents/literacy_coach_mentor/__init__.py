"""
Literacy Coach Mentor Agent System

A multi-agent AI system that provides personalized coaching and feedback
to literacy coaches based on their session data.

Usage:
    from agents.literacy_coach_mentor import create_supervisor_agent
    from agents import Runner
    
    # Create the supervisor agent
    supervisor = create_supervisor_agent()
    
    # Run a query for a specific coach (include user_id in the prompt)
    result = await Runner.run(supervisor, "[Coach User ID: 12345] How am I doing overall?")
    print(result.final_output)
"""

from .supervisor_agent import create_supervisor_agent
from .session_analysis_agent import create_session_analysis_agent
from .differentiation_agent import create_differentiation_agent
from .performance_agent import create_performance_agent
from .tools import (
    get_coach_sessions,
    get_coach_groups,
    calculate_letter_progress,
    get_coach_summary_stats,
    get_benchmark_comparison
)

__all__ = [
    'create_supervisor_agent',
    'create_session_analysis_agent',
    'create_differentiation_agent',
    'create_performance_agent',
    'get_coach_sessions',
    'get_coach_groups',
    'calculate_letter_progress',
    'get_coach_summary_stats',
    'get_benchmark_comparison'
]

