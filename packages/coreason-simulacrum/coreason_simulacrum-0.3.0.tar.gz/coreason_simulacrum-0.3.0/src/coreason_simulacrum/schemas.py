from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ScenarioType(str, Enum):
    """
    Enumeration of simulation scenario types.

    Attributes:
        ADVERSARIAL_RL: Tree of Attacks (TAP) logic.
        CHAOS_INFRA: Infrastructure failure simulation (latency, errors).
        CONSTITUTIONAL: Boundary probing against safety constitutions.
    """

    ADVERSARIAL_RL = "ADVERSARIAL_RL"  # TAP / Tree of Attacks
    CHAOS_INFRA = "CHAOS_INFRA"  # Latency / Errors
    CONSTITUTIONAL = "CONSTITUTIONAL"  # Boundary Probing


class AdversaryProfile(BaseModel):
    """
    Profile defining the adversary's persona and strategy.

    Configures the 'Strategist' (High-Reasoning Model) and the 'Attacker'
    (Actor/Uncensored Model) used in the simulation.
    """

    name: str = Field(..., description="Name of the adversary persona (e.g., 'The Hacker')")
    goal: str = Field(..., description="The objective of the attack (e.g., 'Extract PII')")
    strategy_model: str = Field(..., description="Model used for the Strategist/Mastermind (e.g., 'claude-3-opus')")
    attack_model: str = Field(..., description="Model used for the Attacker/Actor (e.g., 'llama-3-uncensored')")


class ChaosConfig(BaseModel):
    """
    Configuration for infrastructure chaos injection.

    Controls the rates and types of failures injected into the agent's environment
    to test GxP resilience.
    """

    latency_ms: int = Field(default=0, ge=0, description="Latency injection in milliseconds")
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Probability of error injection (0.0 to 1.0)")
    noise_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Probability of noise/corruption injection (0.0 to 1.0)"
    )
    token_throttle: bool = Field(default=False, description="Enable token stream throttling")
    exception_type: str = Field(default="RuntimeError", description="Type of exception to raise (e.g. 'RuntimeError')")
    exception_msg: str = Field(default="Chaos injected error", description="Message for the injected exception")


class SimulationScenario(BaseModel):
    """
    Encapsulates the configuration for a simulation run.

    Aggregates the profile, chaos settings, and scenario type into a single
    execution context.
    """

    type: ScenarioType = Field(..., description="Type of the simulation scenario")
    profile: AdversaryProfile = Field(..., description="Profile of the adversary")
    chaos_config: ChaosConfig = Field(default_factory=ChaosConfig, description="Chaos configuration")


class Message(BaseModel):
    """
    Represents a message in the conversation.
    """

    role: str = Field(..., description="Role of the message sender (e.g., 'user', 'assistant', 'system')")
    content: str = Field(..., description="Content of the message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the message")


class SimulationResult(BaseModel):
    """
    Result of a simulation execution.

    Contains the full trace and success metrics of the adversarial run.
    """

    trace_id: UUID = Field(..., description="Unique identifier for the simulation trace")
    dialogue: List[Message] = Field(..., description="List of messages in the conversation")
    attack_success: bool = Field(..., description="Did the Attacker achieve the goal?")
    chaos_resilience: bool = Field(..., description="Did the Agent handle errors gracefully?")
    generated_dpo_triplet: Optional[dict[str, Any]] = Field(
        default=None, description="Generated DPO triplet for auto-training"
    )
