"""
Progress Assessment agent implementation.

This module contains the implementation of the Progress Assessment agent, which is responsible
for evaluating whether meaningful progress was made in solving the user's task.
"""
from typing import Dict, Any, Tuple
from multi_hop_agent.models.schema import AgentState
from multi_hop_agent.prompts.system_prompts import PROGRESS_ASSESSMENT_PROMPT
from multi_hop_agent.utils.llm import chat

def assess_progress_with_llm(state: AgentState, llm, progress_parser):
    """
    Use LLM to assess if meaningful progress was made.
    
    Args:
        state: Current agent state
        llm: LLM instance
        progress_parser: Parser for progress assessment output
        
    Returns:
        Progress assessment result
    """
    user_task = state.get("task", "")
    answered_questions = state.get("answered_questions", {})
    latest_question = state.get("last_question", "")
    latest_response = state.get("last_agent_reply", "")
    
    # Get PREVIOUS questions (excluding the current one being assessed)
    previous_questions = {q: a for q, a in answered_questions.items() if q != latest_question}
    
    # Format previous questions nicely
    answered_q_str = "\n".join([f"Q: {q}\nA: {a}" for q, a in previous_questions.items()]) if previous_questions else "None"
    
    # Create assessment input - exactly like the original script
    assessment_input = PROGRESS_ASSESSMENT_PROMPT.format(
        user_task=user_task,
        answered_questions=answered_q_str,
        latest_question=latest_question,
        latest_response=latest_response,
        format_instructions=progress_parser.get_format_instructions()
    )
    system_prompt = "You are an objective progress assessor."
    system_prompt += f"\n\n{progress_parser.get_format_instructions()}"
    
    # Get assessment using the parser - match original chat function signature
    assessment = chat(llm, system_prompt, assessment_input, parser=progress_parser)
    return assessment

def update_progress_tracker(state: AgentState, llm, progress_parser) -> Tuple[Dict[str, Any], str]:
    """
    Update progress tracker based on LLM assessment.
    
    Args:
        state: Current agent state
        llm: LLM instance
        progress_parser: Parser for progress assessment output
        
    Returns:
        Tuple of (updated progress tracker, progress reason)
    """
    # Get or initialize tracker - handle None case
    tracker = state.get("progress_tracker") or {"stall_count": 0}
    
    # Only assess if we have a recent interaction
    if state.get("last_question") and state.get("last_agent_reply"):
        # Get LLM assessment
        assessment = assess_progress_with_llm(state, llm, progress_parser)
        
        # With Pydantic model, we access attributes directly or as dict
        is_progress = False
        progress_reason = "No reason provided"
        
        # Handle both direct object and dict responses
        if isinstance(assessment, dict):
            is_progress = assessment.get("is_progress_being_made", False)
            progress_reason = assessment.get("progress_reason", "No reason provided")
        else:
            # Try to access as object attributes
            try:
                is_progress = assessment.is_progress_being_made
                progress_reason = assessment.progress_reason
            except:
                # Fallback if neither approach works
                print("Error accessing progress assessment fields")
        
        # Update stall count based on progress
        if is_progress:
            tracker["stall_count"] = 0  # Reset on progress
        else:
            tracker["stall_count"] += 1  # Increment on stall
        
        # Store assessment for debugging
        tracker["last_assessment"] = {
            "is_progress_being_made": is_progress,
            "progress_reason": progress_reason
        }
        
        return tracker, progress_reason
    
    return tracker, "No recent interaction to assess"

def progress_assessment_node(state: AgentState, llm, progress_parser) -> AgentState:
    """
    Progress Assessment Node: Assess progress and update stall counter.
    
    Args:
        state: Current agent state
        llm: LLM instance
        progress_parser: Parser for progress assessment output
        
    Returns:
        Updated agent state with progress assessment
    """
    print("\n=== Progress Assessment Node Start ===")
    
    # Get interaction details
    sender = state.get("sender", "")
    reply = state.get("reply", "")
    last_prompt = state.get("prompt", "")
    
    # Store interaction for assessment
    state_updates = {
        "last_question": last_prompt,
        "last_agent_reply": reply
    }
    
    # AGGREGATION LOGIC (moved from Orchestrator)
    if sender in ["FactRecall", "Coder"] and reply is not None:
        print(f"ProgressAssessment: Aggregating result from {sender}.")
        
        # Get current aggregated data
        fact_sheet = state.get("fact_sheet", "")
        answered_questions = state.get("answered_questions", {})
        
        # Aggregate the response
        question_answered = last_prompt
        
        # Handle both string and structured outputs
        if sender == "FactRecall":
            response_text = reply
            if isinstance(reply, dict) and "answer" in reply:
                response_text = reply["answer"]
            answered_questions[question_answered] = response_text
            
            if fact_sheet: 
                fact_sheet += "\n"
            fact_sheet += f"- Q: {question_answered}\nA: {response_text}"
            
        elif sender == "Coder":
            # For Coder, extract just the output (not the code)
            output_text = ""
            if isinstance(reply, dict) and "output" in reply:
                output_text = reply["output"]
            else:
                output_text = str(reply)
            
            # Store the instruction and output in answered_questions
            answered_questions[question_answered] = output_text
            
            if fact_sheet: 
                fact_sheet += "\n"
            fact_sheet += f"- Coder Action: {question_answered}\nResult: {output_text}"
        
        # Update aggregated data
        state_updates["answered_questions"] = answered_questions
        state_updates["fact_sheet"] = fact_sheet
        
        # Clear coder fields if from coder
        if sender == "Coder":
            state_updates["coder_code"] = None
            state_updates["coder_result"] = None
    
    # Update progress tracker
    progress_tracker, progress_reason = update_progress_tracker({**state, **state_updates}, llm, progress_parser)
    stall_count = progress_tracker.get("stall_count", 0)
    
    # Propagate stall count to top level for consistency
    state_updates["stall_count"] = stall_count
    
    # Set stall_reason when no progress is made
    if stall_count > 0 and progress_tracker.get("last_assessment", {}).get("is_progress_being_made") is False:
        state_updates["stall_reason"] = progress_reason
    
    log_update = f"Progress Assessment: Aggregated {sender} response. Stall Count = {stall_count}, Reason: {progress_reason}"
    print(log_update)
    
    # Note high stall count but let the orchestrator handle termination
    if stall_count >= 3:
        print(f"Stall count >= 3, letting Orchestrator handle termination decision")
        log_update += f", ALERT: {stall_count} consecutive stalls detected"
        # We don't route to END directly, the Orchestrator will handle this
    
    # Always route to orchestrator for next decision
    print("=== Progress Assessment Node End ===")
    return {
        **state,
        **state_updates,
        "progress_tracker": progress_tracker,
        "log": [log_update],
        "next_node": "Orchestrator"
    } 