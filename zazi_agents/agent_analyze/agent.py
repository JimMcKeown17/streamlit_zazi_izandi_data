from openai import OpenAI
import streamlit as st
import sys
import os
import json

# Add the root directory to the Python path to access data_loader
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
# Add the current directory to the Python path to access tool_schema and tools
sys.path.append(os.path.dirname(__file__))

from data_loader import load_zazi_izandi_2025, load_zazi_izandi_2023, load_zazi_izandi_2024
from tool_schema import TOOL_SCHEMAS
from tools import TOOLS

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Header
st.title("🤖 ZaziAnalyze")
st.info("""Hi there! I'm ZaziAnalyze. I'm here to help analyze, summarize, or explain the results of the Zazi Literacy Programme. You can ask me questions such as:
- How did the Grade R children do learning their letter sounds?
- What percent of Grade 1 children met the benchmark?
- What are South African benchmarks for children?
- How do Zazi iZandi children do compared to control groups?
""")

if "messages" not in st.session_state:
    # System prompt FIRST so tools are in context
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")
        with open(prompt_path, "r") as f:
            system_prompt_template = f.read()
        
            # I can add code here to dynamically add data into the prompt if necessary. Such as calculating total number of current youth or schools.
            system_prompt = system_prompt_template
            
    except FileNotFoundError:
        system_prompt = "You are a helpful assistant."  # Fallback
    except KeyError as e:
        st.error(f"Error formatting prompt: {e}")
        system_prompt = "You are a helpful assistant."  # Fallback
    
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

# Display chat history
for message in st.session_state.messages:
    # Handle both dicts and objects for gracefully handling old session states
    role = message.get("role") if isinstance(message, dict) else message.role
    if role in ["user", "assistant"]:
        content = message.get("content") if isinstance(message, dict) else message.content
        if content:  # Don't display empty assistant messages from tool calls
            with st.chat_message(role):
                st.write(content)

# Get user prompt and process it                
prompt = st.chat_input("Enter a message")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Normalize messages to a list of dicts for the API
        api_messages = []
        for msg in st.session_state.messages:
            if isinstance(msg, dict):
                api_messages.append(msg)
            else:
                api_messages.append(msg.model_dump())

        MAX_TOOL_CALLS = 8
        final_response = None
        
        for _ in range(MAX_TOOL_CALLS):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=api_messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
            )
            response_message = response.choices[0].message
            api_messages.append(response_message.model_dump())

            if not response_message.tool_calls:
                final_response = response_message.content
                message_placeholder.markdown(final_response)
                break

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_to_call = TOOLS[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                api_messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
        else:
            final_response = "Reached maximum number of tool calls."
            message_placeholder.markdown(final_response)
        
        # Only append the final assistant message to session state
        if final_response:
            st.session_state.messages.append({"role": "assistant", "content": final_response})