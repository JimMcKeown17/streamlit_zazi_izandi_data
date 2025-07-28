from openai import OpenAI
import streamlit as st
import json

from agents.agentv1.tool_schemas_v1 import TOOL_SCHEMAS
from agents.agentv1.tools_v1 import TOOLS

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Header
st.title("🤖 MasiAnalyze")
st.info("""Hi there! I'm MasiAnalyze. I'm here to help analyze, summarize, or explain the results of Masi's core literacy programme. You can ask me questions such as:
- How did the Grade R children do learning their letter sounds?
- Which schools performed the best?
- How did the children at Fumisukoma do? Please break it out by grade.
- How are the preschool children doing?
- What schools are struggling where we need to intervene?
""")

if "messages" not in st.session_state:
    # System prompt FIRST so tools are in context
    try:
        with open("/agents/agentv1/prompt.txt", "r") as f:
            system_prompt_template = f.read()
            
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
                # tools=TOOL_SCHEMAS,
                # tool_choice="auto",
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