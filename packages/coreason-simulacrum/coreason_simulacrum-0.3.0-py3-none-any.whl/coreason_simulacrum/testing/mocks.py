from typing import Any, List, Optional
from uuid import UUID

from coreason_simulacrum.interfaces import LLMProvider, MockCoreasonConnect, MockGrader


class MockLLM(LLMProvider):
    async def generate(self, prompt: str, system_instruction: Optional[str] = None, **kwargs: Any) -> str:
        if "SIMULATE" in prompt:
            return "Refusal" if "bad" in prompt else "Compliance"

        # Add logic to detect Strategist calls vs Attacker calls
        if system_instruction and "Strategist" in system_instruction:
            return "Strategist Instruction: Pivot to emotional appeal."

        return f"Generated variant for: {prompt}"

    async def generate_batch(
        self, prompt: str, n: int = 1, system_instruction: Optional[str] = None, **kwargs: Any
    ) -> List[str]:
        # Return unique variants
        return [f"Variant {i} for {prompt}" for i in range(n)]


class MockLLMEcho(LLMProvider):
    async def generate(self, prompt: str, system_instruction: Optional[str] = None, **kwargs: Any) -> str:
        if "SIMULATE" in prompt:
            return "Compliance"
        if system_instruction and "Strategist" in system_instruction:
            return "Try a social engineering approach"
        return f"Gen: {prompt}"

    async def generate_batch(
        self, prompt: str, n: int = 1, system_instruction: Optional[str] = None, **kwargs: Any
    ) -> List[str]:
        return [f"Variant {i} for {prompt}" for i in range(n)]


class MockLLMEmpty(LLMProvider):
    async def generate(self, prompt: str, system_instruction: Optional[str] = None, **kwargs: Any) -> str:
        return "Simulated response"

    async def generate_batch(
        self, prompt: str, n: int = 1, system_instruction: Optional[str] = None, **kwargs: Any
    ) -> List[str]:
        # Return empty list to trigger fallback
        return []


class MockLLMError(LLMProvider):
    async def generate(self, prompt: str, system_instruction: Optional[str] = None, **kwargs: Any) -> str:
        raise RuntimeError("Strategist generation failed")

    async def generate_batch(
        self, prompt: str, n: int = 1, system_instruction: Optional[str] = None, **kwargs: Any
    ) -> List[str]:
        return ["Variant"] * n


class MockTargetError(MockCoreasonConnect):
    async def send_message(self, message: str) -> str:
        raise RuntimeError("Simulated connection error")


class MockGraderError(MockGrader):
    async def grade_conversation(
        self, conversation_id: UUID, conversation_history: List[dict[str, Any]]
    ) -> dict[str, Any]:
        raise RuntimeError("Grading failed")


class MockGraderInvalid(MockGrader):
    async def grade_conversation(
        self, conversation_id: UUID, conversation_history: List[dict[str, Any]]
    ) -> Any:  # Returning invalid type
        return "Not a dictionary"


__all__ = [
    "MockLLM",
    "MockLLMEcho",
    "MockLLMEmpty",
    "MockLLMError",
    "MockTargetError",
    "MockGraderError",
    "MockGraderInvalid",
    "MockCoreasonConnect",
    "MockGrader",
]
