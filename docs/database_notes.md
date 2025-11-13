July 2025 - Oct 2025:
- We pulled data via the teampact API in the script api/teampact_session_api.py.
- We then saved that into a table on our Render Postgres instance called teampact_nmb_sessions
- We then had the streamlit page connect to the database and populate the table.
- The downside here was having to wait 30+ minutes after hitting the refresh button for the page to load & update.

Oct 28, 2025 onwards
- We created a management command in Django to call the API each night and populate the database on Render.
- Because I was struggling a bit w/ the API from Django, I created a new table called teampact_sessions_complete.
- We then created a cron job on Render to update this each evening.
- I then updated the database_utils.py file to pull the data from this table instead.
- Removed the manual "Refresh Data" button from teampact_sessions_2025.py since data is now auto-updated via cron job.

Column differences between tables:
- Old table (teampact_nmb_sessions): had 'total_duration_minutes' column
- New table (teampact_sessions_complete): has 'session_duration' column (in seconds, not minutes)
- The teampact_sessions_2025.py file now converts session_duration to total_duration_minutes automatically

User Experience Changes:
- No more manual refresh button - data auto-updates nightly
- Page shows "Data last updated: X min/hours ago | Auto-refreshes nightly via cron job"
- Error messages direct users to contact system admin for manual refresh if needed