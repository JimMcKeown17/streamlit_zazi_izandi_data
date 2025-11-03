"""
Differentiation Agent - Checks if coach is teaching different groups at appropriate levels
"""

import os
import sys

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from agents import Agent
from .tools import get_coach_groups, get_coach_sessions
from .prompts import DIFFERENTIATION_INSTRUCTIONS


def create_differentiation_agent():
    """Create and return the Differentiation Agent"""
    return Agent(
        name="Differentiation Agent",
        instructions=DIFFERENTIATION_INSTRUCTIONS,
        model="gpt-4o-mini",
        tools=[get_coach_groups, get_coach_sessions]
    )

