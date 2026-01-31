from typing import Any, Dict, List, Optional, TypedDict

from typing_extensions import NotRequired

from coreason_simulacrum.schemas import Message


class GraphState(TypedDict):
    """
    Represents the state of the simulation graph.

    This state is passed between nodes in the LangGraph workflow, maintaining
    context for the Strategist, Attacker, and Target interactions.
    """

    # The main conversation history (The Chosen Trajectory)
    messages: List[Message]

    # The current instruction from the Strategist to the Attacker
    strategist_instruction: Optional[str]

    # Storage for rejected branches to support DPO triplet generation.
    # Structure: List of dictionaries containing {prompt, response, score} or similar.
    rejected_branches: List[Dict[str, Any]]

    # Current turn counter
    current_turn: int

    # Flag to indicate if the attack was successful
    success: bool

    # The generated DPO triplet if the attack succeeds
    generated_dpo_triplet: NotRequired[Optional[Dict[str, Any]]]
