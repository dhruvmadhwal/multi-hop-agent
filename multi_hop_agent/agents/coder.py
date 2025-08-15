"""
Coder agent implementation.

This module contains the implementation of the Coder agent, which is responsible
for executing Python code to perform calculations or analyses.
"""
import re
from multi_hop_agent.models.schema import AgentState
from multi_hop_agent.prompts.system_prompts import CODER_SYS
from multi_hop_agent.utils.llm import chat
from langchain_experimental.tools.python.tool import PythonREPLTool

# Regex to find Python code blocks
PYTHON_CODE_BLOCK_REGEX = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

# Initialize Python REPL tool
python_tool = PythonREPLTool()

def coder_node(state: AgentState, llm, coder_parser=None) -> AgentState:
    """
    Coder Node: Executes Python code to perform calculations or analyses.
    Invoked by Orchestrator when decision is ASK_CODER.
    
    Args:
        state: Current agent state
        llm: LLM instance
        coder_parser: Optional parser for coder output
        
    Returns:
        Updated agent state with code execution results
    """
    print("\n=== Coder Node Start ===")
    prompt = state["prompt"]

    print(f"Coder - Prompt: {prompt}")

    # Call the LLM to generate code/response
    system_msg = CODER_SYS
    llm_response = chat(llm, system_msg, prompt)
    print(f"Coder - LLM Raw Response: {llm_response}")

    generated_code = None
    execution_output = None

    # Parse the LLM's response for a Python code block
    match = PYTHON_CODE_BLOCK_REGEX.search(str(llm_response))

    if match:
        generated_code = match.group(1).strip()
        print(f"Coder: Found code block:\n{generated_code}")

        # Execute the code block using the Python REPL Tool
        try:
            print("Coder: Executing code...")
            execution_output = python_tool.run(generated_code)
            print(f"Coder: Execution Output:\n{execution_output}")
            
            # Create a structured output
            reply_message = {"output": execution_output}
            log_entry = f"Coder: Prompt='{prompt}', Code Executed, Output='{execution_output}'"
        except Exception as e:
            print(f"Coder: Error during code execution: {e}")
            execution_output = f"Error during execution: {e}"
            reply_message = {"output": f"Error: {execution_output}"}
            log_entry = f"Coder: Prompt='{prompt}', Code Execution Failed, Error='{execution_output}'"
    else:
        print("Coder: No Python code block found in LLM response.")
        # Handle both string and structured outputs
        if isinstance(llm_response, dict) and "output" in llm_response:
            reply_message = llm_response
        else:
            reply_message = {"output": str(llm_response)}
        log_entry = f"Coder: Prompt='{prompt}', No Code Generated, Reply='{str(reply_message)}'"

    print("=== Coder Node End ===")
    return {
        **state,
        "reply": reply_message,  # Now just contains the output or error
        "sender": "Coder",
        "log": [log_entry],
        "next_node": "ProgressAssessment",
        "coder_code": generated_code,
        "coder_result": execution_output
    } 