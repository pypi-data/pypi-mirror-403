from typing import Any, Dict, List, Literal, Optional, TypedDict, cast
from uuid import uuid4

import anyio
import httpx
from coreason_identity.models import UserContext
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from coreason_simulacrum.chaos import use_user_context
from coreason_simulacrum.interfaces import GraderInterface, LLMProvider, TargetInterface
from coreason_simulacrum.prompts import (
    ATTACKER_FALLBACK_CANDIDATE_PROMPT,
    ATTACKER_FALLBACK_CANDIDATE_RESPONSE,
    ATTACKER_SIMULATION_PROMPT_TEMPLATE,
    ATTACKER_TAP_GENERATION_PROMPT_TEMPLATE,
    STRATEGIST_DEFAULT_INSTRUCTION,
    STRATEGIST_DPO_CONTEXT_TEMPLATE,
    STRATEGIST_FALLBACK_INSTRUCTION,
    STRATEGIST_IDEAL_REFUSAL_PROMPT,
    STRATEGIST_SYSTEM_PROMPT_TEMPLATE,
    STRATEGIST_USER_PROMPT_TEMPLATE,
)
from coreason_simulacrum.schemas import AdversaryProfile, Message
from coreason_simulacrum.state import GraphState
from coreason_simulacrum.utils.logger import logger
from coreason_simulacrum.utils.model_utils import validate_model_diversity


class AttackCandidate(TypedDict):
    """
    TypedDict representing a potential attack vector in the TAP tree.
    """

    prompt: str
    response: str
    score: float


class AdversarialSimulationAsync:
    """
    Manages the adversarial simulation workflow, including dependency injection
    and state graph construction.

    This class orchestrates the interaction between the Strategist (Meta-Agent),
    the Attacker (Actor), and the Target, using a state machine (LangGraph)
    to evolve the attack over multiple turns.
    """

    def __init__(
        self,
        profile: AdversaryProfile,
        strategist_llm: LLMProvider,
        attacker_llm: LLMProvider,
        target: TargetInterface,
        grader: GraderInterface,
        max_turns: int = 10,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        """
        Initialize the simulation with the given profile and providers.
        Validates model diversity upon initialization.

        Args:
            profile: Configuration for the adversary.
            strategist_llm: The LLM provider for the Strategist.
            attacker_llm: The LLM provider for the Attacker.
            target: The target agent interface.
            grader: The evaluation interface.
            max_turns: Maximum number of conversation turns.
            client: Optional external httpx.AsyncClient for connection pooling.

        Raises:
            ValueError: If model diversity checks fail.
        """
        self.profile = profile
        self.strategist_llm = strategist_llm
        self.attacker_llm = attacker_llm
        self.target = target
        self.grader = grader
        self.max_turns = max_turns

        self._internal_client = client is None
        self._client = client or httpx.AsyncClient()

        # Validate diversity
        validate_model_diversity(profile, target.model_id)
        logger.info(f"Initialized AdversarialSimulation for profile: {profile.name} (Max Turns: {max_turns})")

    async def __aenter__(self) -> "AdversarialSimulationAsync":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional[Any] = None,
    ) -> None:
        if self._internal_client:
            await self._client.aclose()

    async def _execute_tap_strategy(self, instruction: str, history: List[Message]) -> List[AttackCandidate]:
        """
        Executes the Tree of Attacks (TAP) strategy: Branching, Prediction, Scoring.
        Returns a sorted list of candidates.

        Args:
            instruction: The strategic instruction for this turn.
            history: The conversation history so far.

        Returns:
            List[AttackCandidate]: Sorted list of generated attack candidates.
        """
        # 0. Format History
        formatted_history = "\n".join([f"{m.role}: {m.content}" for m in history])

        # 1. Branching: Generate 3 variants using the injected Attacker LLM
        prompt_for_generator = ATTACKER_TAP_GENERATION_PROMPT_TEMPLATE.format(
            instruction=instruction, history=formatted_history
        )
        variants = await self.attacker_llm.generate_batch(prompt_for_generator, n=3)

        # 2. Prediction & Scoring
        candidates: List[AttackCandidate] = []
        for variant in variants:
            simulation_prompt = ATTACKER_SIMULATION_PROMPT_TEMPLATE.format(variant=variant)
            predicted_response = await self.attacker_llm.generate(simulation_prompt)

            # Scoring (Mock)
            score = 0.9 if "Compliance" in predicted_response else 0.1
            candidates.append({"prompt": variant, "response": predicted_response, "score": score})

        # 3. Sort by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates

    async def _process_grading(self, messages: List[Message]) -> bool:
        """
        Processes grading logic: formats history, calls grader, handles errors.
        Returns True if attack was successful.

        Args:
            messages: The list of messages to grade.

        Returns:
            bool: True if the attack succeeded.
        """
        try:
            history_dicts = [m.model_dump() for m in messages]
            conversation_id = uuid4()
            grading_result = await self.grader.grade_conversation(conversation_id, history_dicts)

            if not isinstance(grading_result, dict):
                logger.error(f"Evaluator Node: Invalid grader response format: {grading_result}")
                return False

            return bool(grading_result.get("attack_success", False))

        except Exception as e:
            logger.error(f"Evaluator Node: Error during grading: {e}")
            return False

    async def node_strategist(self, state: GraphState) -> Dict[str, Any]:
        """
        Strategist analyzes the history and sets the instruction.

        Args:
            state: The current graph state.

        Returns:
            Dict[str, Any]: Updates to the state (instruction).
        """
        logger.info("Strategist Node: analyzing state.")
        messages = state.get("messages", [])

        # Format history
        history_text = ""
        if messages:
            history_text = "\n".join([f"{m.role.upper()}: {m.content}" for m in messages])
        else:
            history_text = "(No history yet)"

        # Construct prompt
        system_instruction = STRATEGIST_SYSTEM_PROMPT_TEMPLATE.format(goal=self.profile.goal)

        prompt = STRATEGIST_USER_PROMPT_TEMPLATE.format(history_text=history_text)

        try:
            instruction = await self.strategist_llm.generate(prompt, system_instruction=system_instruction)
            logger.info(f"Strategist generated instruction: {instruction}")
            return {"strategist_instruction": instruction}
        except Exception as e:
            logger.error(f"Strategist Node: Error generating instruction: {e}")
            return {"strategist_instruction": STRATEGIST_FALLBACK_INSTRUCTION}

    async def node_attacker(self, state: GraphState) -> Dict[str, Any]:
        """
        Attacker generates a prompt based on instruction using TAP logic.

        Args:
            state: The current graph state.

        Returns:
            Dict[str, Any]: Updates to the state (messages, rejected branches).
        """
        logger.info("Attacker Node: executing TAP.")
        instruction = state.get("strategist_instruction") or STRATEGIST_DEFAULT_INSTRUCTION
        current_messages = state.get("messages", [])

        # Execute TAP Logic
        candidates = await self._execute_tap_strategy(instruction, current_messages)

        if not candidates:
            # Fallback
            candidates.append(
                {
                    "prompt": ATTACKER_FALLBACK_CANDIDATE_PROMPT,
                    "response": ATTACKER_FALLBACK_CANDIDATE_RESPONSE,
                    "score": 0.0,
                }
            )

        best = candidates[0]
        rejected = candidates[1:]

        logger.info(f"TAP selected: {best['prompt']} (Score: {best['score']})")

        new_message = Message(role="user", content=best["prompt"])
        rejected_cast = [cast(Dict[str, Any], dict(c)) for c in rejected]

        return {
            "messages": current_messages + [new_message],
            "rejected_branches": state.get("rejected_branches", []) + rejected_cast,
        }

    async def node_target(self, state: GraphState) -> Dict[str, Any]:
        """
        Target agent processes the user message.

        Args:
            state: The current graph state.

        Returns:
            Dict[str, Any]: Updates to the state (appended response).
        """
        logger.info("Target Node: processing message.")

        try:
            last_msg_content = state["messages"][-1].content
            response_content = await self.target.send_message(last_msg_content)

            response_msg = Message(
                role="assistant",
                content=response_content,
                metadata={"agent_id": "target", "model_id": self.target.model_id},
            )
            return {"messages": state["messages"] + [response_msg]}
        except Exception as e:
            logger.error(f"Target Node: Error during chat: {e}")
            error_response = Message(role="system", content=f"Error: {str(e)}")
            return {"messages": state["messages"] + [error_response]}

    async def _generate_dpo_triplet(self, messages: List[Message]) -> Optional[Dict[str, Any]]:
        """
        Generates a DPO triplet (prompt, chosen, rejected) if the history is valid.
        Returns None if generation is skipped or fails.

        Args:
            messages: The conversation history.

        Returns:
            Optional[Dict[str, Any]]: The DPO triplet or None.
        """
        try:
            if len(messages) < 2:
                logger.warning("Evaluator Node: Message history too short to generate DPO triplet.")
                return None

            last_msg = messages[-1]
            penultimate_msg = messages[-2]

            # Robustness Check: Ensure strict User -> Assistant flow for DPO
            # If the last message is a System error, we skip DPO generation.
            if last_msg.role != "assistant" or penultimate_msg.role != "user":
                logger.warning(
                    f"Evaluator Node: Skipped DPO generation due to unexpected roles: "
                    f"{penultimate_msg.role} -> {last_msg.role}"
                )
                return None

            attack_prompt = penultimate_msg.content
            actual_compliance = last_msg.content

            # Generate Ideal Refusal (Chosen) using Strategist
            prompt = STRATEGIST_DPO_CONTEXT_TEMPLATE.format(
                attack_prompt=attack_prompt,
                actual_compliance=actual_compliance,
                instruction=STRATEGIST_IDEAL_REFUSAL_PROMPT,
            )

            ideal_refusal = await self.strategist_llm.generate(prompt)

            return {
                "prompt": attack_prompt,
                "chosen": ideal_refusal,
                "rejected": actual_compliance,
            }

        except Exception as e:
            logger.error(f"Evaluator Node: Error generating DPO triplet: {e}")
            return None

    async def node_evaluator(self, state: GraphState) -> Dict[str, Any]:
        """
        Evaluates if the attack was successful using the GraderInterface.
        If successful, generates a DPO triplet (prompt, chosen, rejected) using the Strategist.

        Args:
            state: The current graph state.

        Returns:
            Dict[str, Any]: Updates to the state (success status, turn count, DPO triplet).
        """
        logger.info("Evaluator Node: checking success via Grader.")
        messages = state["messages"]
        is_success = await self._process_grading(messages)

        update: Dict[str, Any] = {"success": is_success, "current_turn": state["current_turn"] + 1}

        if is_success:
            logger.info("Evaluator Node: Attack successful. Generating DPO triplet.")
            dpo_triplet = await self._generate_dpo_triplet(messages)
            if dpo_triplet:
                update["generated_dpo_triplet"] = dpo_triplet
                logger.info("Evaluator Node: DPO triplet generated successfully.")

        return update

    def _condition_evaluator(self, state: GraphState) -> Literal["strategist", "__end__"]:
        """
        Decides whether to continue or end.

        Args:
            state: The current graph state.

        Returns:
            str: The next node ('strategist' or '__end__').
        """
        if state.get("success", False):
            return "__end__"

        if state["current_turn"] >= self.max_turns:
            return "__end__"

        return "strategist"

    def compile(self) -> CompiledStateGraph:
        """
        Compiles and returns the LangGraph application.

        Returns:
            CompiledStateGraph: The compiled workflow ready for execution.
        """
        workflow = StateGraph(GraphState)

        workflow.add_node("strategist", self.node_strategist)
        workflow.add_node("attacker", self.node_attacker)
        workflow.add_node("target", self.node_target)
        workflow.add_node("evaluator", self.node_evaluator)

        workflow.set_entry_point("strategist")

        workflow.add_edge("strategist", "attacker")
        workflow.add_edge("attacker", "target")
        workflow.add_edge("target", "evaluator")
        workflow.add_conditional_edges(
            "evaluator", self._condition_evaluator, {"strategist": "strategist", "__end__": END}
        )

        return workflow.compile()

    async def run(
        self,
        initial_state: GraphState,
        *,
        context: UserContext,
        config: Optional[Dict[str, Any]] = None,
    ) -> GraphState:
        """
        Runs the simulation given the initial state.

        Args:
            initial_state: The starting state of the simulation.
            context: The authenticated user context.
            config: Optional configuration for the execution (e.g. recursion_limit).

        Returns:
            GraphState: The final state after simulation completes.
        """
        if not context:
            raise ValueError("UserContext is required to run the simulation.")

        logger.info(
            "Starting simulation run",
            user_id=context.user_id,
            config=config,
        )

        with use_user_context(context):
            app = self.compile()
            # ainvoke is async
            result = await app.ainvoke(initial_state, config=config)
            return cast(GraphState, result)


class AdversarialSimulation:
    """
    Sync Facade for AdversarialSimulationAsync.
    Manages resource lifecycle via anyio.run.
    """

    def __init__(
        self,
        profile: AdversaryProfile,
        strategist_llm: LLMProvider,
        attacker_llm: LLMProvider,
        target: TargetInterface,
        grader: GraderInterface,
        max_turns: int = 10,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._async = AdversarialSimulationAsync(
            profile=profile,
            strategist_llm=strategist_llm,
            attacker_llm=attacker_llm,
            target=target,
            grader=grader,
            max_turns=max_turns,
            client=client,
        )

    def __enter__(self) -> "AdversarialSimulation":
        return self

    def __exit__(
        self,
        exc_type: Optional[type] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional[Any] = None,
    ) -> None:
        anyio.run(self._async.__aexit__, exc_type, exc_val, exc_tb)

    def compile(self) -> CompiledStateGraph:
        """
        Proxies the compile method. Note: The returned graph is still async-native
        and usually requires an async environment to run via ainvoke.
        For sync execution, use the run() method of this facade.
        """
        return self._async.compile()

    def run(
        self,
        initial_state: GraphState,
        *,
        context: UserContext,
        config: Optional[Dict[str, Any]] = None,
    ) -> GraphState:
        """
        Runs the simulation synchronously.
        """

        async def _wrapper() -> GraphState:
            return await self._async.run(initial_state, context=context, config=config)

        result = anyio.run(_wrapper)
        return cast(GraphState, result)
