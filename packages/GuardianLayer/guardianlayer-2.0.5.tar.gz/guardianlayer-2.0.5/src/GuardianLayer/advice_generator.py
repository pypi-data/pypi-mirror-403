"""
Advice Generator - Customizable Prompt Injection for Self-Awareness
Generates context-aware directives based on the AI's past experiences.
Now with caching for performance optimization.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Optional

from .interfaces import AsyncCacheProvider, CacheProvider
from .providers import InMemoryCacheProvider

logger = logging.getLogger(__name__)


class AdviceStyle(Enum):
    """Predefined advice formatting styles"""

    CONCISE = "concise"  # Short and direct (for smaller models)
    EXPERT = "expert"  # Technical details (for powerful models)
    FRIENDLY = "friendly"  # Conversational tone


@dataclass
class AdviceContext:
    """Context passed to advice resolvers"""

    tool_name: str
    failure_count: int
    last_error: Optional[str]
    similar_success: Optional[Dict]
    tool_reliability: Optional[float]


class AdviceGenerator:
    """
    Generates prompt injections based on the agent's experiences.
    Supports multiple styles, custom resolvers, and caching.

    v2.0: Now with built-in caching to avoid regenerating identical advice.
    """

    def __init__(
        self,
        style: AdviceStyle = AdviceStyle.CONCISE,
        cache_provider: Optional[CacheProvider] = None,
    ):
        self._style = style
        self._custom_resolver: Optional[Callable[[AdviceContext], str]] = None

        # v2.0: Optional cache
        self._cache = (
            cache_provider
            if cache_provider
            else InMemoryCacheProvider(max_size=500, default_ttl=3600)
        )
        self._is_async = isinstance(self._cache, AsyncCacheProvider)

    def set_style(self, style: AdviceStyle):
        """Change the advice formatting style"""
        self._style = style

    def set_custom_resolver(self, resolver: Callable[[AdviceContext], str]):
        """
        Set a custom resolver function for full control over advice generation.

        Args:
            resolver: A function that takes an AdviceContext and returns a string.
                     Return empty string for no advice.
        """
        self._custom_resolver = resolver
        logger.info("🎯 Custom advice resolver registered")

    def generate(self, context: AdviceContext) -> str:
        """
        Generate advice based on the current context.
        Uses cache when available to avoid regenerating identical advice.
        """
        cache_key = self._generate_cache_key(context)

        # Check cache first (Sync-compatible only)
        if self._cache and not self._is_async:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        # Generate advice
        advice = self._generate_advice(context)

        # Cache the result (v2.0)
        if self._cache and advice and not self._is_async:
            self._cache.set(cache_key, advice)

        return advice

    async def generate_async(self, context: AdviceContext) -> str:
        """
        True async version of generate.
        Handles non-blocking cache lookups.
        """
        cache_key = self._generate_cache_key(context)

        # Check cache
        if self._cache:
            if self._is_async:
                cached = await self._cache.get(cache_key)
            else:
                cached = self._cache.get(cache_key)

            if cached is not None:
                return cached

        # Generate advice
        advice = self._generate_advice(context)

        # Cache the result
        if self._cache and advice:
            if self._is_async:
                await self._cache.set(cache_key, advice)
            else:
                self._cache.set(cache_key, advice)

        return advice

    def _generate_cache_key(self, context: AdviceContext) -> str:
        """Create a cache key for AdviceContext"""
        # We need a string key for CacheProvider
        # Simple string formatting:
        return f"advice:{context.tool_name}:{context.failure_count}:{self._style.value}:{context.tool_reliability}"

    def _generate_advice(self, context: AdviceContext) -> str:
        """Internal method to actually generate advice"""
        # Use custom resolver if set
        if self._custom_resolver:
            try:
                return self._custom_resolver(context)
            except Exception as e:
                logger.error(f"Custom resolver error: {e}")

        # No issues? No advice needed
        if context.failure_count == 0 and context.tool_reliability is None:
            return ""

        # Generate based on style
        if self._style == AdviceStyle.CONCISE:
            return self._generate_concise(context)
        elif self._style == AdviceStyle.EXPERT:
            return self._generate_expert(context)
        elif self._style == AdviceStyle.FRIENDLY:
            return self._generate_friendly(context)

        return ""

    def get_cache_stats(self) -> Optional[Dict]:
        """Get cache statistics if caching is enabled"""
        return self._cache.get_stats()

    def _generate_concise(self, context: AdviceContext) -> str:
        """Short, direct warnings"""
        parts = []

        if context.failure_count >= 3:
            parts.append(
                f" Tool '{context.tool_name}' failed {context.failure_count}x. Change approach."
            )
        elif context.failure_count > 0:
            parts.append(f"Note: '{context.tool_name}' failed {context.failure_count}x.")

        if context.similar_success:
            parts.append(f"Try format: {context.similar_success}")

        if context.tool_reliability and context.tool_reliability < 0.5:
            parts.append(
                f"'{context.tool_name}' has {int(context.tool_reliability * 100)}% success rate."
            )

        return " ".join(parts)

    def _generate_expert(self, context: AdviceContext) -> str:
        """Technical, detailed analysis"""
        lines = ["[SELF-AWARENESS INJECTION]"]

        if context.failure_count > 0:
            lines.append(f"- Tool: {context.tool_name}")
            lines.append(f"- Failure count: {context.failure_count}")
            if context.last_error:
                lines.append(f"- Last error: {context.last_error}")

        if context.tool_reliability is not None:
            lines.append(f"- Historical reliability: {context.tool_reliability:.1%}")

        if context.similar_success:
            lines.append(f"- Known working pattern: {context.similar_success}")

        if context.failure_count >= 3:
            lines.append("- RECOMMENDATION: Consider alternative tool or abort task.")

        return "\n".join(lines) if len(lines) > 1 else ""

    def _generate_friendly(self, context: AdviceContext) -> str:
        """Conversational, helpful tone"""
        if context.failure_count >= 3:
            msg = f"Hey, I noticed you've tried '{context.tool_name}' {context.failure_count} times without success. "
            if context.similar_success:
                msg += f"Maybe try this format instead: {context.similar_success}"
            else:
                msg += "Perhaps we should try a different approach?"
            return msg
        elif context.failure_count > 0:
            return f"Quick note: '{context.tool_name}' didn't work last time. Double-check your parameters!"

        return ""
