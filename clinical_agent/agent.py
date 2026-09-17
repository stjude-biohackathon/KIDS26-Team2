import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage

from tools.text_to_sql import execute_sql_query
from tools.rag_engine import search_discharge_notes
from tools.clinical_stats import generate_descriptive_stats
from tools.data_viz import generate_graph

load_dotenv()

SYSTEM_PROMPT = """You are an advanced clinical data assistant querying the MIMIC-IV database.
You have two tools:
1. 'execute_sql_query': Run T-SQL queries against the 'mimiciv_derived' schema.
   Available views:
   - mimiciv_derived.v_patient_encounters(subject_id, gender, anchor_age, anchor_year, hadm_id, admission_type, admittime, dischtime, hospital_expire_flag, stay_id, first_careunit, last_careunit, icu_intime, icu_outtime, icu_los_days, icu_escalation_flag)
   - mimiciv_derived.v_patient_diagnoses(subject_id, hadm_id, seq_num, icd_code, icd_version, diagnosis_description)
   - mimiciv_derived.v_patient_labs(labevent_id, subject_id, hadm_id, charttime, lab_name, lab_fluid, lab_category, lab_value, lab_unit, ref_range_lower, ref_range_upper, abnormal_flag)
   - mimiciv_derived.v_patient_medications(subject_id, hadm_id, pharmacy_id, starttime, stoptime, drug, drug_type, dose, dose_unit, route, doses_per_24_hrs)
   - mimiciv_derived.v_microbiology(microevent_id, subject_id, hadm_id, chartdate, charttime, specimen_type, test_name, organism_identified, antibiotic_tested, dilution_comparison, dilution_value, interpretation)

2. 'search_discharge_notes': Performs hybrid search across clinical notes and discharge summaries.

RULES:
- When querying labs, use LIKE on lab_name (e.g., lab_name LIKE '%Hemoglobin%') and filter out NULL lab_value.
- Chain tools sequentially: Query SQL first to locate relevant IDs, then call search_discharge_notes using that context.
- Never attempt INSERT, UPDATE, DROP, or DELETE queries.
- If the user asks for averages, percentiles, or statistical analysis on numerical data, use the 'generate_stats_report_tool'.
- If the user asks to visualize, plot, chart, or graph data, use the 'create_visualization_tool'.
"""

# 1. Wrap your existing functions in LangChain @tool decorators
@tool
def execute_sql_query_tool(query: str) -> str:
    """Executes a SELECT T-SQL query on the mimiciv_derived schema."""
    return str(execute_sql_query(query))

@tool
def search_discharge_notes_tool(search_term: str) -> str:
    """Searches textual discharge summaries for narratives and plans."""
    return str(search_discharge_notes(search_term))

@tool
def generate_stats_report_tool(query: str, target_column: str) -> str:
    """Run a SQL query and generate a statistical summary report (mean, median, std dev) for a numerical column."""
    return str(generate_descriptive_stats(query, target_column))

@tool
def create_visualization_tool(query: str, plot_type: str, x_column: str, y_column: str = None) -> str:
    """
    Generates a graph from SQL data. 
    plot_type must be one of: 'histogram', 'scatter', 'bar', 'box'.
    y_column is required for scatter and bar charts.
    """
    return str(generate_graph(query, plot_type, x_column, y_column))

tools = [execute_sql_query_tool, search_discharge_notes_tool, generate_stats_report_tool, create_visualization_tool]
tool_node = ToolNode(tools)

# 2. Initialize Claude
model = ChatAnthropic(
    model="claude-sonnet-5", 
    api_key=os.getenv("ANTHROPIC_API_KEY")
)
model_with_tools = model.bind_tools(tools)

# 3. Define the Agent Logic
def call_model(state: MessagesState):
    # Inject the system prompt before the conversation history
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

# 4. Define the Routing Logic (replaces the manual while loop)
def should_continue(state: MessagesState) -> str:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# 5. Build the State Graph
workflow = StateGraph(MessagesState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

# 6. Add Built-In Memory Checkpointer
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)

# 7. Update your turn logic to stream from the graph
def run_agent_turn(user_prompt: str, session_id: str = "default_clinical_session"):
    print(f"\n==========================================")
    print(f"User Query: {user_prompt} | Session: {session_id}")
    print(f"==========================================")
    
    # LangGraph remembers the history inside this thread_id
    config = {"configurable": {"thread_id": session_id}}
    
    # Stream tokens incrementally as Claude generates them
    for msg, metadata in graph.stream(
        {"messages": [HumanMessage(content=user_prompt)]}, 
        config, 
        stream_mode="messages"
    ):
        # We only want to yield text spoken by the agent node directly
        if metadata.get("langgraph_node") == "agent" and msg.content:
            if isinstance(msg.content, str):
                yield msg.content
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        yield block.get("text")
                    elif hasattr(block, "text"):
                        yield block.text

