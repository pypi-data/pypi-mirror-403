"""Context Manager - Smart context pruning and cost management.

Prevents context bloat by:
1. Estimating tokens before sending to LLM
2. Pruning old messages to fit within limits
3. Optionally summarizing older context
4. Tracking costs

Usage:
    manager = ContextManager(max_tokens=4000)
    pruned = manager.prune_messages(messages)
    cost = manager.estimate_cost(messages, model="gpt-4o")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Approximate token costs per 1K tokens (as of 2024)
MODEL_COSTS = {
    # OpenAI
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    # Anthropic
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
}

# Context window limits
MODEL_CONTEXT_LIMITS = {
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16385,
    "claude-3-5-sonnet-20241022": 200000,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
}


def estimate_tokens(text: str) -> int:
    """Estimate token count. Roughly 4 chars per token for English."""
    if not text:
        return 0
    return len(text) // 4 + 1


def estimate_message_tokens(message: dict[str, Any]) -> int:
    """Estimate tokens for a single message."""
    content = message.get("content", "")
    role = message.get("role", "")
    # Add overhead for role/formatting (~4 tokens)
    return estimate_tokens(content) + estimate_tokens(role) + 4


def estimate_messages_tokens(messages: list[dict[str, Any]]) -> int:
    """Estimate total tokens for a list of messages."""
    return sum(estimate_message_tokens(m) for m in messages)


@dataclass
class ContextStats:
    """Statistics about context usage."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    messages_count: int = 0
    messages_pruned: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class ContextManager:
    """Manages LLM context to prevent bloat and control costs.

    Attributes:
        max_context_tokens: Maximum tokens to send (leave room for output)
        max_output_tokens: Expected max output tokens
        reserve_tokens: Tokens to reserve for system prompt etc.
        prioritize_recent: Keep most recent messages when pruning
    """

    max_context_tokens: int = 4000
    max_output_tokens: int = 1000
    reserve_tokens: int = 500  # For system prompt, tool definitions, etc.
    prioritize_recent: bool = True

    # Running totals
    total_input_tokens: int = field(default=0, init=False)
    total_output_tokens: int = field(default=0, init=False)
    total_cost_usd: float = field(default=0.0, init=False)
    call_count: int = field(default=0, init=False)

    def available_tokens(self) -> int:
        """Tokens available for context after reserves."""
        return self.max_context_tokens - self.max_output_tokens - self.reserve_tokens

    def prune_messages(
        self,
        messages: list[dict[str, Any]],
        *,
        keep_system: bool = True,
        min_recent: int = 3,
    ) -> tuple[list[dict[str, Any]], ContextStats]:
        """Prune messages to fit within token limit.

        Args:
            messages: List of messages to prune
            keep_system: Always keep system messages
            min_recent: Minimum recent messages to keep

        Returns:
            Tuple of (pruned messages, stats)
        """
        if not messages:
            return [], ContextStats()

        available = self.available_tokens()
        stats = ContextStats(messages_count=len(messages))

        # Separate system messages and conversation
        system_msgs = []
        conversation = []

        for msg in messages:
            if msg.get("role") == "system" and keep_system:
                system_msgs.append(msg)
            else:
                conversation.append(msg)

        # Calculate system tokens
        system_tokens = estimate_messages_tokens(system_msgs)
        remaining = available - system_tokens

        if remaining <= 0:
            # Even system prompts exceed limit!
            stats.messages_pruned = len(conversation)
            return system_msgs[:1], stats  # Keep only first system message

        # Prune conversation to fit
        pruned_conversation = []
        current_tokens = 0

        if self.prioritize_recent:
            # Work backwards from most recent
            for msg in reversed(conversation):
                msg_tokens = estimate_message_tokens(msg)
                if current_tokens + msg_tokens <= remaining:
                    pruned_conversation.insert(0, msg)
                    current_tokens += msg_tokens
                elif len(pruned_conversation) < min_recent:
                    # Force keep minimum recent
                    pruned_conversation.insert(0, msg)
                    current_tokens += msg_tokens
                else:
                    stats.messages_pruned += 1
        else:
            # Keep oldest first
            for msg in conversation:
                msg_tokens = estimate_message_tokens(msg)
                if current_tokens + msg_tokens <= remaining:
                    pruned_conversation.append(msg)
                    current_tokens += msg_tokens
                else:
                    stats.messages_pruned += 1

        result = system_msgs + pruned_conversation
        stats.input_tokens = estimate_messages_tokens(result)
        stats.total_tokens = stats.input_tokens

        return result, stats

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int = 0,
        model: str = "gpt-4o",
    ) -> float:
        """Estimate cost in USD for a call.

        Args:
            input_tokens: Input token count
            output_tokens: Output token count (or estimate)
            model: Model name

        Returns:
            Estimated cost in USD
        """
        costs = MODEL_COSTS.get(model, MODEL_COSTS["gpt-4o"])
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        return input_cost + output_cost

    def record_call(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "gpt-4o",
    ) -> ContextStats:
        """Record a completed LLM call for tracking.

        Args:
            input_tokens: Actual input tokens used
            output_tokens: Actual output tokens generated
            model: Model used

        Returns:
            Stats for this call
        """
        cost = self.estimate_cost(input_tokens, output_tokens, model)

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost_usd += cost
        self.call_count += 1

        return ContextStats(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost_usd=cost,
        )

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all tracked calls."""
        return {
            "call_count": self.call_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "avg_tokens_per_call": (
                (self.total_input_tokens + self.total_output_tokens) / self.call_count
                if self.call_count > 0
                else 0
            ),
        }


def prune_chat_history(
    messages: list[dict[str, Any]],
    max_tokens: int = 3000,
    min_recent: int = 3,
) -> list[dict[str, Any]]:
    """Convenience function to prune chat history.

    Args:
        messages: Chat messages
        max_tokens: Maximum tokens for history (this IS the available space)
        min_recent: Minimum recent messages to keep

    Returns:
        Pruned messages
    """
    # For this convenience function, max_tokens IS the available space
    # So set reserves to 0
    manager = ContextManager(
        max_context_tokens=max_tokens,
        max_output_tokens=0,
        reserve_tokens=0,
    )
    pruned, _ = manager.prune_messages(messages, min_recent=min_recent)
    return pruned


__all__ = [
    "ContextManager",
    "ContextStats",
    "estimate_tokens",
    "estimate_messages_tokens",
    "prune_chat_history",
    "MODEL_COSTS",
    "MODEL_CONTEXT_LIMITS",
]
