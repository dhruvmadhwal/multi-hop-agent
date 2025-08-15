"""
Main runner for the Multi-Hop Agent system.

This module provides functions to run the agent on individual tasks or in batch mode.
"""
import os
import json
import asyncio
import traceback
from io import StringIO
from contextlib import redirect_stdout
from typing import Dict, Any, Optional, List

from multi_hop_agent.models.schema import AgentState
from multi_hop_agent.utils.llm import initialize_llm
from multi_hop_agent.utils.helpers import save_answers
from multi_hop_agent.graph.agent_graph import build_agent_graph
from multi_hop_agent.config.settings import DATASET_FILE, ANSWERS_FILE, LOGS_DIR

def create_initial_state(task: str) -> AgentState:
    """
    Create initial agent state for a given task.
    
    Args:
        task: The user's task/question
        
    Returns:
        Initial agent state
    """
    initial_state: AgentState = {
        "task": task,
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
        "final_answer_instruction": None
    }
    return initial_state

async def run_agent_async(app, task: str) -> Dict[str, Any]:
    """
    Run the agent asynchronously on a single task.
    
    Args:
        app: Compiled agent graph
        task: The user's task/question
        
    Returns:
        Final agent state
    """
    initial_state = create_initial_state(task)
    final_state_before_end = None
    current_state = initial_state.copy()
    
    try:
        async for step_output in app.astream(
            current_state,
            config={"recursion_limit": 100}
        ):
            for node_name, node_update in step_output.items():
                if 'log' in node_update:
                    current_state['log'] = current_state.get('log', []) + node_update['log']
                current_state.update({k: v for k, v in node_update.items() if k != 'log'})
                if node_update.get("next_node") == "END":
                    final_state_before_end = current_state.copy()
                    break
    except Exception as e:
        print(f"Error running agent: {e}")
        traceback.print_exc()
    
    return final_state_before_end or current_state

def run_agent_on_prompt(task: str, temperature: float = 0.1, top_p: float = 0.95, top_k: int = 40) -> Dict[str, Any]:
    """
    Run the agent on a single task.
    
    Args:
        task: The user's task/question
        temperature: Controls randomness in responses (0.0-2.0)
        top_p: Controls diversity via nucleus sampling (0.0-1.0)
        top_k: Limits vocabulary to top k tokens (1-100)
        
    Returns:
        Final agent state
    """
    # Initialize LLM with specified parameters
    llm = initialize_llm(temperature=temperature, top_p=top_p, top_k=top_k)
    
    # Build agent graph
    app = build_agent_graph(llm)
    
    # Run agent
    loop = asyncio.get_event_loop()
    final_state = loop.run_until_complete(run_agent_async(app, task))
    
    return final_state

def load_examples() -> List[Dict[str, str]]:
    """
    Load examples from the dataset file.
    
    Returns:
        List of examples
    """
    with open(DATASET_FILE) as f:
        frames_examples = json.load(f)
    
    examples = []
    for example in frames_examples:
        examples.append({
            "id": example.get("id", ""),
            "question": example.get("question", ""),
            "expected_answer": example.get("answer", ""),
        })
    
    return examples

def batch_run():
    """
    Run the agent on all examples in the dataset.
    """
    # Load examples
    examples = load_examples()
    
    # Initialize LLM
    llm = initialize_llm()
    
    # Build agent graph
    app = build_agent_graph(llm)
    
    # Load existing answers
    all_answers = []
    already_answered_ids = set()
    if os.path.exists(ANSWERS_FILE):
        with open(ANSWERS_FILE) as f:
            all_answers = json.load(f)
            already_answered_ids = {a["id"] for a in all_answers}
    
    # Initialize counters
    total_tokens = 0
    total_cost = 0.0
    
    # Process each example
    for idx, example in enumerate(examples):
        example_id = example["id"]
        
        # Skip already answered examples
        if example_id in already_answered_ids:
            continue
        
        prompt = example["question"]
        
        # Print progress info
        print(f"\n=== Running Example {idx+1}/{len(examples)}: ID={example_id} ===")
        
        # Capture stdout
        stdout_capture = StringIO()
        state = None
        
        try:
            with redirect_stdout(stdout_capture):
                # Run agent
                loop = asyncio.get_event_loop()
                state = loop.run_until_complete(run_agent_async(app, prompt))
        except Exception:
            continue
        
        # Get answer
        answer = state.get("reply", "") if state else ""
        
        # Token/cost info (dummy values, replace with actual if available)
        example_tokens = state.get("tokens_used", 0) if state else 0
        example_cost = state.get("cost", 0.0) if state else 0.0
        total_tokens += example_tokens
        total_cost += example_cost
        
        # Add to answers
        all_answers.append({
            "id": example_id,
            "question": prompt,
            "answer": answer,
            "expected_answer": example["expected_answer"],
            "tokens_used": example_tokens,
            "cost": example_cost
        })
        
        # Save log
        log_file_path = os.path.join(LOGS_DIR, f"log_{example_id}.txt")
        try:
            full_stdout = stdout_capture.getvalue()
            with open(log_file_path, "w") as log_f:
                log_f.write(full_stdout)
        except Exception:
            pass
        
        # Save answers after each example for robustness
        save_answers(all_answers, ANSWERS_FILE)
        
        # Print progress info
        print(f"Tokens used: {example_tokens}, Cost: ${example_cost:.6f}")
        print(f"Total tokens: {total_tokens}, Total cost: ${total_cost:.6f}")
    
    print(f"\nBatch run complete. Results saved to {ANSWERS_FILE}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        batch_run()
    else:
        print("Please run with 'batch' argument for batch processing.") 