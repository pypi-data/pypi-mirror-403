# Agentic OS Requirements Mapping to Kaizen

## Executive Summary

This document maps the requirements of the Agentic OS platform to what Kaizen must provide. Agentic OS is an enterprise operating system where AI agents replace traditional applications, requiring deep integration with Kaizen for agent execution, trust verification, streaming, and session management.

**Key Integration Points:**
- AgentExecutionService (primary execution bridge)
- SSE streaming with specific event types
- Agent discovery and access control
- Trust/EATP verification at every action
- Session and cost tracking

---

## 1. AgentExecutionService Requirements

### 1.1 Core Execution Interface

**Agentic OS Requirement:**
```python
from agentic_os.services import AgentExecutionService

service = AgentExecutionService()

# Execute objective with streaming
async for event in service.execute_objective(
    user_id="user-123",
    objective="Analyze the codebase",
    request_id="request-456",
    organization_id="org-789",
    agent_id="agent-001",
    trust_chain_id="trust-abc",
):
    print(event)
```

**What Kaizen Must Provide:**

| Requirement | Kaizen Component | Status | Gap |
|-------------|------------------|--------|-----|
| Async execution with streaming | `Agent.stream()` | Partial | Needs rich event types |
| Session management | `Agent._session_id` | Partial | Needs persistence |
| Cost tracking | `kaizen.cost.tracker.CostTracker` | Exists | Needs integration |
| Trust chain integration | `kaizen.trust.operations.TrustOperations` | Exists | Needs execution wrapper |
| Tool invocation tracking | `AgentResult.tool_calls` | Exists | Needs real-time events |
| Subagent spawning | `kaizen.orchestration.registry.AgentRegistry` | Exists | Needs spawn events |
| Configuration overrides | `AgentConfig` | Exists | Needs runtime override |

### 1.2 Required Kaizen API

**New Unified Execution API:**
```python
from kaizen.api import Agent
from kaizen.execution import StreamingExecutor

class StreamingExecutor:
    """
    Kaizen MUST provide this interface for Agentic OS integration.
    """

    async def execute_with_events(
        self,
        agent: Agent,
        task: str,
        *,
        trust_chain_id: Optional[str] = None,
        session_id: Optional[str] = None,
        on_event: Callable[[ExecutionEvent], None] = None,
    ) -> AsyncIterator[ExecutionEvent]:
        """
        Execute agent task yielding typed events.

        Events must include:
        - started (execution_id, agent_id, session_id)
        - thinking (content)
        - message (role, content)
        - tool_use (tool, input)
        - tool_result (tool, output, error)
        - subagent_spawn (subagent_id, subagent_name, task)
        - cost_update (tokens, cost_cents)
        - completed (execution_id, total_tokens, total_cost_cents)
        - error (execution_id, message)
        """
        pass
```

---

## 2. Streaming Event Types

### 2.1 Required Event Types

Agentic OS expects these specific SSE event types from Kaizen:

| Event Type | Fields | When Emitted | Kaizen Source |
|------------|--------|--------------|---------------|
| `started` | `execution_id`, `agent_id`, `session_id`, `agent_name` | Execution begins | New |
| `thinking` | `content` | Agent reasoning | `Agent._execute_autonomous` |
| `message` | `role`, `content` | Agent response | `AgentResult.text` |
| `tool_use` | `tool`, `input` | Before tool call | `on_progress` callback |
| `tool_result` | `tool`, `output`, `error` | After tool call | `on_progress` callback |
| `subagent_spawn` | `subagent_id`, `subagent_name`, `task` | Delegation occurs | **NEW REQUIRED** |
| `cost_update` | `tokens`, `cost_cents` | After each LLM call | `CostTracker` |
| `progress` | `percentage`, `step`, `details` | During execution | **NEW REQUIRED** |
| `completed` | `execution_id`, `total_tokens`, `total_cost_cents` | Execution ends | New |
| `error` | `execution_id`, `message` | On failure | `AgentResult.error` |

### 2.2 Critical: `subagent_spawn` Event

**This is the most critical gap.** Agentic OS needs to track when agents delegate to subagents for:
- Progress visualization (TaskGraph)
- Cost attribution
- Trust chain propagation
- Audit trail

**Kaizen Must Provide:**
```python
@dataclass
class SubagentSpawnEvent:
    """Event emitted when agent delegates to subagent."""
    subagent_id: str           # Unique ID for this subagent instance
    subagent_name: str         # Human-readable name
    task: str                  # Delegated task description
    parent_agent_id: str       # Parent agent
    trust_chain_id: str        # Propagated trust chain
    capabilities: List[str]    # Delegated capabilities
    timestamp: str             # ISO 8601
```

**Implementation Location:**
- `kaizen/orchestration/runtime.py` - OrchestrationRuntime
- `kaizen/trust/operations.py` - delegate() must emit event
- `kaizen/agents/autonomous/base.py` - When spawning subagents

---

## 3. Agent Discovery Requirements

### 3.1 Accessible Agents Query

**Agentic OS Requirement:**
```python
# Get agents user can invoke
agents = await access_service.get_accessible_agents(
    user_id="user-123",
    organization_id="org-789",
)

# Each agent includes _access metadata
{
    "id": "agent-456",
    "name": "Financial Agent",
    "capabilities": ["analyze_data", "generate_reports"],
    "_access": {
        "permission_level": "execute",
        "constraints": {"max_daily_invocations": 100}
    }
}
```

**What Kaizen Must Provide:**

| Requirement | Kaizen Component | Status | Gap |
|-------------|------------------|--------|-----|
| Agent registry | `AgentRegistry` | Exists | Needs user filtering |
| Capability indexing | `capability_index` | Exists | Works |
| A2A card metadata | `A2AAgentCard` | Exists | Works |
| Permission filtering | N/A | **Missing** | Needs RBAC integration |
| Constraint metadata | N/A | **Missing** | Needs from trust chain |

### 3.2 Required Kaizen Extension

```python
class AgentRegistry:
    """Existing registry needs these additions."""

    async def find_agents_for_user(
        self,
        user_id: str,
        organization_id: str,
        trust_ops: TrustOperations,
    ) -> List[AgentWithAccess]:
        """
        Return agents user can invoke with access metadata.

        Must check:
        1. User's trust delegation chain
        2. Organization's agent permissions
        3. Capability constraints
        """
        pass
```

---

## 4. Skill Invocation Requirements

### 4.1 Agent as Skill Pattern

Agentic OS treats registered agents as "skills" that can be invoked:

```python
# User selects an agent/skill
await service.execute_objective(
    agent_id="financial-analyst",  # This is a "skill"
    objective="Analyze Q4 revenue",
)
```

**What Kaizen Must Provide:**

| Requirement | Kaizen Component | Status |
|-------------|------------------|--------|
| Agent instantiation by ID | `AgentRegistry.get_agent()` | Exists |
| Agent execution | `Agent.run()` | Exists |
| Capability validation | `TrustOperations.verify()` | Exists |
| Configuration overrides | `AgentConfig` | Exists |

### 4.2 Skill Metadata

Agentic OS needs this agent metadata for UI:

```python
@dataclass
class AgentSkillMetadata:
    """Metadata Kaizen must provide per agent."""
    id: str
    name: str
    description: str
    capabilities: List[str]
    suggested_prompts: List[str]  # Example objectives
    input_schema: Optional[Dict]  # Expected input format
    output_types: List[str]       # What it produces
    avg_execution_time_seconds: float
    avg_cost_cents: float
```

**Implementation:** Add to `A2AAgentCard` or create new `AgentSkillCard`.

---

## 5. Trust/EATP Integration Requirements

### 5.1 Trust Verification Flow

Agentic OS requires trust verification at multiple points:

```
User submits objective
    |
    v
[1] verify_execution_allowed(user, agent, objective)
    |
    v
Agent starts execution
    |
    v
[2] For each tool: verify_tool_use(agent, tool, input)
    |
    v
[3] For each subagent: verify_delegation(agent, subagent, capabilities)
    |
    v
[4] create_audit_anchor() for each action
    |
    v
Execution completes
```

### 5.2 Required Trust Operations

| Operation | Kaizen Component | Status | Agentic OS Use |
|-----------|------------------|--------|----------------|
| `verify_execution_allowed` | `TrustOperations.verify()` | Exists | Pre-execution check |
| `verify_tool_use` | `TrustOperations.verify()` | Exists | Tool permission check |
| `verify_delegation` | Custom needed | Partial | Subagent permission |
| `create_audit_anchor` | `TrustOperations.audit()` | Exists | Audit trail |
| `establish_trust_chain` | `TrustOperations.establish()` | Exists | New session |
| `delegate_trust` | `TrustOperations.delegate()` | Exists | Subagent trust |

### 5.3 Trust Postures

Agentic OS needs trust posture from verification:

```python
class TrustPosture(Enum):
    FULL_AUTONOMY = "full_autonomy"      # Act freely
    SUPERVISED = "supervised"            # Log all actions
    HUMAN_DECIDES = "human_decides"      # Require approval
    BLOCKED = "blocked"                  # Deny action
```

**Kaizen Mapping:**
- `FULL_AUTONOMY` = `VerificationResult.valid=True` with no constraints
- `SUPERVISED` = `VerificationResult.valid=True` with `audit_required` constraint
- `HUMAN_DECIDES` = Needs human-in-loop integration
- `BLOCKED` = `VerificationResult.valid=False`

### 5.4 Human Origin Tracking

**Critical EATP Requirement:** Every action must trace back to human authorization.

```python
# Kaizen already has this:
@dataclass
class HumanOrigin:
    human_id: str           # alice@corp.com
    session_id: str         # Original session
    authorized_at: datetime
    authentication_method: str
```

Agentic OS needs Kaizen to:
1. Accept `HumanOrigin` when starting execution
2. Propagate through all delegations
3. Include in all audit anchors

---

## 6. Session Management Requirements

### 6.1 Work Session Lifecycle

```
User claims task
    |
    v
start_session(request_id, user_id, agent_id)
    |
    v
[Execution with streaming events]
    |
    v
add_message(), add_tool_invocation(), update_metrics()
    |
    v
end_session(status, final_tokens, final_cost)
```

### 6.2 Session State Requirements

| Field | Kaizen Source | Status |
|-------|---------------|--------|
| `session_id` | `Agent._session_id` | Exists |
| `agent_id` | `Agent.model` or custom | Exists |
| `messages` | Memory provider | Exists |
| `tool_invocations` | `AgentResult.tool_calls` | Exists |
| `tokens_used` | `CostTracker` | Exists |
| `cost_usd_cents` | `CostTracker` | Exists |
| `subagent_calls` | **NEW** | Missing |
| `trust_chain_id` | `TrustOperations` | Exists |

### 6.3 Required Session API

```python
class KaizenSessionManager:
    """Kaizen must provide for Agentic OS integration."""

    async def start_session(
        self,
        agent: Agent,
        trust_chain_id: str,
        metadata: Dict[str, Any],
    ) -> str:
        """Start tracked session, return session_id."""
        pass

    async def get_session_state(
        self,
        session_id: str,
    ) -> SessionState:
        """Get current session state."""
        pass

    async def end_session(
        self,
        session_id: str,
        status: str,
    ) -> SessionSummary:
        """End session, return summary with totals."""
        pass
```

---

## 7. Cost Tracking Requirements

### 7.1 Real-Time Cost Updates

Agentic OS needs cost updates during execution:

```python
# Event format
{"type": "cost_update", "tokens": 1500, "cost_cents": 45}
```

### 7.2 Required Kaizen Integration

```python
from kaizen.cost.tracker import CostTracker

class StreamingCostTracker(CostTracker):
    """Extended for streaming cost events."""

    def __init__(self, on_update: Callable[[int, int], None]):
        self.on_update = on_update

    def track_usage(self, tokens: int, cost_cents: int):
        super().track_usage(tokens, cost_cents)
        # Emit real-time update
        self.on_update(self.total_tokens, self.total_cost_cents)
```

---

## 8. Gap Analysis Summary

### 8.1 Critical Gaps (Must Fix)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| `subagent_spawn` event | Cannot track delegations | Medium | P0 |
| Streaming event types | Cannot build UI | Medium | P0 |
| Session persistence | Cannot resume sessions | Medium | P0 |
| User-filtered agent discovery | Cannot show accessible agents | Low | P0 |

### 8.2 Important Gaps (Should Fix)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Progress events | Limited progress UI | Low | P1 |
| Skill metadata schema | Incomplete agent info | Low | P1 |
| Real-time cost streaming | Delayed cost display | Low | P1 |
| Trust posture mapping | Manual posture handling | Low | P1 |

### 8.3 Nice-to-Have

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Estimated completion time | Better UX | Medium | P2 |
| Semantic capability search | Better discovery | High | P2 |

---

## 9. Implementation Recommendations

### 9.1 Phase 1: Core Execution Bridge (Week 1)

1. **Create `StreamingExecutor`** in `kaizen/execution/streaming_executor.py`
   - Wraps `Agent.run()` with event emission
   - Integrates `CostTracker` for real-time updates
   - Emits all required event types

2. **Add `subagent_spawn` event** to:
   - `kaizen/orchestration/runtime.py`
   - `kaizen/trust/operations.py` (in delegate)

3. **Create session persistence** in `kaizen/session/manager.py`
   - Store session state in DataFlow
   - Support resume/pause

### 9.2 Phase 2: Trust Integration (Week 2)

1. **Create `TrustVerificationMiddleware`**
   - Wraps execution with pre/post trust checks
   - Propagates `HumanOrigin` through chain

2. **Add trust posture mapping**
   - Map `VerificationResult` to `TrustPosture`
   - Support human-in-loop for `HUMAN_DECIDES`

### 9.3 Phase 3: Discovery and Access (Week 3)

1. **Extend `AgentRegistry`**
   - Add user-filtered queries
   - Include access metadata

2. **Create `AgentSkillCard`**
   - Standard metadata for UI
   - Suggested prompts, schemas

---

## 10. File Locations

### Agentic OS (Consumer)

```
kaizen-studio/src/agentic_os/services/
  agent_execution_service.py   # Uses Kaizen's StreamingExecutor
  trust_integration.py         # Uses Kaizen's TrustOperations
  sse_formatter.py            # Formats Kaizen events to SSE
```

### Kaizen (Provider) - Required Changes

```
kailash-kaizen/src/kaizen/
  execution/
    streaming_executor.py     # NEW: Event-based execution
    events.py                 # NEW: Event type definitions
  session/
    manager.py                # NEW: Session persistence
    state.py                  # NEW: Session state model
  orchestration/
    registry.py               # EXTEND: User-filtered queries
    runtime.py                # EXTEND: Emit subagent_spawn
  trust/
    operations.py             # EXTEND: Emit events on delegate
    postures.py               # NEW: Trust posture mapping
```

---

## 11. Testing Strategy

### Unit Tests

```python
# Test streaming executor emits all event types
async def test_streaming_executor_events():
    executor = StreamingExecutor()
    events = []
    async for event in executor.execute_with_events(agent, "test"):
        events.append(event)

    event_types = {e.type for e in events}
    assert "started" in event_types
    assert "completed" in event_types or "error" in event_types
```

### Integration Tests

```python
# Test full execution with trust verification
async def test_execution_with_trust():
    trust_ops = TrustOperations(...)
    executor = StreamingExecutor(trust_ops=trust_ops)

    async for event in executor.execute_with_events(
        agent=my_agent,
        task="Analyze data",
        trust_chain_id="chain-123",
    ):
        if event.type == "tool_use":
            # Verify trust was checked
            assert event.trust_verified
```

---

## 12. Success Criteria

Kaizen is ready for Agentic OS when:

1. **Streaming Works**: All 10 event types emit correctly
2. **Subagent Tracking**: `subagent_spawn` events appear for delegations
3. **Trust Integration**: All actions verified against trust chain
4. **Session Persistence**: Sessions survive restart
5. **Cost Tracking**: Real-time cost updates flow to UI
6. **Agent Discovery**: Users see only accessible agents

---

## Appendix A: Event Schema

```python
from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum

class ExecutionEventType(str, Enum):
    STARTED = "started"
    THINKING = "thinking"
    MESSAGE = "message"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    SUBAGENT_SPAWN = "subagent_spawn"
    COST_UPDATE = "cost_update"
    PROGRESS = "progress"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class ExecutionEvent:
    type: ExecutionEventType
    data: Dict[str, Any]
    timestamp: str  # ISO 8601
    execution_id: str
    session_id: str
```

## Appendix B: Trust Verification Points

```
[PRE-EXECUTION]
- verify_execution_allowed(user_id, agent_id, objective)
- establish_trust_chain(agent_id, authority_id, capabilities)

[DURING EXECUTION]
- verify(agent_id, tool_name) before each tool call
- audit(agent_id, tool_name, result) after each tool call
- delegate(delegator_id, delegatee_id, capabilities) for subagents

[POST-EXECUTION]
- audit(agent_id, "objective_complete", summary)
- revoke_delegation() if temporary subagent
```
