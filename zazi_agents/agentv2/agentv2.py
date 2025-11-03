from dotenv import load_dotenv
from agents import Agent, Runner, trace
from openai.types.responses import ResponseTextDeltaEvent
from typing import Dict
import sendgrid
import os
from sendgrid.helpers.mail import Mail, Email, To, Content
import asyncio
# gradio is only imported when running standalone (see bottom of file)


load_dotenv(override=True)

# Import prompts
try:
    from .promptv2 import (
        ZZ_BACKGROUND,
        INSTRUCTIONS_2023,
        INSTRUCTIONS_2024,
        INSTRUCTIONS_2025,
        INSTRUCTIONS_SUPERVISOR
    )
except ImportError:
    from promptv2 import (
        ZZ_BACKGROUND,
        INSTRUCTIONS_2023,
        INSTRUCTIONS_2024,
        INSTRUCTIONS_2025,
        INSTRUCTIONS_SUPERVISOR
    )


def send_test_email():
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("jim@masinyusane.org")
    to_email = To("jim@masinyusane.org")
    content = Content("text/plain", "This is an important test email")
    mail = Mail(from_email, to_email, "Test email", content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print(response.status_code)

# IMPORT TOOLS
import sys

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import tools (try relative first, fallback to absolute)
try:
    from .tools import (
        get_grade_performance_2024,
        percentage_at_benchmark_2024,
        improvement_scores_2024,
        total_scores_2024
    )
except ImportError:
    from tools import (
        get_grade_performance_2024,
        percentage_at_benchmark_2024,
        improvement_scores_2024,
        total_scores_2024
    )

zazi_2023_agent = Agent(
        name="Zazi 2023 Agent",
        instructions=INSTRUCTIONS_2023,
        model="gpt-5-mini",
        tools=[]
)

zazi_2024_agent = Agent(
        name="Zazi 2024 Agent",
        instructions=INSTRUCTIONS_2024,
        model="gpt-5-mini",
        tools=[
            get_grade_performance_2024,
            percentage_at_benchmark_2024,
            improvement_scores_2024,
            total_scores_2024
        ]
)

zazi_2025_agent = Agent(
        name="Zazi 2025 Agent",
        instructions=INSTRUCTIONS_2025,
        model="gpt-5-mini",
        tools=[]
)

tool_2023 = zazi_2023_agent.as_tool(tool_name="2023_researcher", tool_description="Provides information, data, and statistics about the Zazi iZandi 2023 programme.")
tool_2024 = zazi_2024_agent.as_tool(tool_name="2024_researcher", tool_description="Provides information, data, and statistics about the Zazi iZandi 2024 programme.")
tool_2025 = zazi_2025_agent.as_tool(tool_name="2025_researcher", tool_description="Provides information, data, and statistics about the Zazi iZandi 2025 programme.")

zazi_supervisor = Agent(
        name="Zazi Supervisor",
        instructions=INSTRUCTIONS_SUPERVISOR,
        model="gpt-5-mini",
        tools=[tool_2023, tool_2024, tool_2025]
)

# with trace("Zazi iZandi Supervisor Agent"):
#     result = await Runner.run(zazi_supervisor, question)
# Define an async wrapper for your chatbot logic
async def chat_async(message, history):
    # You could also parse history if needed
    result = await Runner.run(zazi_supervisor, message)
    return str(result.final_output)

def chat(message, history):
    return asyncio.run(chat_async(message, history))

def create_gradio_interface():
    """Create and return the Gradio ChatInterface for embedding in Streamlit"""
    import gradio as gr
    return gr.ChatInterface(
        fn=chat,
        title="Zazi iZandi AI Assistant",
        description="Ask anything about the 2023, 2024, or 2025 literacy programme data.",
    )

# Only launch if running directly (not when imported)
if __name__ == "__main__":
    import gradio as gr  # Only import gradio when running standalone
    create_gradio_interface().launch()
