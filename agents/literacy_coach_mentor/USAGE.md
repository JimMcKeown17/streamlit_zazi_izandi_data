# Literacy Coach Mentor - Usage Guide

## Quick Start

### 1. Running the Streamlit Interface

The easiest way to use the Literacy Coach Mentor is through the Streamlit web interface:

```bash
streamlit run new_pages/coach_assistant.py
```

Then:
1. Enter your TeamPact User ID in the sidebar
2. Click "Login"
3. Start asking questions about your coaching performance

### 2. Using the Agent Programmatically

```python
import asyncio
from agents.literacy_coach_mentor import create_supervisor_agent
from agents import Runner

async def get_coaching_feedback(user_id, question):
    # Create the supervisor agent
    supervisor = create_supervisor_agent()
    
    # Include user_id in the prompt
    prompt = f"[Coach User ID: {user_id}] {question}"
    
    # Run the agent
    result = await Runner.run(supervisor, prompt)
    
    return result.final_output

# Example usage
user_id = 12345
question = "How am I doing overall?"
response = asyncio.run(get_coaching_feedback(user_id, question))
print(response)
```

### 3. Testing the System

Run the comprehensive test suite:

```bash
python agents/literacy_coach_mentor/test_agent.py [user_id]
```

If you don't provide a user_id, it will automatically select a coach from the database.

## Example Questions

### Overall Performance
- "How am I doing overall?"
- "Give me a comprehensive review of my coaching performance"
- "What are my strengths and areas for improvement?"

### Session Frequency & Pacing
- "How is my pacing compared to expectations?"
- "Am I delivering sessions frequently enough?"
- "How many sessions per week am I doing?"
- "Am I moving through letters too fast or too slow?"

### Group Differentiation
- "Am I teaching my groups at the right levels?"
- "Are my groups differentiated appropriately?"
- "Should I be teaching different letters to different groups?"

### Performance & Benchmarks
- "How do my learners compare to benchmarks?"
- "How are my learners performing compared to other coaches?"
- "What is my attendance rate?"
- "How far through the letter sequence have my groups progressed?"

### Specific Guidance
- "What should I focus on improving?"
- "How can I improve my differentiation?"
- "What can I do to improve attendance?"
- "Give me tips for better pacing"

## Understanding the Response

The AI mentor will:
1. Analyze your actual session data from the database
2. Compare your performance to benchmarks and targets
3. Provide specific, actionable feedback
4. Celebrate your successes
5. Gently identify areas for growth
6. Offer concrete suggestions for improvement

## Data Sources

All analysis is based on your session data in the `teampact_sessions_complete` table, including:
- Session dates and frequency
- Letters taught in each session
- Groups you're working with
- Attendance rates
- Session notes and comments

## Benchmarks Used

### National Context
- Eastern Cape Grade 1: Only 27% reach 40 letters per minute
- National Grade 1: <50% know all letters by year end

### Zazi iZandi Targets
- Expected pace: 2 new letters every 3 sessions for Grade 1
- Attendance target: >80%
- Session frequency: 3+ sessions per week ideal
- Groups should be differentiated by level

## Troubleshooting

### "No data found for user_id"
- Check that your user_id is correct
- Ensure you have recorded sessions with letters taught
- Verify the database connection is working

### Agent not responding
- Check that your OpenAI API key is set in .env
- Verify database connection (RENDER_DATABASE_URL in .env)
- Check the console for error messages

### Slow responses
- First query may take longer as data is fetched
- Subsequent queries should be faster
- Complex questions requiring multiple agents may take 10-30 seconds

## Technical Details

### Architecture
- **Supervisor Agent**: Orchestrates analysis (GPT-4o)
- **Session Analysis Agent**: Analyzes frequency and pacing (GPT-4o-mini)
- **Differentiation Agent**: Checks group-level teaching (GPT-4o-mini)
- **Performance Agent**: Compares to benchmarks (GPT-4o-mini)

### Database Tools
- `get_coach_sessions`: Fetches all session data
- `get_coach_groups`: Gets group-level progress
- `get_coach_summary_stats`: Overall statistics
- `get_benchmark_comparison`: Performance vs benchmarks

### Letter Sequence
Letters are taught in frequency order:
```
a, e, i, o, u, b, l, m, k, p, s, h, z, n, d, y, f, w, v, x, g, t, q, r, c, j
```

## Support

For issues or questions:
1. Check the README.md in the agents/literacy_coach_mentor/ directory
2. Review the test_agent.py output for debugging
3. Contact your programme mentor or technical support

