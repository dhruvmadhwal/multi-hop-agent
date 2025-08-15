"""
FinalAnswer agent implementation.

This module contains the implementation of the FinalAnswer agent, which is responsible
for synthesizing the final answer from accumulated facts and coder results.
"""
from multi_hop_agent.models.schema import AgentState
from multi_hop_agent.prompts.system_prompts import FINALANSWER_SYS
from multi_hop_agent.utils.llm import chat

def final_answer_node(state: AgentState, llm, final_parser) -> AgentState:
    """
    FinalAnswer Node: Synthesizes concise final answer from accumulated facts and coder results.
    Invoked by Orchestrator when decision is FINAL_ANSWER or by ProgressAssessment when stall count exceeds threshold.
    
    Args:
        state: Current agent state
        llm: LLM instance
        final_parser: Parser for final answer output
        
    Returns:
        Updated agent state with final answer
    """
    print("\n=== FinalAnswer Node Start ===")
    
    task = state["task"]
    fact_sheet = state.get("fact_sheet", "")
    answered_questions = state.get("answered_questions", {})
    progress_tracker = state.get("progress_tracker", {})
    if progress_tracker is None:
        progress_tracker = {}
    stall_count = progress_tracker.get("stall_count", 0)
    final_answer_instruction = state.get("final_answer_instruction", "")
    
    # Prepare synthesis input
    synthesis_prompt = f"""
    User Task: {task}
    
    
    Answered Questions:
    {chr(10).join([f"Q: {q}\nA: {a}" for q, a in answered_questions.items()]) if answered_questions else "None"}
    """
    
    # Add stall context if terminated early
    if stall_count >= 3:
        synthesis_prompt += f"\nNote: Analysis terminated due to {stall_count} consecutive stalls - provide best possible answer with available information."
    
    print(f"FinalAnswer - Synthesis Input: {synthesis_prompt}")
    
    # Generate final answer using the parser
    final_response = chat(llm, FINALANSWER_SYS, synthesis_prompt, parser=final_parser)
    
    # Extract answer text
    answer_text = ""
    if isinstance(final_response, dict) and "answer" in final_response:
        answer_text = final_response["answer"]
    else:
        # Fallback if parser fails
        answer_text = str(final_response)
    
    print(f"FinalAnswer - Generated: {answer_text}")
    
    log_entry = f"FinalAnswer: Synthesized final response from {len(answered_questions)} facts"
    print("=== FinalAnswer Node End ===")
    
    return {
        **state,
        "prompt": answer_text,
        "reply": answer_text,
        "sender": "FinalAnswer",
        "log": [log_entry],
        "next_node": "END"
    } 