# Agent Capability Taxonomy

**Document Status:** Architecture Specification for Kaizen Development Team
**Version:** 1.0.0
**Date:** 2026-01-21

---

## Executive Summary

This document defines the taxonomy of agent capabilities for the Coursewright AI platform. After extensive analysis, we recommend a **Configuration-Driven Strategy Pattern** rather than class hierarchy. This approach provides flexibility, runtime switching, and clean separation of concerns.

---

## The Problem: Why Not Class Hierarchy?

### Naive Approach: Inheritance Hierarchy

```python
# ❌ BAD: Class hierarchy explosion
class Agent: ...
class SingleTurnAgent(Agent): ...
class MultiTurnAgent(Agent): ...
class AutonomousAgent(Agent): ...
class SingleTurnWithMemoryAgent(SingleTurnAgent): ...
class AutonomousWithPersistentMemoryAgent(AutonomousAgent): ...
class AutonomousWithPersistentMemoryAndToolsAgent(AutonomousAgent): ...
# ... 48+ classes needed for all combinations
```

### Problems with Hierarchy

1. **Combinatorial Explosion**: 3 execution modes × 4 memory levels × 4 tool levels = 48 classes
2. **No Runtime Switching**: Can't change from single-turn to autonomous without creating new object
3. **Orthogonal Concerns Mixed**: Memory and tools are independent of execution mode
4. **Inflexible**: Adding new capability requires restructuring entire hierarchy

---

## The Solution: Three Orthogonal Axes

Agent capabilities exist on **three independent axes**:

```
                     EXECUTION MODE
                          |
         single-turn -----+------ multi-turn -----+------ autonomous
                          |
              MEMORY      |
              DEPTH       |
                          |
    stateless ------------|------------- persistent ----------- learning
                          |
                          |
                      TOOL ACCESS
                          |
         no tools --------|-------- constrained -------- full autonomy
```

### Axis 1: Execution Mode

**How the agent processes requests.**

| Mode | Description | Loop Structure | Use Case |
|------|-------------|----------------|----------|
| **single** | One request → one response | Single inference | Q&A, lookups |
| **multi** | Conversational with history | Session loop | Tutoring, discussions |
| **autonomous** | Self-directed until completion | Agentic loop with tools | Research, coding tasks |

### Axis 2: Memory Depth

**How state persists across interactions.**

| Level | Scope | Persistence | Example |
|-------|-------|-------------|---------|
| **stateless** | None | None | Stateless API |
| **session** | Current conversation | Until session ends | Chat session |
| **persistent** | Cross-session | Database storage | User preferences |
| **learning** | Pattern detection | ML-enhanced | Adaptive tutoring |

### Axis 3: Tool Access

**What external capabilities the agent has.**

| Level | Tools Available | Approval | Risk |
|-------|-----------------|----------|------|
| **none** | No tools | N/A | Lowest |
| **read-only** | Read, Glob, Grep, WebFetch | Auto | Low |
| **constrained** | Read, Write, limited Bash | Per-session | Medium |
| **full** | All tools including dangerous | Per-action | Highest |

---

## Architecture: Configuration-Driven Strategy Pattern

### Core Design

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum

class ExecutionMode(Enum):
    SINGLE = "single"
    MULTI = "multi"
    AUTONOMOUS = "autonomous"

class MemoryDepth(Enum):
    STATELESS = "stateless"
    SESSION = "session"
    PERSISTENT = "persistent"
    LEARNING = "learning"

class ToolAccess(Enum):
    NONE = "none"
    READ_ONLY = "read_only"
    CONSTRAINED = "constrained"
    FULL = "full"

@dataclass
class AgentCapabilities:
    """
    Defines what an agent CAN do.

    This is configuration, not behavior.
    Actual behavior comes from strategy selection.
    """
    execution_modes: List[ExecutionMode] = field(
        default_factory=lambda: [ExecutionMode.SINGLE]
    )
    max_memory_depth: MemoryDepth = MemoryDepth.SESSION
    tool_access: ToolAccess = ToolAccess.READ_ONLY

    # Specific tool restrictions
    allowed_tools: Optional[List[str]] = None
    denied_tools: Optional[List[str]] = None

    # Limits
    max_turns: int = 10
    max_tool_calls: int = 50
    max_tokens_per_turn: int = 4096

    def can_execute(self, mode: ExecutionMode) -> bool:
        """Check if agent supports this execution mode."""
        return mode in self.execution_modes

    def can_use_tool(self, tool_name: str) -> bool:
        """Check if agent can use a specific tool."""
        if self.tool_access == ToolAccess.NONE:
            return False
        if self.denied_tools and tool_name in self.denied_tools:
            return False
        if self.allowed_tools and tool_name not in self.allowed_tools:
            return False
        return True
```

### Strategy Pattern for Execution

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any

class ExecutionStrategy(ABC):
    """
    Abstract strategy for executing agent tasks.

    Different strategies implement different execution patterns:
    - SingleTurnStrategy: One inference
    - MultiTurnStrategy: Conversation loop
    - AutonomousStrategy: Agentic loop with tools
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy identifier."""
        pass

    @abstractmethod
    async def execute(
        self,
        agent: "Agent",
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the task using this strategy."""
        pass

    @abstractmethod
    async def stream(
        self,
        agent: "Agent",
        task: str,
        context: Dict[str, Any]
    ) -> AsyncIterator[str]:
        """Stream execution output."""
        pass


class SingleTurnStrategy(ExecutionStrategy):
    """Single request → single response."""

    @property
    def name(self) -> str:
        return "single"

    async def execute(
        self,
        agent: "Agent",
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Build messages
        messages = self._build_messages(agent, task, context)

        # Single LLM call
        response = await agent.llm_provider.complete(
            messages=messages,
            tools=None,  # No tools in single-turn
            **agent.config.llm_params
        )

        return {
            "output": response["content"],
            "tokens": response.get("usage", {}),
            "cost": self._calculate_cost(response),
            "status": "complete"
        }

    async def stream(
        self,
        agent: "Agent",
        task: str,
        context: Dict[str, Any]
    ) -> AsyncIterator[str]:
        messages = self._build_messages(agent, task, context)

        async for chunk in agent.llm_provider.stream(messages):
            yield chunk


class MultiTurnStrategy(ExecutionStrategy):
    """Conversational with history."""

    @property
    def name(self) -> str:
        return "multi"

    async def execute(
        self,
        agent: "Agent",
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        session_id = context.get("session_id")

        # Load conversation history from memory
        history = await agent.memory.recall(
            session_id=session_id,
            max_messages=agent.capabilities.max_turns * 2
        )

        # Build messages with history
        messages = self._build_messages_with_history(agent, task, history)

        # LLM call
        response = await agent.llm_provider.complete(
            messages=messages,
            **agent.config.llm_params
        )

        # Store in memory
        await agent.memory.store(
            session_id=session_id,
            role="user",
            content=task
        )
        await agent.memory.store(
            session_id=session_id,
            role="assistant",
            content=response["content"]
        )

        return {
            "output": response["content"],
            "tokens": response.get("usage", {}),
            "cost": self._calculate_cost(response),
            "status": "complete",
            "session_id": session_id
        }


class AutonomousStrategy(ExecutionStrategy):
    """Self-directed agentic loop with tools."""

    @property
    def name(self) -> str:
        return "autonomous"

    async def execute(
        self,
        agent: "Agent",
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        max_cycles = context.get("max_cycles", agent.capabilities.max_turns)
        tools = self._get_available_tools(agent)

        messages = self._build_messages(agent, task, context)
        total_cost = 0.0
        tool_calls = []

        for cycle in range(max_cycles):
            # LLM call with tools
            response = await agent.llm_provider.complete(
                messages=messages,
                tools=tools,
                **agent.config.llm_params
            )

            total_cost += self._calculate_cost(response)

            # Check if done (no tool calls)
            if not response.get("tool_calls"):
                return {
                    "output": response["content"],
                    "tool_calls": tool_calls,
                    "cycles": cycle + 1,
                    "cost": total_cost,
                    "status": "complete"
                }

            # Execute tool calls
            for tool_call in response["tool_calls"]:
                # Permission check
                if not await agent.permission_manager.check(
                    tool_call["name"],
                    tool_call["arguments"]
                ):
                    tool_calls.append({
                        **tool_call,
                        "status": "denied"
                    })
                    continue

                # Execute tool
                result = await agent.tool_executor.execute(
                    tool_call["name"],
                    tool_call["arguments"]
                )

                tool_calls.append({
                    **tool_call,
                    "result": result,
                    "status": "executed"
                })

                # Add to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": str(result)
                })

        # Max cycles reached
        return {
            "output": "Maximum cycles reached without completion",
            "tool_calls": tool_calls,
            "cycles": max_cycles,
            "cost": total_cost,
            "status": "max_cycles_reached"
        }

    def _get_available_tools(self, agent: "Agent") -> List[Dict]:
        """Get tools based on agent's tool access level."""
        all_tools = agent.tool_registry.list_tools()

        return [
            tool for tool in all_tools
            if agent.capabilities.can_use_tool(tool["name"])
        ]
```

### Unified Agent Class

```python
class Agent:
    """
    Unified agent with configurable capabilities.

    Supports all execution modes through strategy pattern.
    Memory and tools are composed independently.
    """

    def __init__(
        self,
        model: str = "gpt-4",
        execution_mode: str = "single",
        memory_depth: str = "session",
        tool_access: str = "read_only",
        **kwargs
    ):
        # Build capabilities from parameters
        self.capabilities = AgentCapabilities(
            execution_modes=[ExecutionMode(m) for m in kwargs.get(
                "execution_modes", [execution_mode]
            )],
            max_memory_depth=MemoryDepth(memory_depth),
            tool_access=ToolAccess(tool_access),
            **{k: v for k, v in kwargs.items() if hasattr(AgentCapabilities, k)}
        )

        # Initialize strategies
        self._strategies = {
            ExecutionMode.SINGLE: SingleTurnStrategy(),
            ExecutionMode.MULTI: MultiTurnStrategy(),
            ExecutionMode.AUTONOMOUS: AutonomousStrategy(),
        }
        self._current_mode = ExecutionMode(execution_mode)

        # Initialize components
        self._init_llm_provider(model, kwargs)
        self._init_memory(memory_depth, kwargs)
        self._init_tools(tool_access, kwargs)

    @property
    def strategy(self) -> ExecutionStrategy:
        """Current execution strategy."""
        return self._strategies[self._current_mode]

    def set_mode(self, mode: str) -> "Agent":
        """
        Switch execution mode at runtime.

        Returns self for chaining.
        """
        new_mode = ExecutionMode(mode)
        if not self.capabilities.can_execute(new_mode):
            raise ValueError(f"Agent doesn't support {mode} mode")
        self._current_mode = new_mode
        return self

    async def run(
        self,
        task: str,
        mode: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute task with current or specified mode.

        Args:
            task: The task or prompt
            mode: Override execution mode (optional)
            **kwargs: Additional context

        Returns:
            Execution result dict
        """
        # Temporary mode switch if specified
        original_mode = self._current_mode
        if mode:
            self.set_mode(mode)

        try:
            # Build context
            context = self._build_context(task, kwargs)

            # Add memory context
            if self.memory:
                context["memory"] = await self.memory.build_context(
                    task,
                    max_tokens=kwargs.get("memory_tokens", 4000)
                )

            # Execute via strategy
            result = await self.strategy.execute(self, task, context)

            # Store result in memory
            if self.memory:
                await self._store_result(task, result, context)

            return result

        finally:
            # Restore original mode
            self._current_mode = original_mode
```

---

## Capability Presets

For common use cases, provide capability presets:

```python
class CapabilityPresets:
    """Pre-configured capability combinations."""

    @staticmethod
    def qa_assistant() -> AgentCapabilities:
        """Simple Q&A without tools or memory."""
        return AgentCapabilities(
            execution_modes=[ExecutionMode.SINGLE],
            max_memory_depth=MemoryDepth.STATELESS,
            tool_access=ToolAccess.NONE
        )

    @staticmethod
    def tutor() -> AgentCapabilities:
        """Educational tutor with session memory."""
        return AgentCapabilities(
            execution_modes=[ExecutionMode.SINGLE, ExecutionMode.MULTI],
            max_memory_depth=MemoryDepth.SESSION,
            tool_access=ToolAccess.READ_ONLY,
            max_turns=50
        )

    @staticmethod
    def researcher() -> AgentCapabilities:
        """Research agent with web access."""
        return AgentCapabilities(
            execution_modes=[ExecutionMode.AUTONOMOUS],
            max_memory_depth=MemoryDepth.PERSISTENT,
            tool_access=ToolAccess.READ_ONLY,
            allowed_tools=["web_search", "web_fetch", "read_file"],
            max_turns=20
        )

    @staticmethod
    def developer() -> AgentCapabilities:
        """Full developer agent with all tools."""
        return AgentCapabilities(
            execution_modes=[
                ExecutionMode.SINGLE,
                ExecutionMode.MULTI,
                ExecutionMode.AUTONOMOUS
            ],
            max_memory_depth=MemoryDepth.PERSISTENT,
            tool_access=ToolAccess.FULL,
            max_turns=100,
            max_tool_calls=500
        )

    @staticmethod
    def ifm_assistant() -> AgentCapabilities:
        """FNCE210 IFM learning assistant."""
        return AgentCapabilities(
            execution_modes=[ExecutionMode.SINGLE, ExecutionMode.MULTI],
            max_memory_depth=MemoryDepth.SESSION,
            tool_access=ToolAccess.READ_ONLY,
            allowed_tools=[
                "read_file",      # Read knowledge base
                "search_content", # Search formulas
                "list_directory", # Browse chapters
                "calculate_irp",  # IRP calculator
                "calculate_ppp",  # PPP calculator
            ],
            max_turns=30
        )
```

---

## Usage Examples

### Basic Usage

```python
# Simple Q&A
agent = Agent(model="gpt-4")  # Defaults to single-turn
answer = await agent.run("What is covered interest parity?")

# Conversational tutor
agent = Agent(
    model="gpt-4",
    execution_mode="multi",
    memory_depth="session"
)
await agent.run("Let's learn about FX hedging", session_id="user123")
await agent.run("What are the main strategies?", session_id="user123")
await agent.run("Compare forward vs options", session_id="user123")

# Autonomous researcher
agent = Agent(
    model="gpt-4",
    execution_mode="autonomous",
    tool_access="read_only",
    max_cycles=20
)
report = await agent.run("Research currency hedging strategies and summarize")
```

### Runtime Mode Switching

```python
# Same agent, different modes
agent = Agent(
    model="gpt-4",
    execution_modes=["single", "multi", "autonomous"]
)

# Quick lookup
answer = await agent.run("Define IRP", mode="single")

# Deep discussion
await agent.set_mode("multi")
await agent.run("Explain IRP step by step", session_id="sess1")
await agent.run("Now give me an example", session_id="sess1")

# Autonomous task
result = await agent.run(
    "Create a comparison table of parity conditions",
    mode="autonomous",
    max_cycles=10
)
```

### Using Presets

```python
# Use preset capabilities
from kaizen.agent import Agent, CapabilityPresets

# IFM tutor with appropriate capabilities
agent = Agent(
    model="gpt-4",
    capabilities=CapabilityPresets.ifm_assistant()
)

# Developer agent with full access
dev_agent = Agent(
    model="gpt-4",
    capabilities=CapabilityPresets.developer()
)
```

---

## Implementation Notes

### Memory Integration

Memory is a cross-cutting concern that applies to all execution modes:

```python
# Memory is configured independently of execution mode
agent = Agent(
    model="gpt-4",
    execution_mode="single",      # Single-turn...
    memory_depth="persistent"     # ...but with persistent memory
)

# Even single-turn can recall past interactions
result = await agent.run(
    "What did I ask about yesterday?",
    session_id="user123"
)
```

### Tool Access Enforcement

Tool access is enforced at the strategy level:

```python
# Constrained tool access
agent = Agent(
    model="gpt-4",
    execution_mode="autonomous",
    tool_access="constrained",
    allowed_tools=["read_file", "search_content"]
)

# Agent can use autonomous loop but only with allowed tools
result = await agent.run("Find all mentions of IRP in the knowledge base")
```

### Progressive Capability Enhancement

Agents can "grow" capabilities without structural changes:

```python
# Start simple
agent = Agent(model="gpt-4")

# Add memory
agent.capabilities.max_memory_depth = MemoryDepth.PERSISTENT
agent._init_memory("persistent", {})

# Add tools
agent.capabilities.tool_access = ToolAccess.READ_ONLY
agent._init_tools("read_only", {})

# Enable autonomous mode
agent.capabilities.execution_modes.append(ExecutionMode.AUTONOMOUS)
```

---

## Summary

The Configuration-Driven Strategy Pattern provides:

1. **Flexibility**: Any combination of execution mode, memory, and tools
2. **Runtime Switching**: Change modes without creating new objects
3. **Clean Separation**: Each axis is independent
4. **Progressive Enhancement**: Start simple, add capabilities as needed
5. **Developer-Friendly**: Intuitive API with sensible defaults

**Key Insight**: Agent capabilities are configuration, not class identity. The same agent can operate in different modes based on the task at hand.

---

**Next Document**: [03-runtime-abstraction-layer.md](./03-runtime-abstraction-layer.md) - How to abstract over multiple autonomous agent runtimes.
