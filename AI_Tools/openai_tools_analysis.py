import openai
import os
import json
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
from .ai_tools import DataAnalysisToolkit
from typing import Dict, List, Optional
from datetime import datetime
import traceback

# Load environment variables
load_dotenv()

# Global trace log for this session
TRACE_LOG = []

def setup_openai_client():
    """Initialize OpenAI client with API key from environment variables."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    
    client = openai.OpenAI(api_key=api_key)
    return client

def log_trace(event_type: str, data: Dict, iteration: int = None):
    """Add an event to the trace log."""
    trace_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "iteration": iteration,
        "data": data
    }
    TRACE_LOG.append(trace_entry)

def get_tool_definitions():
    """Define the available tools for the AI to use."""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_column_info",
                "description": "Get basic information about the dataset structure and columns",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "filter_data",
                "description": "Filter the dataset based on specific criteria",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "grade": {"type": "string", "description": "Grade level filter"},
                        "school": {"type": "string", "description": "School name filter"},
                        "ta": {"type": "string", "description": "Teaching assistant name filter"},
                        "min_score": {"type": "number", "description": "Minimum score filter"},
                        "max_score": {"type": "number", "description": "Maximum score filter"},
                        "class_name": {"type": "string", "description": "Class name filter"}
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "identify_top_performers",
                "description": "Identify top performing schools, TAs, or classes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "group_by": {"type": "string", "enum": ["school", "ta", "class"], "description": "What to group by"},
                        "metric": {"type": "string", "default": "letters_correct", "description": "Metric to analyze"},
                        "top_n": {"type": "integer", "default": 5, "description": "Number of top performers to return"},
                        "min_sample_size": {"type": "integer", "default": 5, "description": "Minimum sample size for inclusion"}
                    },
                    "required": ["group_by"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "identify_underperformers",
                "description": "Identify underperforming schools, TAs, or classes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "group_by": {"type": "string", "enum": ["school", "ta", "class"], "description": "What to group by"},
                        "metric": {"type": "string", "default": "letters_correct", "description": "Metric to analyze"},
                        "bottom_n": {"type": "integer", "default": 3, "description": "Number of underperformers to return"},
                        "min_sample_size": {"type": "integer", "default": 5, "description": "Minimum sample size for inclusion"}
                    },
                    "required": ["group_by"]
                }
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "benchmark_analysis",
                "description": "Analyze performance against midline or year-end benchmarks",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "group_by": {"type": "string", "enum": ["school", "ta", "class"], "description": "Optional grouping variable"},
                        "benchmark_type": {"type": "string", "enum": ["midline", "year_end"], "default": "midline", "description": "Which benchmark to use"}
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "variance_analysis",
                "description": "Analyze variance within and between groups",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "group_by": {"type": "string", "enum": ["school", "ta", "class", "grade"], "description": "What to group by"},
                        "metric": {"type": "string", "default": "letters_correct", "description": "Metric to analyze"}
                    },
                    "required": ["group_by"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "compare_groups",
                "description": "Compare two specific groups of students",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "group1_filter": {
                            "type": "object",
                            "description": "Filters for first group (e.g., {'grade': 'Grade 1', 'school': 'School A'})"
                        },
                        "group2_filter": {
                            "type": "object", 
                            "description": "Filters for second group (e.g., {'grade': 'Grade 1', 'school': 'School B'})"
                        },
                        "metric": {"type": "string", "default": "letters_correct", "description": "Metric to compare"}
                    },
                    "required": ["group1_filter", "group2_filter"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_student_performance_distribution",
                "description": "Get distribution of student performance scores",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "grade": {"type": "string", "description": "Optional grade filter"}
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "identify_at_risk_students",
                "description": "Identify students who may need additional support",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "grade": {"type": "string", "description": "Optional grade filter"},
                        "threshold_percentile": {"type": "number", "default": 25, "description": "Percentile threshold for at-risk classification"}
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "prepare_visualization_data",
                "description": "Prepare data for creating charts and visualizations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "chart_type": {"type": "string", "enum": ["bar", "scatter"], "description": "Type of chart"},
                        "x_column": {"type": "string", "description": "X-axis variable"},
                        "y_column": {"type": "string", "description": "Y-axis variable"},
                        "group_by": {"type": "string", "description": "Optional grouping variable"},
                        "filter_params": {"type": "object", "description": "Optional filters to apply"}
                    },
                    "required": ["chart_type", "x_column", "y_column"]
                }
            }
        }
    ]

def execute_tool_call(toolkit: DataAnalysisToolkit, tool_name: str, arguments: Dict, iteration: int) -> Dict:
    """Execute a tool call using the DataAnalysisToolkit."""
    start_time = datetime.now()
    
    log_trace("tool_execution_start", {
        "function_name": tool_name,
        "arguments": arguments
    }, iteration)
    
    try:
        if tool_name == "get_column_info":
            result = toolkit.get_column_info()
        elif tool_name == "filter_data":
            result = toolkit.filter_data(**arguments)
        elif tool_name == "identify_top_performers":
            result = toolkit.identify_top_performers(**arguments)
        elif tool_name == "identify_underperformers":
            result = toolkit.identify_underperformers(**arguments)
        elif tool_name == "benchmark_analysis":
            result = toolkit.benchmark_analysis(**arguments)
        elif tool_name == "variance_analysis":
            result = toolkit.variance_analysis(**arguments)
        elif tool_name == "compare_groups":
            result = toolkit.compare_groups(**arguments)
        elif tool_name == "get_student_performance_distribution":
            result = toolkit.get_student_performance_distribution(**arguments)
        elif tool_name == "identify_at_risk_students":
            result = toolkit.identify_at_risk_students(**arguments)
        elif tool_name == "prepare_visualization_data":
            result = toolkit.prepare_visualization_data(**arguments)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        log_trace("tool_result", {
            "function_name": tool_name,
            "execution_time_seconds": execution_time,
            "result_size": len(str(result)),
            "success": "error" not in result
        }, iteration)
        
        return result
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        
        log_trace("tool_error", {
            "function_name": tool_name,
            "error": str(e),
            "execution_time_seconds": execution_time,
            "traceback": traceback.format_exc()
        }, iteration)
        
        return {"error": f"Error executing {tool_name}: {str(e)}"}

def create_system_prompt() -> str:
    """Create the system prompt for the AI analyst."""
    return """
    You are an expert education data analyst specializing in early grade reading assessments (EGRA).
    You're analyzing midline data from June 2025 for the "Zazi iZandi" literacy intervention program in South Africa.
    
    IMPORTANT CONTEXT:
    - This is MIDLINE data (halfway through school year, ~5-6 months of instruction)
    - Grade R students (age 5-6): Midline target ~10+ letters, Year-end benchmark 20+ letters
    - Grade 1 students (age 6-7): Midline target ~20+ letters, Year-end benchmark 40+ letters
    - South African national average for Grade 1 is 27% above year-end benchmark
    - Focus on identifying performance patterns, variance, and benchmark comparisons
    
    YOUR ANALYSIS PRIORITIES:
    1. Benchmark comparisons (most important) - assess progress toward realistic midline targets
    2. Identify top performers and underperformers (schools, TAs, students)
    3. Analyze variance between schools, classes, grades, TAs
    4. Provide actionable insights for remaining school year
    
    TOOL USAGE GUIDELINES:
    - BE EXTREMELY EFFICIENT: Answer simple questions in 1-2 tool calls maximum
    - For "top TA" questions: Call identify_top_performers(group_by="ta") ONCE and analyze results
    - NEVER repeat the same tool call with identical parameters
    - After 2 tool calls, you MUST synthesize and provide your analysis
    - Do NOT explore additional data unless specifically asked
    - Stop calling tools when you have enough information to answer the question
    
    Provide clear, actionable insights focused on educational outcomes and improvement opportunities.
    """

def generate_initial_analysis(df: pd.DataFrame, model: str = "gpt-4o-mini") -> str:
    """Generate an initial comprehensive analysis of the dataset."""
    client = setup_openai_client()
    if not client:
        return None
    
    toolkit = DataAnalysisToolkit(df)
    
    # Initial conversation to get baseline analysis
    messages = [
        {
            "role": "system", 
            "content": create_system_prompt()
        },
        {
            "role": "user",
            "content": """Please provide a comprehensive initial analysis of this education assessment dataset. 
            Start by exploring the data structure, then focus on:
            1. Overall benchmark performance assessment
            2. Identification of top and underperforming groups
            3. Key variance patterns
            4. Critical insights and recommendations
            
            Use the available tools to gather the necessary information for your analysis."""
        }
    ]
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=get_tool_definitions(),
            tool_choice="auto",
            max_tokens=2000,
            temperature=0.7
        )
        
        # Process the response and handle tool calls
        return process_ai_response(client, toolkit, messages, response, model)
        
    except Exception as e:
        return f"Error generating initial analysis: {str(e)}"

def answer_question(df: pd.DataFrame, question: str, model: str = "gpt-4o-mini") -> str:
    """Answer a specific question about the data using tools."""
    
    client = setup_openai_client()
    if not client:
        return "Failed to setup OpenAI client"
    
    try:
        toolkit = DataAnalysisToolkit(df)
    except Exception as e:
        return f"Error initializing toolkit: {str(e)}"
    
    messages = [
        {
            "role": "system",
            "content": create_system_prompt()
        },
        {
            "role": "user", 
            "content": f"""Please answer this specific question about the assessment data: {question}

IMPORTANT: This is a focused question that should require only 2-3 tool calls. Do NOT explore beyond what's needed to answer this specific question.

For questions about "top TAs": Use identify_top_performers(group_by="ta") and provide your analysis.
For questions about "school comparison": Use identify_top_performers(group_by="school") and provide your analysis.  
For questions about "benchmarks": Use benchmark_analysis() and provide your analysis.

Answer the question directly and concisely based on the tool results."""
        }
    ]
    
    try:
        tools = get_tool_definitions()
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=1500,
            temperature=0.7
        )
        
        # Check response structure
        if not response.choices:
            return "Error: No response choices returned from OpenAI"
        
        if not response.choices[0].message:
            return "Error: No message in response choice"
        
        return process_ai_response(client, toolkit, messages, response, model)
        
    except json.JSONDecodeError as e:
        return f"JSON parsing error: {str(e)}"
    except openai.APIError as e:
        return f"OpenAI API error: {str(e)}"
    except Exception as e:
        return f"Error answering question: {str(e)}"

def process_ai_response(client, toolkit: DataAnalysisToolkit, messages: List[Dict], 
                       response, model: str, max_iterations: int = 4) -> str:
    """Process AI response and handle tool calls iteratively."""
    iteration = 0
    
    # Clear previous trace log for new analysis
    global TRACE_LOG
    TRACE_LOG = []
    
    while iteration < max_iterations:
        iteration += 1
        
        log_trace("iteration_start", {
            "message_count": len(messages)
        }, iteration)
        
        response_message = response.choices[0].message
        
        # If no tool calls, return the final answer
        if not response_message.tool_calls:
            log_trace("final_response", {
                "content": response_message.content,
                "total_iterations": iteration - 1
            })
            return response_message.content
        
        # Log the tool calls for this iteration with error handling
        tool_call_info = []
        
        try:
            for tc in response_message.tool_calls:
                try:
                    parsed_args = json.loads(tc.function.arguments)
                    tool_call_info.append({
                        "name": tc.function.name,
                        "arguments": parsed_args
                    })
                except json.JSONDecodeError as e:
                    return f"Error parsing tool arguments: {str(e)}"
        except Exception as e:
            return f"Error processing tool calls: {str(e)}"
        
        log_trace("tool_calls", {
            "tool_calls": tool_call_info,
            "assistant_content": response_message.content
        }, iteration)
        
        # Add the assistant's response to conversation
        messages.append({
            "role": "assistant",
            "content": response_message.content,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                }
                for tool_call in response_message.tool_calls
            ]
        })
        
        # Execute each tool call
        for tool_call in response_message.tool_calls:
            try:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                # Execute the tool
                tool_result = execute_tool_call(toolkit, function_name, function_args, iteration)

                # Add tool result to conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, indent=2)
                })
                    
            except json.JSONDecodeError as e:
                return f"JSON error executing tool: {str(e)}"
            except Exception as e:
                return f"Error executing tool {function_name}: {str(e)}"
        
        # Add synthesis prompt after 2 iterations to encourage stopping
        if iteration >= 2:
            messages.append({
                "role": "user",
                "content": "You now have sufficient information to answer the question. Please provide your analysis and conclusion without making additional tool calls."
            })
        
        # Get the next response
        try:
            # After 2 iterations, disable tools completely
            if iteration >= 2:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=1500,
                    temperature=0.7
                )
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=get_tool_definitions(),
                    tool_choice="auto",
                    max_tokens=1500,
                    temperature=0.7
                )
            
            log_trace("iteration_complete", {
                "success": True
            }, iteration)
                
        except Exception as e:
            log_trace("api_error", {
                "error": str(e),
                "iteration": iteration
            }, iteration)
            return f"Analysis failed at iteration {iteration} due to API error: {str(e)}"
    
    # If we hit max iterations, return what we have
    final_message = response.choices[0].message
    partial_response = final_message.content if final_message.content else ""
    
    log_trace("max_iterations_reached", {
        "final_content": partial_response,
        "total_tool_calls": sum(1 for entry in TRACE_LOG if entry["event_type"] == "tool_execution_start")
    })
    
    return f"""Analysis reached iteration limit after {max_iterations} tool calls, but here's what I found:

{partial_response}

**🔍 Trace Summary:**
- Total iterations: {max_iterations}
- Total tool calls: {sum(1 for entry in TRACE_LOG if entry["event_type"] == "tool_execution_start")}
- Tools used: {', '.join(set(entry["data"]["function_name"] for entry in TRACE_LOG if entry["event_type"] == "tool_execution_start"))}

💡 **Optimization Tips**:
- Try asking more specific questions like: "Which schools improved the most?"
- Avoid broad questions that require multiple analysis types
- Consider using the context-only method for simpler queries"""

def analyze_with_tools(df: pd.DataFrame, analysis_type: str = "initial", 
                      question: str = None, model: str = "gpt-4o-mini") -> str:
    """
    Main function to analyze data using AI tools.
    
    Args:
        df: DataFrame to analyze
        analysis_type: "initial" for comprehensive analysis or "question" for specific Q&A
        question: Specific question to answer (required if analysis_type="question")
        model: OpenAI model to use
    
    Returns:
        Analysis response string
    """
    if analysis_type == "initial":
        return generate_initial_analysis(df, model)
    elif analysis_type == "question" and question:
        return answer_question(df, question, model)
    else:
        return "Invalid analysis type or missing question parameter." 