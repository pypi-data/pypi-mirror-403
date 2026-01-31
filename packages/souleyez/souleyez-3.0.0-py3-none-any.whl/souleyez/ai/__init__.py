"""
souleyez.ai - AI-powered attack path recommendations and report generation
"""

from .ollama_service import OllamaService, OLLAMA_AVAILABLE
from .context_builder import ContextBuilder
from .recommender import AttackRecommender
from .llm_provider import LLMProvider, LLMProviderType
from .ollama_provider import OllamaProvider
from .claude_provider import (
    ClaudeProvider,
    ANTHROPIC_AVAILABLE,
    set_claude_api_key,
    clear_claude_api_key,
)
from .llm_factory import LLMFactory
from .report_context import ReportContextBuilder
from .report_service import AIReportService

__all__ = [
    "OllamaService",
    "ContextBuilder",
    "AttackRecommender",
    "OLLAMA_AVAILABLE",
    "LLMProvider",
    "LLMProviderType",
    "OllamaProvider",
    "ClaudeProvider",
    "ANTHROPIC_AVAILABLE",
    "set_claude_api_key",
    "clear_claude_api_key",
    "LLMFactory",
    "ReportContextBuilder",
    "AIReportService",
]
