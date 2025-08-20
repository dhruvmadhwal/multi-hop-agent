import streamlit as st
import asyncio
import nest_asyncio
import sys
import os
import time

# Add parent directory to Python path to find multi_hop_agent package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_hop_agent.runner import run_agent_on_prompt
from multi_hop_agent.config.settings import get_llm_config

# Apply nest_asyncio for Streamlit compatibility
nest_asyncio.apply()

# Page configuration
st.set_page_config(
    page_title="Multi-Hop Reasoning Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar for configuration
st.sidebar.title("Configuration")

# LLM parameter controls
st.sidebar.markdown("### LLM Settings")
temperature = st.sidebar.slider(
    "Temperature", 
    min_value=0.0, 
    max_value=2.0, 
    value=0.1, 
    step=0.1,
    help="Controls randomness in responses. Lower = more focused, Higher = more creative"
)

top_p = st.sidebar.slider(
    "Top-p", 
    min_value=0.0, 
    max_value=1.0, 
    value=0.95, 
    step=0.05,
    help="Controls diversity via nucleus sampling. Lower = more focused, Higher = more diverse"
)

top_k = st.sidebar.slider(
    "Top-k", 
    min_value=1, 
    max_value=100, 
    value=40, 
    step=1,
    help="Limits vocabulary to top k tokens. Lower = more focused, Higher = more diverse"
)

st.sidebar.markdown("### Current Settings")
llm_model_name = get_llm_config()
st.sidebar.info(f"**Model:** {llm_model_name}")
st.sidebar.info(f"**Temperature:** {temperature}")
st.sidebar.info(f"**Top-p:** {top_p}")
st.sidebar.info(f"**Top-k:** {top_k}")

# Add GitHub link in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.markdown("[📚 Learn more about this agent](https://github.com/dhruvmadhwal/multi-hop-agent)")

# Check if credentials are configured via Streamlit secrets
def check_credentials():
    """Check if all required Google Cloud credentials are available"""
    try:
        secrets = st.secrets.get("google", {})
        required_fields = ["service_account_json", "project_id", "location"]
        missing_fields = [field for field in required_fields if not secrets.get(field)]
        
        if missing_fields:
            return False, f"Missing: {', '.join(missing_fields)}"
        return True, "All credentials available"
    except:
        return False, "Could not access Streamlit secrets"

# Check credentials
credentials_ok, credentials_message = check_credentials()

if not credentials_ok:
    st.error(f"{credentials_message}")
    st.info("""
    **To run this app:**
    1. Deploy to Streamlit Cloud
    2. Go to Settings → Secrets
    3. Add your Google API credentials in TOML format:
    
    ```toml
    [google]
    service_account_json = "your_full_json_content_here"
    project_id = "your_project_id_here"
    location = "us-central1"
    ```
    """)
    st.stop()

# Main app
st.title("🧠 Multi-Hop Reasoning Agent")
st.markdown("This agent uses a multi-step reasoning pipeline to answer complex questions. Learn more about the agent [here](https://github.com/dhruvmadhwal/multi-hop-agent).")

# Example questions dropdown
example_questions = {
    "Select an example question...": "",
    "🏟️ What is the batting hand of each of the first five picks in the 1998 MLB draft? (FanoutQA)": "What is the batting hand of each of the first five picks in the 1998 MLB draft?",
    "📚 I am the narrator character in the final novel written by the recipient of the 1963 Hugo Award for Best Novel. Who am I? (Frames)": "I am the narrator character in the final novel written by the recipient of the 1963 Hugo Award for Best Novel. Who am I?",
    "🏭 What is the symbol of the Saints from the headquarters location of Ten High's manufacturer called? (Musique)": "What is the symbol of the Saints from the headquarters location of Ten High's manufacturer called?"
}

selected_example = st.selectbox(
    "💡 Try an example question:",
    options=list(example_questions.keys()),
    help="Select an example to see what kind of complex questions this agent can handle"
)

user_question = st.text_area(
    "Enter your question:",
    value=example_questions[selected_example] if selected_example != "Select an example question..." else "",
    placeholder="e.g., What is the population density of the driest capital city in the world?",
    height=100
)

# Agent diagram - Define the nodes and connections
def create_agent_diagram(active_node=None):
    # Define the diagram with highlighted active node
    nodes = ["Orchestrator", "Decomposer", "FactRecall", "Coder", "FinalAnswer", "ProgressAssessment"]
    
    mermaid_code = f"""
    flowchart TD
        start_node([start]):::special
        end_node([end]):::special
        
        orchestrator_node["Orchestrator"]:::{"active" if active_node == "Orchestrator" else "default"}
        decomposer_node["Decomposer"]:::{"active" if active_node == "Decomposer" else "default"}
        factrecall_node["FactRecall"]:::{"active" if active_node == "FactRecall" else "default"}
        coder_node["Coder"]:::{"active" if active_node == "Coder" else "default"}
        finalanswer_node["FinalAnswer"]:::{"active" if active_node == "FinalAnswer" else "default"}
        progressassessment_node["ProgressAssessment"]:::{"active" if active_node == "ProgressAssessment" else "default"}
        
        start_node --> orchestrator_node
        
        orchestrator_node -.-> decomposer_node
        orchestrator_node -.-> coder_node
        orchestrator_node -.-> finalanswer_node
        orchestrator_node -.-> factrecall_node
        
        decomposer_node --> factrecall_node
        decomposer_node --> orchestrator_node
        
        factrecall_node --> progressassessment_node
        coder_node --> progressassessment_node
        
        progressassessment_node --> orchestrator_node
        
        finalanswer_node --> end_node
        
        classDef default fill:#e9ecef,stroke:#ced4da,stroke-width:1px
        classDef active fill:#f9c74f,stroke:#e09f3e,stroke-width:2px
        classDef special fill:#c7b5e6,stroke:#9d84d2,stroke-width:1px
    """
    
    # Clean up the mermaid code (remove indentation)
    mermaid_code = "\n".join(line.strip() for line in mermaid_code.strip().split("\n"))
    return mermaid_code

# Helper function to extract questions and answers from log
def extract_questions_and_answers(log_entries):
    qa_pairs = []
    current_question = None
    
    for entry in log_entries:
        if ":" in entry:
            node_name, content = entry.split(":", 1)
            node_name = node_name.strip()
            content = content.strip()
            
            # Capture questions from Orchestrator to Decomposer
            if node_name == "Orchestrator" and "NEXT: Decomposer" in content:
                current_question = content.split("USER: ")[-1].split("\n")[0] if "USER: " in content else None
            
            # Capture answers from Decomposer back to Orchestrator
            elif node_name == "Decomposer" and current_question:
                qa_pairs.append({
                    "question": current_question,
                    "answer": content,
                    "node": "Decomposer"
                })
                current_question = None
            
            # Capture questions from Orchestrator to FactRecall
            elif node_name == "Orchestrator" and "NEXT: FactRecall" in content:
                current_question = content.split("USER: ")[-1].split("\n")[0] if "USER: " in content else None
            
            # Capture answers from FactRecall back to Orchestrator
            elif node_name == "FactRecall" and current_question:
                qa_pairs.append({
                    "question": current_question,
                    "answer": content,
                    "node": "FactRecall"
                })
                current_question = None
            
            # Capture questions from Orchestrator to Coder
            elif node_name == "Orchestrator" and "NEXT: Coder" in content:
                current_question = content.split("USER: ")[-1].split("\n")[0] if "USER: " in content else None
            
            # Capture answers from Coder back to Orchestrator
            elif node_name == "Coder" and current_question:
                qa_pairs.append({
                    "question": current_question,
                    "answer": content,
                    "node": "Coder"
                })
                current_question = None
            
            # Capture questions from Orchestrator to ProgressAssessment
            elif node_name == "Orchestrator" and "NEXT: ProgressAssessment" in content:
                current_question = content.split("USER: ")[-1].split("\n")[0] if "USER: " in content else None
            
            # Capture answers from ProgressAssessment back to Orchestrator
            elif node_name == "ProgressAssessment" and current_question:
                qa_pairs.append({
                    "question": current_question,
                    "answer": content,
                    "node": "ProgressAssessment"
                })
                current_question = None
    
    return qa_pairs
# Helper function to extract questions and answers from agent state and logs
def extract_questions_and_answers_from_agent(agent_state, log_entries):
    qa_pairs = []
    
    # First, try to get Q&A pairs from the agent's answered_questions state
    if 'answered_questions' in agent_state and agent_state['answered_questions']:
        for question, answer in agent_state['answered_questions'].items():
            qa_pairs.append({
                "question": question,
                "answer": answer,
                "node": "Multi-Hop Agent"
            })
    
    # If no answered_questions, try to extract from log entries
    if not qa_pairs and log_entries:
        current_question = None
        
        for entry in log_entries:
            if ":" in entry:
                node_name, content = entry.split(":", 1)
                node_name = node_name.strip()
                content = content.strip()
                
                # Look for Decomposer generating questions
                if node_name == "Decomposer" and "Generated question" in content:
                    # Extract the question from the log entry
                    if "'" in content:
                        question = content.split("'")[1] if len(content.split("'")) > 1 else content
                        current_question = question
                
                # Look for FactRecall answering questions
                elif node_name == "FactRecall" and current_question:
                    # Extract the answer from the log entry
                    if "Reply=" in content:
                        answer = content.split("Reply=")[1].strip()
                        qa_pairs.append({
                            "question": current_question,
                            "answer": answer,
                            "node": "FactRecall"
                        })
                        current_question = None
                
                # Look for Coder results
                elif node_name == "Coder" and current_question:
                    if "Result:" in content:
                        answer = content.split("Result:")[1].strip()
                        qa_pairs.append({
                            "question": current_question,
                            "answer": answer,
                            "node": "Coder"
                        })
                        current_question = None
    
    return qa_pairs

# Run Agent button right after the question input
if st.button("🚀 Run Agent", type="primary", use_container_width=True):
    # Create placeholders for real-time updates
    execution_placeholder = st.empty()
    questions_placeholder = st.empty()
    answer_placeholder = st.empty()

    if user_question.strip():
        # Initialize session state for tracking execution
        if 'execution_data' not in st.session_state:
            st.session_state.execution_data = []
        else:
            st.session_state.execution_data = []
        
        if 'active_node' not in st.session_state:
            st.session_state.active_node = None
        
        if 'qa_pairs' not in st.session_state:
            st.session_state.qa_pairs = []
        
        # Setup the execution table
        st.subheader("🔄 Execution Flow")
        execution_table = st.empty()
        
        # Setup the final answer placeholder
        status_text = st.empty()
        status_text.info("🚀 Agent is running...")
        
        # Run the agent with real-time updates
        with st.spinner("Running multi-hop reasoning..."):
            try:
                # Create a custom async function to process results in real-time
                async def process_agent_results():
                    # Initialize LLM and build agent graph (simplified - actual implementation in runner.py)
                    from multi_hop_agent.utils.llm import initialize_llm
                    from multi_hop_agent.graph.agent_graph import build_agent_graph
                    from multi_hop_agent.models.schema import AgentState
                    
                    # Initialize LLM
                    llm = initialize_llm(temperature=temperature, top_p=top_p, top_k=top_k)
                    
                    # Build agent graph
                    app = build_agent_graph(llm)
                    
                    # Create initial state
                    initial_state: AgentState = {
                        "task": user_question,
                        "log": [],
                        "fact_sheet": "",
                        "answered_questions": {},
                        "prompt": "",
                        "reply": "",
                        "sender": "",
                        "next_node": "Orchestrator",
                        "coder_code": None,
                        "coder_result": None,
                        "progress_tracker": None,
                        "last_question": None,
                        "last_agent_reply": None,
                        "last_answer": None,
                        "last_sender": None,
                        "stall_reason": None,
                        "stall_count": 0,
                        "final_answer_instruction": None,
                        "progress_assessment": None,
                        "progress_status": None
                    }
                    
                    # Stream through the agent graph
                    current_state = initial_state.copy()
                    final_state_before_end = None
                    
                    try:
                        async for step_output in app.astream(
                            current_state,
                            config={"recursion_limit": 100}
                        ):
                            for node_name, node_update in step_output.items():
                                # Update active node status
                                if "next_node" in node_update:
                                    st.session_state.active_node = node_update["next_node"]
                                    
                                    # Show progress indicators for different nodes
                                    if node_update["next_node"] == "Decomposer":
                                        status_text.info("🔍 Decomposer is breaking down the question into sub-questions...")
                                    elif node_update["next_node"] == "FactRecall":
                                        status_text.info("📚 FactRecall is retrieving relevant information...")
                                    elif node_update["next_node"] == "Coder":
                                        status_text.info("💻 Coder is executing code to find answers...")
                                    elif node_update["next_node"] == "ProgressAssessment":
                                        status_text.info("🔄 ProgressAssessment is analyzing the current state and determining next steps...")
                                    elif node_update["next_node"] == "FinalAnswer":
                                        status_text.success("🎯 FinalAnswer is generating the final response...")
                                    elif node_update["next_node"] == "END":
                                        status_text.success("✅ Multi-hop reasoning completed!")
                                
                                # Update log entries
                                if 'log' in node_update:
                                    current_state['log'] = current_state.get('log', []) + node_update['log']
                                    
                                    # Update execution data for table
                                    for entry in node_update['log']:
                                        if ":" in entry:
                                            node, output = entry.split(":", 1)
                                            st.session_state.execution_data.append({
                                                "Step": len(st.session_state.execution_data) + 1,
                                                "Node": node.strip(),
                                                "Output": output.strip()[:100] + "..." if len(output.strip()) > 100 else output.strip()
                                            })
                                        else:
                                            st.session_state.execution_data.append({
                                                "Step": len(st.session_state.execution_data) + 1,
                                                "Node": "Unknown",
                                                "Output": entry[:100] + "..." if len(entry) > 100 else entry
                                            })
                                    
                                    # Update execution table
                                    execution_table.dataframe(
                                        st.session_state.execution_data,
                                        use_container_width=True,
                                        hide_index=True,
                                        column_config={
                                            "Step": st.column_config.NumberColumn("Step", width="small"),
                                            "Node": st.column_config.TextColumn("Node", width="medium"),
                                            "Output": st.column_config.TextColumn("Output", width="large")
                                        }
                                    )
                                    
                                    # Extract and update questions and answers for the collapsible element
                                    st.session_state.qa_pairs = extract_questions_and_answers_from_agent(current_state, current_state['log'])
                                
                                # Update current state
                                current_state.update({k: v for k, v in node_update.items() if k != 'log'})
                                
                                # Check for end condition
                                if node_update.get("next_node") == "END":
                                    final_state_before_end = current_state.copy()
                                    break
                    except Exception as e:
                        st.error(f"Error during agent execution: {e}")
                    
                    return final_state_before_end or current_state
                
                # Run the async function
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(process_agent_results())
                
                if result:
                    # Show final answer from the correct field
                    status_text.success("🎯 Final answer:")
                    final_answer = result.get("reply", result.get("prompt", "No answer generated"))
                    st.write(final_answer)
                    
                    # Extract Q&A pairs from the final agent state
                    final_qa_pairs = extract_questions_and_answers_from_agent(result, result.get('log', []))
                    
                    # Show question decomposition in a collapsible element
                    with st.expander("🔍 Question Decomposition", expanded=False):
                        st.markdown("""
                        <h2 style="font-size: 2em; margin-bottom: 15px;">
                            🤔 Decomposed Questions & Answers
                        </h2>
                        """, unsafe_allow_html=True)
                        
                        if final_qa_pairs and len(final_qa_pairs) > 0:
                            for i, qa in enumerate(final_qa_pairs):
                                st.markdown(f"**Q{i+1}: {qa['question']}**")
                                st.markdown(f"**Answer:** {qa['answer']}")
                                st.divider()
                        else:
                            st.warning("No question decomposition data found. This might be because:")
                            st.markdown("""
                            - The agent didn't generate sub-questions
                            - The agent completed without going through decomposition steps
                            - The answered_questions state is empty
                            """)
                            
                            # Show debug info about the agent state
                            st.subheader("🔍 Agent State Debug Info")
                            st.json({
                                "has_answered_questions": bool(result.get('answered_questions')),
                                "answered_questions_count": len(result.get('answered_questions', {})),
                                "log_entries_count": len(result.get('log', [])),
                                "final_node": result.get('next_node'),
                                "sender": result.get('sender')
                            })
                    
                else:
                    st.error("❌ Agent failed to complete")
                    
            except Exception as e:
                st.error(f"Error running agent: {str(e)}")
                st.exception(e)
    else:
        st.warning("Please enter a question.") 