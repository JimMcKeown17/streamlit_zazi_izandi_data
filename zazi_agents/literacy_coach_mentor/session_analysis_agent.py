"""
Session Analysis Agent - Analyzes session frequency, pacing, and consistency
"""

import os
import sys

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from agents import Agent
from .tools import get_coach_sessions, get_coach_summary_stats
from .prompts import SESSION_ANALYSIS_INSTRUCTIONS


def create_session_analysis_agent():
    """Create and return the Session Analysis Agent"""
    return Agent(
        name="Session Analysis Agent",
        instructions=SESSION_ANALYSIS_INSTRUCTIONS,
        model="gpt-4o-mini",
        tools=[get_coach_sessions, get_coach_summary_stats]
    )

