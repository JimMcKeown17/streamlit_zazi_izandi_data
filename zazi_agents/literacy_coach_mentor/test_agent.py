"""
Test script for the Literacy Coach Mentor Agent System
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path - handle both direct execution and module import
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Also add the agents directory itself
AGENTS_DIR = os.path.join(ROOT_DIR, 'agents')
if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)

try:
    from agents import Runner, trace
except ImportError:
    print("❌ Error: Could not import 'agents' module")
    print(f"ROOT_DIR: {ROOT_DIR}")
    print(f"sys.path: {sys.path}")
    print("\nMake sure you have 'openai-agents' installed:")
    print("  pip install openai-agents")
    sys.exit(1)

try:
    # Import from the local package
    import literacy_coach_mentor
    create_supervisor_agent = literacy_coach_mentor.create_supervisor_agent
    get_coach_sessions = literacy_coach_mentor.get_coach_sessions
    get_coach_groups = literacy_coach_mentor.get_coach_groups
    get_coach_summary_stats = literacy_coach_mentor.get_coach_summary_stats
    get_benchmark_comparison = literacy_coach_mentor.get_benchmark_comparison
except ImportError as e:
    print(f"❌ Error importing literacy_coach_mentor: {e}")
    print(f"\nCurrent directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(__file__)}")
    print(f"ROOT_DIR: {ROOT_DIR}")
    print(f"AGENTS_DIR: {AGENTS_DIR}")
    print("\nTrying alternative import method...")
    
    # Alternative: direct import from files
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from supervisor_agent import create_supervisor_agent
        from tools import (
            get_coach_sessions,
            get_coach_groups,
            get_coach_summary_stats,
            get_benchmark_comparison
        )
        print("✅ Successfully imported using alternative method")
    except ImportError as e2:
        print(f"❌ Alternative import also failed: {e2}")
        sys.exit(1)


async def test_tools(user_id):
    """Test individual tools with a sample user_id"""
    print(f"\n{'='*80}")
    print(f"TESTING TOOLS FOR USER_ID: {user_id}")
    print(f"{'='*80}\n")
    
    # Test get_coach_summary_stats
    print("1. Testing get_coach_summary_stats...")
    print("-" * 80)
    try:
        result = get_coach_summary_stats(user_id)
        print(result[:500] + "..." if len(result) > 500 else result)
        print("✅ get_coach_summary_stats working\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Test get_coach_groups
    print("2. Testing get_coach_groups...")
    print("-" * 80)
    try:
        result = get_coach_groups(user_id)
        print(result[:500] + "..." if len(result) > 500 else result)
        print("✅ get_coach_groups working\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Test get_coach_sessions
    print("3. Testing get_coach_sessions...")
    print("-" * 80)
    try:
        result = get_coach_sessions(user_id)
        print(result[:500] + "..." if len(result) > 500 else result)
        print("✅ get_coach_sessions working\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Test get_benchmark_comparison
    print("4. Testing get_benchmark_comparison...")
    print("-" * 80)
    try:
        result = get_benchmark_comparison(user_id)
        print(result[:500] + "..." if len(result) > 500 else result)
        print("✅ get_benchmark_comparison working\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")


async def test_agent(user_id, question):
    """Test the full agent system with a question"""
    print(f"\n{'='*80}")
    print(f"TESTING AGENT WITH USER_ID: {user_id}")
    print(f"QUESTION: {question}")
    print(f"{'='*80}\n")
    
    try:
        # Create supervisor agent
        supervisor = create_supervisor_agent()
        
        # Enhance question with user_id context
        enhanced_question = f"[Coach User ID: {user_id}] {question}"
        
        # Run the agent
        with trace("Literacy Coach Mentor Test"):
            result = await Runner.run(supervisor, enhanced_question)
            
        print("AGENT RESPONSE:")
        print("-" * 80)
        print(result.final_output)
        print("-" * 80)
        print("✅ Agent test completed successfully\n")
        
        return result.final_output
        
    except Exception as e:
        print(f"❌ Error running agent: {e}")
        import traceback
        traceback.print_exc()
        return None


async def run_full_test():
    """Run comprehensive tests"""
    print("\n" + "="*80)
    print("LITERACY COACH MENTOR AGENT - COMPREHENSIVE TEST")
    print("="*80)
    
    # Get user_id from command line or use default
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
    else:
        # Try to get a sample user_id from the database
        from database_utils import get_database_engine
        import pandas as pd
        
        try:
            engine = get_database_engine()
            query = """
            SELECT DISTINCT user_id, user_name 
            FROM teampact_sessions_complete 
            WHERE letters_taught IS NOT NULL 
            AND letters_taught <> ''
            LIMIT 5
            """
            df = pd.read_sql(query, engine)
            
            if not df.empty:
                print("\nAvailable coaches in database:")
                print(df.to_string(index=False))
                user_id = int(df.iloc[0]['user_id'])
                print(f"\nUsing first coach: User ID {user_id} ({df.iloc[0]['user_name']})")
            else:
                print("\n❌ No coaches found in database with session data.")
                print("Please ensure the database has data and try again.")
                return
        except Exception as e:
            print(f"\n❌ Error connecting to database: {e}")
            print("Please check your database connection and try again.")
            return
    
    # Test individual tools
    await test_tools(user_id)
    
    # Test agent with different questions
    questions = [
        "How am I doing overall?",
        "Am I teaching my groups at the right levels?",
        "How is my pacing compared to expectations?",
    ]
    
    for question in questions:
        await test_agent(user_id, question)
        await asyncio.sleep(2)  # Brief pause between tests
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80 + "\n")


if __name__ == "__main__":
    print("\n🚀 Starting Literacy Coach Mentor Agent Tests...\n")
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ ERROR: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in the .env file")
        sys.exit(1)
    
    # Check for database connection
    if not os.getenv('RENDER_DATABASE_URL'):
        print("❌ ERROR: RENDER_DATABASE_URL not found in environment variables")
        print("Please set your database URL in the .env file")
        sys.exit(1)
    
    # Run tests
    asyncio.run(run_full_test())

