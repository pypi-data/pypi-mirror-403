# Developer UX Guide

**Document Status:** Architecture Specification for Kaizen Development Team
**Version:** 1.0.0
**Date:** 2026-01-21

---

## Executive Summary

Developer experience is a first-class architectural concern. The Coursewright AI platform must:

1. **Minimize time-to-first-success**: 2 lines to "Hello World"
2. **Enable progressive complexity**: Simple → Expert with no cliff
3. **Provide sensible defaults**: Zero-config works for 80% of cases
4. **Maintain consistency**: Same patterns across all capability axes
5. **Flow naturally**: No surprising behaviors or "gotchas"

This document defines the UX patterns that achieve these goals.

---

## Design Principles

### 1. Progressive Disclosure

Complexity should be **revealed, not imposed**. Developers should only see what they need:

```python
# Level 1: "I just want to chat with an AI" (2 lines)
agent = Agent(model="gpt-4")
result = agent.run("What is IRP?")

# Level 2: "I want autonomous execution" (+1 param)
agent = Agent(model="gpt-4", execution_mode="autonomous")

# Level 3: "I want to use Claude Code runtime" (+1 param)
agent = Agent(model="claude-sonnet", runtime="claude_code")

# Level 4: "I want multi-LLM routing" (+1 block)
agent = Agent(
    model="gpt-4",
    llm_routing={
        "simple": "gpt-3.5-turbo",
        "complex": "claude-3-opus",
        "code": "gpt-4"
    }
)

# Level 5: "I want full control" (expert config)
agent = Agent(
    config=AgentConfig(
        execution_mode="autonomous",
        max_cycles=100,
        memory=HierarchicalMemory(...),
        runtime=ClaudeCodeAdapter(...),
        llm_router=CustomRouter(...),
        tools=[...],
        checkpoint_strategy="on_cycle"
    )
)
```

### 2. Sensible Defaults

Every parameter should have a default that works for most cases:

| Parameter | Default | Rationale |
|-----------|---------|-----------|
| `model` | **Required** | Forces explicit choice (cost awareness) |
| `execution_mode` | `"single"` | Simplest, safest mode |
| `runtime` | `"local"` | LocalKaizenAdapter (most flexible) |
| `memory` | `SessionMemory()` | Conversation continuity expected |
| `tool_access` | `"none"` | Security by default |
| `max_cycles` | `50` | Prevents infinite loops |

### 3. Fail-Fast with Helpful Errors

Invalid configurations should fail immediately with actionable messages:

```python
# Bad
agent = Agent(model="gpt-4", runtime="claude_code")
# Error: "Invalid configuration"  # ❌ Unhelpful

# Good
agent = Agent(model="gpt-4", runtime="claude_code")
# Error: "ClaudeCodeAdapter requires a Claude model (sonnet/opus/haiku).
#         You specified 'gpt-4'. Either:
#         1. Use model='claude-sonnet' with runtime='claude_code'
#         2. Use runtime='local' to use gpt-4 with LocalKaizenAdapter"
```

### 4. Consistency Across Axes

Same patterns everywhere—no special cases:

```python
# Configuration follows same pattern regardless of axis
agent = Agent(
    # Execution axis
    execution_mode="autonomous",
    max_cycles=50,

    # Memory axis
    memory="persistent",  # or MemoryProvider instance
    memory_path="./memory",

    # Tool axis
    tool_access="constrained",
    allowed_tools=["read_file", "search"],

    # Runtime axis
    runtime="claude_code",  # or RuntimeAdapter instance
)
```

---

## The Unified Agent API

### Core Interface

```python
from kaizen.agent import Agent

class Agent:
    """
    Unified agent interface supporting all capability combinations.

    Supports:
    - Single-turn, multi-turn, and autonomous execution
    - Any LLM provider (via LocalKaizenAdapter) or specific runtime
    - Stateless, session, persistent, or learning memory
    - No tools, read-only, constrained, or full tool access
    """

    def __init__(
        self,
        # Required
        model: str,

        # Execution (optional)
        execution_mode: Literal["single", "multi", "autonomous"] = "single",
        max_cycles: int = 50,
        timeout_seconds: float = 300.0,

        # Memory (optional)
        memory: Union[str, MemoryProvider] = "session",
        memory_path: Optional[str] = None,

        # Tools (optional)
        tool_access: Literal["none", "read_only", "constrained", "full"] = "none",
        tools: Optional[List[Tool]] = None,
        allowed_tools: Optional[List[str]] = None,

        # Runtime (optional)
        runtime: Union[str, RuntimeAdapter] = "local",

        # LLM Routing (optional)
        llm_routing: Optional[Dict[str, str]] = None,
        routing_strategy: str = "balanced",

        # Expert config (optional - overrides above)
        config: Optional[AgentConfig] = None
    ):
        """Initialize agent with progressive configuration."""
        ...

    # Core methods
    async def run(self, task: str, **kwargs) -> AgentResult:
        """Execute task and return result."""
        ...

    async def stream(self, task: str, **kwargs) -> AsyncIterator[str]:
        """Execute task with streaming output."""
        ...

    # Conversation methods (multi-turn/autonomous)
    async def chat(self, message: str) -> AgentResult:
        """Continue conversation with message."""
        ...

    def reset(self) -> None:
        """Reset conversation state."""
        ...

    # Control methods (autonomous)
    def pause(self) -> None:
        """Pause autonomous execution."""
        ...

    def resume(self) -> None:
        """Resume autonomous execution."""
        ...

    def stop(self) -> None:
        """Stop autonomous execution gracefully."""
        ...
```

### Configuration Shorthand

String shortcuts for common configurations:

```python
# Memory shortcuts
"stateless"   → StatelessMemory()
"session"     → SessionMemory()
"persistent"  → PersistentMemory(path="./memory")
"learning"    → LearningMemory(path="./memory")

# Runtime shortcuts
"local"       → LocalKaizenAdapter()
"claude_code" → ClaudeCodeAdapter()
"codex"       → OpenAICodexAdapter()
"gemini_cli"  → GeminiCLIAdapter()

# Tool access shortcuts
"none"        → ToolPolicy(access=ToolAccess.NONE)
"read_only"   → ToolPolicy(access=ToolAccess.READ_ONLY)
"constrained" → ToolPolicy(access=ToolAccess.CONSTRAINED)
"full"        → ToolPolicy(access=ToolAccess.FULL)
```

---

## Usage Patterns

### Pattern 1: Quick Q&A (Simplest)

```python
from kaizen.agent import Agent

agent = Agent(model="gpt-3.5-turbo")
result = await agent.run("What is covered interest parity?")
print(result.text)
```

### Pattern 2: Conversation

```python
agent = Agent(
    model="gpt-4",
    execution_mode="multi",
    memory="session"
)

# First message
result = await agent.chat("I'm learning about IRP. Can you explain it?")

# Follow-up (remembers context)
result = await agent.chat("What's the formula for the forward premium?")

# Another follow-up
result = await agent.chat("Can you give me an example with real numbers?")
```

### Pattern 3: Autonomous Task Execution

```python
agent = Agent(
    model="claude-sonnet",
    execution_mode="autonomous",
    runtime="claude_code",
    tool_access="full",
    max_cycles=100
)

# Agent works autonomously
result = await agent.run("""
    Create a Python module that calculates IRP forward rates.
    Include unit tests and documentation.
    Save to ./irp_calculator.py
""")

# Can monitor progress
agent.on_cycle(lambda cycle: print(f"Cycle {cycle.number}: {cycle.summary}"))
```

### Pattern 4: Multi-LLM Routing

```python
agent = Agent(
    model="gpt-4",  # Default
    runtime="local",  # Required for multi-LLM
    llm_routing={
        "simple": "gpt-3.5-turbo",
        "code": "gpt-4",
        "analysis": "claude-3-opus",
        "structured": "gpt-4-turbo"
    },
    routing_strategy="cost_optimized"
)

# Tasks automatically routed
await agent.run("What is 2+2?")  # → gpt-3.5-turbo
await agent.run("Implement an IRP calculator")  # → gpt-4
await agent.run("Analyze this complex hedging scenario...")  # → claude-3-opus
```

### Pattern 5: Full Expert Configuration

```python
from kaizen.agent import Agent, AgentConfig
from kaizen.memory import HierarchicalMemory
from kaizen.runtime import ClaudeCodeAdapter
from kaizen.tools import FileTools, BashTools

agent = Agent(
    config=AgentConfig(
        # Execution
        execution_mode="autonomous",
        max_cycles=200,
        timeout_seconds=600,
        checkpoint_strategy="on_cycle",
        checkpoint_interval=10,

        # Memory
        memory=HierarchicalMemory(
            hot_size=100,
            warm_backend="postgresql",
            warm_dsn="postgresql://...",
            cold_backend="s3",
            cold_bucket="agent-memory"
        ),

        # Runtime
        runtime=ClaudeCodeAdapter(
            model="claude-3-opus",
            allowed_tools=["Read", "Edit", "Bash", "Grep"],
            working_directory="/workspace"
        ),

        # Tools
        tool_access="constrained",
        tools=[
            FileTools(allowed_paths=["/workspace"]),
            BashTools(allowed_commands=["python", "pytest", "git"])
        ],

        # Hooks
        on_cycle=my_cycle_handler,
        on_tool_call=my_tool_handler,
        on_error=my_error_handler
    )
)
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Model-Runtime Mismatch

```python
# ❌ WRONG: GPT-4 with Claude Code runtime
agent = Agent(model="gpt-4", runtime="claude_code")
# ClaudeCodeAdapter only supports Claude models!

# ✅ CORRECT: Match model to runtime
agent = Agent(model="claude-sonnet", runtime="claude_code")
# OR
agent = Agent(model="gpt-4", runtime="local")  # LocalKaizenAdapter supports any
```

### Anti-Pattern 2: Autonomous Without Safeguards

```python
# ❌ DANGEROUS: Unlimited autonomous execution
agent = Agent(
    model="gpt-4",
    execution_mode="autonomous",
    tool_access="full",
    max_cycles=float('inf')  # Never do this!
)

# ✅ SAFE: Bounded execution with checkpoints
agent = Agent(
    model="gpt-4",
    execution_mode="autonomous",
    tool_access="constrained",
    max_cycles=100,
    timeout_seconds=300,
    config=AgentConfig(checkpoint_strategy="on_cycle")
)
```

### Anti-Pattern 3: Ignoring Runtime Constraints

```python
# ❌ WRONG: Expecting multi-LLM with Claude Code
agent = Agent(
    model="claude-sonnet",
    runtime="claude_code",
    llm_routing={  # This is ignored! Claude Code uses Claude only.
        "simple": "gpt-3.5-turbo"
    }
)

# ✅ CORRECT: Use local runtime for multi-LLM
agent = Agent(
    model="gpt-4",
    runtime="local",
    llm_routing={
        "simple": "gpt-3.5-turbo",
        "complex": "claude-3-opus"
    }
)
```

### Anti-Pattern 4: Over-Configuration

```python
# ❌ OVER-ENGINEERED: Unnecessary complexity for simple use
agent = Agent(
    model="gpt-4",
    execution_mode="single",
    memory=HierarchicalMemory(
        hot_size=1000,
        warm_backend="postgresql",
        cold_backend="s3"
    ),
    tool_access="full",
    tools=[...],
    runtime=ClaudeCodeAdapter(...),
    config=AgentConfig(
        checkpoint_strategy="on_cycle",
        ...
    )
)
result = await agent.run("What is IRP?")  # Simple Q&A!

# ✅ RIGHT-SIZED: Match complexity to need
agent = Agent(model="gpt-4")
result = await agent.run("What is IRP?")
```

---

## Error Messages Design

Clear, actionable error messages:

```python
class ConfigurationError(Exception):
    """Configuration validation errors with remediation guidance."""

    @classmethod
    def model_runtime_mismatch(cls, model: str, runtime: str) -> "ConfigurationError":
        runtime_models = {
            "claude_code": ["claude-sonnet", "claude-opus", "claude-haiku"],
            "codex": ["gpt-4", "gpt-3.5-turbo"],
            "gemini_cli": ["gemini-pro", "gemini-flash"],
            "local": ["any"]
        }

        valid = runtime_models.get(runtime, ["unknown"])
        return cls(
            f"Model '{model}' is not compatible with runtime '{runtime}'.\n"
            f"\n"
            f"Valid models for '{runtime}': {', '.join(valid)}\n"
            f"\n"
            f"Options:\n"
            f"  1. Change model to one of: {', '.join(valid)}\n"
            f"  2. Change runtime to 'local' (supports any model)\n"
            f"\n"
            f"Example:\n"
            f"  agent = Agent(model='{valid[0]}', runtime='{runtime}')\n"
            f"  # OR\n"
            f"  agent = Agent(model='{model}', runtime='local')"
        )
```

---

## IDE Integration

Type hints and docstrings for excellent IDE support:

```python
class Agent:
    def __init__(
        self,
        model: str,
        *,
        execution_mode: Literal["single", "multi", "autonomous"] = "single",
        # ... other params
    ) -> None:
        """
        Create an AI agent.

        Args:
            model: LLM model name (e.g., "gpt-4", "claude-sonnet").
                   Required to ensure cost awareness.

            execution_mode: How the agent processes requests.
                - "single": One response per request (default)
                - "multi": Conversation with memory
                - "autonomous": Self-directed task completion

        Examples:
            # Simple Q&A
            >>> agent = Agent(model="gpt-4")
            >>> result = await agent.run("What is IRP?")

            # Autonomous code generation
            >>> agent = Agent(
            ...     model="claude-sonnet",
            ...     execution_mode="autonomous",
            ...     runtime="claude_code"
            ... )
            >>> result = await agent.run("Create an IRP calculator")

        Raises:
            ConfigurationError: If model/runtime combination is invalid

        See Also:
            AgentConfig: For expert configuration options
        """
```

---

## Summary: The "Flow" Test

Every API design decision should pass the "flow test":

1. **Can a beginner get started in 2 lines?** ✅
2. **Can they add capabilities one parameter at a time?** ✅
3. **Do defaults do the right thing?** ✅
4. **Are error messages actionable?** ✅
5. **Is there a clear path from simple to expert?** ✅

If any answer is "no," revise the design.

---

## Implementation Checklist

- [ ] Unified `Agent` class with progressive configuration
- [ ] String shortcuts for common configurations
- [ ] Configuration validation with helpful errors
- [ ] Type hints and docstrings for IDE support
- [ ] Consistent parameter patterns across all axes
- [ ] Sensible defaults for all optional parameters
- [ ] Clear documentation with examples at each level

---

**Previous Document**: [05-memory-integration.md](./05-memory-integration.md) - Memory system design.

**Return to**: [00-executive-summary.md](./00-executive-summary.md) - Architecture overview.
