# Kaizen Framework: Strategic Capability Narrative

> **Version**: 2.0.0
> **Last Updated**: 2026-01-12
> **Status**: Approved
> **Kaizen Version**: 0.9.0

## Executive Summary

Kaizen is a **5-layer AI agent framework** built on Kailash Core SDK, providing a clear progression from simple Q&A agents to enterprise multi-agent systems with user journey orchestration.

**The Kaizen Promise**: Build AI agents at any level of complexity, from simple Q&A to enterprise multi-agent systems with user journey orchestration.

---

## Implementation Status

| Layer | Status | Version |
|-------|--------|---------|
| Layer 1: Foundation | **STABLE** | v0.1.0+ |
| Layer 2: Signature | **STABLE** (with __intent__, __guidelines__) | v0.9.0 |
| Layer 3: Agent | **STABLE** | v0.2.0+ |
| Layer 4: Multi-Agent Orchestration | **STABLE** | v0.5.0+ |
| Layer 5: Journey Orchestration | **STABLE** (351 tests) | v0.9.0 |

---

## The Kaizen Capability Pyramid

```
                           ┌─────────────┐
                           │   JOURNEY   │  Layer 5: User flow orchestration
                           │ Orchestration│     (pathways, transitions, intent)
                           │   [STABLE]  │     351 tests
                           └──────┬──────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │     MULTI-AGENT            │  Layer 4: Agent coordination
                    │     Orchestration          │     (patterns, pipelines, A2A)
                    │       [STABLE]             │
                    └─────────────┬─────────────┘
                                  │
              ┌───────────────────┴───────────────────┐
              │           AGENT                        │  Layer 3: Task execution
              │     (BaseAgent + 22+ Specialized)      │     (agents, autonomy)
              │            [STABLE]                    │
              └───────────────────┬───────────────────┘
                                  │
        ┌─────────────────────────┴─────────────────────────┐
        │                    SIGNATURE                       │  Layer 2: Contract definition
        │      (Intent + Guidelines + Field Descriptions)    │     (I/O specification)
        │                    [STABLE]                        │
        └─────────────────────────┬─────────────────────────┘
                                  │
    ┌─────────────────────────────┴─────────────────────────────┐
    │                      FOUNDATION                            │  Layer 1: Core infrastructure
    │            (Kailash Workflows + Runtime)                   │
    │                      [STABLE]                              │
    └───────────────────────────────────────────────────────────┘

    ═══════════════════════════════════════════════════════════════
    CROSS-CUTTING: Memory │ Trust (EATP) │ Tools │ Observability
    ═══════════════════════════════════════════════════════════════
```

---

## Layer-by-Layer Reference

### Layer 1: Foundation (Kailash Core SDK) — STABLE

**Question Answered**: "What powers Kaizen?"

**Key Abstraction**: Kailash Core SDK (WorkflowBuilder + Runtime)

**Purpose**: Kaizen compiles all agent operations to Kailash workflows, ensuring enterprise-grade reliability and observability.

```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime import LocalRuntime, AsyncLocalRuntime

# Every Kaizen agent ultimately executes as a Kailash workflow
workflow = WorkflowBuilder()
workflow.add_node("LLMAgentNode", "agent", {"model": "gpt-4"})
runtime = AsyncLocalRuntime()
results, run_id = await runtime.execute_workflow_async(workflow.build())
```

**Key Components**:
- `WorkflowBuilder` - Declarative workflow construction
- `LocalRuntime` / `AsyncLocalRuntime` - Sync/async execution
- 110+ built-in nodes for any operation

---

### Layer 2: Signature (The Contract) — STABLE

**Question Answered**: "What does this agent do?"

**Key Abstraction**: `Signature` class with typed fields, intent, and guidelines

**Purpose**: Define type-safe I/O contracts with explicit behavioral specifications.

```python
from kaizen.signatures import Signature, InputField, OutputField

class CustomerSupportSignature(Signature):
    """You are a helpful customer support agent."""

    __intent__ = "Resolve customer issues efficiently and empathetically"

    __guidelines__ = [
        "Acknowledge the customer's concern before providing solutions",
        "Use empathetic language throughout the conversation",
        "Escalate to human support if issue cannot be resolved in 3 turns"
    ]

    query: str = InputField(description="Customer's question or issue")
    context: str = InputField(description="Previous conversation context", default="")

    response: str = OutputField(description="Helpful response addressing the concern")
    sentiment: str = OutputField(description="Detected sentiment: positive/neutral/negative")
    escalation_needed: bool = OutputField(description="Whether human escalation is required")

# Immutable composition methods
sig = CustomerSupportSignature()
enhanced_sig = sig.with_instructions("New instructions")  # Returns new instance
enhanced_sig = sig.with_guidelines(["Additional guideline"])  # Returns new instance
```

**Components**:
- `Signature` - Base class with `SignatureMeta` metaclass processing
- `__doc__` (docstring) - Serves as instructions (extracted as `_signature_description`)
- `__intent__` - High-level purpose (WHY the agent exists)
- `__guidelines__` - Behavioral constraints (HOW the agent should behave)
- `InputField(description=...)` / `OutputField(description=...)` - Typed I/O with descriptions
- `with_instructions()` - Create new signature with modified instructions (immutable)
- `with_guidelines()` - Create new signature with additional guidelines (immutable)
- `_clone()` - Internal method for immutable operations

**Signature Philosophy**:
> "The signature IS the specification. Reading the signature tells you everything about what the agent does."

---

### Layer 3: Agent (The Executor) — STABLE

**Question Answered**: "Who executes the task?"

**Key Abstraction**: `BaseAgent` with strategy pattern execution

**Purpose**: Execute tasks using production-ready agents with built-in error handling, memory, and observability.

```python
from kaizen.core.base_agent import BaseAgent
from kaizen.agents import (
    # Single-Shot Agents
    SimpleQAAgent,
    ChainOfThoughtAgent,
    MemoryAgent,
    CodeGenerationAgent,

    # Multi-Modal Agents
    VisionAgent,
    TranscriptionAgent,
    MultiModalAgent,

    # Autonomous Agents
    ReActAgent,
    RAGResearchAgent,
    PlanningAgent,
    PEVAgent,
    ToTAgent,
)

# All agents share the same BaseAgent foundation
class MyAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config=config, signature=MySignature())

    def process(self, query: str) -> dict:
        return self.run(query=query)
```

**Agent Categories (22+ agents)**:

| Category | Agents | Count | Characteristics |
|----------|--------|-------|-----------------|
| **Single-Shot** | SimpleQA, ChainOfThought, Memory, Code, Batch, Resilient, Streaming, SelfReflection | 8 | One execution cycle |
| **Multi-Modal** | Vision, Transcription, MultiModal, DocumentExtraction | 4 | Image/audio/video processing |
| **Autonomous** | ReAct, RAG Research, Planning, PEV, ToT | 5 | Multi-cycle with tools |
| **Specialized** | HumanApproval, ClaudeCode, Codex, BaseAutonomous | 4+ | Production patterns |

**BaseAgent Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                        BaseAgent                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Signature  │  │   Config    │  │      Strategy       │  │
│  │  (Layer 2)  │  │ (provider,  │  │ (AsyncSingleShot,   │  │
│  │             │  │  model...)  │  │  Stream, Batch...)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                              │                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Memory    │  │    Tools    │  │    Observability    │  │
│  │  (3-tier)   │  │  (12+ MCP)  │  │   (hooks, traces)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                              │                               │
│                    .run(**inputs) → outputs                  │
│                    .to_a2a_card() → A2AAgentCard             │
└─────────────────────────────────────────────────────────────┘
```

---

### Layer 4: Multi-Agent Orchestration (Coordination) — STABLE

**Question Answered**: "How do agents work together?"

**Key Abstraction**: `Pipeline` patterns + A2A protocol

**Purpose**: Coordinate multiple agents for complex tasks using semantic capability matching.

```python
from kaizen.orchestration.pipeline import Pipeline

# 9 composable pipeline patterns
pipeline = Pipeline.sequential([agent1, agent2, agent3])
pipeline = Pipeline.parallel([agent1, agent2, agent3])
pipeline = Pipeline.router(agents, routing_strategy="semantic")
pipeline = Pipeline.ensemble(agents, synthesizer=coordinator)
pipeline = Pipeline.supervisor_worker(supervisor, workers)
pipeline = Pipeline.blackboard(agents, controller)
pipeline = Pipeline.consensus(agents)
pipeline = Pipeline.debate(agents, judge)
pipeline = Pipeline.handoff(agents)

# A2A semantic matching (no hardcoded if/else!)
result = pipeline.run(task="Analyze sales data and create report")
# Automatically routes to best-matched agents based on capabilities
```

**Coordination Patterns**:

| Pattern | Use Case | A2A Support |
|---------|----------|-------------|
| **Supervisor-Worker** | Task decomposition with central coordination | Yes |
| **Router** | Intelligent routing to best agent | Yes |
| **Ensemble** | Multi-perspective with synthesis | Yes |
| **Blackboard** | Controller-driven iterative solving | Yes |
| **Sequential** | Linear agent chain | No |
| **Parallel** | Concurrent execution | No |
| **Consensus** | Voting-based decisions | No |
| **Debate** | Adversarial reasoning | No |
| **Handoff** | Tier escalation | No |

**A2A Protocol**:
```python
from kaizen.nodes.ai.a2a import A2AAgentCard, Capability

# Every agent can generate an A2A capability card
card = agent.to_a2a_card()

# Semantic matching for task routing
score = card.calculate_match_score(["analyze data", "create visualization"])
# Returns 0.0-1.0 match score based on capabilities
```

**Scaling Tiers**:
- **< 10 agents**: Basic pipeline patterns
- **10-100 agents**: `OrchestrationRuntime` (single process)
- **100+ agents**: `AgentRegistry` (distributed, multi-node)

---

### Layer 5: Journey Orchestration (User Flow) — STABLE (v0.9.0)

**Question Answered**: "How does the user flow through the experience?"

**Key Abstraction**: `Journey` + `Pathway` + `Transition`

**Purpose**: Orchestrate user journeys across multiple turns and pathways with intent-driven transitions.

> **Status**: This layer is fully implemented with 351 tests covering all components.

```python
from kaizen.journey import Journey, Pathway, Transition, IntentTrigger

class HealthcareReferralJourney(Journey):
    """Healthcare referral booking journey."""

    __entry_pathway__ = "intake"

    class IntakePath(Pathway):
        __signature__ = IntakeSignature
        __agents__ = ["document_processor", "verification_agent"]
        __pipeline__ = "sequential"
        __next__ = "booking"

    class BookingPath(Pathway):
        __signature__ = BookingSignature
        __agents__ = ["slot_finder", "doctor_matcher"]
        __pipeline__ = "parallel"
        __accumulate__ = ["rejected_doctors", "preferences"]
        __next__ = "confirmation"

    class FAQPath(Pathway):
        __signature__ = FAQSignature
        __agents__ = ["rag_agent"]
        __return_behavior__ = ReturnToPrevious()

    __transitions__ = [
        Transition(
            trigger=IntentTrigger(patterns=["question", "help", "what is"]),
            from_pathway="*",
            to_pathway="faq"
        ),
        Transition(
            trigger=IntentTrigger(patterns=["different doctor", "change"]),
            from_pathway="booking",
            to_pathway="booking",
            context_update={"rejected_doctors": "append:selected_doctor"}
        ),
    ]
```

**Key Distinction from Layer 4**:

| Aspect | Layer 4: Multi-Agent Orchestration | Layer 5: Journey Orchestration |
|--------|-----------------------------------|-------------------------------|
| **Scope** | Single complex task | Entire user session |
| **Trigger** | Task decomposition | User intent |
| **Duration** | One execution | Multiple turns/sessions |
| **State** | Shared memory for task | Journey context across pathways |
| **Flow** | Agent coordination patterns | User pathway transitions |

**Components**:
- `Journey` - Declarative journey definition class (metaclass-based)
- `Pathway` - A phase in the user journey with agents
- `Transition` - Rules for switching between pathways
- `IntentTrigger` - LLM-powered intent detection for transitions
- `ConditionTrigger` - Context-condition based transitions
- `PathwayManager` - Runtime pathway state management
- `ContextAccumulator` - Cross-pathway context persistence with merge strategies
- `JourneyStateManager` - Session persistence (Memory, DataFlow backends)
- `ReturnToPrevious` / `ReturnToSpecific` - Return behaviors
- `JourneyNexusAdapter` - Nexus deployment integration

---

## Cross-Cutting Concerns

### Memory (3-Tier Hierarchical Storage) — STABLE

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY SYSTEM                             │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  HOT TIER   │  │  WARM TIER  │  │     COLD TIER       │  │
│  │  < 1ms      │  │  < 10ms     │  │     < 100ms         │  │
│  │  In-memory  │  │  Local DB   │  │  Remote storage     │  │
│  │  LRU cache  │  │  SQLite     │  │  PostgreSQL/S3      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                              │
│  SharedMemoryPool (multi-agent) │ PersistentBuffer (session) │
└─────────────────────────────────────────────────────────────┘
```

**Key Classes**:
- `kaizen.memory.tiers` - Tier system (Hot/Warm/Cold)
- `kaizen.memory.shared_memory.SharedMemoryPool` - Multi-agent coordination
- `kaizen.memory.persistent_buffer.PersistentBufferMemory` - Session persistence
- `kaizen.memory.backends.DataFlowBackend` - DataFlow database backend

### Trust (Enterprise Agent Trust Protocol - EATP) — STABLE (v0.8.0+)

```python
from kaizen.trust import TrustedAgent, SecureChannel, TrustLineageChain

# Cryptographic trust chains for AI agents
agent = TrustedAgent(config, signature, trust_config)
channel = SecureChannel(agent1, agent2)
chain = TrustLineageChain()
```

**Key Classes**:
- `kaizen.trust.TrustedAgent` - BaseAgent with trust verification
- `kaizen.trust.SecureChannel` - End-to-end encrypted messaging
- `kaizen.trust.TrustLineageChain` - Cryptographic trust chains
- `kaizen.trust.A2AService` - HTTP service for cross-organization trust

### Tools (MCP Integration) — STABLE

```python
# 12 builtin tools via MCP
agent = BaseAgent(
    config=config,
    signature=signature,
    tools="all"  # or custom_mcp_servers=[...]
)

# Discover and execute tools
tools = await agent.discover_tools(category="file")
result = await agent.execute_tool("read_file", {"path": "data.txt"})
```

**Tool Categories**:
- **File (5)**: read_file, write_file, delete_file, list_directory, file_exists
- **HTTP (4)**: http_get, http_post, http_put, http_delete
- **Bash (1)**: bash_command
- **Web (2)**: fetch_url, extract_links

### Observability (Hooks System) — STABLE

```python
from kaizen.core.autonomy.hooks import HookManager, HookEvent

# Event-driven observability
hook_manager = HookManager()
hook_manager.register(HookEvent.POST_AGENT_RUN, my_hook)
```

**Key Classes**:
- `kaizen.core.autonomy.hooks.HookManager` - Hook registration and dispatch
- `kaizen.core.autonomy.hooks.HookEvent` - Event types (PRE/POST events)
- `kaizen.core.autonomy.hooks.security` - RBAC, isolation, resource limits

---

## Developer Decision Guide

**"Which layer should I start at?"**

| Your Need | Start At | Key Class | Example | Status |
|-----------|----------|-----------|---------|--------|
| Simple Q&A bot | Layer 3 | `SimpleQAAgent` | `agent.ask("question")` | STABLE |
| Custom I/O contract | Layer 2 | `Signature` | Define `InputField`/`OutputField` with `__intent__` | STABLE |
| Multi-agent collaboration | Layer 4 | `Pipeline` | `Pipeline.ensemble([...])` | STABLE |
| User journey with pathways | Layer 5 | `Journey` | Define `Pathway` classes with transitions | STABLE |
| Enterprise security | Cross-cutting | `TrustedAgent` | EATP trust chains | STABLE |

---

## Module Structure

```
kaizen/
├── __init__.py              # Framework entry point (v0.8.2)
├── core/                    # Layer 2-3: BaseAgent, signatures
│   ├── base_agent.py        # BaseAgent with A2A, memory, tools
│   ├── autonomy/            # 6 subsystems
│   │   ├── hooks/           # Event-driven observability
│   │   ├── state/           # Checkpoint/resume/fork
│   │   ├── interrupts/      # Graceful shutdown
│   │   ├── permissions/     # Authorization
│   │   ├── control/         # Bidirectional protocol
│   │   └── observability/   # Metrics, tracing
│   └── structured_output.py # OpenAI Structured Outputs
├── signatures/              # Layer 2: Signature system
│   ├── core.py              # Signature, InputField, OutputField, SignatureMeta
│   ├── enterprise.py        # Enterprise extensions
│   └── multi_modal.py       # Multi-modal field types
├── agents/                  # Layer 3: 22+ specialized agents
│   ├── specialized/         # SimpleQA, ChainOfThought, Planning, PEV, ToT, etc.
│   ├── multi_modal/         # Vision, Transcription, MultiModal
│   └── autonomous/          # ReAct, RAGResearch, BaseAutonomous
├── orchestration/           # Layer 4: Multi-agent coordination
│   ├── pipeline.py          # 9 pipeline patterns
│   ├── patterns/            # SupervisorWorker, Consensus, Debate, Blackboard
│   ├── runtime.py           # OrchestrationRuntime (10-100 agents)
│   └── registry.py          # AgentRegistry (100+ agents, distributed)
├── journey/                 # Layer 5: Journey orchestration [STABLE]
│   ├── __init__.py          # Public exports
│   ├── core.py              # Journey, Pathway, metaclasses
│   ├── transitions.py       # Transition, IntentTrigger, ConditionTrigger
│   ├── intent.py            # IntentDetector, caching
│   ├── manager.py           # PathwayManager
│   ├── context.py           # ContextAccumulator, MergeStrategy
│   ├── state.py             # JourneyStateManager, backends
│   ├── nexus.py             # JourneyNexusAdapter
│   ├── behaviors.py         # ReturnToPrevious, ReturnToSpecific
│   ├── models.py            # DataFlow models
│   └── errors.py            # Journey exceptions
├── memory/                  # Cross-cutting: 3-tier storage
│   ├── tiers.py             # Hot/Warm/Cold tier system
│   ├── shared_memory.py     # SharedMemoryPool
│   ├── persistent_buffer.py # PersistentBufferMemory
│   └── backends/            # DataFlowBackend, etc.
├── trust/                   # Cross-cutting: EATP (v0.8.0+)
│   ├── trusted_agent.py     # TrustedAgent
│   ├── messaging/channel.py # SecureChannel
│   └── chain.py             # TrustLineageChain
├── nodes/                   # AI nodes
│   └── ai/a2a.py            # A2AAgentCard, Capability
├── mcp/                     # MCP integration
│   └── builtin_server/      # 12 builtin tools (module)
├── providers/               # LLM providers (9 supported)
└── monitoring/              # Metrics, alerts, analytics
```

---

## Summary

Kaizen provides a **clear, layered approach** to building AI agents:

| Layer | Name | Status | Purpose |
|-------|------|--------|---------|
| **1** | Foundation | STABLE | Enterprise-grade Kailash SDK workflows |
| **2** | Signature | STABLE | Type-safe contracts with intent/guidelines |
| **3** | Agent | STABLE | 22+ production-ready agents |
| **4** | Orchestration | STABLE | Multi-agent coordination with A2A |
| **5** | Journey | STABLE | User flow with intent-driven pathways (351 tests) |

**Cross-cutting concerns** (Memory, Trust, Tools, Observability) integrate at every layer.

> **The Kaizen Philosophy**: "Each layer builds on the previous, enabling developers to start simple and scale to enterprise complexity without rewriting code."

---

## Reference Implementation

The Healthcare Referral Journey example demonstrates all Layer 5 features:

```
apps/kailash-kaizen/examples/journey/healthcare_referral/
├── journey.py          # 5 pathways with transitions
├── signatures/         # 5 signatures with __intent__, __guidelines__
├── agents/             # 5 agents
└── tests/              # Unit, Integration, E2E tests
```

Run the demo:
```bash
cd apps/kailash-kaizen
python -m examples.journey.healthcare_referral.main --mode demo
```
