import streamlit as st
import asyncio
import nest_asyncio
import sys
import os
import traceback
import json
from google.oauth2 import service_account

# Add parent directory to Python path to find multi_hop_agent package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_hop_agent.runner import run_agent_on_prompt
from multi_hop_agent.config.settings import LLM_MODEL_NAME, GOOGLE_PROJECT_ID, GOOGLE_LOCATION, GOOGLE_CREDENTIALS_JSON
from multi_hop_agent.utils.helpers import extract_after_think
from langchain_google_vertexai import ChatVertexAI

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
st.sidebar.info(f"**Model:** {LLM_MODEL_NAME}")
st.sidebar.info(f"**Temperature:** {temperature}")
st.sidebar.info(f"**Top-p:** {top_p}")
st.sidebar.info(f"**Top-k:** {top_k}")



# Check if credentials are configured via Streamlit secrets
def get_google_api_key():
    """Get Google API key from Streamlit secrets"""
    try:
        return st.secrets.get("google", {}).get("api_key")
    except:
        return None

def get_google_credentials_path():
    """Get Google credentials path from Streamlit secrets"""
    try:
        # Since we have the full JSON in secrets, we'll use a temporary file path
        return st.secrets.get("google", {}).get("service_account_json")
    except:
        return None

# Check credentials
google_api_key = get_google_api_key()
google_credentials_json = get_google_credentials_path()

if not google_api_key:
    st.error("⚠️ GOOGLE_API_KEY not found in Streamlit secrets!")
    st.info("""
    **To run this app:**
    1. Deploy to Streamlit Cloud
    2. Go to Settings → Secrets
    3. Add your Google API credentials in TOML format:
    
    ```toml
    [google]
    api_key = "your_actual_api_key_here"
    service_account_json = "your_full_json_content_here"
    ```
    """)
    st.stop()

# Main app
st.title("🧠 Multi-Hop Reasoning Agent")
st.markdown("This agent uses a multi-step reasoning pipeline to answer complex questions.")

# Single question input
st.header("❓ Ask a Question")

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

if st.button("🚀 Run Agent", type="primary", use_container_width=True):
    if user_question.strip():

        with st.spinner("Running multi-hop reasoning (may take a minute)..."):
            try:
                # Run the agent with current temperature, top_p, and top_k settings
                result = run_agent_on_prompt(user_question, temperature=temperature, top_p=top_p, top_k=top_k)
                
                if result:
                    st.success("🎯 Multi-hop reasoning completed! Here's your answer:")
                    
                    # Display the final answer
                    st.subheader("📋 Final Answer")
                    st.write(result.get("prompt", "No answer generated"))
                    
                    # Display execution flow table
                    if result.get("log"):
                        st.subheader("🔄 Execution Flow")
                        
                        # Create a clean table showing execution order and outputs
                        execution_data = []
                        for i, entry in enumerate(result.get("log", []), 1):
                            # Parse the log entry to extract node name and output
                            if ":" in entry:
                                node_name, output = entry.split(":", 1)
                                execution_data.append({
                                    "Step": i,
                                    "Node": node_name.strip(),
                                    "Output": output.strip()[:100] + "..." if len(output.strip()) > 100 else output.strip()
                                })
                            else:
                                execution_data.append({
                                    "Step": i,
                                    "Node": "Unknown",
                                    "Output": entry[:100] + "..." if len(entry) > 100 else entry
                                })
                        
                        if execution_data:
                            st.dataframe(
                                execution_data,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "Step": st.column_config.NumberColumn("Step", width="small"),
                                    "Node": st.column_config.TextColumn("Node", width="medium"),
                                    "Output": st.column_config.TextColumn("Output", width="large")
                                }
                            )
                else:
                    st.error("❌ Agent failed to complete")
                    
            except Exception as e:
                st.error(f"❌ Error running agent: {str(e)}")
                st.exception(e)
    else:
        st.warning("Please enter a question.") 