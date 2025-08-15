"""
Orchestrator agent implementation.

This module contains the implementation of the Orchestrator agent, which is responsible
for routing to the appropriate node based on the current state.
"""
from typing import Dict, Any
from multi_hop_agent.models.schema import AgentState
from multi_hop_agent.prompts.system_prompts import ORCH_SYS, ORCH_PROGRESS_PROMPT
from multi_hop_agent.utils.llm import chat

def orchestrator_node(state: AgentState, llm, orch_parser) -> AgentState:
    """
    Orchestrator Node: Policy router that selects next agent based on current state.
    Routes to: Decomposer, Coder, or FinalAnswer.
    
    Args:
        state: Current agent state
        llm: LLM instance
        orch_parser: Parser for orchestrator output
        
    Returns:
        Updated agent state with routing decision
    """
    print("\n=== Orchestrator Node Start ===")
    task = state["task"]
    sender = state.get("sender", "")
    reply = state.get("reply", "")
    last_prompt = state.get("prompt", "")

    # Get ledger state (maintained by ProgressAssessment)
    answered_questions = state.get("answered_questions", {})
    coder_code = state.get("coder_code", None)
    coder_result = state.get("coder_result", None)

    # Get progress tracking
    progress_tracker = state.get("progress_tracker", {})
    if progress_tracker is None:
        progress_tracker = {}
    stall_count = progress_tracker.get("stall_count", 0)
    stall_reason = state.get("stall_reason", "")

    state_updates: Dict[str, Any] = {}
    next_node = "Orchestrator"
    next_prompt = ""
    log_update = ""

    print(f"Orchestrator: Making decision based on current facts (stall_count: {stall_count}, stall_reason: {stall_reason})")
    
    # Check termination conditions first (as per playbook)
    if stall_count >= 3:
        print("Orchestrator: Stall count >= 3, routing to FinalAnswer for partial completion")
        next_node = "FinalAnswer"
        state_updates["stall_reason"] = f"Terminated due to {stall_count} consecutive stalls"
        log_update = f"Orchestrator: Routing to FinalAnswer due to stall termination"
        # Skip decision making and return immediately
        state_updates['next_node'] = next_node
        state_updates["log"] = [log_update]
        print("=== Orchestrator Node End (Early Termination) ===")
        return {
            **state,
            **state_updates
        }
    # Handle initial state - route to Decomposer if no questions answered yet
    elif not answered_questions:
        print("Orchestrator: Initial state detected, routing to Decomposer for first sub-question")
        next_node = "Decomposer"
        log_update = f"Orchestrator: Initial routing to Decomposer"
    else:
        # Build context for decision making
        coder_activity_str = ""
        if sender == "Coder" and reply is not None:
            instruction = last_prompt
            execution_output = ""
            if isinstance(reply, dict) and "output" in reply:
                execution_output = reply["output"]
            elif "Execution Output:" in str(reply):
                execution_output = str(reply).split("Execution Output:")[1].strip()
            else:
                execution_output = str(reply)
            coder_activity_str = f"Instruction: {instruction}\nResult: {execution_output}"
        elif sender == "Coder" and coder_result is not None:
            coder_activity_str = f"Instruction: {last_prompt}\nResult: {coder_result}"
        
        # Prepare orchestrator decision prompt
        progress_prompt = ORCH_PROGRESS_PROMPT.format(
            task=task,
            answered_questions="\n".join([f"- Q: {q}\nA: {a}" for q, a in answered_questions.items()]) if answered_questions else "None",
            last_agent=sender or "None",
            last_prompt=last_prompt or "None",
            last_reply=str(reply) if reply else "None", 
            coder_activity=coder_activity_str if coder_activity_str else "None",
            stall_count=stall_count,
            stall_reason=stall_reason if stall_reason else "None"
        )
        
        # Get decision using the parser with proper format instructions
        progress_decision = chat(llm, ORCH_SYS, progress_prompt, parser=orch_parser)
        
        # Handle accessing decision fields
        if isinstance(progress_decision, dict):
            decision_type = progress_decision.get("decision")
            decision_reasoning = progress_decision.get("reasoning", "No reasoning provided.")
            decision_instruction = progress_decision.get("instruction_or_question", "")
        else:
            try:
                decision_type = progress_decision.decision
                decision_reasoning = progress_decision.reasoning
                decision_instruction = progress_decision.instruction_or_question
            except:
                print("Error accessing decision fields")
                decision_type = "ERROR"
                decision_reasoning = "Failed to parse decision"
                decision_instruction = ""

        log_update = f"Orchestrator Decision: {decision_type} - {decision_reasoning}"

        # Route based on decision (as per playbook)
        if decision_type == "DECOMPOSE":
            # Route to Decomposer instead of handling decomposition internally
            print("Orchestrator: Routing to Decomposer for sub-question generation")
            next_node = "Decomposer"
            
            # We're not using refinement directives anymore
            # But we still log the stall reason for debugging
            if stall_reason:
                print(f"Orchestrator: Stall reason detected: {stall_reason} (not passing to nodes)")
                
            log_update += " → Routing to Decomposer"
                
        elif decision_type == "ASK_CODER":
            # Pass coder instruction directly
            next_prompt = decision_instruction
            state_updates["prompt"] = next_prompt
            next_node = "Coder"
            log_update += f" → Routing to Coder: '{next_prompt}'"

        elif decision_type == "FINAL_ANSWER":
            # Route to FinalAnswer node instead of handling synthesis internally
            print("Orchestrator: Routing to FinalAnswer for final synthesis")
            next_node = "FinalAnswer"
            # Optionally pass the instruction as context
            if decision_instruction:
                state_updates["final_answer_instruction"] = decision_instruction
            log_update += " → Routing to FinalAnswer"

        else:
            next_prompt = f"ERROR: Unexpected decision type: {decision_type}"
            state_updates["prompt"] = next_prompt
            next_node = "END"
            log_update += f" → ERROR: Unexpected decision, ending"

    # Update state
    state_updates['next_node'] = next_node
    if next_prompt:
        state_updates['prompt'] = next_prompt

    if log_update:
        state_updates["log"] = [log_update]

    print("=== Orchestrator Node End ===")
    return {
        **state,
        **state_updates
    } 