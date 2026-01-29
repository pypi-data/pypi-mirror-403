"""
Agent execution system for the Kaizen framework.

This module provides structured output parsing, pattern-specific execution
logic for signature-based programming, and execution event types for
autonomous agent runtime.
"""

from .events import (
    # Core enum and base
    EventType,
    ExecutionEvent,
    # Agentic-OS Core Events (TODO-204)
    StartedEvent,
    ThinkingEvent,
    MessageEvent,
    ToolUseEvent,
    ToolResultEvent,
    ProgressEvent,
    CompletedEvent,
    ErrorEvent,
    # Subagent events (TODO-203)
    SubagentSpawnEvent,
    SubagentCompleteEvent,
    # Skill events (TODO-203)
    SkillInvokeEvent,
    SkillCompleteEvent,
    # Cost tracking
    CostUpdateEvent,
)
from .parser import OutputParser, ResponseParser, StructuredOutputParser
from .patterns import ChainOfThoughtExecutor, PatternExecutor, ReActExecutor
from .streaming_executor import ExecutionMetrics, StreamingExecutor, format_sse
from .subagent_result import SkillResult, SubagentResult

__all__ = [
    # Output parsing
    "OutputParser",
    "ResponseParser",
    "StructuredOutputParser",
    # Pattern execution
    "PatternExecutor",
    "ChainOfThoughtExecutor",
    "ReActExecutor",
    # Streaming execution (TODO-204)
    "StreamingExecutor",
    "ExecutionMetrics",
    "format_sse",
    # Execution events - Core enum and base
    "EventType",
    "ExecutionEvent",
    # Execution events - Agentic-OS Core Events (TODO-204)
    "StartedEvent",
    "ThinkingEvent",
    "MessageEvent",
    "ToolUseEvent",
    "ToolResultEvent",
    "ProgressEvent",
    "CompletedEvent",
    "ErrorEvent",
    # Execution events - Subagent (TODO-203)
    "SubagentSpawnEvent",
    "SubagentCompleteEvent",
    # Execution events - Skill (TODO-203)
    "SkillInvokeEvent",
    "SkillCompleteEvent",
    # Execution events - Cost
    "CostUpdateEvent",
    # Result types (TODO-203)
    "SubagentResult",
    "SkillResult",
]
