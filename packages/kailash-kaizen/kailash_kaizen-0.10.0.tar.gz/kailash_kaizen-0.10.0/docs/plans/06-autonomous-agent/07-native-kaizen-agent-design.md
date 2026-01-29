# Native Kaizen Autonomous Agent Design

**Document Status:** Architecture Specification for Kaizen Development Team
**Version:** 1.0.0
**Date:** 2026-01-21

---

## Executive Summary

This document provides comprehensive architectural analysis and design specifications for building a **Kaizen-native autonomous agent** that provides Claude Code-like capabilities while working with **ANY LLM provider**. This is the key differentiator from wrapper-based approaches.

### The Core Insight

Claude Code SDK is tied to Claude models (sonnet/opus/haiku). When you use `ClaudeCodeAdapter`, you're locked to Anthropic's models. The native Kaizen autonomous agent provides:

1. **Multi-LLM flexibility** - Use OpenAI, Anthropic, Ollama, or any provider
2. **Custom tool sets** - Our own file/bash/search tools, not dependent on Claude Code
3. **Fine-grained control** - Full observability, checkpointing, memory integration
4. **Learning memory** - Persistent learning from interactions
5. **Custom planning strategies** - PEV, Tree-of-Thoughts, ReAct variations

---

## Part 1: What Makes Claude Code Autonomous?

### 1.1 Claude Code's Execution Model

From analyzing Claude Code's behavior and the Claude Agent SDK, the autonomous execution model consists of:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Claude Code Agentic Loop                          │
│                                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │  THINK   │───>│   ACT    │───>│ OBSERVE  │───>│  DECIDE  │──┐   │
│  │          │    │          │    │          │    │          │  │   │
│  │ Reason   │    │ Execute  │    │ Process  │    │ Continue │  │   │
│  │ about    │    │ tool     │    │ results  │    │ or stop? │  │   │
│  │ task     │    │ calls    │    │          │    │          │  │   │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │   │
│       ^                                               │         │   │
│       └───────────────────────────────────────────────┘         │   │
│                       (loop until done)                         │   │
└─────────────────────────────────────────────────────────────────┴───┘
```

### 1.2 Key Components

| Component | Claude Code Implementation | Kaizen Native Equivalent |
|-----------|---------------------------|--------------------------|
| **LLM Inference** | Claude models only | Any LLM via provider abstraction |
| **File Tools** | `Read`, `Write`, `Edit`, `Glob`, `Grep` | `KaizenFileTools` (12 operations) |
| **Bash Tools** | Native `Bash` tool | `KaizenBashTools` (sandboxed) |
| **Search Tools** | `WebFetch`, `WebSearch` | `KaizenSearchTools` (customizable) |
| **Task Management** | `Task`, `TodoWrite` | `KaizenTaskTools` (with persistence) |
| **MCP Integration** | Native MCP support | Kailash SDK MCP module |
| **Checkpointing** | Conversation state | Full state (memory, plan, budget) |
| **Multi-turn** | Implicit via conversation | Explicit via StateManager |

### 1.3 Claude Code's Decision Process

The "DECIDE" phase in Claude Code determines:

1. **Goal Achieved?** - Has the task been completed?
2. **More Actions Needed?** - Are there pending steps?
3. **Errors to Handle?** - Did any tool call fail?
4. **Budget Exceeded?** - Is the token/cost limit reached?
5. **Max Cycles?** - Has the iteration limit been hit?

---

## Part 2: How Kaizen Can Replicate This Natively

### 2.1 LocalKaizenAdapter Architecture

```python
"""
LocalKaizenAdapter - Native autonomous agent runtime.

Provides Claude Code-like capabilities with ANY LLM provider:
- Think-Act-Observe-Decide loop
- Native file/bash/search tools
- Full checkpointing and resume
- Multi-LLM routing support
- Learning memory integration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, AsyncIterator
from enum import Enum
import asyncio

from kaizen.core.base_agent import BaseAgent
from kaizen.core.autonomy.state.manager import StateManager
from kaizen.core.autonomy.hooks import HookManager, HookEvent
from kaizen.memory import LongTermMemory, SemanticMemory

class AutonomousPhase(Enum):
    """Phases of autonomous execution."""
    THINK = "think"      # Reasoning about next action
    ACT = "act"          # Executing tool calls
    OBSERVE = "observe"  # Processing results
    DECIDE = "decide"    # Determining next step

@dataclass
class AutonomousConfig:
    """Configuration for autonomous execution."""
    # LLM settings
    llm_provider: str = "openai"
    model: str = "gpt-4"
    temperature: float = 0.7

    # Execution limits
    max_cycles: int = 50
    budget_limit_usd: float = 5.0
    timeout_seconds: float = 300.0

    # Checkpointing
    checkpoint_frequency: int = 5
    checkpoint_on_interrupt: bool = True
    resume_from_checkpoint: bool = True

    # Memory
    enable_learning: bool = True
    memory_backend: str = "sqlite"

    # Planning
    planning_strategy: str = "react"  # "react", "pev", "tree_of_thoughts"

    # Tool settings
    tools: str = "all"  # "all", "safe_only", List[str]
    require_approval: bool = False
    auto_approve_safe: bool = True

@dataclass
class ExecutionState:
    """Complete state of autonomous execution."""
    # Core state
    task: str
    session_id: str
    current_cycle: int = 0
    phase: AutonomousPhase = AutonomousPhase.THINK

    # Conversation
    messages: List[Dict[str, Any]] = field(default_factory=list)

    # Plan (if using planning strategy)
    plan: Optional[List[str]] = None
    plan_index: int = 0

    # Tool execution
    pending_tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)

    # Memory
    working_memory: Dict[str, Any] = field(default_factory=dict)
    learned_patterns: List[Dict[str, Any]] = field(default_factory=list)

    # Budget tracking
    tokens_used: int = 0
    cost_usd: float = 0.0

    # Status
    status: str = "running"  # "running", "completed", "interrupted", "error"
    result: Optional[str] = None
    error: Optional[str] = None

class LocalKaizenAdapter:
    """
    Native autonomous agent adapter for Kaizen.

    Key differentiators from ClaudeCodeAdapter:
    1. Works with ANY LLM provider (OpenAI, Anthropic, Ollama, etc.)
    2. Custom tool implementations (not dependent on Claude Code)
    3. Full state management with learning memory
    4. Multiple planning strategies
    5. Fine-grained observability and control
    """

    def __init__(
        self,
        config: AutonomousConfig,
        state_manager: Optional[StateManager] = None,
        hook_manager: Optional[HookManager] = None,
        memory: Optional[LongTermMemory] = None,
    ):
        self.config = config
        self.state_manager = state_manager or self._create_default_state_manager()
        self.hook_manager = hook_manager or self._create_default_hook_manager()
        self.memory = memory

        # Initialize tool registry
        self._tools = self._create_tool_registry()

        # Initialize LLM provider
        self._llm = self._create_llm_provider()

        # Planning strategy
        self._planner = self._create_planner()

        # Current execution state
        self._state: Optional[ExecutionState] = None

        # Interrupt flag
        self._interrupted = False

    async def execute(
        self,
        task: str,
        session_id: str,
        on_progress: Optional[Callable[[str, float], None]] = None,
        resume_checkpoint_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute autonomous task with think-act-observe-decide loop.

        Args:
            task: The task to accomplish
            session_id: Unique session identifier
            on_progress: Optional progress callback (message, percentage)
            resume_checkpoint_id: Resume from specific checkpoint

        Returns:
            Execution result with output, tool_calls, cost, etc.
        """
        # Initialize or restore state
        if resume_checkpoint_id and self.config.resume_from_checkpoint:
            self._state = await self._restore_checkpoint(resume_checkpoint_id)
        else:
            self._state = ExecutionState(task=task, session_id=session_id)

        # Fire PRE_EXECUTION hook
        await self._fire_hook(HookEvent.PRE_EXECUTION, {
            "task": task,
            "session_id": session_id,
            "config": self.config,
        })

        try:
            # Main autonomous loop
            while not self._should_stop():
                self._state.current_cycle += 1

                # Report progress
                if on_progress:
                    progress = min(self._state.current_cycle / self.config.max_cycles, 0.99)
                    on_progress(f"Cycle {self._state.current_cycle}", progress * 100)

                # THINK phase
                await self._think_phase()
                if self._should_stop():
                    break

                # ACT phase
                await self._act_phase()
                if self._should_stop():
                    break

                # OBSERVE phase
                await self._observe_phase()
                if self._should_stop():
                    break

                # DECIDE phase
                should_continue = await self._decide_phase()
                if not should_continue:
                    break

                # Checkpoint if needed
                if self._state.current_cycle % self.config.checkpoint_frequency == 0:
                    await self._save_checkpoint()

            # Mark completion
            if self._state.status == "running":
                self._state.status = "completed"

            # Fire POST_EXECUTION hook
            await self._fire_hook(HookEvent.POST_EXECUTION, {
                "state": self._state,
                "result": self._state.result,
            })

            # Learn from execution (if enabled)
            if self.config.enable_learning and self.memory:
                await self._learn_from_execution()

            return self._build_result()

        except Exception as e:
            self._state.status = "error"
            self._state.error = str(e)

            # Checkpoint on error
            if self.config.checkpoint_on_interrupt:
                await self._save_checkpoint()

            raise

    # ========================================
    # AUTONOMOUS LOOP PHASES
    # ========================================

    async def _think_phase(self):
        """
        THINK: Reason about the task and determine next action.

        Uses the configured planning strategy:
        - react: Simple reasoning about next step
        - pev: Plan-Execute-Verify loop
        - tree_of_thoughts: Multi-path exploration
        """
        self._state.phase = AutonomousPhase.THINK

        await self._fire_hook(HookEvent.PRE_THINK, {
            "cycle": self._state.current_cycle,
            "messages": self._state.messages,
        })

        # Build context for LLM
        context = self._build_thinking_context()

        # Get LLM response with tool selection
        response = await self._llm.complete(
            messages=context,
            tools=self._tools.get_tool_schemas(),
            temperature=self.config.temperature,
        )

        # Update state
        self._state.tokens_used += response.get("usage", {}).get("total_tokens", 0)
        self._state.cost_usd += self._calculate_cost(response)

        # Extract tool calls (if any)
        if response.get("tool_calls"):
            self._state.pending_tool_calls = response["tool_calls"]
            self._state.messages.append({
                "role": "assistant",
                "content": response.get("content", ""),
                "tool_calls": response["tool_calls"],
            })
        else:
            # No tool calls - this is the final response
            self._state.result = response.get("content", "")
            self._state.messages.append({
                "role": "assistant",
                "content": self._state.result,
            })

        await self._fire_hook(HookEvent.POST_THINK, {
            "response": response,
            "tool_calls": self._state.pending_tool_calls,
        })

    async def _act_phase(self):
        """
        ACT: Execute pending tool calls.

        Handles:
        - Tool execution with approval workflow
        - Error handling and retries
        - Result collection
        """
        self._state.phase = AutonomousPhase.ACT

        if not self._state.pending_tool_calls:
            return

        await self._fire_hook(HookEvent.PRE_ACT, {
            "tool_calls": self._state.pending_tool_calls,
        })

        self._state.tool_results = []

        for tool_call in self._state.pending_tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call.get("arguments", {})

            # Check approval
            if self.config.require_approval:
                approved = await self._request_approval(tool_name, tool_args)
                if not approved:
                    self._state.tool_results.append({
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
                        "result": "Tool execution denied by user",
                        "status": "denied",
                    })
                    continue

            # Execute tool
            try:
                result = await self._tools.execute(tool_name, tool_args)
                self._state.tool_results.append({
                    "tool_call_id": tool_call["id"],
                    "name": tool_name,
                    "result": result,
                    "status": "success",
                })
            except Exception as e:
                self._state.tool_results.append({
                    "tool_call_id": tool_call["id"],
                    "name": tool_name,
                    "result": f"Error: {str(e)}",
                    "status": "error",
                })

        # Clear pending tool calls
        self._state.pending_tool_calls = []

        await self._fire_hook(HookEvent.POST_ACT, {
            "tool_results": self._state.tool_results,
        })

    async def _observe_phase(self):
        """
        OBSERVE: Process tool results and update context.

        Adds tool results to conversation history for next thinking cycle.
        """
        self._state.phase = AutonomousPhase.OBSERVE

        if not self._state.tool_results:
            return

        await self._fire_hook(HookEvent.PRE_OBSERVE, {
            "tool_results": self._state.tool_results,
        })

        # Add tool results to messages
        for result in self._state.tool_results:
            self._state.messages.append({
                "role": "tool",
                "tool_call_id": result["tool_call_id"],
                "name": result["name"],
                "content": str(result["result"]),
            })

        # Update working memory with key findings
        for result in self._state.tool_results:
            if result["status"] == "success":
                self._state.working_memory[result["name"]] = result["result"]

        await self._fire_hook(HookEvent.POST_OBSERVE, {
            "working_memory": self._state.working_memory,
        })

    async def _decide_phase(self) -> bool:
        """
        DECIDE: Determine whether to continue or stop.

        Checks:
        1. Task completion (no more tool calls and final response)
        2. Budget limits
        3. Cycle limits
        4. Interrupts

        Returns:
            True to continue, False to stop
        """
        self._state.phase = AutonomousPhase.DECIDE

        await self._fire_hook(HookEvent.PRE_DECIDE, {
            "cycle": self._state.current_cycle,
            "result": self._state.result,
        })

        # Check for completion (result set, no pending tools)
        if self._state.result and not self._state.pending_tool_calls:
            self._state.status = "completed"
            return False

        # Check budget
        if self._state.cost_usd >= self.config.budget_limit_usd:
            self._state.status = "budget_exceeded"
            self._state.result = f"Budget limit exceeded (${self._state.cost_usd:.2f})"
            return False

        # Check cycle limit
        if self._state.current_cycle >= self.config.max_cycles:
            self._state.status = "max_cycles"
            self._state.result = f"Maximum cycles reached ({self.config.max_cycles})"
            return False

        # Check interrupts
        if self._interrupted:
            self._state.status = "interrupted"
            return False

        await self._fire_hook(HookEvent.POST_DECIDE, {
            "continue": True,
            "status": self._state.status,
        })

        return True

    # ========================================
    # HELPER METHODS
    # ========================================

    def _build_thinking_context(self) -> List[Dict[str, str]]:
        """Build context messages for LLM reasoning."""
        system_prompt = self._build_system_prompt()

        messages = [{"role": "system", "content": system_prompt}]

        # Add memory context if available
        if self.memory and self._state.working_memory:
            memory_context = self._format_memory_context()
            messages.append({
                "role": "system",
                "content": f"Relevant memory:\n{memory_context}",
            })

        # Add conversation history
        messages.extend(self._state.messages)

        # Add task if first cycle
        if self._state.current_cycle == 1:
            messages.append({
                "role": "user",
                "content": self._state.task,
            })

        return messages

    def _build_system_prompt(self) -> str:
        """Build system prompt based on planning strategy."""
        base_prompt = """You are an autonomous AI assistant with access to tools.

Your goal is to accomplish the user's task by:
1. Reasoning about what needs to be done
2. Using tools to gather information and take actions
3. Iterating until the task is complete

Available tools will be provided. Use them as needed."""

        if self.config.planning_strategy == "pev":
            base_prompt += """

Follow the Plan-Execute-Verify pattern:
1. PLAN: Create a step-by-step plan
2. EXECUTE: Execute one step at a time
3. VERIFY: Check if the step succeeded before continuing"""

        elif self.config.planning_strategy == "tree_of_thoughts":
            base_prompt += """

Follow the Tree-of-Thoughts pattern:
1. Generate multiple possible approaches
2. Evaluate each approach's likelihood of success
3. Select the most promising approach
4. If stuck, backtrack and try alternative"""

        return base_prompt

    def _should_stop(self) -> bool:
        """Check if execution should stop."""
        return (
            self._state.status != "running"
            or self._interrupted
            or self._state.cost_usd >= self.config.budget_limit_usd
            or self._state.current_cycle >= self.config.max_cycles
        )

    def _build_result(self) -> Dict[str, Any]:
        """Build final execution result."""
        return {
            "output": self._state.result or "",
            "status": self._state.status,
            "cycles_used": self._state.current_cycle,
            "tokens_used": self._state.tokens_used,
            "cost_usd": self._state.cost_usd,
            "tool_calls": [r for r in self._state.tool_results],
            "session_id": self._state.session_id,
            "working_memory": self._state.working_memory,
        }

    async def _learn_from_execution(self):
        """Store learned patterns in long-term memory."""
        if not self.memory:
            return

        # Store successful patterns
        for result in self._state.tool_results:
            if result["status"] == "success":
                await self.memory.store(
                    content=f"Tool {result['name']} succeeded for task: {self._state.task[:100]}",
                    metadata={
                        "tool": result["name"],
                        "task_type": self._classify_task(self._state.task),
                        "success": True,
                    },
                    importance=0.7,
                )

        # Store overall execution pattern
        if self._state.status == "completed":
            await self.memory.store(
                content=f"Successfully completed: {self._state.task[:200]}",
                metadata={
                    "cycles": self._state.current_cycle,
                    "cost": self._state.cost_usd,
                    "tools_used": list(set(r["name"] for r in self._state.tool_results)),
                },
                importance=0.8,
            )
```

### 2.2 Native Tool Implementations

Unlike Claude Code which has built-in tools, Kaizen needs native implementations:

```python
"""
KaizenTools - Native tool implementations for autonomous agents.

These tools replace Claude Code's built-in tools:
- File operations (Read, Write, Edit, Glob, Grep)
- Bash execution (sandboxed)
- Search operations (web, local)
- Task management
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import os
import glob as glob_module
import subprocess
import asyncio
import aiofiles

@dataclass
class ToolResult:
    """Result of tool execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

class BaseTool(ABC):
    """Base class for all tools."""

    name: str
    description: str
    danger_level: str = "SAFE"  # SAFE, LOW, MEDIUM, HIGH, CRITICAL

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool parameters."""
        pass

# ========================================
# FILE TOOLS
# ========================================

class ReadFileTool(BaseTool):
    """Read file contents."""

    name = "read_file"
    description = "Read the contents of a file at the given path"
    danger_level = "SAFE"

    async def execute(
        self,
        path: str,
        offset: int = 0,
        limit: int = 2000,
    ) -> ToolResult:
        try:
            async with aiofiles.open(path, 'r') as f:
                lines = await f.readlines()

            # Apply offset and limit
            selected_lines = lines[offset:offset + limit]
            content = "".join(selected_lines)

            return ToolResult(
                success=True,
                output=content,
                metadata={"lines_read": len(selected_lines), "total_lines": len(lines)},
            )
        except FileNotFoundError:
            return ToolResult(success=False, output="", error=f"File not found: {path}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
                "offset": {"type": "integer", "description": "Line offset", "default": 0},
                "limit": {"type": "integer", "description": "Max lines to read", "default": 2000},
            },
            "required": ["path"],
        }

class WriteFileTool(BaseTool):
    """Write content to a file."""

    name = "write_file"
    description = "Write content to a file, creating directories if needed"
    danger_level = "MEDIUM"

    async def execute(self, path: str, content: str) -> ToolResult:
        try:
            # Create directories if needed
            os.makedirs(os.path.dirname(path), exist_ok=True)

            async with aiofiles.open(path, 'w') as f:
                await f.write(content)

            return ToolResult(
                success=True,
                output=f"Wrote {len(content)} bytes to {path}",
                metadata={"bytes_written": len(content)},
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        }

class EditFileTool(BaseTool):
    """Edit file with string replacement."""

    name = "edit_file"
    description = "Replace a specific string in a file with new content"
    danger_level = "MEDIUM"

    async def execute(
        self,
        path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> ToolResult:
        try:
            async with aiofiles.open(path, 'r') as f:
                content = await f.read()

            if old_string not in content:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"String not found in file: {old_string[:50]}...",
                )

            if replace_all:
                new_content = content.replace(old_string, new_string)
            else:
                new_content = content.replace(old_string, new_string, 1)

            async with aiofiles.open(path, 'w') as f:
                await f.write(new_content)

            return ToolResult(
                success=True,
                output=f"Edited {path}",
                metadata={"replacements": content.count(old_string) if replace_all else 1},
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to edit"},
                "old_string": {"type": "string", "description": "String to replace"},
                "new_string": {"type": "string", "description": "Replacement string"},
                "replace_all": {"type": "boolean", "description": "Replace all occurrences", "default": False},
            },
            "required": ["path", "old_string", "new_string"],
        }

class GlobTool(BaseTool):
    """Find files matching a pattern."""

    name = "glob"
    description = "Find files matching a glob pattern"
    danger_level = "SAFE"

    async def execute(self, pattern: str, path: str = ".") -> ToolResult:
        try:
            full_pattern = os.path.join(path, pattern)
            matches = glob_module.glob(full_pattern, recursive=True)

            # Sort by modification time (most recent first)
            matches.sort(key=lambda x: os.path.getmtime(x), reverse=True)

            return ToolResult(
                success=True,
                output=matches[:100],  # Limit results
                metadata={"total_matches": len(matches)},
            )
        except Exception as e:
            return ToolResult(success=False, output=[], error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern (e.g., **/*.py)"},
                "path": {"type": "string", "description": "Base path", "default": "."},
            },
            "required": ["pattern"],
        }

class GrepTool(BaseTool):
    """Search file contents."""

    name = "grep"
    description = "Search for a pattern in files"
    danger_level = "SAFE"

    async def execute(
        self,
        pattern: str,
        path: str = ".",
        file_glob: str = "*",
        case_insensitive: bool = False,
    ) -> ToolResult:
        try:
            # Use ripgrep if available, else fall back to grep
            cmd = ["rg", "--json"]
            if case_insensitive:
                cmd.append("-i")
            cmd.extend(["-g", file_glob, pattern, path])

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return ToolResult(
                    success=True,
                    output=stdout.decode(),
                    metadata={"command": " ".join(cmd)},
                )
            elif process.returncode == 1:
                # No matches
                return ToolResult(success=True, output="No matches found")
            else:
                return ToolResult(success=False, output="", error=stderr.decode())
        except FileNotFoundError:
            # Ripgrep not installed, use Python fallback
            return await self._python_grep(pattern, path, file_glob, case_insensitive)

    async def _python_grep(self, pattern, path, file_glob, case_insensitive):
        """Fallback Python grep implementation."""
        import re
        flags = re.IGNORECASE if case_insensitive else 0
        regex = re.compile(pattern, flags)

        matches = []
        for filepath in glob_module.glob(os.path.join(path, "**", file_glob), recursive=True):
            if os.path.isfile(filepath):
                try:
                    async with aiofiles.open(filepath, 'r') as f:
                        for i, line in enumerate(await f.readlines(), 1):
                            if regex.search(line):
                                matches.append(f"{filepath}:{i}:{line.rstrip()}")
                except:
                    pass

        return ToolResult(
            success=True,
            output="\n".join(matches[:100]),
            metadata={"total_matches": len(matches)},
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Search pattern (regex)"},
                "path": {"type": "string", "description": "Directory to search", "default": "."},
                "file_glob": {"type": "string", "description": "File pattern", "default": "*"},
                "case_insensitive": {"type": "boolean", "default": False},
            },
            "required": ["pattern"],
        }

# ========================================
# BASH TOOL
# ========================================

class BashTool(BaseTool):
    """Execute bash commands in a sandboxed environment."""

    name = "bash"
    description = "Execute a bash command"
    danger_level = "HIGH"

    def __init__(self, sandbox_mode: bool = True, allowed_commands: List[str] = None):
        self.sandbox_mode = sandbox_mode
        self.allowed_commands = allowed_commands or []
        self.blocked_patterns = [
            "rm -rf /",
            "rm -rf ~",
            "> /dev/sda",
            "mkfs",
            "dd if=",
            ":(){:|:&};:",  # Fork bomb
        ]

    async def execute(
        self,
        command: str,
        timeout: int = 120,
        cwd: str = None,
    ) -> ToolResult:
        # Security checks
        if self.sandbox_mode:
            for blocked in self.blocked_patterns:
                if blocked in command:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Blocked dangerous pattern: {blocked}",
                    )

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Command timed out after {timeout}s",
                )

            output = stdout.decode() + (stderr.decode() if stderr else "")

            return ToolResult(
                success=process.returncode == 0,
                output=output[:30000],  # Limit output size
                error=None if process.returncode == 0 else f"Exit code: {process.returncode}",
                metadata={"exit_code": process.returncode},
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Bash command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 120},
                "cwd": {"type": "string", "description": "Working directory"},
            },
            "required": ["command"],
        }

# ========================================
# SEARCH TOOLS
# ========================================

class WebSearchTool(BaseTool):
    """Search the web."""

    name = "web_search"
    description = "Search the web for information"
    danger_level = "SAFE"

    def __init__(self, search_provider: str = "duckduckgo"):
        self.provider = search_provider

    async def execute(self, query: str, num_results: int = 5) -> ToolResult:
        # Implementation depends on search provider
        # Could use DuckDuckGo, SerpAPI, Tavily, etc.
        try:
            if self.provider == "duckduckgo":
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=num_results))
                return ToolResult(
                    success=True,
                    output=results,
                    metadata={"provider": self.provider, "query": query},
                )
            else:
                return ToolResult(
                    success=False,
                    output=[],
                    error=f"Unknown search provider: {self.provider}",
                )
        except Exception as e:
            return ToolResult(success=False, output=[], error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "description": "Number of results", "default": 5},
            },
            "required": ["query"],
        }

class WebFetchTool(BaseTool):
    """Fetch content from a URL."""

    name = "web_fetch"
    description = "Fetch and parse content from a URL"
    danger_level = "SAFE"

    async def execute(self, url: str, extract_text: bool = True) -> ToolResult:
        try:
            import aiohttp
            from bs4 import BeautifulSoup

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    html = await response.text()

            if extract_text:
                soup = BeautifulSoup(html, 'html.parser')
                # Remove script and style elements
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
                return ToolResult(
                    success=True,
                    output=text[:20000],  # Limit size
                    metadata={"url": url, "content_type": "text"},
                )
            else:
                return ToolResult(
                    success=True,
                    output=html[:50000],
                    metadata={"url": url, "content_type": "html"},
                )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "extract_text": {"type": "boolean", "description": "Extract text only", "default": True},
            },
            "required": ["url"],
        }

# ========================================
# TOOL REGISTRY
# ========================================

class KaizenToolRegistry:
    """Registry for managing tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """Register a tool."""
        self._tools[tool.name] = tool

    def register_defaults(self, categories: List[str] = None):
        """Register default tools by category."""
        categories = categories or ["file", "bash", "search"]

        if "file" in categories:
            self.register(ReadFileTool())
            self.register(WriteFileTool())
            self.register(EditFileTool())
            self.register(GlobTool())
            self.register(GrepTool())

        if "bash" in categories:
            self.register(BashTool())

        if "search" in categories:
            self.register(WebSearchTool())
            self.register(WebFetchTool())

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tools."""
        return list(self._tools.keys())

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all tools (for LLM)."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.get_schema(),
                },
            }
            for tool in self._tools.values()
        ]

    async def execute(self, name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool by name."""
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")

        result = await tool.execute(**args)

        if result.success:
            return result.output
        else:
            raise RuntimeError(f"Tool execution failed: {result.error}")
```

---

## Part 3: Kaizen's Existing Capabilities for Autonomous Agents

### 3.1 BaseAgent Foundation

Kaizen already has a robust BaseAgent that provides:

```python
# From kaizen-baseagent-quick.md
class BaseAgent:
    """
    Foundation providing:
    - Config auto-conversion
    - Async execution (2-3x faster)
    - Error handling with retries
    - Performance tracking
    - Memory management
    - A2A capability cards
    - Workflow generation
    - Tool calling (v0.2.0)
    - Bidirectional communication (v0.2.0)
    """

    def run(self, **kwargs) -> Dict:
        """Sync execution interface."""

    async def run_async(self, **kwargs) -> Dict:
        """Async execution for high-throughput."""

    async def execute_tool(self, tool_name: str, params: Dict) -> Any:
        """Execute registered tool."""
```

### 3.2 Checkpoint/Resume System

From `kaizen-checkpoint-resume.md`:

```python
# Already production-ready checkpoint system
from kaizen.core.autonomy.state.manager import StateManager
from kaizen.core.autonomy.state.storage import FilesystemStorage

storage = FilesystemStorage(
    base_dir=".kaizen/checkpoints",
    compress=True  # >50% size reduction
)

state_manager = StateManager(
    storage=storage,
    checkpoint_frequency=5,
    retention_count=10
)

# State captured includes:
# - Step number
# - Conversation history
# - Memory entries
# - Current plan
# - Budget info
# - Agent status
```

### 3.3 Tool Calling System

From `kaizen-tool-calling.md`:

```python
# 12 builtin tools via MCP
tools = [
    # File: read_file, write_file, delete_file, list_directory, file_exists
    # HTTP: http_get, http_post, http_put, http_delete
    # Bash: bash_command
    # Web: fetch_url, extract_links
]

# Danger levels for approval workflow
# SAFE -> LOW -> MEDIUM -> HIGH -> CRITICAL

# Tool chaining
results = await agent.execute_tool_chain([
    {"tool_name": "read_file", "params": {"path": "input.txt"}},
    {"tool_name": "http_post", "params": {"url": "...", "data": "${previous.content}"}},
])
```

### 3.4 Control Protocol

From `kaizen-control-protocol.md`:

```python
# Bidirectional communication during execution
class ControlProtocol:
    async def ask_user_question(question: str, options: List[str]) -> str
    async def request_approval(action: str, details: Dict) -> bool
    async def report_progress(message: str, percentage: float)

# 4 transports: CLI, HTTP/SSE, stdio, memory
```

### 3.5 Memory System

From `kaizen-memory-system.md`:

```python
# Complete memory stack
ShortTermMemory  # Session-scoped, TTL-based
LongTermMemory   # Persistent cross-session
SemanticMemory   # Concept extraction, similarity search

# Learning mechanisms
PatternRecognizer    # FAQ detection
PreferenceLearner    # User preferences
MemoryPromoter       # Short->Long promotion
ErrorCorrectionLearner  # Learn from mistakes
```

### 3.6 Planning Agents

From `kaizen-agent-patterns.md`:

```python
# Single-agent patterns
PlanningAgent      # Plan -> Validate -> Execute
PEVAgent           # Plan -> Execute -> Verify -> Refine loop
TreeOfThoughtsAgent  # Multi-path exploration

# Pipeline patterns
Pipeline.supervisor_worker(supervisor, workers)
Pipeline.router(agents)  # Intelligent routing
Pipeline.ensemble(agents, synthesizer, top_k=3)
```

---

## Part 4: Implementation Strategy

### Phase 1: Wrapper Baselines (Week 1-2)

Create adapters for existing autonomous agent runtimes:

```python
# 1. ClaudeCodeAdapter - Claude models ONLY
class ClaudeCodeAdapter(RuntimeAdapter):
    """
    Wraps Claude Code SDK for Claude Code-like execution.

    IMPORTANT: This adapter is LOCKED to Claude models.
    - model: Literal["sonnet", "opus", "haiku"]
    - Uses Claude Code's native tools (Read, Write, Bash, etc.)
    - Full MCP support
    """

    @property
    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(
            runtime_name="claude_code",
            provider="anthropic",
            supports_streaming=True,
            supports_tool_calling=True,
            supports_file_access=True,
            supports_code_execution=True,
            supports_web_access=True,
            native_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch"],
        )

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        # Delegate to Claude Code SDK
        ...

# 2. OpenAICodexAdapter - OpenAI models ONLY
class OpenAICodexAdapter(RuntimeAdapter):
    """
    Wraps OpenAI Assistant API with Code Interpreter.

    IMPORTANT: This adapter is LOCKED to OpenAI models.
    """
    ...

# 3. GeminiCLIAdapter - Gemini models ONLY
class GeminiCLIAdapter(RuntimeAdapter):
    """
    Wraps Gemini CLI / Vertex AI.

    IMPORTANT: This adapter is LOCKED to Gemini models.
    """
    ...
```

### Phase 2: Native Tools (Week 3-4)

Implement Kaizen-native tools:

```python
# File tools
KaizenFileTools = [
    ReadFileTool(),
    WriteFileTool(),
    EditFileTool(),
    GlobTool(),
    GrepTool(),
    ListDirectoryTool(),
    FileExistsTool(),
]

# Bash tools (sandboxed)
KaizenBashTools = [
    BashTool(sandbox_mode=True),
]

# Search tools
KaizenSearchTools = [
    WebSearchTool(provider="duckduckgo"),
    WebFetchTool(),
]

# Task management
KaizenTaskTools = [
    CreateTaskTool(),
    UpdateTaskTool(),
    ListTasksTool(),
]
```

### Phase 3: AutonomousExecutionStrategy (Week 5-6)

Build the core autonomous loop:

```python
class AutonomousExecutionStrategy:
    """
    Production autonomous execution for LocalKaizenAdapter.

    Features:
    - Think-Act-Observe-Decide loop
    - Multiple planning strategies (ReAct, PEV, ToT)
    - Full checkpoint/resume
    - Budget and cycle limits
    - Interrupt handling
    - Learning memory integration
    """

    async def execute(
        self,
        task: str,
        config: AutonomousConfig,
        tools: KaizenToolRegistry,
        llm: LLMProvider,
    ) -> ExecutionResult:
        ...
```

### Phase 4: Testing & Parity (Week 7-8)

Test against Claude Code behavior:

```python
# Test scenarios
TEST_SCENARIOS = [
    # File operations
    "Read this file and summarize it",
    "Create a new Python file with a hello world function",
    "Find all Python files and count lines of code",

    # Research tasks
    "Research the latest AI news and summarize",
    "Find information about topic X and create a report",

    # Code tasks
    "Fix the bug in this code",
    "Add error handling to this function",
    "Refactor this code to be more efficient",

    # Multi-step tasks
    "Create a data pipeline that reads CSV, processes, and outputs JSON",
    "Build a simple web scraper for product prices",
]

# Parity metrics
PARITY_METRICS = {
    "task_completion_rate": 0.95,  # 95% same tasks completed
    "tool_call_similarity": 0.90,  # 90% similar tool usage
    "output_quality": 0.85,        # 85% quality rating
}
```

---

## Part 5: Key Differentiators

### 5.1 What Native Kaizen Offers That Wrappers Can't

| Feature | ClaudeCodeAdapter | LocalKaizenAdapter |
|---------|-------------------|-------------------|
| **Multi-LLM Routing** | Claude only | Any provider |
| **Custom Tool Sets** | Claude's tools | Fully customizable |
| **Tool Approval** | Basic | Danger-level based |
| **Learning Memory** | None | Full integration |
| **Planning Strategies** | Fixed | ReAct, PEV, ToT |
| **Checkpoint Granularity** | Conversation | Full state |
| **Observability** | Limited | Full hooks |
| **Cost Optimization** | Per-call | Task-based routing |

### 5.2 Multi-LLM Routing in Native Mode

```python
# Only possible with LocalKaizenAdapter
agent = Agent(
    model="gpt-4",
    runtime="kaizen_local",
    llm_routing={
        "simple_queries": "gpt-3.5-turbo",   # Cheap for simple
        "code_generation": "gpt-4",           # Best for code
        "analysis": "claude-3-opus",          # Claude for analysis
        "fast_iteration": "llama3.2",         # Local for speed
    }
)
```

### 5.3 Custom Tool Sets

```python
# Create domain-specific tools
@tool(name="query_database", danger_level="LOW")
async def query_database(query: str) -> Dict:
    """Query the application database."""
    ...

@tool(name="send_notification", danger_level="MEDIUM")
async def send_notification(channel: str, message: str) -> bool:
    """Send notification to Slack/Teams."""
    ...

# Register with agent
registry = KaizenToolRegistry()
registry.register_defaults(["file", "bash"])
registry.register(query_database)
registry.register(send_notification)

agent = LocalKaizenAdapter(
    config=config,
    tools=registry,
)
```

### 5.4 Learning Memory Integration

```python
# Agent learns from executions
agent = LocalKaizenAdapter(
    config=AutonomousConfig(enable_learning=True),
    memory=LongTermMemory(storage=SQLiteStorage("agent_memory.db")),
)

# After execution, agent remembers:
# - Successful patterns
# - Failed approaches
# - User preferences
# - Task classifications

# Future queries benefit from past learning
result = await agent.execute("Similar task to before")
# Agent uses learned patterns to complete faster
```

### 5.5 Fine-Grained Control

```python
# Hook into every phase
hook_manager = HookManager()

@hook_manager.on(HookEvent.PRE_THINK)
async def log_thinking(context):
    print(f"Cycle {context.data['cycle']}: Thinking...")

@hook_manager.on(HookEvent.POST_ACT)
async def audit_tools(context):
    for result in context.data['tool_results']:
        await audit_log.write(result)

@hook_manager.on(HookEvent.PRE_DECIDE)
async def check_constraints(context):
    if context.data['cost_usd'] > budget_warning:
        await notify_user("Approaching budget limit")

agent = LocalKaizenAdapter(
    config=config,
    hook_manager=hook_manager,
)
```

---

## Part 6: Architecture Decision Records

### ADR-001: Native vs Wrapper Approach

**Decision**: Implement BOTH wrapper adapters AND native autonomous agent

**Context**:
- Wrappers provide quick integration with existing runtimes
- Native implementation provides flexibility and control

**Consequences**:
- Users can choose based on needs
- More development effort initially
- Better long-term maintainability

### ADR-002: Tool Implementation Strategy

**Decision**: Implement Kaizen-native tools, don't depend on Claude Code tools

**Context**:
- Claude Code tools are proprietary
- Need tools that work with any LLM

**Consequences**:
- Full control over tool behavior
- Can customize for domain needs
- Must maintain tool implementations

### ADR-003: Planning Strategy Selection

**Decision**: Support multiple planning strategies via configuration

**Context**:
- Different tasks benefit from different strategies
- ReAct is simple, PEV is thorough, ToT explores alternatives

**Consequences**:
- Users can match strategy to task
- More complex implementation
- Better task completion rates

---

## Part 7: Summary

### What We're Building

A **Kaizen-native autonomous agent** that:

1. **Executes autonomously** with think-act-observe-decide loop
2. **Works with ANY LLM** via provider abstraction
3. **Has native tools** for file, bash, search, and task management
4. **Supports checkpointing** for long-running tasks
5. **Integrates learning memory** for improvement over time
6. **Provides full observability** via hooks
7. **Offers multiple planning strategies** for different task types

### Key Files to Create

```
src/kaizen/
├── runtime/
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py                 # RuntimeAdapter interface
│   │   ├── claude_code.py          # ClaudeCodeAdapter
│   │   ├── openai_codex.py         # OpenAICodexAdapter
│   │   └── kaizen_local.py         # LocalKaizenAdapter
│   └── strategies/
│       ├── __init__.py
│       ├── autonomous.py           # AutonomousExecutionStrategy
│       └── planning/
│           ├── react.py            # ReAct planner
│           ├── pev.py              # PEV planner
│           └── tree_of_thoughts.py # ToT planner
├── tools/
│   ├── __init__.py
│   ├── registry.py                 # KaizenToolRegistry
│   ├── base.py                     # BaseTool
│   ├── file_tools.py               # File operations
│   ├── bash_tools.py               # Bash execution
│   ├── search_tools.py             # Web search/fetch
│   └── task_tools.py               # Task management
└── core/
    └── agents.py                   # Unified Agent class
```

### Success Criteria

1. **Feature Parity**: Complete same tasks as Claude Code
2. **Multi-LLM**: Successfully route to different providers
3. **Performance**: <10% overhead vs direct LLM calls
4. **Reliability**: 99%+ task completion rate
5. **Learning**: Measurable improvement from memory

---

**Document Prepared By:** Claude (Ultrathink Analyst)
**Date:** 2026-01-21
**Status:** Ready for Implementation
