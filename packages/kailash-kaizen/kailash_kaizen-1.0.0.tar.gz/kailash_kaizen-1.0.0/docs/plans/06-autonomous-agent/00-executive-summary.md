# Coursewright AI Architecture: Executive Summary

**Document Status:** Architecture Specification for Kaizen Development Team
**Version:** 2.0.0
**Date:** 2026-01-21

---

## Purpose

This document series provides comprehensive architectural analysis and specifications for building the Coursewright AI Assistant platform. The platform must deliver Claude Code-like autonomous capabilities while supporting:

1. **Multiple execution modes** (single-turn, multi-turn, autonomous)
2. **Multiple LLM backends** (via Kaizen Native runtime; external runtimes use their native models)
3. **Multiple autonomous agent runtimes** (Claude Code, OpenAI Codex, Gemini CLI, Kaizen Native)
4. **Proper memory integration** as a cross-cutting concern
5. **Developer-friendly UX** that "flows" naturally

---

## Key Architectural Decisions

### 1. Agent Capability Classification

**Decision: Configuration-Driven Strategy Pattern with Capability Composition**

We explicitly **reject class hierarchy** for agent capabilities because:
- Capability combinations would create 48+ classes (3 modes × 4 memory × 4 tool levels)
- Runtime switching between modes would require object replacement
- Memory and tools are orthogonal to execution mode

**The Three Orthogonal Axes:**

| Axis | Values | Description |
|------|--------|-------------|
| **Execution Mode** | single, multi, autonomous | How agent processes requests |
| **Memory Depth** | stateless, session, persistent, learning | State persistence level |
| **Tool Access** | none, read-only, constrained, full | External capability level |

**See:** [02-agent-capability-taxonomy.md](./02-agent-capability-taxonomy.md)

### 2. Runtime Abstraction Layer

**Decision: First-Class Runtime Abstraction**

Claude Code is just ONE autonomous agent runtime. The architecture must abstract over:

| Runtime | Backend | Key Capability | Model Constraint |
|---------|---------|---------------|------------------|
| **Claude Code** | Claude SDK | Native file/bash tools, MCP | Claude only (sonnet/opus/haiku) |
| **OpenAI Codex** | Assistant API | Code Interpreter, threads | OpenAI only |
| **Gemini CLI** | Vertex AI | Google integration | Gemini only |
| **Kaizen Native** | Local | Full control, any LLM | **Any provider** ✅ |

**RuntimeAdapter Interface:**
```python
class RuntimeAdapter(ABC):
    @property
    def capabilities(self) -> RuntimeCapabilities: ...
    async def execute(self, context: ExecutionContext) -> ExecutionResult: ...
    async def stream(self, context: ExecutionContext) -> AsyncIterator[str]: ...
    def map_tools(self, kaizen_tools: list) -> list: ...
```

**See:** [03-runtime-abstraction-layer.md](./03-runtime-abstraction-layer.md)

### 3. Multi-LLM Routing

**Decision: LLM Router with Task-Based Routing**

> ⚠️ **Critical Clarification: Claude Code SDK Model Limitations**
>
> Investigation of the Claude Agent SDK (`claude-agent-sdk-python`) reveals that **Claude Code is tied to Claude models specifically**:
> - `AgentDefinition.model` only accepts `Literal["sonnet", "opus", "haiku", "inherit"]`
> - The SDK wraps `@anthropic-ai/claude-code` npm package (Anthropic's proprietary CLI)
> - No LLM provider abstraction exists within Claude Code itself
>
> **Implication:** Multi-LLM support comes from the **Runtime Abstraction Layer**, not from Claude Code. When using `ClaudeCodeAdapter`, you are locked to Claude models. For true multi-LLM flexibility, use `LocalKaizenAdapter`.

**Runtime-to-Model Mapping:**

| Runtime | Available Models | Multi-LLM? |
|---------|-----------------|------------|
| **Claude Code** | Claude only (sonnet/opus/haiku) | ❌ No |
| **OpenAI Codex** | OpenAI only (GPT-4, etc.) | ❌ No |
| **Gemini CLI** | Gemini only | ❌ No |
| **Kaizen Native** | Any LLM provider | ✅ Yes |

**Multi-LLM Strategy:**
- Use `LocalKaizenAdapter` (Kaizen Native) for multi-LLM routing
- External runtimes (Claude Code, Codex, Gemini CLI) use their native models
- LLM Router operates at Kaizen Native level, not within external runtimes

**Routing Strategies (Kaizen Native only):**
- `task_complexity`: Analyze task and route to appropriate model
- `cost_optimized`: Minimize cost while meeting requirements
- `latency_optimized`: Minimize response time
- `capability_match`: Route by required capabilities

**See:** [04-multi-llm-routing.md](./04-multi-llm-routing.md)

### 4. Memory Integration

**Decision: Memory as Cross-Cutting Concern with Hierarchical Storage**

Memory is **NOT** tied to execution strategy. Instead:

| Tier | Latency | Scope | Storage |
|------|---------|-------|---------|
| **Hot** | <1ms | Current messages | In-memory buffer |
| **Warm** | 10-50ms | Session/persistent | Database |
| **Cold** | 100ms+ | Archival | Object storage |

Memory integrates at agent level, not execution strategy level.

**See:** [05-memory-integration.md](./05-memory-integration.md)

### 5. Developer UX

**Decision: Progressive Disclosure API**

```python
# Level 1: Dead simple (2 lines)
agent = Agent(model="gpt-4")
result = agent.run("What is IRP?")

# Level 2: Configure execution mode
agent = Agent(model="gpt-4", execution_mode="autonomous", max_cycles=50)

# Level 3: Select runtime
agent = Agent(model="gpt-4", runtime="claude_code")

# Level 4: Multi-LLM routing
agent = Agent(model="gpt-4", llm_routing={"code": "gpt-4", "simple": "gpt-3.5"})

# Level 5: Expert configuration
agent = Agent(memory=custom_memory, runtime=custom_runtime, llm_router=custom_router)
```

**See:** [06-developer-ux-guide.md](./06-developer-ux-guide.md)

---

## Document Index

| Document | Description | Status |
|----------|-------------|--------|
| [00-executive-summary.md](./00-executive-summary.md) | This document | ✅ Complete |
| [01-kaizen-claude-sdk-integration.md](./01-kaizen-claude-sdk-integration.md) | Claude Code wrapping via Kaizen | ✅ Complete |
| [02-agent-capability-taxonomy.md](./02-agent-capability-taxonomy.md) | Agent classification and patterns | ✅ Complete |
| [03-runtime-abstraction-layer.md](./03-runtime-abstraction-layer.md) | Multi-runtime abstraction | ✅ Complete |
| [04-multi-llm-routing.md](./04-multi-llm-routing.md) | LLM routing architecture | ✅ Complete |
| [05-memory-integration.md](./05-memory-integration.md) | Memory system design | ✅ Complete |
| [06-developer-ux-guide.md](./06-developer-ux-guide.md) | Developer experience patterns | ✅ Complete |
| [07-native-kaizen-agent-design.md](./07-native-kaizen-agent-design.md) | Native Kaizen autonomous agent | ✅ Complete |

---

## Implementation Priorities

> **Strategy: Wrappers First, Then Native**
>
> External runtime wrappers (ClaudeCodeAdapter, OpenAICodexAdapter) serve as **baselines** for understanding autonomous execution patterns. Once validated, we build the native LocalKaizenAdapter using learnings from the wrappers.

### Phase 1: Core Agent Infrastructure (Week 1-2)
| Component | Effort | Priority |
|-----------|--------|----------|
| Unified Agent class | Medium | P0 |
| AgentConfig dataclass | Low | P0 |
| ExecutionStrategy interface | Medium | P0 |
| Single/multi-turn execution | Low | P0 |

### Phase 2: Wrapper Runtimes (Week 3-4) — BASELINE
| Component | Effort | Priority | Notes |
|-----------|--------|----------|-------|
| RuntimeAdapter interface | Medium | P0 | Abstract base for all adapters |
| **ClaudeCodeAdapter** | High | **P0** | Primary baseline (Claude models only) |
| **OpenAICodexAdapter** | High | P1 | Secondary baseline (OpenAI models only) |
| RuntimeSelector | Medium | P1 | Choose adapter based on config |

### Phase 3: Native Tool System (Week 5-6)
| Component | Effort | Priority | Notes |
|-----------|--------|----------|-------|
| KaizenFileTools | Medium | P0 | Read, Write, Edit, Glob, Grep |
| KaizenBashTools | Medium | P0 | Sandboxed bash execution |
| KaizenSearchTools | Medium | P1 | WebFetch, WebSearch |
| KaizenToolRegistry | Low | P0 | Tool discovery and validation |

### Phase 4: Native Autonomous Agent (Week 7-8)
| Component | Effort | Priority | Notes |
|-----------|--------|----------|-------|
| **LocalKaizenAdapter** | High | **P0** | Multi-LLM autonomous execution |
| AutonomousExecutionStrategy | High | P0 | Think-Act-Observe-Decide loop |
| ExecutionState management | Medium | P0 | Full state tracking |
| Checkpoint/resume | Medium | P1 | StateManager integration |

### Phase 5: Multi-LLM & Memory (Week 9-10)
| Component | Effort | Priority |
|-----------|--------|----------|
| LLMRouter | Medium | P1 |
| HierarchicalMemoryProvider | High | P1 |
| Memory context building | Medium | P1 |
| Learning memory integration | Medium | P2 |

**See:** [07-native-kaizen-agent-design.md](./07-native-kaizen-agent-design.md) for detailed native agent architecture.

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Runtime adapter incompatibility | Medium | High | Extensive capability negotiation, graceful fallback |
| Memory context overflow | Medium | Medium | Token-aware context building with summarization |
| LLM routing inconsistency | Low | Medium | Explicit routing rules with default fallback |
| Tool mapping errors | Medium | High | Comprehensive tool mapping tests |
| Autonomous loop non-convergence | Medium | High | Cycle limits, timeouts, checkpointing |

---

## Success Criteria

1. **Unified Interface**: Single `Agent` class supports all execution modes
2. **Runtime Agnostic**: Same code works across Claude Code, Codex, Kaizen native
3. **Multi-LLM**: Task-based routing works transparently
4. **Memory Integrated**: Hierarchical memory works across all modes
5. **Developer Friendly**: Progressive disclosure from 2-line quickstart to expert config

---

## Related Documents

- **Claude Code Execution Model**: [docs/architecture/claude-code-kaizen-integration-analysis.md](../../architecture/claude-code-kaizen-integration-analysis.md)
- **Coursewright Overview**: [docs/agentic/README.md](../README.md)
- **Implementation Plan**: [docs/agentic/02-plans/02-implementation-plan.md](../02-plans/02-implementation-plan.md)

---

**Prepared For:** Kaizen Development Team
**Review Status:** Ready for Implementation
