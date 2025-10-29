# Literacy Coach Mentor Agent System

An AI-powered coaching system that provides personalized feedback to literacy coaches based on their session data from the TeamPact database.

## Overview

This multi-agent system uses OpenAI's agent framework to analyze literacy coach performance across three key dimensions:

1. **Session Analysis**: Frequency, pacing, and consistency of sessions
2. **Differentiation**: Whether coaches are teaching different groups at appropriate levels
3. **Performance**: How learners compare against national and program benchmarks

## Architecture

### Supervisor Agent
The main orchestrator that provides a conversational interface and routes queries to specialized agents.

### Specialized Agents

**Session Analysis Agent**
- Analyzes session frequency over time
- Calculates pacing (letters per week/per 3 sessions)
- Identifies gaps in session delivery
- Expected pace: Grade 1 = 2 new letters every 3 sessions

**Differentiation Agent**
- Checks if different groups are at different letter positions
- Flags if 3+ groups are at the same progress level
- Validates appropriate progression through letter sequence

**Performance Agent**
- Compares learner performance against benchmarks
- Provides context on attendance rates
- Highlights areas of strength and improvement

## Usage

### In Streamlit Application

```python
from agents.literacy_coach_mentor import create_supervisor_agent
from agents import Runner

# Create the supervisor agent
supervisor = create_supervisor_agent()

# Run a query for a specific coach
result = await Runner.run(supervisor, "How am I doing overall?", context={"user_id": 12345})
```

### Available Tools

- `get_coach_sessions(user_id)` - Fetch all sessions for a coach
- `get_coach_groups(user_id)` - Get groups taught by coach with progress
- `calculate_group_progress(sessions_df, group_name)` - Calculate letter progress
- `get_coach_summary_stats(user_id)` - Overall statistics
- `get_benchmark_comparison(user_id)` - Compare against benchmarks

## Benchmarks

### National Context
- Eastern Cape Grade 1: Only 27% reach 40 letters per minute
- National Grade 1: <50% know all letters by year end
- Median Grade 2 fluency: 11 correct words per minute (benchmark = 30+)

### Zazi iZandi Targets
- 2023: 74% reaching benchmarks
- 2024: 53% reaching benchmarks
- Expected pace: 2 letters per week for Grade 1
- Attendance target: >80%
- Session frequency: 3+ sessions per week ideal

## Letter Sequence

Coaches teach letters in frequency-based order:
```
a, e, i, o, u, b, l, m, k, p, s, h, z, n, d, y, f, w, v, x, g, t, q, r, c, j
```

## Data Source

All data is pulled from the `teampact_sessions_complete` table in the PostgreSQL database.

## Dependencies

- openai-agents
- pandas
- sqlalchemy
- python-dotenv

