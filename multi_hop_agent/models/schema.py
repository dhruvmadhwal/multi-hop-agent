"""
Schema definitions for the Multi-Hop Agent system.

This module contains Pydantic models for structured outputs and TypedDict definitions
for state management.
"""
from pydantic import BaseModel, Field
from typing import TypedDict, List, Annotated, Optional, Dict, Any, Literal
import operator

# Output format models
class OrchDecision(BaseModel):
    decision: Literal["DECOMPOSE", "ASK_CODER", "FINAL_ANSWER"] = Field(
        description="Next action the orchestrator chooses"
    )
    reasoning: str = Field(
        description="Brief rationale for why this choice was made and strategic thinking"
    )
    instruction_or_question: str = Field(
        description="Coder instruction, blank in all other cases"
    )

class ProgressOut(BaseModel):
    is_progress_being_made: bool = Field(
        description="true or false value conveying whether progress is being made"
    )
    progress_reason: str = Field(
        description="Brief explanation of assessment"
    )
    
class RecallOut(BaseModel):
    answer: str = Field(
        description="Answer to the question"
    )
    
class CoderOut(BaseModel):
    output: str = Field(description="Stdout or error string from the run")

class DecompOut(BaseModel):
    question: str = Field(description="Single atomic sub-question to ask next")

class FinalAnswerOut(BaseModel):
    answer: str = Field(description="Concise final or best-effort answer")

# State management TypedDict definitions
class _RequiredAgentState(TypedDict):
    task: str  # The user's task is always required

class AgentState(TypedDict):
    task: str
    prompt: str
    reply: str
    sender: str
    log: Annotated[List[str], operator.add]
    next_node: Optional[str]
    fact_sheet: str
    answered_questions: Dict[str, str]
    coder_code: Optional[str]
    coder_result: Optional[str]
    # Progress tracking fields
    progress_tracker: Optional[Dict[str, Any]]
    last_question: Optional[str]
    last_agent_reply: Optional[str]
    # New fields for stall handling (from playbook)
    last_answer: Optional[str]
    last_sender: Optional[str] 
    stall_reason: Optional[str]
    stall_count: Optional[int]
    # Final answer context
    final_answer_instruction: Optional[str] 