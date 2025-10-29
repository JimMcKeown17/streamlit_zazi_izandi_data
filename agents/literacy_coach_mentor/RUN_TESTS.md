# How to Run Tests

## The Issue

You got a `ModuleNotFoundError` because:
1. The files were created in the **worktree**: `/Users/jimmckeown/.cursor/worktrees/ZZ_Data_Site/o5mLr/`
2. But you tried to run from the **original location**: `/Users/jimmckeown/Library/Mobile Documents/com~apple~CloudDocs/Python/ZZ Data Site/`

## Solution 1: Run from the Worktree (Recommended)

```bash
# Navigate to the worktree
cd /Users/jimmckeown/.cursor/worktrees/ZZ_Data_Site/o5mLr

# Run the test
python agents/literacy_coach_mentor/test_agent.py
```

## Solution 2: Copy Files to Your Main Project

If you want to use the files in your main project directory, copy them:

```bash
# From the worktree to your main project
cp -r /Users/jimmckeown/.cursor/worktrees/ZZ_Data_Site/o5mLr/agents/literacy_coach_mentor \
      "/Users/jimmckeown/Library/Mobile Documents/com~apple~CloudDocs/Python/ZZ Data Site/agents/"

cp /Users/jimmckeown/.cursor/worktrees/ZZ_Data_Site/o5mLr/new_pages/coach_assistant.py \
   "/Users/jimmckeown/Library/Mobile Documents/com~apple~CloudDocs/Python/ZZ Data Site/new_pages/"
```

Then run from your main project:
```bash
cd "/Users/jimmckeown/Library/Mobile Documents/com~apple~CloudDocs/Python/ZZ Data Site"
python agents/literacy_coach_mentor/test_agent.py
```

## Solution 3: Run the Streamlit App

The easiest way to test is just to run the Streamlit interface:

```bash
# From the worktree
cd /Users/jimmckeown/.cursor/worktrees/ZZ_Data_Site/o5mLr
streamlit run new_pages/coach_assistant.py
```

Or from your main project (after copying files):
```bash
cd "/Users/jimmckeown/Library/Mobile Documents/com~apple~CloudDocs/Python/ZZ Data Site"
streamlit run new_pages/coach_assistant.py
```

## Quick Test Without Running Script

You can also test directly in Python:

```bash
cd /Users/jimmckeown/.cursor/worktrees/ZZ_Data_Site/o5mLr
python
```

Then in Python:
```python
import asyncio
from agents.literacy_coach_mentor import create_supervisor_agent
from agents import Runner

# Create agent
supervisor = create_supervisor_agent()

# Test with a user_id (replace 12345 with a real one)
async def test():
    result = await Runner.run(supervisor, "[Coach User ID: 12345] How am I doing overall?")
    print(result.final_output)

asyncio.run(test())
```

## Understanding Worktrees

Cursor uses Git worktrees to isolate changes. Your files are in:
- **Worktree**: `/Users/jimmckeown/.cursor/worktrees/ZZ_Data_Site/o5mLr/`
- **Original**: `/Users/jimmckeown/Library/Mobile Documents/com~apple~CloudDocs/Python/ZZ Data Site/`

To sync changes back to your main project, either:
1. Commit and push from the worktree, then pull in your main project
2. Copy the files manually (as shown in Solution 2)
3. Work directly in the worktree

## Recommended Workflow

1. **For Development**: Work in the worktree (where Cursor created the files)
2. **For Testing**: Run from the worktree
3. **For Deployment**: Commit changes and merge to main branch
4. **For Production**: Pull changes to your main project directory

## Files Created

All these files are in the worktree:
```
/Users/jimmckeown/.cursor/worktrees/ZZ_Data_Site/o5mLr/
├── agents/literacy_coach_mentor/
│   ├── __init__.py
│   ├── supervisor_agent.py
│   ├── session_analysis_agent.py
│   ├── differentiation_agent.py
│   ├── performance_agent.py
│   ├── tools.py
│   ├── prompts.py
│   ├── test_agent.py
│   ├── README.md
│   ├── USAGE.md
│   ├── QUICKSTART.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   └── RUN_TESTS.md (this file)
└── new_pages/
    └── coach_assistant.py
```

