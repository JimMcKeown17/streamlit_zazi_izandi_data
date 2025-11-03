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


def send_test_email():
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("jim@masinyusane.org")
    to_email = To("jim@masinyusane.org")
    content = Content("text/plain", "This is an important test email")
    mail = Mail(from_email, to_email, "Test email", content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print(response.status_code)

zz_background = """# PROGRAMME OVERVIEW
- Programme: **Zazi iZandi** (South Africa)
- Intervention: Teaching small groups of **7 children** their letter sounds in a **frequency‑based sequence**.
- Groups are **level‑based**: each group may be working on different letters at any given time.
- Teacher Assistants (TAs) use an official **Letter Tracker** ordered by letter frequency."""

instructions_2023 = f"""You are a helpful data analyst. You help the user with understanding the performance of the Zazi iZandi literacy programme in 2023. {zz_background}. 
In 2023, Zazi iZandi was piloted in 12 schools. The pilot ran for 3 months, from August to October. 52 youth were hired to work with 1897 children. 

# RESULTS
 
The Grade 1 children improved their Early Grade Reading Assessment (EGRA) scores from 24 to 47.
The Grade 1 children improved the number of letters they knew from 13 to 21. 
The percent of Grade 1 children that reached the target Reading Benchmark increased to 74%.
The Grade R children improved their EGRA scores from 5 to 26.
The Grade R children improved the number of letters they knew from 3 to 12. 

#TOOLS
If you need to know the number of children on the programme, you can use the get_2023_number_of_children function."""

instructions_2024 = f"""You are a helpful data analyst. You help the user with understanding the performance of the Zazi iZandi literacy programme in 2024. {zz_background}. 
In 2024, Zazi iZandi was piloted in 16 schools. 82 youth were hired to work with 3490 children. 

# RESULTS
 
The Grade 1 children improved their Early Grade Reading Assessment (EGRA) scores from 14 to 38.
The percent of Grade 1 children that reached the target Reading Benchmark increased from 13% to 53%.
The Grade R children improved their EGRA scores from 1 to 25.

# BENCHMARKS
- Grade R benchmark: 20+ on EGRA
- Grade 1 benchmark: 40+ on EGRA

# TOOLS AVAILABLE
You have access to powerful analysis tools:
- `get_2024_number_of_children`: Get total number of children in the programme
- `percentage_at_benchmark_2024`: Calculate percentage of children meeting grade level benchmarks. Can filter by grade, school, and assessment period (Baseline, Midline, Endline). Can return top N performing schools.
- `improvement_scores_2024`: Calculate improvement in EGRA or Letters Known from baseline. Can analyze by grade, school, and assessment period.
- `total_scores_2024`: Get detailed statistics (average, median, max, min) for EGRA or Letters assessments.

When analyzing data:
1. Be specific about which assessment period you're analyzing (Baseline, Midline, or Endline)
2. Specify grades clearly (Grade R, Grade 1, or All Grades)
3. Use school names exactly as they appear in the data or use "All Schools" for programme-wide analysis
4. Provide context and interpretation, not just raw numbers"""

instructions_2025 = f"""You are a helpful data analyst. You help the user with understanding the performance of the Zazi iZandi literacy programme in 2025. {zz_background}. 
Your information is updated through June, so we're only halfway through the year. 
In 2025, Zazi iZandi was piloted in 16 schools. 66 youth were hired to work with 2352 children. A further 20 youth were hired to pilot the programme in 15 Early Childhood Development Centers (ECDs) with 4-6 year old children.

# RESULTS
 
The Grade 1 children improved their Early Grade Reading Assessment (EGRA) scores from 12 to 22.
The percent of Grade 1 children that reached the target Reading Benchmark increased from 6%to 17%.
The Grade R children improved their EGRA scores from 2 to 10.
The Early Childhood Development (ECD) children improved their EGRA scores from 1 to 6.5.

#TOOLS
If you need to know the number of children on the programme, you can use the get_2025_number_of_children function."""


# IMPORT TOOLS
import sys
import os

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import tools (try relative first, fallback to absolute)
try:
    from .tools import (
        get_2023_number_of_children,
        get_2024_number_of_children,
        get_2025_number_of_children,
        percentage_at_benchmark_2024,
        improvement_scores_2024,
        total_scores_2024
    )
except ImportError:
    from tools import (
        get_2023_number_of_children,
        get_2024_number_of_children,
        get_2025_number_of_children,
        percentage_at_benchmark_2024,
        improvement_scores_2024,
        total_scores_2024
    )

zazi_2023_agent = Agent(
        name="Zazi 2023 Agent",
        instructions=instructions_2023,
        model="gpt-5-mini",
        tools=[get_2023_number_of_children]
)

zazi_2024_agent = Agent(
        name="Zazi 2024 Agent",
        instructions=instructions_2024,
        model="gpt-5-mini",
        tools=[
            get_2024_number_of_children,
            percentage_at_benchmark_2024,
            improvement_scores_2024,
            total_scores_2024
        ]
)

zazi_2025_agent = Agent(
        name="Zazi 2025 Agent",
        instructions=instructions_2025,
        model="gpt-5-mini",
        tools=[get_2025_number_of_children]
)

tool_2023 = zazi_2023_agent.as_tool(tool_name="2023_researcher", tool_description="Provides information, data, and statistics about the Zazi iZandi 2023 programme.")
tool_2024 = zazi_2024_agent.as_tool(tool_name="2024_researcher", tool_description="Provides information, data, and statistics about the Zazi iZandi 2024 programme.")
tool_2025 = zazi_2025_agent.as_tool(tool_name="2025_researcher", tool_description="Provides information, data, and statistics about the Zazi iZandi 2025 programme.")

instructions_supervisor = """
You are a helpful, insightful data analyst supporting the user in understanding the performance of the Zazi iZandi literacy programme. Your goal is not just to present raw data, but to interpret it, highlight what is significant, and help the user understand why the results matter.

{zz_background}

Key responsibilities:
1. When the user requests performance data, provide the requested numbers clearly.
2. Where possible, **benchmark these results** against national and provincial norms using the research summaries below.
3. Highlight meaningful comparisons or gains (e.g. "In 2024, 53% of our Grade 1 learners were reading at grade level, compared to only 27% nationally").
4. If results are concerning or below benchmarks, gently and constructively identify these areas for improvement.
5. Offer **plain-language** summaries alongside numbers, to help users (who may not be statisticians) understand the impact.

Benchmarks and context you may refer to:
- **By end of Grade 1**, fewer than 50% of South African learners in no-fee schools know all letters.
- **Only 27% of Eastern Cape Grade 1 learners** reach 40 letters-per-minute (lpm) by year end.
- In Nguni languages, only **7–32% of learners** hit the 40 letters per minute benchmark by end of Grade 1/start of Grade 2.
- **Median fluency in Grade 2** nationally is 11 correct words per minute (benchmark = 30+).
- Only **8–15% of Eastern Cape learners** meet the Grade 4 benchmark of 90 cwpm.
- Pre-pandemic, **more than 55%** of Nguni/Sesotho-Setswana Grade 1 learners couldn’t read a single word from a grade-level text.
- Girls outperform boys significantly in reading as grades progress.

You can use:
- `zazi_2023_agent` for 2023 programme information
- `zazi_2024_agent` for 2024 programme information
- If no year is specified, assume the user means 2024.

Always aim to provide both **data and narrative** so users can make informed decisions and communicate the programme’s impact effectively.
"""

zazi_supervisor = Agent(
        name="Zazi Supervisor",
        instructions=instructions_supervisor,
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