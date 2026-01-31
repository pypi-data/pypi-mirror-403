from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Tuple
from uuid import uuid4

from coreason_identity.models import UserContext
from fastapi import FastAPI
from httpx import AsyncClient

from coreason_simulacrum.chaos import use_chaos_config, use_user_context
from coreason_simulacrum.interfaces import GraderInterface, LLMProvider, TargetInterface
from coreason_simulacrum.schemas import SimulationResult, SimulationScenario
from coreason_simulacrum.state import GraphState
from coreason_simulacrum.testing.mocks import MockCoreasonConnect, MockGrader, MockLLM
from coreason_simulacrum.workflow import AdversarialSimulationAsync


def get_providers(
    scenario: SimulationScenario,
) -> Tuple[LLMProvider, LLMProvider, TargetInterface, GraderInterface]:
    """
    Factory to get the providers for the simulation.
    Currently returns Mocks.
    """
    strategist_llm = MockLLM()
    attacker_llm = MockLLM()
    # Ensure target model ID is distinct from profile models (which default to something or are strings)
    # MockCoreasonConnect takes agent_id and model_id
    target = MockCoreasonConnect(agent_id="target", model_id="mock-model")
    grader = MockGrader()

    return strategist_llm, attacker_llm, target, grader


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize shared httpx client
    app.state.client = AsyncClient()
    yield
    # Cleanup
    await app.state.client.aclose()


app: FastAPI = FastAPI(lifespan=lifespan)


@app.post("/simulate", response_model=SimulationResult)  # type: ignore[misc]
async def simulate(scenario: SimulationScenario) -> SimulationResult:
    # Create a dummy user context for the service execution
    dummy_context = UserContext(user_id="service-account", email="service@coreason.ai", scopes=["*"])

    strategist, attacker, target, grader = get_providers(scenario)

    # Instantiate AdversarialSimulationAsync
    # We pass the shared client from app.state
    # max_turns defaults to 10
    sim = AdversarialSimulationAsync(
        profile=scenario.profile,
        strategist_llm=strategist,
        attacker_llm=attacker,
        target=target,
        grader=grader,
        client=app.state.client,
    )

    app_graph = sim.compile()

    initial_state: GraphState = {
        "messages": [],
        "current_turn": 0,
        "strategist_instruction": None,
        "rejected_branches": [],
        "success": False,
    }

    # Execute simulation within user context and chaos config to allow chaos injection
    with use_user_context(dummy_context), use_chaos_config(scenario.chaos_config):
        result_state = await app_graph.ainvoke(initial_state)

    # Map result to SimulationResult
    # The result_state is a GraphState dict
    final_messages = result_state.get("messages", [])
    success = result_state.get("success", False)
    dpo_triplet = result_state.get("generated_dpo_triplet")

    return SimulationResult(
        trace_id=uuid4(),
        dialogue=final_messages,
        attack_success=bool(success),
        chaos_resilience=True,  # Assuming True if no exception propagated
        generated_dpo_triplet=dpo_triplet,
    )


@app.get("/health")  # type: ignore[misc]
async def health() -> Dict[str, str]:
    return {"status": "ready", "service": "coreason-simulacrum", "version": "0.1.0"}
