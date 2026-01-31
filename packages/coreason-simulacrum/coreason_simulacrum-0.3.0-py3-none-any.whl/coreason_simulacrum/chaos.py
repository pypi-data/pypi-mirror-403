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
Chaos Engineering Utilities for Coreason Simulacrum.

This module provides the `ChaosOrchestrator` and `chaos_inject` decorator,
enabling the simulation of infrastructure failures (latency, errors, noise)
within the adversarial workflow. This ensures that agents are resilient
against transport-layer issues and degrading network conditions.
"""

import asyncio
import builtins
import functools
import inspect
import random
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Callable, Iterator, Optional, TypeVar, cast

from coreason_identity.models import UserContext

from coreason_simulacrum.schemas import ChaosConfig
from coreason_simulacrum.utils.logger import logger

# Define the ContextVar to hold the current configuration
active_chaos_config: ContextVar[Optional[ChaosConfig]] = ContextVar("active_chaos_config", default=None)
active_user_context: ContextVar[Optional[UserContext]] = ContextVar("active_user_context", default=None)


@contextmanager
def use_chaos_config(config: ChaosConfig) -> Iterator[None]:
    """
    Context manager to set the active chaos configuration for the current context.

    Args:
        config: The ChaosConfig object defining latency, error rates, etc.

    Yields:
        None: Control is yielded back to the context block.
    """
    token = active_chaos_config.set(config)
    try:
        yield
    finally:
        active_chaos_config.reset(token)


@contextmanager
def use_user_context(context: UserContext) -> Iterator[None]:
    """
    Context manager to set the active user context for the current context.

    Args:
        context: The UserContext object.

    Yields:
        None: Control is yielded back to the context block.
    """
    token = active_user_context.set(context)
    try:
        yield
    finally:
        active_user_context.reset(token)


class ChaosOrchestrator:
    """
    Encapsulates the logic for applying chaos effects (errors, latency, noise).

    This class serves as the central handler for all chaos injection logic,
    reading the active configuration from context variables and applying
    disruptions to function execution.
    """

    @staticmethod
    def get_config() -> Optional[ChaosConfig]:
        """
        Retrieves the current chaos configuration from the context variable.

        Returns:
            Optional[ChaosConfig]: The current configuration, or None if not set.
        """
        return active_chaos_config.get()

    @staticmethod
    def get_context(context: Optional[UserContext] = None) -> UserContext:
        """
        Retrieves the current user context, raising ValueError if not present.

        Args:
            context: Explicitly provided context (optional).

        Returns:
            UserContext: The active user context.

        Raises:
            ValueError: If context is missing.
        """
        ctx = context or active_user_context.get()
        if not ctx:
            raise ValueError("UserContext is required for chaos operations")
        return ctx

    @staticmethod
    def apply_pre_call(config: Optional[ChaosConfig], context: Optional[UserContext] = None) -> None:
        """
        Apply pre-execution chaos (Errors).

        This method determines if an exception should be raised based on the
        configured error rate.

        Args:
            config: The active ChaosConfig.
            context: The active UserContext.

        Raises:
            RuntimeError: Or other configured exception type, if the random
                roll falls within the error rate.
        """
        if not config:
            return

        ctx = ChaosOrchestrator.get_context(context)

        # Error Injection
        if config.error_rate > 0.0 and random.random() < config.error_rate:
            logger.warning(
                "Injecting chaos fault",
                user_id=ctx.user_id,
                fault_type="error_injection",
                exception_type=config.exception_type,
            )
            exception_class = getattr(builtins, config.exception_type, RuntimeError)
            raise exception_class(config.exception_msg)

    @staticmethod
    def apply_latency_sync(config: Optional[ChaosConfig], context: Optional[UserContext] = None) -> None:
        """
        Apply synchronous latency.

        Args:
            config: The active ChaosConfig.
            context: The active UserContext.
        """
        if config and config.latency_ms > 0:
            ChaosOrchestrator.get_context(context)  # Validation only
            time.sleep(config.latency_ms / 1000.0)

    @staticmethod
    async def apply_latency_async(config: Optional[ChaosConfig], context: Optional[UserContext] = None) -> None:
        """
        Apply asynchronous latency.

        Args:
            config: The active ChaosConfig.
            context: The active UserContext.
        """
        if config and config.latency_ms > 0:
            ChaosOrchestrator.get_context(context)  # Validation only
            await asyncio.sleep(config.latency_ms / 1000.0)

    @staticmethod
    def apply_post_call(result: Any, config: Optional[ChaosConfig], context: Optional[UserContext] = None) -> Any:
        """
        Apply post-execution chaos (Noise Injection).

        This method potentially corrupts string results based on the noise rate.

        Args:
            result: The return value from the function call.
            config: The active ChaosConfig.
            context: The active UserContext.

        Returns:
            Any: The original or mutated result.
        """
        if config and config.noise_rate > 0.0 and isinstance(result, str):
            return ChaosOrchestrator._inject_noise_into_string(result, config.noise_rate, context)
        return result

    @staticmethod
    def should_throttle(config: Optional[ChaosConfig]) -> bool:
        """
        Check if token throttling should be applied.

        Args:
            config: The active ChaosConfig.

        Returns:
            bool: True if throttling is enabled.
        """
        return bool(config and config.token_throttle)

    @staticmethod
    def _inject_noise_into_string(text: str, rate: float, context: Optional[UserContext] = None) -> str:
        """
        Injects noise into a string by randomly mutating characters.

        Mutation types include swapping adjacent characters, dropping characters,
        or inserting random characters.

        Args:
            text: The string to corrupt.
            rate: The percentage of characters to mutate (approximate).
            context: The active UserContext.

        Returns:
            str: The corrupted string.
        """
        if rate <= 0.0 or not text:
            return text

        ctx = ChaosOrchestrator.get_context(context)
        logger.warning(
            "Injecting chaos fault",
            user_id=ctx.user_id,
            fault_type="noise_injection",
        )

        chars = list(text)
        num_mutations = max(1, int(len(chars) * rate))
        indices = random.sample(range(len(chars)), min(len(chars), num_mutations))

        for i in indices:
            mutation_type = random.choice(["swap", "drop", "insert"])
            if mutation_type == "swap" and len(chars) > 1:
                # Swap with a random neighbor
                j = max(0, min(len(chars) - 1, i + random.choice([-1, 1])))
                chars[i], chars[j] = chars[j], chars[i]
            elif mutation_type == "drop":
                chars[i] = ""  # Mark for removal
            elif mutation_type == "insert":
                # Insert a random printable character
                random_char = chr(random.randint(33, 126))
                chars[i] = chars[i] + random_char

        return "".join(chars)


F = TypeVar("F", bound=Callable[..., Any])


def chaos_inject(func: F) -> F:
    """
    Decorator to inject chaos (latency, errors, noise, etc.) based on the active configuration.

    This decorator intercepts calls to the target function and applies
    configured chaos effects such as latency, exception raising, and return
    value corruption. It supports synchronous and asynchronous functions
    and generators.

    Args:
        func: The function to decorate.

    Returns:
        F: The decorated function with chaos injection logic.
    """
    if inspect.isasyncgenfunction(func):

        @functools.wraps(func)
        async def async_gen_wrapper(*args: Any, **kwargs: Any) -> Any:
            config = ChaosOrchestrator.get_config()
            # Retrieve context from ContextVar
            context = active_user_context.get()

            ChaosOrchestrator.apply_pre_call(config, context)
            await ChaosOrchestrator.apply_latency_async(config, context)

            async for item in func(*args, **kwargs):
                if ChaosOrchestrator.should_throttle(config):
                    await asyncio.sleep(1.0)
                yield ChaosOrchestrator.apply_post_call(item, config, context)

        return cast(F, async_gen_wrapper)

    elif inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            config = ChaosOrchestrator.get_config()
            context = active_user_context.get()

            ChaosOrchestrator.apply_pre_call(config, context)
            await ChaosOrchestrator.apply_latency_async(config, context)

            result = await func(*args, **kwargs)
            return ChaosOrchestrator.apply_post_call(result, config, context)

        return cast(F, async_wrapper)

    elif inspect.isgeneratorfunction(func):

        @functools.wraps(func)
        def sync_gen_wrapper(*args: Any, **kwargs: Any) -> Any:
            config = ChaosOrchestrator.get_config()
            context = active_user_context.get()

            ChaosOrchestrator.apply_pre_call(config, context)
            ChaosOrchestrator.apply_latency_sync(config, context)

            for item in func(*args, **kwargs):
                if ChaosOrchestrator.should_throttle(config):
                    time.sleep(1.0)
                yield ChaosOrchestrator.apply_post_call(item, config, context)

        return cast(F, sync_gen_wrapper)

    else:

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            config = ChaosOrchestrator.get_config()
            context = active_user_context.get()

            ChaosOrchestrator.apply_pre_call(config, context)
            ChaosOrchestrator.apply_latency_sync(config, context)

            result = func(*args, **kwargs)
            return ChaosOrchestrator.apply_post_call(result, config, context)

        return cast(F, sync_wrapper)
