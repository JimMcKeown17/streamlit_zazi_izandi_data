# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Streamlit-based data analytics platform ("ZZ Data Portal") for the Zazi iZandi literacy program. Provides interactive dashboards analyzing student assessment data across years (2023-2025), languages (isiXhosa, English, Afrikaans), and regions (Gqebera/Port Elizabeth, East London, ECD centers).

## Commands

```bash
# Activate environment
source venv/bin/activate

# Run the app
streamlit run main.py

# Install dependencies
pip install -r requirements.txt
```

No automated test framework is configured. Testing is manual via the Streamlit UI.

## Architecture

### Entry Point & Navigation
- `main.py` — App entry point with page navigation and simple session-based authentication (hardcoded credentials: zazi/izandi). Pages are either public or internal (login-required).

### Page Organization (`new_pages/`)
Pages are organized by year and purpose:
- `2023/`, `2024/`, `2025/` — Year-specific assessment analysis pages
- `project_management/` — QA dashboards (letter progress, flagging, school reports)
- `ai_assistant.py` — "Zazi Bot" using OpenAI API
- `home_page.py`, `table_of_contents.py` — Navigation pages

### Data Layer (3-phase evolution)
1. **Static files** (2023-2024): CSV/Excel in `data/`, loaded via `data_loader.py`
2. **API integration** (mid-2025): TeamPact API via `data_utility_functions/teampact_apis.py` and `api/`
3. **Database** (Oct 2025+): PostgreSQL on Render, updated nightly via cron job

Key data modules:
- `data_loader.py` — Primary data loading functions (Excel, CSV, Parquet)
- `database_utils.py` — PostgreSQL connection management (`get_database_engine()`)
- `process_teampact_data.py` — TeamPact data transformation
- `grouping_logic.py` — Letter progress calculation logic

### Database Tables (PostgreSQL on Render)
- `teampact_sessions_complete` — Production session data (nightly updates). Columns: letters_taught, num_letters_taught, session_started_at, user_name, program_name, class_name, session_text
- `teampact_assessment_endline_2025` — Cohort 2 endline assessments with QA flags
- `api_tasession` — Legacy TA session tracking

### AI/Agent Integration
- `zazi_agents/` — Experimental AI agents (literacy coach, report creator)
- OpenAI API for the Zazi Bot assistant page

## Key Patterns

### Data Loading
- Always use `@st.cache_data(ttl=3600)` for caching
- Fallback chain: Parquet → Excel/CSV, Database → CSV
- Database access via SQLAlchemy engine from `database_utils.get_database_engine()`

### Standard Letter Sequence
The EA program follows this fixed order (used in `grouping_logic.py` and progress pages):
```python
['a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p', 's', 'h', 'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x', 'g', 't', 'q', 'r', 'c', 'j']
```

### Environment Variables (`.env`)
- `OPENAI_API_KEY` — AI assistant
- `TEAMPACT_API_TOKEN` — TeamPact API
- `SENDGRID_API_KEY` — Email
- `RENDER_DATABASE_URL` / `DATABASE_URL` / `EXTERNAL_DATABASE_URL` — PostgreSQL
