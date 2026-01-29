# Integration with Existing Kaizen Components

> **Priority**: P1
> **Effort**: 4 days
> **Files**: `kaizen/journey/__init__.py`, updates to existing modules

## Purpose

Define how Journey Orchestration integrates with existing Kaizen components: Pipeline patterns, Memory system, DataFlow persistence, and Nexus deployment.

## Integration Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         JOURNEY ORCHESTRATION (Layer 5)                          │
│                                                                                  │
│  Journey ──► Pathway ──► Pipeline ──► Agent(s) ──► Signature                    │
│     │           │            │            │             │                        │
│     │           │            │            │             ▼                        │
│     │           │            │            │    Layer 2: Signature               │
│     │           │            │            │    (__intent__, __guidelines__)     │
│     │           │            │            │                                      │
│     │           │            │            ▼                                      │
│     │           │            │     Layer 3: BaseAgent                           │
│     │           │            │     (WorkflowGenerator, tools, memory)           │
│     │           │            │                                                   │
│     │           │            ▼                                                   │
│     │           │     Layer 4: Pipeline Patterns                                │
│     │           │     (Sequential, Parallel, Router, Ensemble, etc.)            │
│     │           │                                                                │
│     │           ▼                                                                │
│     │    PathwayManager + ContextAccumulator                                    │
│     │                                                                            │
│     ▼                                                                            │
│  JourneyStateManager ──► DataFlow (persistence)                                 │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
                              Nexus (deployment)
                         API │ CLI │ MCP channels
```

## Requirements

### REQ-INT-001: Signature Integration

Journey pathways consume and produce Signature-defined contracts:

```python
# Pathway uses existing Signature with new enhancements
from kaizen.signatures import Signature, InputField, OutputField

class IntakeSignature(Signature):
    """Gather patient symptoms and preferences."""

    # NEW: Explicit intent (Layer 2 enhancement)
    __intent__ = "Collect comprehensive patient information for referral"

    # NEW: Behavioral guidelines (Layer 2 enhancement)
    __guidelines__ = [
        "Ask about symptoms before demographics",
        "Use empathetic, non-clinical language",
        "Confirm understanding before proceeding"
    ]

    # Existing field definitions
    patient_message: str = InputField(desc="Patient's description")
    symptoms: list = OutputField(desc="Extracted symptoms")
    severity: str = OutputField(desc="Assessed severity level")
    preferences: dict = OutputField(desc="Patient preferences")


# Pathway references the signature
class IntakePath(Pathway):
    __signature__ = IntakeSignature
    __agents__ = ["intake_agent"]
    __accumulate__ = ["symptoms", "preferences"]
    __next__ = "booking"
```

### REQ-INT-002: Pipeline Pattern Integration

Pathways use existing Pipeline patterns for multi-agent coordination:

```python
from kaizen.orchestration.pipeline import Pipeline
from kaizen.journey.core import Pathway

class AnalysisPath(Pathway):
    """Multi-agent analysis pathway."""

    __signature__ = AnalysisSignature
    __agents__ = ["symptom_analyzer", "urgency_classifier", "recommendation_engine"]
    __pipeline__ = "ensemble"  # Uses Pipeline.ensemble() internally

    # Custom pipeline configuration (optional)
    __pipeline_config__ = {
        "discovery_mode": "a2a",
        "top_k": 3,
        "fallback_strategy": "sequential"
    }


# Internal implementation in Pathway._build_pipeline()
def _build_pipeline(self, agents: List[BaseAgent]) -> Pipeline:
    pipeline_type = self._pipeline
    config = getattr(self, "_pipeline_config", {})

    if pipeline_type == "sequential":
        return Pipeline.sequential(agents)

    elif pipeline_type == "parallel":
        return Pipeline.parallel(agents, **config)

    elif pipeline_type == "router":
        return Pipeline.router(
            agents,
            routing_strategy=config.get("routing_strategy", "semantic"),
            **config
        )

    elif pipeline_type == "ensemble":
        synthesizer = config.get("synthesizer")
        return Pipeline.ensemble(
            agents,
            synthesizer=synthesizer,
            discovery_mode=config.get("discovery_mode", "a2a"),
            top_k=config.get("top_k", 3)
        )

    elif pipeline_type == "supervisor_worker":
        supervisor = agents[0] if agents else None
        workers = agents[1:] if len(agents) > 1 else []
        return Pipeline.supervisor_worker(supervisor, workers, **config)

    else:
        raise ValueError(f"Unknown pipeline type: {pipeline_type}")
```

### REQ-INT-003: Memory System Integration

Journey sessions integrate with Kaizen's 3-tier memory system:

```python
from kaizen.memory.tiers import HotMemoryTier, WarmMemoryTier
from kaizen.memory.backends import DataFlowBackend

class PathwayManager:
    """Extended with memory integration."""

    def __init__(self, journey, session_id, config):
        # ... existing init ...

        # Memory integration
        self._hot_memory = HotMemoryTier(
            max_size=config.memory_hot_max_size,
            eviction_policy="lru"
        )
        self._warm_memory = None  # Lazy-init with DataFlow

    def _init_warm_memory(self, db: "DataFlow") -> None:
        """Initialize warm memory tier with DataFlow backend."""
        self._warm_memory = WarmMemoryTier(
            backend=DataFlowBackend(db, model_name="JourneyConversation")
        )

    async def process_message(self, message: str) -> JourneyResponse:
        # Store in hot memory for fast access
        await self._hot_memory.put(
            key=f"{self.session_id}:last_message",
            value={"content": message, "timestamp": datetime.utcnow().isoformat()},
            ttl=self.config.memory_hot_ttl
        )

        # ... rest of processing ...

        # Persist to warm memory after response
        if self._warm_memory:
            await self._warm_memory.put(
                key=f"{self.session_id}:history",
                value=self._session.conversation_history
            )

        return response
```

### REQ-INT-004: DataFlow Persistence Integration

Journey state persists via DataFlow models:

```python
# Journey session model for DataFlow
# File: kaizen/journey/models.py

from dataflow import DataFlow
from typing import Optional

# Initialize DataFlow for Journey module
journey_db = DataFlow(auto_migrate=False)


@journey_db.model
class JourneySession:
    """Persisted journey session."""
    id: str                          # session_id
    journey_class: str               # Fully qualified class name
    current_pathway_id: str          # Current pathway
    pathway_stack: str               # JSON-serialized stack
    conversation_history: str        # JSON-serialized history
    accumulated_context: str         # JSON-serialized context
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@journey_db.model
class JourneyConversation:
    """Individual conversation messages for memory tier."""
    id: str
    session_id: str
    role: str                        # "user" or "assistant"
    content: str
    pathway_id: str
    timestamp: str
    metadata: Optional[str] = None   # JSON-serialized


@journey_db.model
class IntentCache:
    """Cached intent classifications."""
    id: str
    message_hash: str                # Hash of normalized message
    intent: str                      # Detected intent
    confidence: float
    pathway_context: str             # Pathway when detected
    expires_at: str                  # TTL-based expiration
```

```python
# DataFlowStateBackend implementation
# File: kaizen/journey/state.py (updated)

class DataFlowStateBackend(StateBackend):
    """Production DataFlow backend for journey state."""

    def __init__(self, db: "DataFlow"):
        self.db = db
        self._ensure_tables_exist()

    async def _ensure_tables_exist(self):
        """Create tables if not exists (for auto_migrate=False)."""
        await self.db.create_tables_async()

    async def save(self, session_id: str, data: Dict[str, Any]) -> None:
        """Save or update session."""
        import json
        from datetime import datetime

        # Serialize complex fields
        serialized = {
            "id": session_id,
            "journey_class": data.get("journey_class", ""),
            "current_pathway_id": data.get("current_pathway_id", ""),
            "pathway_stack": json.dumps(data.get("pathway_stack", [])),
            "conversation_history": json.dumps(data.get("conversation_history", [])),
            "accumulated_context": json.dumps(data.get("accumulated_context", {})),
        }

        # Use DataFlow Express for fast operations
        existing = await self.db.express.read("JourneySession", session_id)

        if existing:
            await self.db.express.update("JourneySession", session_id, serialized)
        else:
            await self.db.express.create("JourneySession", serialized)

    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session from DataFlow."""
        import json

        record = await self.db.express.read("JourneySession", session_id)
        if not record:
            return None

        return {
            "session_id": record["id"],
            "journey_class": record.get("journey_class", ""),
            "current_pathway_id": record.get("current_pathway_id", ""),
            "pathway_stack": json.loads(record.get("pathway_stack", "[]")),
            "conversation_history": json.loads(record.get("conversation_history", "[]")),
            "accumulated_context": json.loads(record.get("accumulated_context", "{}")),
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at")
        }

    async def delete(self, session_id: str) -> None:
        """Delete session."""
        await self.db.express.delete("JourneySession", session_id)

    async def list_sessions(self) -> list[str]:
        """List all session IDs."""
        records = await self.db.express.list("JourneySession", fields=["id"])
        return [r["id"] for r in records]
```

### REQ-INT-005: Nexus Deployment Integration

Deploy journeys via Nexus multi-channel platform:

```python
from nexus import Nexus
from kaizen.journey import Journey, Pathway
from kaizen.journey.nexus import JourneyNexusAdapter


# Define journey
class BookingJourney(Journey):
    __entry_pathway__ = "intake"

    class IntakePath(Pathway):
        __signature__ = IntakeSignature
        __agents__ = ["intake_agent"]
        __next__ = "booking"

    class BookingPath(Pathway):
        __signature__ = BookingSignature
        __agents__ = ["booking_agent"]


# Create Nexus-compatible adapter
adapter = JourneyNexusAdapter(
    journey_class=BookingJourney,
    agents={
        "intake_agent": intake_agent,
        "booking_agent": booking_agent
    }
)

# Deploy via Nexus
nexus = Nexus(
    title="Healthcare Booking Platform",
    enable_api=True,
    enable_cli=True,
    enable_mcp=True
)

# Register journey endpoints
nexus.register("booking_journey", adapter.to_workflow())

# API: POST /workflows/booking_journey
#   Body: {"session_id": "...", "message": "..."}
# CLI: nexus run booking_journey --session-id=... --message="..."
# MCP: booking_journey tool for AI assistants
```

```python
# File: kaizen/journey/nexus.py

from typing import Any, Dict, Type
from kailash.workflow.builder import WorkflowBuilder
from kaizen.journey import Journey, PathwayManager, JourneyConfig


class JourneyNexusAdapter:
    """Adapt Journey for Nexus deployment."""

    def __init__(
        self,
        journey_class: Type[Journey],
        agents: Dict[str, "BaseAgent"],
        config: JourneyConfig = None
    ):
        self.journey_class = journey_class
        self.agents = agents
        self.config = config or JourneyConfig()
        self._managers: Dict[str, PathwayManager] = {}

    def to_workflow(self) -> WorkflowBuilder:
        """Convert journey to Nexus-compatible workflow."""
        workflow = WorkflowBuilder()

        # Add PythonCode node for journey execution
        workflow.add_node("PythonCodeNode", "journey_executor", {
            "code": self._generate_executor_code(),
            "inputs": ["session_id", "message", "action"],
            "outputs": ["response", "pathway_id", "context"]
        })

        return workflow

    def _generate_executor_code(self) -> str:
        """Generate executor code for PythonCode node."""
        return '''
async def execute(session_id: str, message: str, action: str = "process"):
    from kaizen.journey.nexus import JourneyNexusAdapter

    # Get or create manager
    manager = adapter.get_or_create_manager(session_id)

    if action == "start":
        session = await manager.start_session()
        return {
            "response": "Session started",
            "pathway_id": session.current_pathway_id,
            "context": session.accumulated_context
        }

    elif action == "process":
        response = await manager.process_message(message)
        return {
            "response": response.message,
            "pathway_id": response.pathway_id,
            "context": response.accumulated_context
        }

    elif action == "status":
        session = await manager.get_session_state()
        return {
            "response": "Session active",
            "pathway_id": session.current_pathway_id if session else None,
            "context": session.accumulated_context if session else {}
        }
'''

    def get_or_create_manager(self, session_id: str) -> PathwayManager:
        """Get existing or create new pathway manager."""
        if session_id not in self._managers:
            journey = self.journey_class(session_id, self.config)

            # Register agents
            for agent_id, agent in self.agents.items():
                journey.manager.register_agent(agent_id, agent)

            self._managers[session_id] = journey.manager

        return self._managers[session_id]
```

### REQ-INT-006: BaseAgent Integration

Pathways use BaseAgent instances with automatic signature binding:

```python
from kaizen.core.base_agent import BaseAgent
from kaizen.journey import Pathway, PathwayContext

class Pathway:
    """Extended with BaseAgent integration."""

    async def execute(self, context: PathwayContext) -> PathwayResult:
        """Execute pathway with signature-bound agents."""
        try:
            agents = self._resolve_agents()
            pipeline = self._build_pipeline(agents)

            # Prepare input with signature fields
            inputs = context.to_input_dict()

            # Bind signature to pipeline
            if self.signature:
                # Merge pathway guidelines with signature
                sig = self.signature
                if self._guidelines:
                    sig = sig.with_guidelines(self._guidelines)

                # Pass signature to agents for prompt generation
                for agent in agents:
                    if hasattr(agent, "bind_signature"):
                        agent.bind_signature(sig)

            # Execute pipeline
            result = await pipeline.execute(inputs)

            # Validate outputs against signature
            if self.signature:
                self._validate_outputs(result)

            # Extract accumulated fields
            accumulated = self._extract_accumulated_fields(result)

            return PathwayResult(
                outputs=result,
                accumulated=accumulated,
                next_pathway=self._next,
                is_complete=True
            )

        except Exception as e:
            return PathwayResult(
                outputs={},
                accumulated={},
                next_pathway=None,
                is_complete=False,
                error=str(e)
            )

    def _validate_outputs(self, result: Dict[str, Any]) -> None:
        """Validate outputs against signature contract."""
        if not self.signature:
            return

        missing = []
        for field_name in self.signature._signature_outputs:
            if field_name not in result:
                missing.append(field_name)

        if missing:
            raise ValueError(
                f"Pathway output missing required fields: {missing}"
            )
```

### REQ-INT-007: Hooks System Integration

Journey lifecycle events integrate with Kaizen hooks:

```python
from kaizen.core.autonomy.hooks import HookManager, HookEvent
from kaizen.journey import PathwayManager


# Define Journey-specific hook events
class JourneyHookEvent(str, Enum):
    PRE_SESSION_START = "journey.pre_session_start"
    POST_SESSION_START = "journey.post_session_start"
    PRE_PATHWAY_EXECUTE = "journey.pre_pathway_execute"
    POST_PATHWAY_EXECUTE = "journey.post_pathway_execute"
    PRE_TRANSITION = "journey.pre_transition"
    POST_TRANSITION = "journey.post_transition"
    SESSION_COMPLETE = "journey.session_complete"
    SESSION_ERROR = "journey.session_error"


class PathwayManager:
    """Extended with hooks integration."""

    def __init__(self, journey, session_id, config):
        # ... existing init ...
        self._hook_manager = HookManager()

    def register_hook(
        self,
        event: JourneyHookEvent,
        handler: Callable,
        priority: int = 100
    ) -> None:
        """Register lifecycle hook."""
        self._hook_manager.register(event, handler, priority)

    async def start_session(self, initial_context: Optional[Dict] = None):
        """Start session with hooks."""
        # PRE hook
        await self._hook_manager.trigger(
            JourneyHookEvent.PRE_SESSION_START,
            {
                "session_id": self.session_id,
                "journey_class": type(self.journey).__name__,
                "initial_context": initial_context
            }
        )

        # ... existing session start logic ...

        # POST hook
        await self._hook_manager.trigger(
            JourneyHookEvent.POST_SESSION_START,
            {
                "session_id": self.session_id,
                "entry_pathway": self._session.current_pathway_id,
                "session": self._session
            }
        )

        return self._session

    async def process_message(self, message: str) -> JourneyResponse:
        """Process message with hooks."""
        # PRE pathway execute
        await self._hook_manager.trigger(
            JourneyHookEvent.PRE_PATHWAY_EXECUTE,
            {
                "session_id": self.session_id,
                "pathway_id": self._session.current_pathway_id,
                "message": message
            }
        )

        # ... check transitions ...

        if transition_result.triggered:
            # Transition hooks
            await self._hook_manager.trigger(
                JourneyHookEvent.PRE_TRANSITION,
                {
                    "session_id": self.session_id,
                    "from_pathway": self._session.current_pathway_id,
                    "to_pathway": transition_result.target_pathway,
                    "trigger": transition_result.matched_intent
                }
            )

            await self._switch_pathway(...)

            await self._hook_manager.trigger(
                JourneyHookEvent.POST_TRANSITION,
                {
                    "session_id": self.session_id,
                    "new_pathway": self._session.current_pathway_id
                }
            )

        # ... execute pathway ...

        # POST pathway execute
        await self._hook_manager.trigger(
            JourneyHookEvent.POST_PATHWAY_EXECUTE,
            {
                "session_id": self.session_id,
                "pathway_id": self._session.current_pathway_id,
                "result": pathway_result,
                "response": response
            }
        )

        return response
```

## Public API

```python
# File: kaizen/journey/__init__.py

"""
Kaizen Journey Orchestration - Layer 5

User journey management with declarative pathway definitions,
intent-driven transitions, and cross-pathway context accumulation.
"""

from kaizen.journey.core import (
    Journey,
    JourneyMeta,
    Pathway,
    PathwayMeta,
    JourneyConfig,
    PathwayContext,
    PathwayResult,
)

from kaizen.journey.transitions import (
    Transition,
    TransitionResult,
    BaseTrigger,
    IntentTrigger,
    ConditionTrigger,
    AlwaysTrigger,
)

from kaizen.journey.intent import (
    IntentDetector,
    IntentResult,
    IntentClassificationSignature,
)

from kaizen.journey.manager import (
    PathwayManager,
    JourneySession,
    JourneyResponse,
)

from kaizen.journey.context import (
    ContextAccumulator,
    MergeStrategy,
    AccumulatedField,
    ContextSnapshot,
)

from kaizen.journey.state import (
    JourneyStateManager,
    StateBackend,
    MemoryStateBackend,
    DataFlowStateBackend,
)

from kaizen.journey.behaviors import (
    ReturnBehavior,
    ReturnToPrevious,
    ReturnToSpecific,
)

from kaizen.journey.nexus import (
    JourneyNexusAdapter,
)

from kaizen.journey.errors import (
    JourneyError,
    PathwayNotFoundError,
    SessionNotStartedError,
    ContextSizeExceededError,
    MaxPathwayDepthError,
)

__all__ = [
    # Core classes
    "Journey",
    "JourneyMeta",
    "Pathway",
    "PathwayMeta",
    "JourneyConfig",
    "PathwayContext",
    "PathwayResult",

    # Transitions
    "Transition",
    "TransitionResult",
    "BaseTrigger",
    "IntentTrigger",
    "ConditionTrigger",
    "AlwaysTrigger",

    # Intent detection
    "IntentDetector",
    "IntentResult",
    "IntentClassificationSignature",

    # Runtime
    "PathwayManager",
    "JourneySession",
    "JourneyResponse",

    # Context
    "ContextAccumulator",
    "MergeStrategy",
    "AccumulatedField",
    "ContextSnapshot",

    # State management
    "JourneyStateManager",
    "StateBackend",
    "MemoryStateBackend",
    "DataFlowStateBackend",

    # Behaviors
    "ReturnBehavior",
    "ReturnToPrevious",
    "ReturnToSpecific",

    # Nexus integration
    "JourneyNexusAdapter",

    # Errors
    "JourneyError",
    "PathwayNotFoundError",
    "SessionNotStartedError",
    "ContextSizeExceededError",
    "MaxPathwayDepthError",
]

__version__ = "0.9.0"
```

## Test Scenarios

### Test 1: Signature Integration
```python
def test_pathway_uses_signature_fields():
    class TestSig(Signature):
        __intent__ = "Test intent"
        question: str = InputField(desc="Q")
        answer: str = OutputField(desc="A")

    class TestPath(Pathway):
        __signature__ = TestSig
        __agents__ = ["test_agent"]

    pathway = TestPath(mock_manager)
    assert pathway.signature.intent == "Test intent"

def test_pathway_merges_guidelines():
    class TestSig(Signature):
        __guidelines__ = ["Base guideline"]
        q: str = InputField(desc="Q")
        a: str = OutputField(desc="A")

    class TestPath(Pathway):
        __signature__ = TestSig
        __guidelines__ = ["Pathway guideline"]
        __agents__ = ["test_agent"]

    pathway = TestPath(mock_manager)
    sig = pathway.signature
    assert "Base guideline" in sig.guidelines
    assert "Pathway guideline" in sig.guidelines
```

### Test 2: Pipeline Integration
```python
@pytest.mark.asyncio
async def test_pathway_builds_ensemble_pipeline():
    class EnsemblePath(Pathway):
        __signature__ = TestSig
        __agents__ = ["agent1", "agent2", "agent3"]
        __pipeline__ = "ensemble"

    manager = create_test_manager()
    manager.register_agent("agent1", mock_agent1)
    manager.register_agent("agent2", mock_agent2)
    manager.register_agent("agent3", mock_agent3)

    pathway = EnsemblePath(manager)
    pipeline = pathway._build_pipeline(pathway._resolve_agents())

    assert pipeline.pattern_type == "ensemble"
```

### Test 3: DataFlow Integration
```python
@pytest.mark.asyncio
async def test_session_persists_to_dataflow(dataflow_db):
    backend = DataFlowStateBackend(dataflow_db)

    session_data = {
        "journey_class": "TestJourney",
        "current_pathway_id": "intake",
        "pathway_stack": ["intake"],
        "conversation_history": [{"role": "user", "content": "Hi"}],
        "accumulated_context": {"name": "Alice"}
    }

    await backend.save("session-123", session_data)
    loaded = await backend.load("session-123")

    assert loaded["current_pathway_id"] == "intake"
    assert loaded["accumulated_context"]["name"] == "Alice"
```

### Test 4: Nexus Integration
```python
@pytest.mark.asyncio
async def test_journey_deploys_via_nexus():
    adapter = JourneyNexusAdapter(
        journey_class=TestJourney,
        agents={"test_agent": mock_agent}
    )

    workflow = adapter.to_workflow()

    # Verify workflow structure
    assert "journey_executor" in workflow._nodes
    assert workflow._nodes["journey_executor"]["type"] == "PythonCodeNode"
```

## Implementation Tasks

| Task | Effort | Dependencies |
|------|--------|--------------|
| Signature integration (intent/guidelines merge) | 0.5 day | Layer 2 enhancements |
| Pipeline pattern integration | 0.5 day | Pathway class |
| Memory tier integration | 0.5 day | PathwayManager |
| DataFlow models definition | 0.5 day | DataFlow |
| DataFlowStateBackend implementation | 0.5 day | DataFlow models |
| JourneyNexusAdapter | 1 day | PathwayManager |
| Hooks integration | 0.5 day | PathwayManager |
| Public API (__init__.py) | 0.25 day | All modules |
| Integration tests | 0.75 day | All integration |
