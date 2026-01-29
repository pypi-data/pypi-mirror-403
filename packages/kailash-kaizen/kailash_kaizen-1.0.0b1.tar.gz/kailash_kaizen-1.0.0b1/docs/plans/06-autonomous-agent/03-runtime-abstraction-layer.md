# Runtime Abstraction Layer (RAL)

**Document Status:** Architecture Specification for Kaizen Development Team
**Version:** 1.0.0
**Date:** 2026-01-21

---

## Executive Summary

Claude Code is just ONE autonomous agent runtime. The market has multiple:

| Runtime | Provider | Key Strength |
|---------|----------|--------------|
| **Claude Code** | Anthropic | Native file/bash tools, MCP integration |
| **OpenAI Codex** | OpenAI | Code Interpreter, Assistant API threads |
| **Gemini CLI** | Google | Google ecosystem integration |
| **Cursor Agent** | Cursor | IDE integration |
| **GitHub Copilot Workspace** | GitHub | Repository context |
| **Custom (LangGraph, AutoGen, CrewAI)** | Various | Full customization |

The Runtime Abstraction Layer (RAL) provides a unified interface to work with any of these runtimes while maintaining Kaizen's enterprise features.

---

## The Need for Abstraction

### Problem: Runtime Lock-In

Without abstraction, code becomes tightly coupled to a specific runtime:

```python
# ❌ BAD: Tightly coupled to Claude Code
from claude_agent_sdk import ClaudeSDKClient

async def execute_task(task: str):
    async with ClaudeSDKClient(options=claude_options) as client:
        await client.query(task)
        async for msg in client.receive_response():
            # Claude-specific message handling
            ...
```

This creates problems:
- Can't switch runtimes without rewriting code
- Can't use different runtimes for different tasks
- Can't A/B test runtime performance
- Vendor lock-in

### Solution: Runtime Adapter Pattern

```python
# ✅ GOOD: Abstracted via adapter
from kaizen.runtime import get_runtime

async def execute_task(task: str, runtime: str = "auto"):
    adapter = get_runtime(runtime)  # Returns appropriate adapter
    result = await adapter.execute(ExecutionContext(task=task, ...))
    return result  # Normalized result regardless of runtime
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Unified Agent API                            │
│  agent.run(task, runtime="claude_code")                             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       RuntimeSelector                                │
│  - Capability negotiation                                           │
│  - Cost/latency optimization                                        │
│  - Automatic fallback                                               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  ClaudeCode     │  │   OpenAICodex   │  │  LocalKaizen    │
│    Adapter      │  │     Adapter     │  │    Adapter      │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ • Claude SDK    │  │ • Assistant API │  │ • Any LLM       │
│ • Native tools  │  │ • Code Interp.  │  │ • Kaizen tools  │
│ • MCP support   │  │ • File search   │  │ • Full control  │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Normalized ExecutionResult                       │
│  { output, tool_calls, tokens, cost, status, metadata }             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Interfaces

### RuntimeCapabilities

Describes what a runtime can do:

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class RuntimeCapabilities:
    """
    Capabilities supported by a runtime.

    Used for:
    1. Runtime selection (can this runtime handle the task?)
    2. Capability negotiation (what features are available?)
    3. Tool mapping (which tools need translation?)
    """

    # Identity
    runtime_name: str
    provider: str
    version: str

    # Core capabilities
    supports_streaming: bool = True
    supports_tool_calling: bool = True
    supports_parallel_tools: bool = False
    supports_vision: bool = False
    supports_audio: bool = False
    supports_code_execution: bool = False
    supports_file_access: bool = False
    supports_web_access: bool = False
    supports_interrupt: bool = True

    # Context limits
    max_context_tokens: int = 128000
    max_output_tokens: int = 8192

    # Native tools (handled by runtime, don't need mapping)
    native_tools: List[str] = field(default_factory=list)

    # Cost (approximate)
    cost_per_1k_input_tokens: float = 0.01
    cost_per_1k_output_tokens: float = 0.03

    # Latency characteristics
    typical_latency_ms: int = 1000
    cold_start_ms: int = 0

    def supports(self, requirement: str) -> bool:
        """Check if a specific capability is supported."""
        mapping = {
            "streaming": self.supports_streaming,
            "tools": self.supports_tool_calling,
            "parallel_tools": self.supports_parallel_tools,
            "vision": self.supports_vision,
            "audio": self.supports_audio,
            "code_execution": self.supports_code_execution,
            "file_access": self.supports_file_access,
            "web_access": self.supports_web_access,
            "interrupt": self.supports_interrupt,
        }
        return mapping.get(requirement, False)

    def meets_requirements(self, requirements: List[str]) -> bool:
        """Check if all requirements are met."""
        return all(self.supports(req) for req in requirements)
```

### ExecutionContext

Input to runtime execution:

```python
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class ExecutionContext:
    """
    Context for runtime execution.

    Contains everything the runtime needs to execute a task.
    This is the universal input format - adapters translate to
    runtime-specific formats.
    """

    # Task
    task: str
    session_id: str

    # Tools (Kaizen format - adapters translate)
    tools: List[Dict[str, Any]] = field(default_factory=list)

    # Memory/context
    memory_context: str = ""
    system_prompt: str = ""
    conversation_history: List[Dict[str, str]] = field(default_factory=list)

    # Constraints
    constraints: Dict[str, Any] = field(default_factory=lambda: {
        "max_cycles": 10,
        "max_tokens": 4096,
        "budget_usd": 1.0,
        "timeout_seconds": 300,
    })

    # Permissions
    permission_mode: str = "prompt"  # "auto", "prompt", "deny"
    pre_approved_tools: List[str] = field(default_factory=list)

    # Routing hints
    preferred_model: Optional[str] = None
    preferred_runtime: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### ExecutionResult

Normalized output from any runtime:

```python
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum

class ExecutionStatus(Enum):
    COMPLETE = "complete"
    INTERRUPTED = "interrupted"
    ERROR = "error"
    MAX_CYCLES = "max_cycles"
    BUDGET_EXCEEDED = "budget_exceeded"
    TIMEOUT = "timeout"

@dataclass
class ToolCallRecord:
    """Record of a tool call during execution."""
    name: str
    arguments: Dict[str, Any]
    result: Any
    status: str  # "executed", "denied", "error"
    duration_ms: int
    error: Optional[str] = None

@dataclass
class ExecutionResult:
    """
    Normalized result from any runtime.

    All adapters MUST return this format, regardless of
    the underlying runtime's native format.
    """

    # Core output
    output: str
    status: ExecutionStatus

    # Tool execution details
    tool_calls: List[ToolCallRecord] = field(default_factory=list)

    # Resource usage
    tokens_used: Dict[str, int] = field(default_factory=lambda: {
        "input": 0,
        "output": 0,
        "total": 0
    })
    cost_usd: float = 0.0
    cycles_used: int = 0
    duration_ms: int = 0

    # Runtime info
    runtime_name: str = ""
    model_used: str = ""
    session_id: str = ""

    # Error details (if status is ERROR)
    error_message: Optional[str] = None
    error_type: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### RuntimeAdapter Interface

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Callable

class RuntimeAdapter(ABC):
    """
    Abstract adapter for autonomous agent runtimes.

    Implementations:
    - ClaudeCodeAdapter: Claude Code SDK
    - OpenAICodexAdapter: OpenAI Assistant API
    - GeminiAdapter: Gemini CLI / Vertex AI
    - LocalKaizenAdapter: Kaizen native runtime
    """

    @property
    @abstractmethod
    def capabilities(self) -> RuntimeCapabilities:
        """Return runtime capabilities."""
        pass

    @abstractmethod
    async def execute(
        self,
        context: ExecutionContext,
        on_progress: Optional[Callable[[str], None]] = None
    ) -> ExecutionResult:
        """
        Execute task in this runtime.

        Args:
            context: Execution context with task, tools, constraints
            on_progress: Optional callback for progress updates

        Returns:
            Normalized execution result
        """
        pass

    @abstractmethod
    async def stream(
        self,
        context: ExecutionContext
    ) -> AsyncIterator[str]:
        """
        Stream execution output token by token.

        Yields:
            String chunks as they're generated
        """
        pass

    @abstractmethod
    async def interrupt(
        self,
        session_id: str,
        mode: str = "graceful"
    ) -> bool:
        """
        Interrupt ongoing execution.

        Args:
            session_id: Session to interrupt
            mode: "graceful" (finish current step) or "immediate"

        Returns:
            True if successfully interrupted
        """
        pass

    @abstractmethod
    def map_tools(
        self,
        kaizen_tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Map Kaizen tool definitions to runtime-specific format.

        This is CRITICAL for interoperability - each runtime has
        different tool calling conventions.

        Args:
            kaizen_tools: Tools in Kaizen format

        Returns:
            Tools in runtime-specific format
        """
        pass

    @abstractmethod
    def normalize_result(
        self,
        raw_result: Any
    ) -> ExecutionResult:
        """
        Normalize runtime-specific result to common format.

        Args:
            raw_result: Runtime's native result format

        Returns:
            Normalized ExecutionResult
        """
        pass
```

---

## Adapter Implementations

### ClaudeCodeAdapter

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

class ClaudeCodeAdapter(RuntimeAdapter):
    """
    Adapter for Claude Code SDK.

    Claude Code is special because:
    1. It IS Claude (model is built-in)
    2. Has native file/bash/browser tools
    3. Uses MCP for tool discovery
    4. Supports multi-turn naturally
    """

    def __init__(self, config: Dict[str, Any]):
        self._config = config
        self._capabilities = RuntimeCapabilities(
            runtime_name="claude_code",
            provider="anthropic",
            version="1.0",
            supports_streaming=True,
            supports_tool_calling=True,
            supports_parallel_tools=True,
            supports_vision=True,
            supports_code_execution=True,
            supports_file_access=True,
            supports_web_access=True,
            supports_interrupt=True,
            max_context_tokens=200000,
            max_output_tokens=8192,
            native_tools=[
                "Read", "Write", "Edit", "Bash", "Glob", "Grep",
                "WebFetch", "WebSearch", "Task", "Skill"
            ],
            cost_per_1k_input_tokens=0.003,
            cost_per_1k_output_tokens=0.015,
        )

    @property
    def capabilities(self) -> RuntimeCapabilities:
        return self._capabilities

    async def execute(
        self,
        context: ExecutionContext,
        on_progress: Optional[Callable] = None
    ) -> ExecutionResult:
        # Build Claude options
        options = self._build_options(context)

        # Map tools (filter out native tools)
        custom_tools = self.map_tools(context.tools)

        output_parts = []
        tool_calls = []
        start_time = time.time()

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(context.task)

                async for msg in client.receive_response():
                    if isinstance(msg, AssistantMessage):
                        for block in msg.content:
                            if isinstance(block, TextBlock):
                                output_parts.append(block.text)
                                if on_progress:
                                    on_progress(block.text)
                            elif isinstance(block, ToolUseBlock):
                                tool_calls.append(ToolCallRecord(
                                    name=block.name,
                                    arguments=block.input,
                                    result=None,  # Filled by result
                                    status="executed",
                                    duration_ms=0
                                ))

                    elif isinstance(msg, ResultMessage):
                        # Final result
                        return ExecutionResult(
                            output="\n".join(output_parts),
                            status=ExecutionStatus.COMPLETE,
                            tool_calls=tool_calls,
                            tokens_used={
                                "input": msg.usage.input_tokens if msg.usage else 0,
                                "output": msg.usage.output_tokens if msg.usage else 0,
                                "total": (msg.usage.input_tokens + msg.usage.output_tokens) if msg.usage else 0
                            },
                            cost_usd=msg.cost.total_cost if msg.cost else 0.0,
                            runtime_name="claude_code",
                            model_used=msg.model if hasattr(msg, 'model') else "claude",
                            session_id=context.session_id,
                            duration_ms=int((time.time() - start_time) * 1000)
                        )

        except Exception as e:
            return ExecutionResult(
                output="",
                status=ExecutionStatus.ERROR,
                error_message=str(e),
                error_type=type(e).__name__,
                runtime_name="claude_code",
                session_id=context.session_id,
                duration_ms=int((time.time() - start_time) * 1000)
            )

    def map_tools(self, kaizen_tools: List[Dict]) -> List[Dict]:
        """Map Kaizen tools to Claude Code MCP format."""
        # Filter out native tools
        custom_tools = [
            t for t in kaizen_tools
            if t["name"] not in self._capabilities.native_tools
        ]

        # Convert to MCP format
        return [self._to_mcp_tool(t) for t in custom_tools]

    def _to_mcp_tool(self, tool: Dict) -> Dict:
        """Convert Kaizen tool to MCP format."""
        return {
            "name": f"mcp__kaizen__{tool['name']}",
            "description": tool.get("description", ""),
            "inputSchema": tool.get("parameters", {})
        }

    def _build_options(self, context: ExecutionContext) -> ClaudeAgentOptions:
        """Build ClaudeAgentOptions from context."""
        return ClaudeAgentOptions(
            system_prompt=context.system_prompt,
            max_turns=context.constraints.get("max_cycles", 10),
            max_budget_usd=context.constraints.get("budget_usd", 1.0),
            permission_mode=self._map_permission_mode(context.permission_mode),
            cwd=context.metadata.get("cwd", "."),
        )
```

### LocalKaizenAdapter

```python
class LocalKaizenAdapter(RuntimeAdapter):
    """
    Adapter for Kaizen's native runtime.

    This is the fallback and provides:
    1. Full control over execution
    2. Works with any LLM
    3. Uses Kaizen's tool system
    4. Integrates with Kaizen memory/observability
    """

    def __init__(self, config: Dict[str, Any]):
        self._config = config
        self._llm_provider = self._create_llm_provider(config)
        self._tool_executor = self._create_tool_executor(config)

        self._capabilities = RuntimeCapabilities(
            runtime_name="kaizen_local",
            provider="kaizen",
            version="1.0",
            supports_streaming=True,
            supports_tool_calling=True,
            supports_parallel_tools=False,
            supports_vision=True,  # Depends on LLM
            supports_code_execution=True,
            supports_file_access=True,
            supports_web_access=True,
            supports_interrupt=True,
            max_context_tokens=128000,  # Depends on LLM
            max_output_tokens=8192,
            native_tools=[],  # All tools are Kaizen tools
        )

    @property
    def capabilities(self) -> RuntimeCapabilities:
        return self._capabilities

    async def execute(
        self,
        context: ExecutionContext,
        on_progress: Optional[Callable] = None
    ) -> ExecutionResult:
        """Execute using Kaizen's native agentic loop."""
        max_cycles = context.constraints.get("max_cycles", 10)
        budget_usd = context.constraints.get("budget_usd", 1.0)

        messages = self._build_initial_messages(context)
        tools = self.map_tools(context.tools)
        tool_calls = []
        total_cost = 0.0
        start_time = time.time()

        for cycle in range(max_cycles):
            # Check budget
            if total_cost >= budget_usd:
                return ExecutionResult(
                    output="Budget exceeded",
                    status=ExecutionStatus.BUDGET_EXCEEDED,
                    tool_calls=tool_calls,
                    cost_usd=total_cost,
                    cycles_used=cycle,
                    runtime_name="kaizen_local",
                    session_id=context.session_id,
                    duration_ms=int((time.time() - start_time) * 1000)
                )

            # LLM call
            response = await self._llm_provider.complete(
                messages=messages,
                tools=tools if tools else None,
                **self._config.get("llm_params", {})
            )

            total_cost += self._calculate_cost(response)

            # Check if done (no tool calls)
            if not response.get("tool_calls"):
                return ExecutionResult(
                    output=response["content"],
                    status=ExecutionStatus.COMPLETE,
                    tool_calls=tool_calls,
                    tokens_used=response.get("usage", {}),
                    cost_usd=total_cost,
                    cycles_used=cycle + 1,
                    runtime_name="kaizen_local",
                    model_used=self._config.get("model", "unknown"),
                    session_id=context.session_id,
                    duration_ms=int((time.time() - start_time) * 1000)
                )

            # Execute tool calls
            for tc in response["tool_calls"]:
                tool_start = time.time()
                try:
                    result = await self._tool_executor.execute(
                        tc["name"],
                        tc["arguments"]
                    )
                    tool_calls.append(ToolCallRecord(
                        name=tc["name"],
                        arguments=tc["arguments"],
                        result=result,
                        status="executed",
                        duration_ms=int((time.time() - tool_start) * 1000)
                    ))
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": str(result)
                    })
                except Exception as e:
                    tool_calls.append(ToolCallRecord(
                        name=tc["name"],
                        arguments=tc["arguments"],
                        result=None,
                        status="error",
                        duration_ms=int((time.time() - tool_start) * 1000),
                        error=str(e)
                    ))

            if on_progress:
                on_progress(f"Cycle {cycle + 1}/{max_cycles} complete")

        # Max cycles reached
        return ExecutionResult(
            output="Maximum cycles reached",
            status=ExecutionStatus.MAX_CYCLES,
            tool_calls=tool_calls,
            cost_usd=total_cost,
            cycles_used=max_cycles,
            runtime_name="kaizen_local",
            session_id=context.session_id,
            duration_ms=int((time.time() - start_time) * 1000)
        )

    def map_tools(self, kaizen_tools: List[Dict]) -> List[Dict]:
        """Tools are already in Kaizen format."""
        return kaizen_tools  # No mapping needed
```

---

## Runtime Selection

### RuntimeSelector

Intelligently selects the best runtime for a task:

```python
class RuntimeSelector:
    """
    Intelligent runtime selection based on task requirements.

    Decision factors:
    1. Required capabilities (vision, code execution, etc.)
    2. Cost constraints
    3. Latency requirements
    4. Tool availability
    5. User preference
    """

    def __init__(self, runtimes: Dict[str, RuntimeAdapter]):
        self.runtimes = runtimes

    def select(
        self,
        context: ExecutionContext,
        strategy: str = "capability_match"
    ) -> RuntimeAdapter:
        """
        Select best runtime for the context.

        Strategies:
        - capability_match: Match required capabilities
        - cost_optimized: Minimize cost
        - latency_optimized: Minimize latency
        - preferred: Use preferred runtime if capable
        """
        # Check for explicit preference
        if context.preferred_runtime:
            if context.preferred_runtime in self.runtimes:
                runtime = self.runtimes[context.preferred_runtime]
                if self._meets_requirements(runtime, context):
                    return runtime

        # Analyze requirements
        requirements = self._analyze_requirements(context)

        # Filter capable runtimes
        capable = [
            (name, rt) for name, rt in self.runtimes.items()
            if rt.capabilities.meets_requirements(requirements)
        ]

        if not capable:
            # Fallback to local Kaizen
            return self.runtimes.get("kaizen_local")

        # Apply selection strategy
        if strategy == "cost_optimized":
            return min(capable, key=lambda x: x[1].capabilities.cost_per_1k_input_tokens)[1]
        elif strategy == "latency_optimized":
            return min(capable, key=lambda x: x[1].capabilities.typical_latency_ms)[1]
        else:  # capability_match (default)
            return capable[0][1]

    def _analyze_requirements(self, context: ExecutionContext) -> List[str]:
        """Analyze context to determine required capabilities."""
        requirements = []

        # Check tools for capability hints
        for tool in context.tools:
            tool_name = tool.get("name", "").lower()
            if "file" in tool_name or "read" in tool_name or "write" in tool_name:
                requirements.append("file_access")
            if "web" in tool_name or "fetch" in tool_name:
                requirements.append("web_access")
            if "code" in tool_name or "execute" in tool_name:
                requirements.append("code_execution")

        # Check task for hints
        task_lower = context.task.lower()
        if "image" in task_lower or "picture" in task_lower or "screenshot" in task_lower:
            requirements.append("vision")
        if "code" in task_lower or "implement" in task_lower or "build" in task_lower:
            requirements.append("code_execution")

        return list(set(requirements))
```

---

## Usage Examples

### Basic Usage

```python
from kaizen.runtime import get_runtime, ExecutionContext

# Auto-select runtime
runtime = get_runtime("auto")
result = await runtime.execute(ExecutionContext(
    task="What is covered interest parity?",
    session_id="sess123"
))

# Specify runtime
claude_runtime = get_runtime("claude_code")
result = await claude_runtime.execute(ExecutionContext(
    task="Create a Python script for FX calculations",
    session_id="sess123",
    tools=[...]
))

# Stream output
async for chunk in runtime.stream(context):
    print(chunk, end="")
```

### With Agent Integration

```python
from kaizen.agent import Agent

# Agent with specific runtime
agent = Agent(
    model="gpt-4",
    execution_mode="autonomous",
    runtime="claude_code"  # Use Claude Code
)

result = await agent.run("Build a hedging calculator")

# Agent with auto-selected runtime
agent = Agent(
    model="gpt-4",
    execution_mode="autonomous",
    runtime="auto",  # Auto-select based on task
    required_capabilities=["code_execution", "file_access"]
)
```

---

## Implementation Notes

### Tool Mapping

Each runtime has different tool calling conventions. The adapter MUST translate:

| Runtime | Tool Format |
|---------|-------------|
| **Claude Code** | MCP format with `mcp__server__tool` naming |
| **OpenAI** | Function calling with `parameters` schema |
| **Gemini** | Function declarations |
| **Kaizen** | Direct tool definitions |

### Error Handling

Adapters must normalize errors:

```python
try:
    result = await runtime.execute(context)
except RuntimeError as e:
    result = ExecutionResult(
        output="",
        status=ExecutionStatus.ERROR,
        error_message=str(e),
        error_type="RuntimeError"
    )
```

### Capability Negotiation

Before execution, check capabilities:

```python
if not runtime.capabilities.supports("code_execution"):
    # Either switch runtime or disable code execution tools
    context.tools = [t for t in context.tools if not is_code_tool(t)]
```

---

## Summary

The Runtime Abstraction Layer provides:

1. **Unified Interface**: Same code works with any runtime
2. **Intelligent Selection**: Auto-select best runtime for task
3. **Normalized Results**: Consistent output format
4. **Tool Interoperability**: Automatic tool mapping
5. **Graceful Fallback**: Always have local Kaizen as backup

**Key Insight**: Treat runtimes as interchangeable execution backends, not as fundamentally different systems. The abstraction layer handles the differences.

---

**Next Document**: [04-multi-llm-routing.md](./04-multi-llm-routing.md) - How to route tasks to different LLMs even within a single runtime.
