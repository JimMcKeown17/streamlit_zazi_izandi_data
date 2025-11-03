"""
Performance Agent - Compares learner performance against benchmarks
"""

import os
import sys

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from agents import Agent
from .tools import get_benchmark_comparison, get_coach_summary_stats, get_coach_groups
from .prompts import PERFORMANCE_INSTRUCTIONS


def create_performance_agent():
    """Create and return the Performance Agent"""
    return Agent(
        name="Performance Agent",
        instructions=PERFORMANCE_INSTRUCTIONS,
        model="gpt-4o-mini",
        tools=[get_benchmark_comparison, get_coach_summary_stats, get_coach_groups]
    )

