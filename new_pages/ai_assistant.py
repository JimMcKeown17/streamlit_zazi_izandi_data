import streamlit as st
import sys
import os
import importlib.util

# Add the root directory to sys.path to import the agent
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

def ai_assistant_page():
    """Streamlit page with embedded Gradio AI Assistant"""
    
    st.title("🤖 Zazi iZandi Bot")
    
    st.markdown("""
    Ask the AI assistant anything about the Zazi iZandi literacy programme data across different years:
    - **2023 Results**: Pilot programme data
    - **2024 Results**: Expanded programme data  
    - **2025 Results**: Current year progress
    
    The assistant can provide insights, compare results against benchmarks, and help interpret the data.
    """)       
        # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Initialize the agent function
    @st.cache_resource
    def load_agent():
        try:
            # Add agents directory to path  
            agents_path = os.path.join(root_dir, 'agents', 'agentv2')
            if agents_path not in sys.path:
                sys.path.append(agents_path)
            
            # Import the agent components
            import importlib.util
            spec = importlib.util.spec_from_file_location("agentv2", os.path.join(agents_path, "agentv2.py"))
            agentv2_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(agentv2_module)
            
            return agentv2_module.zazi_supervisor, agentv2_module.Runner
            
        except Exception as e:
            st.error(f"Error loading agent: {str(e)}")
            return None, None
    
    agent, Runner = load_agent()
    
    if agent and Runner:            
        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # React to user input
        if prompt := st.chat_input("Ask anything about the Zazi iZandi programme..."):
            # Display user message in chat message container
            st.chat_message("user").markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        import asyncio
                        from agents import trace
                        
                        # Run the agent
                        async def get_response():
                            with trace("Zazi iZandi Assistant"):
                                result = await Runner.run(agent, prompt)
                                return str(result.final_output)
                        
                        # Execute the async function
                        response = asyncio.run(get_response())
                        st.markdown(response)
                        
                        # Add assistant response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                    except Exception as e:
                        error_msg = f"Error getting response: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # Add a clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
            
    else:
        st.error("❌ Could not load AI agent")
        st.info("""
        **Troubleshooting:**
        1. Check that all dependencies are installed
        2. Ensure your OpenAI API key is set in .env file
        3. Try running the standalone version: `python agents/agentv2/agentv2.py`
        """)
    


# Run the page function (required for Streamlit multi-page apps)
ai_assistant_page() 