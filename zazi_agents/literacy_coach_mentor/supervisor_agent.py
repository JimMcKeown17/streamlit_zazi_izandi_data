"""
Supervisor Agent - Main orchestrator for the Literacy Coach Mentor system
"""

import os
import sys

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from agents import Agent
from .session_analysis_agent import create_session_analysis_agent
from .differentiation_agent import create_differentiation_agent
from .performance_agent import create_performance_agent
from .prompts import SUPERVISOR_INSTRUCTIONS


def create_supervisor_agent():
    """
    Create and return the Supervisor Agent with specialized sub-agents as tools
    """
    # Create specialized agents
    session_agent = create_session_analysis_agent()
    differentiation_agent = create_differentiation_agent()
    performance_agent = create_performance_agent()
    
    # Convert agents to tools
    session_tool = session_agent.as_tool(
        tool_name="session_analyzer",
        tool_description="Analyzes a literacy coach's session frequency, pacing, and consistency. Use this to answer questions about how often sessions are happening, whether the pace is appropriate, and if there are any gaps in delivery."
    )
    
    differentiation_tool = differentiation_agent.as_tool(
        tool_name="differentiation_analyzer",
        tool_description="Analyzes whether a literacy coach is teaching different groups at appropriate levels. Use this to check if groups are differentiated and progressing through the letter sequence appropriately."
    )
    
    performance_tool = performance_agent.as_tool(
        tool_name="performance_analyzer",
        tool_description="Compares a literacy coach's learner performance against national and programme benchmarks. Use this to provide context on how learners are performing relative to expectations."
    )
    
    # Create supervisor with specialized agents as tools
    supervisor = Agent(
        name="Literacy Coach Mentor",
        instructions=SUPERVISOR_INSTRUCTIONS,
        model="gpt-4o",
        tools=[session_tool, differentiation_tool, performance_tool]
    )
    
    return supervisor

