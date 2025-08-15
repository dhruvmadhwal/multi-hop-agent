"""
Decomposer agent implementation.

This module contains the implementation of the Decomposer agent, which is responsible
for generating atomic sub-questions to help solve the main task.
"""
from multi_hop_agent.models.schema import AgentState
from multi_hop_agent.prompts.system_prompts import DECOMPOSER_SYS
from multi_hop_agent.utils.llm import chat

def decomposer_node(state: AgentState, llm, decomp_parser) -> AgentState:
    """
    Decomposer Node: Produces exactly one atomic sub-question needed to advance toward completing the task.
    Invoked by Orchestrator when decision is DECOMPOSE.
    
    Args:
        state: Current agent state
        llm: LLM instance
        decomp_parser: Parser for decomposer output
        
    Returns:
        Updated agent state with generated sub-question
    """
    print("\n=== Decomposer Node Start ===")
    
    task = state["task"]
    answered_questions = state.get("answered_questions", {})
    
    # Prepare input for decomposer with emphasis on avoiding repetition
    context_info = ""
    if answered_questions:
        answered_q_str = "\n".join([f"Q: {q}\nA: {a}" for q, a in answered_questions.items()])
        context_info += f"\nAlready Answered Questions:\n{answered_q_str}"
    
    # Create a strong prompt that emphasizes avoiding repetition
    decomposer_prompt = f"""
    User Task: {task}
    {context_info}
    
    Based on the User Task and what is already known, generate exactly **one new factual sub-question** that helps move closer to answering the task.
    
    Constraints:
    1. DO NOT repeat any sub-question already answered or attempted (see "Already Answered Questions").
    2. If a previous answer is too vague, you may ask a **more specific version** of that question.
    3. Your sub-question should address the **most critical missing information** right now.
    4. Do not assume or infer — if a fact is needed, ask for it directly.
    
    Return your sub-question in this JSON format:
    {{"question": "your sub-question goes here"}}
    """
    
    print(f"Decomposer - Input: {decomposer_prompt}")
    
    # Get decomposer response using the parser
    response = chat(llm, DECOMPOSER_SYS, decomposer_prompt, parser=decomp_parser)
    
    # Extract the question from the parsed response
    next_question = ""
    if isinstance(response, dict) and "question" in response:
        next_question = response["question"]
    else:
        # Fallback to string handling if parser fails
        next_question = str(response).strip()
    
    print(f"Decomposer - Generated Question: {next_question}")
    
    log_entry = f"Decomposer: Generated question '{next_question}'"
    print("=== Decomposer Node End ===")
    
    return {
        **state,
        "prompt": next_question,
        "sender": "Decomposer", 
        "log": [log_entry],
        "next_node": "FactRecall"
    } 