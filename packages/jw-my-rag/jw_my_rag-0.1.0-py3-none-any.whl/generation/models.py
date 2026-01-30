"""Data models for generation layer.

Contains data classes for LLM responses and generated outputs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from retrieval import ExpandedResult


@dataclass
class LLMResponse:
    """Response from LLM generation.

    Attributes:
        content: Generated text content
        model: Model name used for generation
        usage: Optional token usage information
    """

    content: str
    model: str
    usage: Optional[dict] = None


@dataclass
class GeneratedResponse:
    """Complete RAG response with source attribution.

    Attributes:
        query: Original user query
        answer: Generated answer text
        sources: Retrieved context sources
        model: LLM model used
        timestamp: Generation timestamp
    """

    query: str
    answer: str
    sources: List[ExpandedResult]
    model: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def format_with_sources(self) -> str:
        """Format response with source attribution.

        Returns:
            Formatted string with answer and source list
        """
        lines = [self.answer, "", "---", "Sources:"]
        for i, expanded in enumerate(self.sources, 1):
            source = expanded.result.metadata.get("source", "unknown")
            view = expanded.result.view.value
            similarity = f"{expanded.result.similarity:.2f}"
            lines.append(f"  [{i}] {source} ({view}, sim: {similarity})")
        return "\n".join(lines)


@dataclass
class ConversationTurn:
    """Single turn in a conversation."""

    query: str
    response: GeneratedResponse


@dataclass
class Conversation:
    """Multi-turn conversation state.

    Attributes:
        turns: List of conversation turns
        max_history: Maximum turns to keep in history
    """

    turns: List[ConversationTurn] = field(default_factory=list)
    max_history: int = 5

    def add_turn(self, query: str, response: GeneratedResponse) -> None:
        """Add a turn, maintaining max history."""
        self.turns.append(ConversationTurn(query=query, response=response))
        if len(self.turns) > self.max_history:
            self.turns = self.turns[-self.max_history :]

    def get_history_context(self) -> str:
        """Format conversation history for context.

        Returns:
            Formatted string of recent conversation turns
        """
        if not self.turns:
            return ""

        lines = ["Previous conversation:"]
        for turn in self.turns[-3:]:  # Last 3 turns
            lines.append(f"User: {turn.query}")
            lines.append(f"Assistant: {turn.response.answer[:200]}...")
        return "\n".join(lines)

    def clear(self) -> None:
        """Clear conversation history."""
        self.turns = []


__all__ = [
    "LLMResponse",
    "GeneratedResponse",
    "ConversationTurn",
    "Conversation",
]
