"""
FactRecall agent implementation.

This module contains the implementation of the FactRecall agent, which is responsible
for answering factual sub-questions.
"""
from multi_hop_agent.models.schema import AgentState
from multi_hop_agent.prompts.system_prompts import FACT_RECALL_SYS
from multi_hop_agent.utils.llm import chat

def fact_recall_node(state: AgentState, llm, recall_parser) -> AgentState:
    """
    FactRecall Node: Answers factual sub-questions.
    Invoked by Decomposer after generating a sub-question.
    
    Args:
        state: Current agent state
        llm: LLM instance
        recall_parser: Parser for fact recall output
        
    Returns:
        Updated agent state with answer to the sub-question
    """
    print("\n=== FactRecall Node Start ===")
    # Create the system message with the task, but let chat function handle format_instructions
    system_msg = FACT_RECALL_SYS.replace("{task}", state["task"])
    prompt = state["prompt"]

    print(f"FactRecall - Prompt: {prompt}")
    
    # Use the parser for structured output
    answer = chat(llm, system_msg, prompt, parser=recall_parser)
    
    # Get the actual answer text - handle both structured and raw formats
    answer_text = answer
    if isinstance(answer, dict) and "answer" in answer:
        answer_text = answer["answer"]
    
    print(f"FactRecall - Reply: {answer}")

    log_entry = f"FactRecall: Prompt='{prompt}', Reply='{answer_text}'"
    print("=== FactRecall Node End ===")
    
    return {
        **state,
        "reply": answer, 
        "sender": "FactRecall", 
        "log": [log_entry], 
        "next_node": "ProgressAssessment"
    } 