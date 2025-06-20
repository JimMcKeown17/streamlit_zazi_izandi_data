import streamlit as st
import pandas as pd
import os
from datetime import datetime as dt
from dotenv import load_dotenv
from process_survey_cto_updated import process_egra_data

load_dotenv()

def add_to_conversation(role, content):
    """Add message to conversation history"""
    st.session_state.conversation_history.append({
        "role": role,
        "content": content,
        "timestamp": dt.now()
    })

def get_ai_response_with_context(user_input, conversation_history, dataframe, model):
    """Generate AI response with full conversation context"""
    try:
        import sys
        sys.path.append('..')
        from AI_Tools.openai_tools_analysis import analyze_with_tools
        
        # Build context from conversation history
        context_messages = []
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            if msg["role"] == "user":
                context_messages.append(f"User: {msg['content']}")
            else:
                context_messages.append(f"Assistant: {msg['content']}")
        
        # Create enhanced question with context
        contextual_question = user_input
        if context_messages:
            contextual_question = f"Previous conversation:\n{chr(10).join(context_messages)}\n\nCurrent question: {user_input}"
        
        # Use existing AI tools with conversation context
        analysis = analyze_with_tools(
            dataframe,
            analysis_type="question",
            question=contextual_question,
            model=model
        )
        
        return analysis
        
    except Exception as e:
        return f"Error generating response: {str(e)}"

def handle_user_message(user_input, midline_df, model_choice):
    """Process user message and generate AI response"""
    if not user_input.strip():
        return
    
    # Add user message to conversation
    add_to_conversation("user", user_input)
    
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        error_msg = "API key not found. Please check your environment configuration."
        add_to_conversation("assistant", error_msg)
        return
    
    # Generate AI response with conversation context
    response = get_ai_response_with_context(
        user_input, 
        st.session_state.conversation_history[:-1],  # Exclude the just-added user message
        midline_df, 
        model_choice
    )
    
    if response:
        add_to_conversation("assistant", response)
    else:
        error_msg = "Failed to generate response. Please try again."
        add_to_conversation("assistant", error_msg)

def show():
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'current_model' not in st.session_state:
        st.session_state.current_model = "gpt-4o-mini"

    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    @st.cache_data
    def load_egra_data(children_filename: str, ta_filename: str):
        """Load and cache EGRA data files."""
        children_path = os.path.join(ROOT_DIR, "data", children_filename)
        ta_path = os.path.join(ROOT_DIR, "data", ta_filename)
        df, _ = process_egra_data(children_file=children_path, ta_file=ta_path)
        return df

    # Clean, minimal header
    st.title("🤖 ZazAI – 2025 Midline Data Analyst")
    st.write("Have a conversation with our AI data analyst about your 2025 midline assessment data.")

    try:
        # Load and prepare midline dataset
        df_full = load_egra_data(
            children_filename="EGRA form [Eastern Cape]-assessment_repeat - June 4.csv",
            ta_filename="EGRA form [Eastern Cape] - June 4.csv"
        )
        df_full['submission_date'] = pd.to_datetime(df_full['date'])
        midline_df = df_full[df_full['submission_date'] >= pd.Timestamp('2025-04-15')]

        # Simple top controls
        col1, col2 = st.columns([3, 1])
        
        with col1:
            model_choice = st.selectbox(
                "Model:",
                ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
                index=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"].index(st.session_state.current_model),
                label_visibility="collapsed"
            )
            st.session_state.current_model = model_choice
        
        with col2:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.conversation_history = []
                st.rerun()

        # Main chat interface - smaller container
        st.markdown("---")
        
        # Create a chat container (30% smaller than before)
        chat_container = st.container(height=420)
        
        with chat_container:
            if not st.session_state.conversation_history:
                # Welcome message
                st.chat_message("assistant").write(
                    "Hi! I'm ZazAI, your AI data analyst. I can help you explore and understand your 2025 midline assessment data. "
                    "Ask me about student performance, school comparisons, TA effectiveness, or any specific insights you'd like to discover."
                )
            
            # Display all conversation messages in the chat interface
            for message in st.session_state.conversation_history:
                if message["role"] == "user":
                    st.chat_message("user").write(message["content"])
                else:
                    st.chat_message("assistant").write(message["content"])

        # Chat input at the bottom
        if prompt := st.chat_input("Ask ZazAI about your data..."):
            # Show user message immediately
            with chat_container:
                st.chat_message("user").write(prompt)
            
            # Show thinking indicator
            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        # Process the message
                        handle_user_message(prompt, midline_df, model_choice)
            
            # Refresh to show the response
            st.rerun()

    except Exception as e:
        st.error(f"Error loading data: {e}") 