"""Generation layer for RAG system.

Handles LLM-based response generation with source attribution.

Components:
- GeminiLLMClient: LLM client using Google Gemini API
- GenerationPipeline: Orchestrates context assembly and generation
- PromptTemplate: Manages RAG prompts and context formatting

Rules:
- DEP-GEN-001: MAY import shared (config, exceptions)
- DEP-GEN-002: MAY import retrieval (ExpandedResult for type hints)
- DEP-GEN-BAN-001: MUST NOT import api
- DEP-GEN-BAN-002: MUST NOT import storage directly
- DEP-GEN-BAN-003: MUST NOT import ingestion
"""

from .client import GeminiLLMClient, LLMClientProtocol
from .models import (
    Conversation,
    ConversationTurn,
    GeneratedResponse,
    LLMResponse,
)
from .pipeline import GenerationPipeline
from .prompts import PromptContext, PromptTemplate

__all__ = [
    # Client
    "GeminiLLMClient",
    "LLMClientProtocol",
    # Models
    "LLMResponse",
    "GeneratedResponse",
    "ConversationTurn",
    "Conversation",
    # Prompts
    "PromptTemplate",
    "PromptContext",
    # Pipeline
    "GenerationPipeline",
]
