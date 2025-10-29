"""
AI Coach Assistant - Personalized coaching for literacy coaches
"""

import streamlit as st
import sys
import os
import asyncio

# Add the root directory to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)


def coach_assistant_page():
    """Streamlit page for literacy coach AI mentor"""
    
    st.title("🎓 Literacy Coach Mentor")
    
    st.markdown("""
    Welcome, literacy coach! This AI mentor will help you understand your performance and improve your practice.
    
    **What I can help you with:**
    - 📊 Overall performance review
    - 📚 Letter teaching progress and pacing
    - 👥 Group differentiation analysis
    - 🎯 Comparison against benchmarks
    - 💡 Personalized coaching tips
    """)
    
    # Sidebar for coach authentication
    with st.sidebar:
        st.header("Coach Login")
        
        # Input for user_id
        user_id = st.number_input(
            "Enter your TeamPact User ID",
            min_value=1,
            step=1,
            help="This is your unique ID in the TeamPact system. Ask your mentor if you don't know it."
        )
        
        if st.button("🔐 Login"):
            if user_id:
                st.session_state.coach_user_id = user_id
                st.session_state.coach_authenticated = True
                st.success(f"✅ Logged in as User ID: {user_id}")
            else:
                st.error("Please enter a valid User ID")
        
        # Display current login status
        if st.session_state.get('coach_authenticated', False):
            st.info(f"👤 Current User ID: {st.session_state.coach_user_id}")
            
            if st.button("🚪 Logout"):
                st.session_state.coach_authenticated = False
                st.session_state.coach_user_id = None
                st.session_state.coach_messages = []
                st.rerun()
        
        st.divider()
        
        st.markdown("""
        ### Example Questions
        - "How am I doing overall?"
        - "Am I teaching my groups at the right levels?"
        - "How is my pacing compared to expectations?"
        - "How do my learners compare to benchmarks?"
        - "What should I focus on improving?"
        """)
    
    # Main chat interface
    if not st.session_state.get('coach_authenticated', False):
        st.warning("👈 Please login with your TeamPact User ID in the sidebar to get started.")
        
        st.markdown("""
        ### About This Tool
        
        This AI mentor analyzes your session data to provide personalized feedback on:
        
        1. **Session Frequency & Consistency**
           - How often you're delivering sessions
           - Whether you're maintaining a consistent schedule
           - Comparison to the ideal 3+ sessions per week
        
        2. **Differentiation**
           - Whether your groups are working on different letters
           - If groups are progressing at appropriate levels
           - Flags if multiple groups are at the same level
        
        3. **Performance Against Benchmarks**
           - How your learners compare to national standards
           - Progress relative to Zazi iZandi programme targets
           - Attendance rates and their impact
        
        All feedback is based on your actual session data from TeamPact.
        """)
        
        return
    
    # Initialize chat history for this coach
    if "coach_messages" not in st.session_state:
        st.session_state.coach_messages = []
    
    # Load the agent
    @st.cache_resource
    def load_coach_agent():
        try:
            from agents.literacy_coach_mentor import create_supervisor_agent
            from agents import Runner
            
            agent = create_supervisor_agent()
            return agent, Runner
            
        except Exception as e:
            st.error(f"Error loading coach mentor agent: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return None, None
    
    agent, Runner = load_coach_agent()
    
    if agent and Runner:
        # Display chat messages from history
        for message in st.session_state.coach_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # React to user input
        if prompt := st.chat_input("Ask me anything about your coaching performance..."):
            # Display user message
            st.chat_message("user").markdown(prompt)
            # Add user message to chat history
            st.session_state.coach_messages.append({"role": "user", "content": prompt})
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing your data..."):
                    try:
                        from agents import trace
                        
                        # Create context with user_id
                        user_id = st.session_state.coach_user_id
                        
                        # Enhance the prompt with user_id context
                        enhanced_prompt = f"[Coach User ID: {user_id}] {prompt}"
                        
                        # Run the agent
                        async def get_response():
                            with trace("Literacy Coach Mentor"):
                                result = await Runner.run(agent, enhanced_prompt)
                                return str(result.final_output)
                        
                        # Execute the async function
                        response = asyncio.run(get_response())
                        
                        # Display response
                        st.markdown(response)
                        
                        # Add assistant response to chat history
                        st.session_state.coach_messages.append({"role": "assistant", "content": response})
                        
                    except Exception as e:
                        error_msg = f"Error getting response: {str(e)}"
                        st.error(error_msg)
                        
                        # Show more details for debugging
                        with st.expander("Error Details"):
                            import traceback
                            st.code(traceback.format_exc())
                        
                        st.session_state.coach_messages.append({"role": "assistant", "content": error_msg})
        
        # Add quick action buttons
        st.divider()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 Overall Review"):
                st.session_state.quick_prompt = "Give me a comprehensive overview of my performance as a literacy coach."
                st.rerun()
        
        with col2:
            if st.button("👥 Check Differentiation"):
                st.session_state.quick_prompt = "Am I teaching my different groups at appropriate levels?"
                st.rerun()
        
        with col3:
            if st.button("⏱️ Check Pacing"):
                st.session_state.quick_prompt = "How is my pacing? Am I moving through letters at the right speed?"
                st.rerun()
        
        with col4:
            if st.button("🎯 Benchmarks"):
                st.session_state.quick_prompt = "How do my learners compare to benchmarks?"
                st.rerun()
        
        # Handle quick prompts
        if hasattr(st.session_state, 'quick_prompt'):
            quick_prompt = st.session_state.quick_prompt
            del st.session_state.quick_prompt
            
            # Add to chat
            st.session_state.coach_messages.append({"role": "user", "content": quick_prompt})
            
            # Generate response
            with st.spinner("Analyzing your data..."):
                try:
                    from agents import trace
                    user_id = st.session_state.coach_user_id
                    enhanced_prompt = f"[Coach User ID: {user_id}] {quick_prompt}"
                    
                    async def get_response():
                        with trace("Literacy Coach Mentor"):
                            result = await Runner.run(agent, enhanced_prompt)
                            return str(result.final_output)
                    
                    response = asyncio.run(get_response())
                    st.session_state.coach_messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.session_state.coach_messages.append({"role": "assistant", "content": error_msg})
            
            st.rerun()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.coach_messages = []
            st.rerun()
    
    else:
        st.error("❌ Could not load AI Coach Mentor")
        st.info("""
        **Troubleshooting:**
        1. Check that all dependencies are installed (`openai-agents`, `openai`, etc.)
        2. Ensure your OpenAI API key is set in .env file
        3. Verify the database connection is working
        """)


# Run the page function
coach_assistant_page()

