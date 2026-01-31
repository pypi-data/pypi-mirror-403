# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_simulacrum

"""
Utilities for model management and diversity enforcement.

This module provides functions to identify model families and ensure that
adversarial simulations do not suffer from 'Model Collapse' by verifying
diversity between the attacker and the target.
"""

from coreason_simulacrum.schemas import AdversaryProfile
from coreason_simulacrum.utils.logger import logger


def get_model_family(model_name: str) -> str:
    """
    Extracts and normalizes the model family from a model name.

    Supports: OpenAI (gpt), Anthropic (claude), Meta (llama), Mistral, Google (gemini).

    Args:
        model_name: The raw model identifier string.

    Returns:
        str: A canonical family string (e.g., 'openai', 'anthropic') to ensure
        accurate diversity checks.
    """
    model_name = model_name.lower()

    # Canonical mappings based on known substrings
    if "gpt" in model_name or "openai" in model_name:
        return "openai"
    if "claude" in model_name or "anthropic" in model_name:
        return "anthropic"
    if "llama" in model_name or "meta" in model_name:
        return "meta"
    if "mistral" in model_name or "mixtral" in model_name:
        return "mistral"
    if "gemini" in model_name or "google" in model_name or "palm" in model_name or "gemma" in model_name:
        return "google"

    # Fallback heuristics for unknown models
    if "/" in model_name:
        # e.g. "provider/model-name" -> "provider"
        return model_name.split("/")[0]

    # e.g. "unknown-model-v1" -> "unknown"
    return model_name.split("-")[0]


def validate_model_diversity(profile: AdversaryProfile, target_model: str) -> None:
    """
    Ensures that the Simulator (Strategist & Attacker) uses a different model family than the Target.

    Prevents 'Model Collapse' where models share the same blind spots.

    Args:
        profile: The AdversaryProfile containing strategist and attacker models.
        target_model: The model ID of the target agent.

    Raises:
        ValueError: If there is a conflict in model families.
    """
    target_family = get_model_family(target_model)
    strat_family = get_model_family(profile.strategy_model)
    attack_family = get_model_family(profile.attack_model)

    if strat_family == target_family:
        raise ValueError(
            f"Model Collapse Risk: Strategist model '{profile.strategy_model}' (Family: {strat_family}) "
            f"conflicts with Target '{target_model}' (Family: {target_family})."
        )

    if attack_family == target_family:
        raise ValueError(
            f"Model Collapse Risk: Attacker model '{profile.attack_model}' (Family: {attack_family}) "
            f"conflicts with Target '{target_model}' (Family: {target_family})."
        )

    logger.info(
        f"Model Diversity Check Passed: Target={target_family} vs Strategist={strat_family}, Attacker={attack_family}"
    )
