# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Streamlit-based data analytics and visualization application called "ZZ Data Portal" for analyzing educational assessment data from the Zazi iZandi literacy program. The application provides interactive dashboards for analyzing student performance data across multiple years (2023-2025), languages (isiXhosa, English, Afrikaans), and assessment types.

## Development Environment

### Python Environment
- Uses Python virtual environment located in `venv/`
- Activate with: `source venv/bin/activate` (already activated in current session)
- Python interpreter: `/Users/jimmckeown/Python/ZZ Data Site/venv/bin/python`

### Environment Variables
- `.env` file contains API keys and database credentials (never commit this file)
- Required environment variables:
  - `OPENAI_API_KEY`: For AI assistant functionality
  - `TEAMPACT_API_TOKEN`: For fetching survey data from TeamPact API
  - `SENDGRID_API_KEY`: For email functionality
  - Database connection variables for PostgreSQL

### Dependencies
Install dependencies with: `pip install -r requirements.txt`

Key dependencies include:
- `streamlit`: Main web framework
- `pandas`: Data manipulation and analysis
- `plotly`: Interactive visualizations  
- `openai`: AI assistant integration
- `psycopg2-binary`: PostgreSQL database connectivity
- `sqlalchemy`: Database ORM

## Application Structure

### Entry Point
- `main.py`: Main Streamlit application entry point with navigation and authentication
- Run with: `streamlit run main.py`

### Page Organization
- `new_pages/`: Contains all page modules organized by year
  - `2023/`: 2023 analysis pages
  - `2024/`: 2024 analysis pages  
  - `2025/`: 2025 analysis pages
  - `project_management/`: Project management and reporting pages
- Each page is a standalone Python module with Streamlit page configuration

### Data Management
- `data_loader.py`: Main data loading functions for Excel and CSV files
- `data_utility_functions/`: Utility modules for data processing
  - `data_manager.py`: Central data management functions
  - `teampact_apis.py`: API integration with TeamPact platform
- `process_survey_cto_updated.py`: Survey data processing logic
- `data/`: Directory containing Excel and CSV data files

### Core Modules
- `display_24.py`: 2024 data visualization functions
- `display_23.py`: 2023 data visualization functions  
- `db_api_get_sessions.py`: Database API for session data
- `grouping_logic.py`: Data grouping and categorization logic

### AI Integration
- `agents/`: AI agent modules for automated reporting and analysis
- `new_pages/ai_assistant.py`: "Zazi Bot" AI assistant page

## Authentication
- Simple username/password authentication system in `main.py`
- Credentials are hardcoded (consider moving to environment variables)
- Public vs internal content access based on login status

## Data Sources

The project uses different data sources by year due to evolving data collection methods:

### 2023 Data
- **Source**: CSV files from manual exports
- **Processing**: Legacy data processing functions

### 2024 Data  
- **Sources**: CSV files + SurveyCTO API integration
- **Processing**: Functions in `process_survey_cto_updated.py`

### 2025 Data (Current)
- **Sources**: TeamPact API integration + some CSV files during transition
- **Processing**: Functions in `data_utility_functions/teampact_apis.py`
- **Storage**: Data is being saved to PostgreSQL database for persistence

### Additional Sources
- Excel files from assessment databases (historical data)
- PostgreSQL database for session tracking and current data storage

## Development Commands

### Running the Application
```bash
streamlit run main.py
```

### Data Processing
- Process survey data: Use functions in `process_survey_cto_updated.py` (deprecated)
- Load assessment data: Use functions in `data_loader.py`

### No Testing Framework
- No automated tests are currently configured
- Manual testing through Streamlit interface

## Code Conventions

### File Naming
- Page files use descriptive names with underscores
- Year-specific organization in subdirectories
- Utility functions grouped in `data_utility_functions/`

### Data Loading Patterns
- Centralized data loading functions in `data_loader.py`
- Caching with `@st.cache_data` for performance
- Error handling for missing files and API failures

### Page Structure
- Each page is a self-contained module
- Uses Streamlit's native page navigation system
- Consistent layout with sidebar filters and main content area

## Letter Session Data Access (EA Sessions)

### Overview
EA (Educational Assistant) letter session data is captured from August 2025+ through the TeamPact API integration. This data tracks which letters EAs have been teaching during their sessions with learners.

### Data Storage

#### Primary Tables
1. **`api_tasession`** - Legacy TA sessions table with basic letter tracking
   - **Column**: `letters_worked_on` (varchar(255))
   - **Format**: Simple comma-separated letters (e.g., "a and e", "Ee& Ii", "U and B")
   - **Access**: Use `db_api_get_sessions.py` functions

2. **`teampact_nmb_sessions`** - Current TeamPact session data (August 2025+)
   - **Column**: `letters_taught` (text)
   - **Format**: Comma-separated letter combinations (e.g., "a,e,i", "g,t,q")
   - **Additional fields**:
     - `num_letters_taught`: Count of letters in session
     - `session_text`: Comments and notes from EA
     - `user_name`: EA name
     - `program_name`: School name
     - `class_name`: Group/class identifier
     - `session_started_at`: Session timestamp
   - **Access**: Use `database_utils.py` functions

### Data Access Methods

#### For Current TeamPact Data (August 2025+)
```python
from database_utils import get_database_engine
import pandas as pd

# Get all letter sessions
engine = get_database_engine()
query = """
SELECT
    session_id,
    user_name as ea_name,
    program_name as school_name,
    class_name as group_name,
    session_started_at,
    letters_taught,
    num_letters_taught,
    session_text as comments
FROM teampact_nmb_sessions
WHERE letters_taught IS NOT NULL
AND letters_taught != ''
ORDER BY session_started_at DESC
"""
df = pd.read_sql(query, engine)
```

#### For Legacy TA Sessions
```python
from db_api_get_sessions import get_ta_sessions

# Get TA sessions with letter data
sessions_df = get_ta_sessions(date_filter='2024-01-01')
letter_sessions = sessions_df[sessions_df['letters_worked_on'].notna()]
```

### Letter Progress Analysis

#### Standard Letter Sequence
The EA program follows this letter sequence:
```python
LETTER_SEQUENCE = [
    'a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p',
    's', 'h', 'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x',
    'g', 't', 'q', 'r', 'c', 'j'
]
```

#### Progress Calculation
Use functions in `new_pages/project_management/letter_progress_july_cohort.py`:
- `calculate_letter_progress()`: Determines progress based on rightmost letter taught
- `process_session_data()`: Groups sessions by school/EA/group structure

### Existing Analysis Pages
- `new_pages/project_management/letter_progress_july_cohort.py`: Main letter progress dashboard
- `new_pages/project_management/letter_progress_detailed_july_cohort.py`: Detailed analysis
- Both use TeamPact data for August 2025+ sessions

### Data Fetching and Updates
- **API Integration**: `api/teampact_session_api.py` fetches fresh data from TeamPact
- **Database Updates**: Run data sync to update `teampact_nmb_sessions` table
- **Caching**: Database functions use Streamlit caching for performance

## Important Notes
- Uses environment variables for sensitive data (API keys, credentials)
- Data files are gitignored to protect student privacy
- Application supports both public and authenticated user views
- Real-time data fetching from TeamPact API for current data
- 2025 data now comes via Teampact APIs. 2023-2024 data was pulled via a no-longer used SurveyCTO API or xlsx and csv files.
- Letter session data only available from August 2025+ through TeamPact integration