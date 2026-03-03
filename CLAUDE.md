# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Streamlit-based data analytics platform ("ZZ Data Portal") for the Zazi iZandi literacy program. Provides interactive dashboards analyzing student assessment data across years (2023-2026), languages (isiXhosa, English, Afrikaans), and regions (Gqebera/Port Elizabeth, East London, ECD centers).

## Related Projects

- **Django Backend:** `/Users/jimmckeown/Development/Zazi_iZandi_Website_2025/`
  - Hosts the Django management commands that sync data from TeamPact API into PostgreSQL
  - Key sync commands: `sync_assessments_2026`, `sync_teampact_sessions_2026`, `sync_mentor_visits_2026`
  - Django models define the database schema (Assessment2026, AssessmentCell2026, etc.)
  - API reference: `Zazi_iZandi_Website_2025/docs/teampact_api_reference.md`

## Documentation

All project documentation lives in `docs/`:
- `docs/DATA_SOURCES_DOCUMENTATION.md` — Master reference for all data sources, tables, loading functions, and page mappings
- `docs/TEAMPACT_API_ASSESSMENT_MAPPING_2026.md` — Detailed mapping of how 2026 assessment data flows from TeamPact API (two-step: survey responses + group lookup) into the database, including field-by-field mapping for grade, program_name, and class_name

**Always check `docs/` first** when investigating data sources, API mappings, or database schema questions.

If major changes are made, especially to data sources, update the docs.

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
- `2023/`, `2024/`, `2025/`, `2026/` — Year-specific assessment analysis pages
- `project_management/` — QA dashboards (letter progress, flagging, school reports)
- `ai_assistant.py` — "Zazi Bot" using OpenAI API
- `home_page.py`, `table_of_contents.py` — Navigation pages

### Key Data Modules
- `data_loader.py` — Primary data loading functions (Excel, CSV, Parquet, database)
- `database_utils.py` — PostgreSQL connection management (`get_database_engine()`)
- `process_teampact_data.py` — TeamPact data transformation
- `grouping_logic.py` — Letter progress calculation logic

For database tables, data flow architecture, and environment variables, see `docs/DATA_SOURCES_DOCUMENTATION.md`.

## Key Patterns

### Data Loading
- Always use `@st.cache_data(ttl=3600)` for caching
- Fallback chain: Parquet → Excel/CSV, Database → CSV
- Database access via SQLAlchemy engine from `database_utils.get_database_engine()`
- 2026 data: use `load_assessments_2026()`, `load_sessions_2026()`, `load_mentor_visits_2026()` from `data_loader.py`

### Standard Letter Sequence
The EA program follows this fixed order (used in `grouping_logic.py` and progress pages):
```python
['a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p', 's', 'h', 'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x', 'g', 't', 'q', 'r', 'c', 'j']
```

