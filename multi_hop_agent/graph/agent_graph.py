"""
Agent graph definition for the Multi-Hop Agent system.

This module contains the definition of the agent graph, which connects all the agents
in the system and defines the flow of control between them.
"""
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from multi_hop_agent.models.schema import (
    AgentState, OrchDecision, ProgressOut, RecallOut, 
    CoderOut, DecompOut, FinalAnswerOut
)
from multi_hop_agent.agents.orchestrator import orchestrator_node
from multi_hop_agent.agents.decomposer import decomposer_node
from multi_hop_agent.agents.fact_recall import fact_recall_node
from multi_hop_agent.agents.coder import coder_node
from multi_hop_agent.agents.final_answer import final_answer_node
from multi_hop_agent.agents.progress_assessment import progress_assessment_node

def build_agent_graph(llm):
    """
    Build the agent graph with all nodes and edges.
    
    Args:
        llm: LLM instance to use for all agents
        
    Returns:
        Compiled agent graph
    """
    # Initialize parsers
    orch_parser = JsonOutputParser(pydantic_object=OrchDecision)
    progress_parser = JsonOutputParser(pydantic_object=ProgressOut)
    recall_parser = JsonOutputParser(pydantic_object=RecallOut)
    coder_parser = JsonOutputParser(pydantic_object=CoderOut)
    decomp_parser = JsonOutputParser(pydantic_object=DecompOut)
    final_parser = JsonOutputParser(pydantic_object=FinalAnswerOut)
    
    # Build StateGraph
    graph_builder = StateGraph(AgentState)
    
    # Add nodes with bound LLM and parsers
    graph_builder.add_node(
        "Orchestrator", 
        lambda state: orchestrator_node(state, llm, orch_parser)
    )
    graph_builder.add_node(
        "FactRecall", 
        lambda state: fact_recall_node(state, llm, recall_parser)
    )
    graph_builder.add_node(
        "Coder", 
        lambda state: coder_node(state, llm, coder_parser)
    )
    graph_builder.add_node(
        "ProgressAssessment", 
        lambda state: progress_assessment_node(state, llm, progress_parser)
    )
    graph_builder.add_node(
        "Decomposer", 
        lambda state: decomposer_node(state, llm, decomp_parser)
    )
    graph_builder.add_node(
        "FinalAnswer", 
        lambda state: final_answer_node(state, llm, final_parser)
    )
    
    # Set entry point
    graph_builder.set_entry_point("Orchestrator")
    
    # Define routing function
    def route_based_on_decision(state: AgentState):
        """Routes based on the 'next_node' field set by the Orchestrator or workers."""
        next_node = state.get("next_node")
        print(f"\n--- Routing Decision ---")
        print(f"State's next_node: {next_node}")
        if next_node == "END":
            return END
        elif next_node in ["FactRecall", "Coder", "Orchestrator", "Decomposer", "FinalAnswer"]:
            return next_node
        else:
            print("Routing: Invalid or missing next_node, routing to END")
            return END
    
    # Add conditional edges for Orchestrator (can route to Decomposer, Coder, or FinalAnswer)
    graph_builder.add_conditional_edges(
        "Orchestrator",
        route_based_on_decision,
        {
            "Decomposer": "Decomposer",
            "Coder": "Coder",
            "FinalAnswer": "FinalAnswer",
            END: END
        }
    )
    
    # Add direct edge from ProgressAssessment to Orchestrator
    graph_builder.add_edge("ProgressAssessment", "Orchestrator")
    
    # Add direct edges from worker nodes to ProgressAssessment
    graph_builder.add_edge("FactRecall", "ProgressAssessment")
    graph_builder.add_edge("Coder", "ProgressAssessment")
    
    # Add direct edge from Decomposer to FactRecall
    graph_builder.add_edge("Decomposer", "FactRecall")
    
    # Add direct edge from FinalAnswer to END
    graph_builder.add_edge("FinalAnswer", END)
    
    # Compile the graph
    try:
        app = graph_builder.compile()
        print("\nGraph compiled successfully.")
        return app
    except Exception as e:
        print(f"\nError compiling graph: {e}")
        import traceback
        traceback.print_exc()
        raise 