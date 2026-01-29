# Architectural Analysis: Delivering Claude Code Capabilities via Kaizen

---

## ⚠️ Critical Update: Claude SDK Model Constraints

> **Discovery (2026-01-21):** Investigation of the Claude Agent SDK (`claude-agent-sdk-python`) confirms that **Claude Code is tied to Claude models specifically**:
>
> - `AgentDefinition.model` only accepts `Literal["sonnet", "opus", "haiku", "inherit"]`
> - The SDK wraps `@anthropic-ai/claude-code` npm package (Anthropic's proprietary CLI)
> - No LLM provider abstraction exists
>
> **Implication:** When using `ClaudeCodeAdapter` (this document's approach), you are locked to Anthropic's Claude models. This is acceptable for the **wrapper-first strategy**, but for multi-LLM flexibility, see [07-native-kaizen-agent-design.md](./07-native-kaizen-agent-design.md).
>
> **Strategy Decision:** We adopt a **wrapper-first approach**—build `ClaudeCodeAdapter` as a baseline to understand autonomous execution patterns, then implement `LocalKaizenAdapter` for full LLM flexibility.

---

## Executive Summary

After comprehensive analysis of Kaizen's architecture and the Claude Agent SDK, I recommend **Approach 2: Wrap Claude Code Agent** as the optimal solution **for the baseline implementation**. This approach provides the best balance of:

1. **Full Claude Code Capabilities** - Native Claude Code features (subagents, skills, tool calling)
2. **Minimal Development** - Leverages existing, battle-tested infrastructure
3. **Enterprise Integration** - Kaizen's observability, lifecycle management, and orchestration
4. **Multi-Channel Deployment** - Nexus integration for Discord/Telegram/Web/Mobile

---

## Approach Comparison Matrix

| Criterion | Approach 1: Replicate (Native) | Approach 2: Wrap Claude Code | Approach 3: Inherit/Extend |
|-----------|-------------------------------|------------------------------|---------------------------|
| **Development Time** | 6-8 weeks (after wrapper baseline) | 2-4 weeks | 4-8 weeks |
| **Claude Code Parity** | Custom implementation | 100% (native) | 80-90% (partial) |
| **LLM Flexibility** | **Any LLM** ✅ | Claude only ❌ | Claude only ❌ |
| **Maintenance Burden** | MEDIUM (our code) | LOW (SDK updates) | HIGH (dual maintenance) |
| **Enterprise Features** | Kaizen-native | Integrated via wrapper | Mixed, complex |
| **Multi-Channel** | Full via Nexus | Full via Nexus | Partial |
| **Risk Level** | MEDIUM (informed by wrapper) | LOW (proven patterns) | MEDIUM (integration issues) |
| **Recommendation** | **Phase 2** (after baseline) | **Phase 1 BASELINE** | Not recommended |

> **Updated Strategy:** Approach 2 serves as **baseline** (learn patterns), then Approach 1 provides **multi-LLM flexibility**.

---

## Detailed Analysis

### Approach 1: Replicate via Kaizen

**Description**: Build an independent agentic system using Kaizen's BaseAgent, signatures, multi-agent coordination, and MCP tools.

**Pros**:
- Full control over architecture
- Native Kaizen patterns throughout
- No external SDK dependency
- Potentially optimized for our use case

**Cons**:
- **Massive development effort**: Claude Code has years of development
- **Feature gap**: Would take 6-12 months to reach 60% parity
- **Ongoing maintenance**: Must rebuild every new Claude Code feature
- **Testing burden**: Need to validate LLM interactions extensively

**Implementation Complexity**: **VERY HIGH**

What we'd need to replicate:
1. Claude Code CLI subprocess management
2. Full tool calling (Read, Write, Edit, Glob, Grep, Bash, etc.)
3. Agent spawning and coordination
4. File checkpointing and rewind
5. Context management and compaction
6. Permission and approval workflows
7. Streaming and real-time updates

**Verdict**: Not recommended. The effort required exceeds the benefits.

---

### Approach 2: Wrap Claude Code Agent (RECOMMENDED)

**Description**: Create a Kaizen BaseAgent that wraps `ClaudeSDKClient`, gaining full Claude Code capabilities while leveraging Kaizen's enterprise infrastructure.

**Pros**:
- **100% Claude Code capabilities**: Native subagents, skills, tools
- **Rapid development**: 2-4 weeks to production
- **SDK updates**: Automatically benefits from Claude improvements
- **Enterprise features**: Kaizen hooks, observability, memory, orchestration
- **Multi-channel**: Nexus deployment for Discord/Telegram/Web

**Cons**:
- External dependency on Claude Agent SDK
- Some overhead in translation layer
- Need to handle async coordination

**Implementation Complexity**: **LOW-MEDIUM**

**Verdict**: **Recommended approach**. Best balance of capabilities and effort.

---

### Approach 3: Inherit/Extend

**Description**: Create a specialized agent type that inherits from Kaizen patterns while directly using Claude SDK internals.

**Pros**:
- Tighter integration with Kaizen
- More control over behavior
- Could optimize specific paths

**Cons**:
- **Architectural coupling**: Changes in either SDK could break integration
- **Maintenance burden**: Must track both SDKs
- **Complexity**: Managing two inheritance hierarchies
- **Testing**: Complex interaction patterns

**Implementation Complexity**: **MEDIUM-HIGH**

**Verdict**: Viable but more complex than Approach 2 without significant benefits.

---

## Recommended Architecture: Approach 2

### Architecture Diagram

```
                                    COURSEWRIGHT ARCHITECTURE
                                    ==========================

    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │                              PLATFORM LAYER                                      │
    │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
    │   │   Discord   │  │  Telegram   │  │   Web Chat  │  │ Mobile App  │           │
    │   │     Bot     │  │     Bot     │  │             │  │             │           │
    │   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
    │          │                │                │                │                   │
    │          └────────────────┴────────────────┴────────────────┘                   │
    │                                    │                                             │
    │                           ┌────────┴────────┐                                   │
    │                           │      NEXUS      │                                   │
    │                           │  Multi-Channel  │                                   │
    │                           │    Platform     │                                   │
    │                           └────────┬────────┘                                   │
    └─────────────────────────────────────┼───────────────────────────────────────────┘
                                          │
    ┌─────────────────────────────────────┼───────────────────────────────────────────┐
    │                          ORCHESTRATION LAYER                                     │
    │                                     │                                            │
    │   ┌─────────────────────────────────┴──────────────────────────────────────┐   │
    │   │                        AGENT ORCHESTRATOR                               │   │
    │   │  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │   │
    │   │  │ Query Router   │  │ Session Manager  │  │ Response Formatter   │   │   │
    │   │  │ (A2A-based)    │  │                  │  │ (Platform-specific)  │   │   │
    │   │  └────────┬───────┘  └────────┬─────────┘  └──────────────────────┘   │   │
    │   └───────────┼───────────────────┼─────────────────────────────────────────┘   │
    │               │                   │                                              │
    │   ┌───────────┴───────────────────┴─────────────────────────────────────────┐   │
    │   │                         KAIZEN INFRASTRUCTURE                            │   │
    │   │  ┌──────────────┐  ┌────────────────┐  ┌────────────────────────────┐  │   │
    │   │  │   Hooks &    │  │   Memory &     │  │   Permission System        │  │   │
    │   │  │ Observability│  │   State Mgmt   │  │   (Budget, Cost Control)   │  │   │
    │   │  └──────────────┘  └────────────────┘  └────────────────────────────┘  │   │
    │   └─────────────────────────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────────────────┘
                                          │
    ┌─────────────────────────────────────┼───────────────────────────────────────────┐
    │                            AGENT LAYER                                           │
    │                                     │                                            │
    │   ┌─────────────────────────────────┴──────────────────────────────────────┐   │
    │   │                     CLAUDE CODE WRAPPER AGENT                           │   │
    │   │   (BaseAgent subclass wrapping ClaudeSDKClient)                         │   │
    │   │                                                                          │   │
    │   │   ┌──────────────────────────────────────────────────────────────────┐  │   │
    │   │   │                    ClaudeAgentOptions                             │  │   │
    │   │   │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │  │   │
    │   │   │  │ System      │ │   Custom    │ │    MCP      │ │   Hooks   │  │  │   │
    │   │   │  │ Prompt      │ │   Agents    │ │  Servers    │ │           │  │  │   │
    │   │   │  │ (Skills)    │ │ (Experts)   │ │  (Tools)    │ │           │  │  │   │
    │   │   │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │  │   │
    │   │   └──────────────────────────────────────────────────────────────────┘  │   │
    │   │                                                                          │   │
    │   │   ┌──────────────────────────────────────────────────────────────────┐  │   │
    │   │   │                    ClaudeSDKClient                                │  │   │
    │   │   │    (Bidirectional communication with Claude Code CLI)            │  │   │
    │   │   └──────────────────────────────────────────────────────────────────┘  │   │
    │   └─────────────────────────────────────────────────────────────────────────┘   │
    │                                     │                                            │
    │   ┌─────────────────────────────────┴──────────────────────────────────────┐   │
    │   │                     FOUNDATION AGENTS (via AgentDefinition)             │   │
    │   │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
    │   │   │  Part 1  │ │  Part 2  │ │  Part 3  │ │  Part 4  │ │  Part 5  │    │   │
    │   │   │  Expert  │ │  Expert  │ │  Expert  │ │  Expert  │ │  Expert  │    │   │
    │   │   │ (Ch 1-4) │ │ (Ch 5-7) │ │ (Ch 8-10)│ │(Ch 11-15)│ │(Ch 18-21)│    │   │
    │   │   └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
    │   └─────────────────────────────────────────────────────────────────────────┘   │
    │                                     │                                            │
    │   ┌─────────────────────────────────┴──────────────────────────────────────┐   │
    │   │                     USE-CASE AGENTS (via AgentDefinition)               │   │
    │   │   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │   │
    │   │   │  Curriculum  │ │     Q&A      │ │  Assessment  │ │    Grader    │  │   │
    │   │   │   Designer   │ │    Expert    │ │   Creator    │ │              │  │   │
    │   │   └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘  │   │
    │   └─────────────────────────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────────────────┘
                                          │
    ┌─────────────────────────────────────┼───────────────────────────────────────────┐
    │                          KNOWLEDGE LAYER                                         │
    │                                     │                                            │
    │   ┌─────────────────────────────────┴──────────────────────────────────────┐   │
    │   │                          SKILLS                                         │   │
    │   │   ┌───────────────────────────────────────────────────────────────┐    │   │
    │   │   │ Chapter Skills: ch1-globalization, ch2-monetary-system,       │    │   │
    │   │   │ ch3-bop, ch4-governance, ch5-fx-market, ch6-parity,          │    │   │
    │   │   │ ch7-derivatives, ch8-transaction, ch9-economic...             │    │   │
    │   │   └───────────────────────────────────────────────────────────────┘    │   │
    │   │   ┌───────────────────────────────────────────────────────────────┐    │   │
    │   │   │ Cross-Cutting: ifm-formulas, ifm-exhibits, ifm-case-studies  │    │   │
    │   │   └───────────────────────────────────────────────────────────────┘    │   │
    │   └─────────────────────────────────────────────────────────────────────────┘   │
    │                                     │                                            │
    │   ┌─────────────────────────────────┴──────────────────────────────────────┐   │
    │   │                      KNOWLEDGE BASE                                     │   │
    │   │   docs/fnce210/knowledge_base/                                          │   │
    │   │   ├── chapter_01/ through chapter_21/                                   │   │
    │   │   └── Part_1_Index.md through Part_5_Index.md                           │   │
    │   └─────────────────────────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Code Skeleton

### 1. Core Wrapper Agent

```python
# src/coursewright/agents/claude_code_wrapper.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional, Any
from pathlib import Path
import logging

from kaizen.core.base_agent import BaseAgent
from kaizen.signatures import Signature, InputField, OutputField
from kaizen.core.autonomy.hooks.manager import HookManager
from kaizen.core.autonomy.hooks.types import HookEvent, HookContext, HookResult, HookPriority

# Claude Agent SDK imports
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AgentDefinition,
    McpServerConfig,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ResultMessage,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class ClaudeCodeWrapperConfig:
    """Configuration for ClaudeCodeWrapper agent."""

    # Kaizen BaseAgent config (auto-extracted)
    llm_provider: str = "anthropic"  # Underlying provider is Claude
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 4096

    # Claude Code specific config
    knowledge_base_path: Path = field(default_factory=lambda: Path("docs/fnce210/knowledge_base"))
    agents_path: Path = field(default_factory=lambda: Path(".claude/agents/fnce210"))
    skills_path: Path = field(default_factory=lambda: Path(".claude/skills/fnce210"))

    # Limits
    max_turns: int = 10
    max_budget_usd: float = 1.00

    # Features
    enable_streaming: bool = True
    enable_checkpointing: bool = False

    # Permission mode
    permission_mode: str = "default"  # default, acceptEdits, plan


# ============================================================================
# Signature
# ============================================================================

class ClaudeCodeSignature(Signature):
    """Signature for Claude Code wrapper agent."""

    # Input
    message: str = InputField(desc="User message or question")
    session_id: Optional[str] = InputField(desc="Session ID for conversation continuity", default=None)
    platform: Optional[str] = InputField(desc="Platform (discord, telegram, web, mobile)", default="web")

    # Output
    response: str = OutputField(desc="Agent response text")
    tool_calls: Optional[list] = OutputField(desc="Tool calls made during execution", default_factory=list)
    cost: Optional[float] = OutputField(desc="Cost in USD for this execution", default=0.0)
    agent_used: Optional[str] = OutputField(desc="Name of subagent if delegated", default=None)


# ============================================================================
# Core Wrapper Agent
# ============================================================================

class ClaudeCodeWrapperAgent(BaseAgent):
    """
    Kaizen BaseAgent that wraps Claude Agent SDK's ClaudeSDKClient.

    This agent provides:
    - Full Claude Code capabilities (subagents, skills, tools)
    - Kaizen enterprise features (hooks, observability, permissions)
    - Nexus multi-channel deployment

    Usage:
        config = ClaudeCodeWrapperConfig()
        agent = ClaudeCodeWrapperAgent(config)
        result = await agent.process_message("What is IRP?", session_id="user123")
    """

    def __init__(
        self,
        config: ClaudeCodeWrapperConfig,
        hook_manager: Optional[HookManager] = None,
    ):
        # Initialize Kaizen BaseAgent
        super().__init__(
            config=config,
            signature=ClaudeCodeSignature(),
            hook_manager=hook_manager,
        )

        self.wrapper_config = config
        self._claude_options = self._build_claude_options()
        self._agent_definitions = self._load_agent_definitions()
        self._skill_content = self._load_skills()

        logger.info(f"ClaudeCodeWrapperAgent initialized with {len(self._agent_definitions)} agents")

    # --------------------------------------------------------------------------
    # Configuration Builders
    # --------------------------------------------------------------------------

    def _build_claude_options(self) -> ClaudeAgentOptions:
        """Build ClaudeAgentOptions from wrapper config."""

        # Build system prompt with skills
        system_prompt = self._build_system_prompt()

        # Build agent definitions
        agents = self._load_agent_definitions()

        # Build MCP servers for custom tools
        mcp_servers = self._build_mcp_servers()

        return ClaudeAgentOptions(
            system_prompt=system_prompt,
            agents=agents,
            mcp_servers=mcp_servers,
            allowed_tools=["Read", "Glob", "Grep"],  # Knowledge base tools
            permission_mode=self.wrapper_config.permission_mode,
            max_turns=self.wrapper_config.max_turns,
            max_budget_usd=self.wrapper_config.max_budget_usd,
            cwd=str(self.wrapper_config.knowledge_base_path.parent.parent),  # Project root
        )

    def _build_system_prompt(self) -> str:
        """Build system prompt incorporating skills."""

        base_prompt = """You are an expert AI assistant for International Financial Management (FNCE210).

## Knowledge Base
Your knowledge is stored in: {kb_path}
- Read chapter files for detailed explanations
- Use Grep to find specific formulas or concepts
- Cross-reference related topics

## Response Format
When answering questions:
1. ANSWER: Direct answer to the question
2. FORMULA: Relevant formula(s) if applicable
3. EXAMPLE: Worked example if applicable
4. SOURCES: File paths referenced

## Expert Delegation
For complex questions, you have access to specialized experts:
- part1-expert: Globalization, monetary system, BoP, governance (Ch 1-4)
- part2-expert: FX markets, parity conditions, derivatives (Ch 5-7)
- part3-expert: Transaction, economic, translation exposure (Ch 8-10)
- part4-expert: Banking, bonds, equities, swaps, portfolio (Ch 11-15)
- part5-expert: Capital budgeting, cash, trade finance, tax (Ch 18-21)

{skills}
"""

        return base_prompt.format(
            kb_path=self.wrapper_config.knowledge_base_path,
            skills=self._skill_content,
        )

    def _load_skills(self) -> str:
        """Load skill content from skill files."""
        skills_content = []
        skills_path = self.wrapper_config.skills_path

        if skills_path.exists():
            for skill_file in skills_path.glob("*.md"):
                if skill_file.name != "SKILL.md":
                    content = skill_file.read_text()
                    skills_content.append(f"## Skill: {skill_file.stem}\n{content[:500]}...")

        return "\n\n".join(skills_content) if skills_content else ""

    def _load_agent_definitions(self) -> dict[str, AgentDefinition]:
        """Load agent definitions from markdown files."""
        agents = {}
        agents_path = self.wrapper_config.agents_path

        # Define the 5 part experts
        part_experts = {
            "part1-expert": {
                "description": "Expert in Globalization, Monetary System, BoP, Governance (Chapters 1-4)",
                "prompt": "You are an expert in Part 1 of IFM covering globalization, international monetary system, balance of payments, and corporate governance. Reference chapters 1-4 in the knowledge base.",
                "tools": ["Read", "Glob", "Grep"],
                "model": "sonnet",
            },
            "part2-expert": {
                "description": "Expert in FX Markets, Parity Conditions, Derivatives (Chapters 5-7)",
                "prompt": "You are an expert in Part 2 of IFM covering foreign exchange markets, parity conditions, and currency derivatives. Reference chapters 5-7 in the knowledge base.",
                "tools": ["Read", "Glob", "Grep"],
                "model": "sonnet",
            },
            "part3-expert": {
                "description": "Expert in Transaction, Economic, Translation Exposure (Chapters 8-10)",
                "prompt": "You are an expert in Part 3 of IFM covering foreign exchange exposure management. Reference chapters 8-10 in the knowledge base.",
                "tools": ["Read", "Glob", "Grep"],
                "model": "sonnet",
            },
            "part4-expert": {
                "description": "Expert in International Banking, Bonds, Equities, Swaps, Portfolio (Chapters 11-15)",
                "prompt": "You are an expert in Part 4 of IFM covering international financial markets. Reference chapters 11-15 in the knowledge base.",
                "tools": ["Read", "Glob", "Grep"],
                "model": "sonnet",
            },
            "part5-expert": {
                "description": "Expert in Capital Budgeting, Cash Management, Trade Finance, Tax (Chapters 18-21)",
                "prompt": "You are an expert in Part 5 of IFM covering MNC operations. Reference chapters 18-21 in the knowledge base.",
                "tools": ["Read", "Glob", "Grep"],
                "model": "sonnet",
            },
        }

        for name, config in part_experts.items():
            agents[name] = AgentDefinition(
                description=config["description"],
                prompt=config["prompt"],
                tools=config["tools"],
                model=config["model"],
            )

        return agents

    def _build_mcp_servers(self) -> dict[str, McpServerConfig]:
        """Build MCP server configurations for custom tools."""

        # Custom IFM calculation tools
        from coursewright.tools.ifm_tools import create_ifm_mcp_server

        return {
            "ifm-tools": create_ifm_mcp_server(),
        }

    # --------------------------------------------------------------------------
    # Core Execution
    # --------------------------------------------------------------------------

    async def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        platform: str = "web",
    ) -> dict[str, Any]:
        """
        Process a user message through Claude Code.

        Args:
            message: User's message/question
            session_id: Session ID for conversation continuity
            platform: Platform identifier (discord, telegram, web, mobile)

        Returns:
            Dict with response, tool_calls, cost, agent_used
        """

        # Fire pre-execution hook
        if self._hook_manager:
            await self._hook_manager.execute(
                HookEvent.PRE_AGENT_LOOP,
                HookContext(
                    agent_id=self.agent_id,
                    data={"message": message, "session_id": session_id, "platform": platform}
                )
            )

        response_text = []
        tool_calls = []
        agent_used = None
        total_cost = 0.0

        try:
            async with ClaudeSDKClient(options=self._claude_options) as client:
                # Send the query
                await client.query(message)

                # Receive and process response
                async for msg in client.receive_response():
                    if isinstance(msg, AssistantMessage):
                        for block in msg.content:
                            if isinstance(block, TextBlock):
                                response_text.append(block.text)
                            elif isinstance(block, ToolUseBlock):
                                tool_calls.append({
                                    "name": block.name,
                                    "input": block.input,
                                })

                    elif isinstance(msg, ResultMessage):
                        total_cost = msg.cost.total_cost if msg.cost else 0.0
                        if msg.subagent:
                            agent_used = msg.subagent

        except Exception as e:
            logger.error(f"Claude SDK error: {e}")
            response_text.append(f"I encountered an error processing your request: {str(e)}")

        result = {
            "response": "\n".join(response_text),
            "tool_calls": tool_calls,
            "cost": total_cost,
            "agent_used": agent_used,
            "session_id": session_id,
            "platform": platform,
        }

        # Fire post-execution hook
        if self._hook_manager:
            await self._hook_manager.execute(
                HookEvent.POST_AGENT_LOOP,
                HookContext(
                    agent_id=self.agent_id,
                    data=result
                )
            )

        return result

    async def process_message_streaming(
        self,
        message: str,
        session_id: Optional[str] = None,
        platform: str = "web",
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Process message with streaming response.

        Yields:
            Dict chunks with type (text, tool_call, done) and content
        """

        async with ClaudeSDKClient(options=self._claude_options) as client:
            await client.query(message)

            async for msg in client.receive_messages():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            yield {"type": "text", "content": block.text}
                        elif isinstance(block, ToolUseBlock):
                            yield {"type": "tool_call", "name": block.name, "input": block.input}

                elif isinstance(msg, ResultMessage):
                    yield {
                        "type": "done",
                        "cost": msg.cost.total_cost if msg.cost else 0.0,
                        "agent_used": msg.subagent,
                    }

    # --------------------------------------------------------------------------
    # Kaizen Integration
    # --------------------------------------------------------------------------

    def run(self, **inputs) -> dict[str, Any]:
        """
        Synchronous run method for Kaizen compatibility.
        Uses anyio to run async method in sync context.
        """
        import anyio

        return anyio.from_thread.run(
            self.process_message,
            inputs.get("message", ""),
            inputs.get("session_id"),
            inputs.get("platform", "web"),
        )

    async def run_async(self, **inputs) -> dict[str, Any]:
        """Async run method for Kaizen compatibility."""
        return await self.process_message(
            inputs.get("message", ""),
            inputs.get("session_id"),
            inputs.get("platform", "web"),
        )

    def to_workflow(self):
        """Convert agent to Kailash workflow for Nexus deployment."""
        from kailash.workflow.builder import WorkflowBuilder

        workflow = WorkflowBuilder()

        # Add Python code node that invokes the agent
        workflow.add_node("PythonCodeNode", "claude_agent", {
            "code": f"""
import asyncio
from coursewright.agents.claude_code_wrapper import ClaudeCodeWrapperAgent, ClaudeCodeWrapperConfig

config = ClaudeCodeWrapperConfig()
agent = ClaudeCodeWrapperAgent(config)

# Run async in sync context
loop = asyncio.new_event_loop()
result = loop.run_until_complete(
    agent.process_message(
        message=inputs.get('message', ''),
        session_id=inputs.get('session_id'),
        platform=inputs.get('platform', 'web')
    )
)
loop.close()
""",
            "inputs": ["message", "session_id", "platform"],
            "outputs": ["response", "tool_calls", "cost", "agent_used"],
        })

        return workflow


# ============================================================================
# Factory Functions
# ============================================================================

def create_ifm_assistant(
    config: Optional[ClaudeCodeWrapperConfig] = None,
    enable_observability: bool = True,
) -> ClaudeCodeWrapperAgent:
    """
    Factory function to create a fully-configured IFM assistant.

    Args:
        config: Optional custom configuration
        enable_observability: Enable Kaizen observability hooks

    Returns:
        Configured ClaudeCodeWrapperAgent
    """
    if config is None:
        config = ClaudeCodeWrapperConfig()

    # Setup hook manager with observability
    hook_manager = HookManager()

    if enable_observability:
        from kaizen.core.autonomy.hooks.builtin import LoggingHook, MetricsHook, CostTrackingHook

        hook_manager.register_hook(LoggingHook(log_level="INFO"))
        hook_manager.register_hook(MetricsHook())
        hook_manager.register_hook(CostTrackingHook())

    return ClaudeCodeWrapperAgent(config=config, hook_manager=hook_manager)
```

### 2. IFM Custom Tools

```python
# src/coursewright/tools/ifm_tools.py

from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any


@tool("calculate_irp", "Calculate Interest Rate Parity forward rate", {
    "spot_rate": {"type": "number", "description": "Spot exchange rate"},
    "domestic_rate": {"type": "number", "description": "Domestic interest rate (decimal)"},
    "foreign_rate": {"type": "number", "description": "Foreign interest rate (decimal)"},
    "days": {"type": "number", "description": "Number of days (optional, default 360)", "optional": True},
})
async def calculate_irp(args: dict[str, Any]) -> dict:
    """Calculate forward rate using Interest Rate Parity."""
    spot = args["spot_rate"]
    i_d = args["domestic_rate"]
    i_f = args["foreign_rate"]
    days = args.get("days", 360)

    # IRP formula: F = S * (1 + i_d * days/360) / (1 + i_f * days/360)
    forward = spot * (1 + i_d * days/360) / (1 + i_f * days/360)
    forward_premium = (forward - spot) / spot * (360 / days) * 100

    return {
        "content": [{
            "type": "text",
            "text": f"""Interest Rate Parity Calculation:
- Spot Rate: {spot:.4f}
- Domestic Rate: {i_d*100:.2f}%
- Foreign Rate: {i_f*100:.2f}%
- Days: {days}

Forward Rate: {forward:.4f}
Forward Premium/Discount: {forward_premium:+.2f}% (annualized)

Formula: F = S x (1 + i_d x t) / (1 + i_f x t)
"""
        }]
    }


@tool("calculate_ppp", "Calculate Purchasing Power Parity expected rate", {
    "spot_rate": {"type": "number", "description": "Current spot exchange rate"},
    "domestic_inflation": {"type": "number", "description": "Expected domestic inflation rate (decimal)"},
    "foreign_inflation": {"type": "number", "description": "Expected foreign inflation rate (decimal)"},
})
async def calculate_ppp(args: dict[str, Any]) -> dict:
    """Calculate expected exchange rate using Purchasing Power Parity."""
    spot = args["spot_rate"]
    pi_d = args["domestic_inflation"]
    pi_f = args["foreign_inflation"]

    # Relative PPP: E(S) = S x (1 + pi_d) / (1 + pi_f)
    expected_rate = spot * (1 + pi_d) / (1 + pi_f)
    expected_change = ((expected_rate / spot) - 1) * 100

    return {
        "content": [{
            "type": "text",
            "text": f"""Purchasing Power Parity Calculation:
- Current Spot Rate: {spot:.4f}
- Domestic Inflation: {pi_d*100:.2f}%
- Foreign Inflation: {pi_f*100:.2f}%

Expected Future Spot Rate: {expected_rate:.4f}
Expected Depreciation/Appreciation: {expected_change:+.2f}%

Formula: E(S) = S x (1 + pi_domestic) / (1 + pi_foreign)
"""
        }]
    }


@tool("hedge_forward", "Calculate forward hedge for transaction exposure", {
    "exposure_amount": {"type": "number", "description": "Amount to hedge in foreign currency"},
    "spot_rate": {"type": "number", "description": "Current spot rate"},
    "forward_rate": {"type": "number", "description": "Forward rate for hedge"},
    "direction": {"type": "string", "description": "Direction: 'receivable' or 'payable'"},
})
async def hedge_forward(args: dict[str, Any]) -> dict:
    """Calculate forward hedge outcome."""
    amount = args["exposure_amount"]
    spot = args["spot_rate"]
    forward = args["forward_rate"]
    direction = args["direction"].lower()

    # Calculate locked-in domestic value
    locked_value = amount * forward
    current_value = amount * spot

    if direction == "receivable":
        gain_loss = locked_value - current_value
        action = "sell forward"
    else:  # payable
        gain_loss = current_value - locked_value
        action = "buy forward"

    return {
        "content": [{
            "type": "text",
            "text": f"""Forward Hedge Analysis:
- Exposure: {amount:,.2f} foreign currency ({direction})
- Action: {action.upper()} foreign currency forward

At Current Spot ({spot:.4f}): {current_value:,.2f} domestic
At Forward Rate ({forward:.4f}): {locked_value:,.2f} domestic

Hedge Effect: {gain_loss:+,.2f} domestic vs. spot
Hedge Locks In: {locked_value:,.2f} domestic (certainty)
"""
        }]
    }


def create_ifm_mcp_server():
    """Create MCP server with IFM calculation tools."""
    return create_sdk_mcp_server(
        name="ifm-tools",
        version="1.0.0",
        tools=[calculate_irp, calculate_ppp, hedge_forward]
    )
```

### 3. Nexus Multi-Channel Deployment

```python
# src/coursewright/deployment/nexus_platform.py

from nexus import Nexus
from coursewright.agents.claude_code_wrapper import (
    ClaudeCodeWrapperAgent,
    ClaudeCodeWrapperConfig,
    create_ifm_assistant,
)


def create_coursewright_platform(
    enable_api: bool = True,
    enable_cli: bool = True,
    enable_mcp: bool = True,
    api_port: int = 8000,
) -> Nexus:
    """
    Create Coursewright platform with Nexus multi-channel deployment.

    This provides:
    - REST API: POST /workflows/ifm-assistant
    - CLI: nexus run ifm-assistant --message "What is IRP?"
    - MCP: ifm-assistant tool for AI assistants

    Args:
        enable_api: Enable REST API channel
        enable_cli: Enable CLI channel
        enable_mcp: Enable MCP channel
        api_port: Port for REST API

    Returns:
        Configured Nexus platform
    """

    # Create Nexus platform
    platform = Nexus(
        title="Coursewright - IFM Learning Platform",
        description="AI-powered International Financial Management assistant",
        enable_api=enable_api,
        enable_cli=enable_cli,
        enable_mcp=enable_mcp,
        api_port=api_port,
    )

    # Create and register main IFM assistant
    ifm_agent = create_ifm_assistant()
    ifm_workflow = ifm_agent.to_workflow()

    platform.register(
        "ifm-assistant",
        ifm_workflow.build(),
        metadata={
            "name": "IFM Assistant",
            "description": "Expert in International Financial Management (FNCE210)",
            "parameters": {
                "message": {
                    "type": "string",
                    "description": "Question about IFM topics",
                    "required": True,
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID for conversation continuity",
                    "required": False,
                },
                "platform": {
                    "type": "string",
                    "description": "Platform (discord, telegram, web, mobile)",
                    "required": False,
                    "default": "web",
                },
            },
        }
    )

    return platform


def run_platform():
    """Run the Coursewright platform."""
    platform = create_coursewright_platform()
    platform.run()  # Starts API server and CLI


if __name__ == "__main__":
    run_platform()
```

### 4. Discord Bot Adapter

```python
# src/coursewright/bots/discord_bot.py

import discord
from discord import app_commands
from coursewright.agents.claude_code_wrapper import create_ifm_assistant
import logging

logger = logging.getLogger(__name__)


class CoursewrightDiscordBot(discord.Client):
    """Discord bot adapter for Coursewright IFM assistant."""

    def __init__(self, *args, **kwargs):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, *args, **kwargs)

        self.tree = app_commands.CommandTree(self)
        self.agent = create_ifm_assistant()
        self.sessions: dict[int, str] = {}  # user_id -> session_id

    async def setup_hook(self):
        """Setup slash commands."""
        await self.tree.sync()

    async def on_ready(self):
        logger.info(f"Coursewright bot logged in as {self.user}")

    async def on_message(self, message: discord.Message):
        """Handle direct messages and mentions."""
        if message.author.bot:
            return

        # Check if bot is mentioned or in DM
        if self.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
            # Get or create session
            session_id = self.sessions.get(message.author.id)
            if not session_id:
                session_id = f"discord-{message.author.id}"
                self.sessions[message.author.id] = session_id

            # Clean message (remove mention)
            content = message.content.replace(f"<@{self.user.id}>", "").strip()

            # Show typing indicator
            async with message.channel.typing():
                try:
                    result = await self.agent.process_message(
                        message=content,
                        session_id=session_id,
                        platform="discord",
                    )

                    # Format response for Discord (2000 char limit)
                    response = result["response"]
                    if len(response) > 1900:
                        # Split into multiple messages
                        chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                        for chunk in chunks:
                            await message.reply(chunk)
                    else:
                        await message.reply(response)

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await message.reply("I encountered an error. Please try again.")


@app_commands.command(name="ifm", description="Ask an IFM question")
async def ifm_command(interaction: discord.Interaction, question: str):
    """Slash command for IFM questions."""
    await interaction.response.defer()

    bot: CoursewrightDiscordBot = interaction.client
    session_id = f"discord-{interaction.user.id}"

    try:
        result = await bot.agent.process_message(
            message=question,
            session_id=session_id,
            platform="discord",
        )

        # Send response
        response = result["response"]
        if len(response) > 1900:
            await interaction.followup.send(response[:1900] + "...")
        else:
            await interaction.followup.send(response)

    except Exception as e:
        logger.error(f"Error in slash command: {e}")
        await interaction.followup.send("I encountered an error. Please try again.")


def run_discord_bot(token: str):
    """Run the Discord bot."""
    bot = CoursewrightDiscordBot()
    bot.tree.add_command(ifm_command)
    bot.run(token)
```

### 5. Telegram Bot Adapter

```python
# src/coursewright/bots/telegram_bot.py

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from coursewright.agents.claude_code_wrapper import create_ifm_assistant
import logging

logger = logging.getLogger(__name__)


class CoursewrightTelegramBot:
    """Telegram bot adapter for Coursewright IFM assistant."""

    def __init__(self, token: str):
        self.token = token
        self.agent = create_ifm_assistant()
        self.sessions: dict[int, str] = {}  # user_id -> session_id

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        await update.message.reply_text(
            "Hello! I'm your IFM (International Financial Management) assistant. "
            "Ask me any question about FNCE210 topics like:\n\n"
            "- Foreign exchange markets\n"
            "- Interest Rate Parity\n"
            "- Currency derivatives\n"
            "- Hedging strategies\n"
            "- MNC operations\n\n"
            "Just send me a message!"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        await update.message.reply_text(
            "Commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/clear - Clear conversation history\n\n"
            "Or just send me any IFM question!"
        )

    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command."""
        user_id = update.effective_user.id
        if user_id in self.sessions:
            del self.sessions[user_id]
        await update.message.reply_text("Conversation history cleared!")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user messages."""
        user_id = update.effective_user.id
        message = update.message.text

        # Get or create session
        session_id = self.sessions.get(user_id)
        if not session_id:
            session_id = f"telegram-{user_id}"
            self.sessions[user_id] = session_id

        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        try:
            result = await self.agent.process_message(
                message=message,
                session_id=session_id,
                platform="telegram",
            )

            # Format response for Telegram (4096 char limit)
            response = result["response"]
            if len(response) > 4000:
                # Split into multiple messages
                chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
                for chunk in chunks:
                    await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await update.message.reply_text("I encountered an error. Please try again.")

    def run(self):
        """Run the Telegram bot."""
        application = Application.builder().token(self.token).build()

        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("clear", self.clear_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Start bot
        logger.info("Starting Telegram bot...")
        application.run_polling()


def run_telegram_bot(token: str):
    """Run the Telegram bot."""
    bot = CoursewrightTelegramBot(token)
    bot.run()
```

---

## Integration with FNCE210 Knowledge Base

### Knowledge Base Structure Mapping

```
FNCE210 3-Tier Architecture → Claude Code Integration
═══════════════════════════════════════════════════════

Tier 1: Knowledge Base (Source Content)
  └── docs/fnce210/knowledge_base/
      ├── chapter_01/ ... chapter_21/
      └── Part indexes

  Integration: Read, Glob, Grep tools via ClaudeAgentOptions.allowed_tools

Tier 2: Skills (.claude/skills/fnce210/)
  └── Chapter skills + Cross-cutting skills

  Integration: Loaded into system_prompt via _build_system_prompt()

Tier 3a: Foundation Agents (.claude/agents/fnce210/)
  └── part1-expert through part5-expert

  Integration: ClaudeAgentOptions.agents with AgentDefinition

Tier 3b: Use-Case Agents
  └── curriculum-designer, ifm-qa-expert, assessment-creator, ifm-grader

  Integration: AgentDefinition with specific prompts and tools
```

### Query Flow

```
Student Question
       │
       ▼
┌──────────────────┐
│  Platform Bot    │  Discord / Telegram / Web / Mobile
│  (Adapter)       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ ClaudeCodeWrapper│  Kaizen BaseAgent
│     Agent        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ ClaudeSDKClient  │  Claude Agent SDK
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Claude Code CLI │  Actual execution
│  (subprocess)    │
└────────┬─────────┘
         │
         ├──► AgentDefinition routing → part1-expert / part2-expert / etc.
         │
         ├──► Skills in system prompt → Quick reference formulas
         │
         ├──► Tools (Read/Glob/Grep) → Knowledge base access
         │
         └──► MCP Tools (ifm-tools) → IRP/PPP calculations
```

---

## Benefits of This Architecture

### 1. Full Claude Code Capabilities
- Native subagent spawning via `AgentDefinition`
- Full tool calling (Read, Glob, Grep, custom MCP)
- Context management and compaction
- Streaming responses
- Cost tracking

### 2. Enterprise Features via Kaizen
- **Observability**: LoggingHook, MetricsHook, CostTrackingHook
- **Permission System**: Budget limits, tool restrictions
- **Memory Management**: Session persistence, cross-platform sessions
- **Hooks System**: Pre/post execution hooks for monitoring

### 3. Multi-Channel via Nexus
- **API**: REST endpoint for web integrations
- **CLI**: Command-line interface for developers
- **MCP**: Tool exposure for other AI assistants
- **Bots**: Discord, Telegram with unified backend

### 4. Knowledge Integration
- Skills loaded into system prompt
- Foundation agents as Claude subagents
- Knowledge base accessible via tools
- Custom calculation tools via MCP

---

## Implementation Roadmap

### Phase 1: Core Wrapper (Week 1)
- [ ] Implement `ClaudeCodeWrapperAgent`
- [ ] Build `_build_claude_options()` configuration
- [ ] Load agent definitions from markdown
- [ ] Basic `process_message()` functionality
- [ ] Unit tests with mock Claude SDK

### Phase 2: Tools & Skills (Week 2)
- [ ] Implement IFM calculation tools
- [ ] Create MCP server for tools
- [ ] Load skills from markdown files
- [ ] Integrate skills into system prompt
- [ ] Integration tests with Ollama

### Phase 3: Multi-Channel (Week 3)
- [ ] Nexus platform deployment
- [ ] Discord bot adapter
- [ ] Telegram bot adapter
- [ ] E2E tests across channels

### Phase 4: Production (Week 4)
- [ ] Kaizen observability hooks
- [ ] Cost tracking and limits
- [ ] Session management with Redis
- [ ] Documentation and examples
- [ ] Production deployment

---

## Conclusion

**Approach 2: Wrap Claude Code Agent** is the recommended architecture **as a baseline** because it:

1. **Maximizes Claude Code capabilities** - 100% feature parity via native SDK
2. **Minimizes development time** - 2-4 weeks to production vs 6-12 months
3. **Leverages Kaizen enterprise features** - Observability, hooks, permissions
4. **Enables multi-channel deployment** - Nexus for Discord/Telegram/Web/Mobile
5. **Integrates cleanly with knowledge base** - Skills, agents, and tools

The wrapper pattern allows Coursewright to deliver Claude Code's full agentic capabilities while adding the enterprise infrastructure needed for a production educational platform.

---

## Next Steps: Native Kaizen Agent

**Important:** This wrapper approach locks you to Claude models. For true multi-LLM flexibility, the next phase implements a **Native Kaizen Autonomous Agent** that provides:

1. **Any LLM provider** - OpenAI, Anthropic, Ollama, or custom
2. **Custom tool implementations** - KaizenFileTools, KaizenBashTools, KaizenSearchTools
3. **Full state management** - Checkpointing, learning memory, planning strategies
4. **Fine-grained observability** - Kaizen hooks throughout execution

**See:** [07-native-kaizen-agent-design.md](./07-native-kaizen-agent-design.md) for the complete native agent architecture.

**Implementation Strategy:**
1. **Phase 1 (Weeks 1-4):** Build wrappers (ClaudeCodeAdapter) as baseline
2. **Phase 2 (Weeks 5-6):** Implement native tool system
3. **Phase 3 (Weeks 7-8):** Build LocalKaizenAdapter with full multi-LLM support

This wrapper-first approach ensures we understand autonomous execution patterns before building our own implementation.
