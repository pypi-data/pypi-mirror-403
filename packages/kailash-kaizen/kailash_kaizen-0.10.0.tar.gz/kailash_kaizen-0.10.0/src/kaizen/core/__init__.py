"""
Core Kaizen framework components.

This module contains the foundational classes and interfaces for the Kaizen framework:
- Framework initialization and management
- Base classes and interfaces
- Agent creation and management
- Token counting utilities
"""

from .agents import Agent, AgentManager
from .config import KaizenConfig, MemoryProvider, OptimizationEngine

# PERFORMANCE OPTIMIZED: Use lightweight imports for <100ms startup
from .framework import Kaizen

# Token counting utilities
from .token_counter import (
    TIKTOKEN_AVAILABLE,
    TokenCounter,
    count_tokens,
    get_token_counter,
)

# Signature classes available in kaizen.signatures (Option 3: DSPy-inspired)

__all__ = [
    "Kaizen",
    "MemoryProvider",
    "OptimizationEngine",
    "KaizenConfig",
    "Agent",
    "AgentManager",
    # Token counting
    "TokenCounter",
    "get_token_counter",
    "count_tokens",
    "TIKTOKEN_AVAILABLE",
]
