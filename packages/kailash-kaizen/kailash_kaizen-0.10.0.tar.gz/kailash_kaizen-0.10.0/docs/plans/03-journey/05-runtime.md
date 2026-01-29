# PathwayManager and ContextAccumulator

> **Priority**: P0
> **Effort**: 8 days
> **Files**: `kaizen/journey/manager.py`, `kaizen/journey/context.py`, `kaizen/journey/state.py`

## Purpose

Implement the runtime components that execute Journey definitions, manage pathway transitions, and accumulate context across pathways.

## Component Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PathwayManager                                    │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  PathwayStack   │  │ IntentDetector  │  │   ContextAccumulator        │  │
│  │  (navigation)   │  │ (transitions)   │  │   (cross-pathway state)     │  │
│  └────────┬────────┘  └────────┬────────┘  └──────────────┬──────────────┘  │
│           │                    │                          │                  │
│           ▼                    ▼                          ▼                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     JourneyStateManager                                  ││
│  │              (persistence, sessions, recovery)                           ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

## Requirements

### REQ-PM-001: PathwayManager Core

```python
# File: kaizen/journey/manager.py

from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime

from kaizen.journey.core import Journey, Pathway, PathwayContext, PathwayResult
from kaizen.journey.transitions import Transition, TransitionResult
from kaizen.journey.intent import IntentDetector
from kaizen.journey.context import ContextAccumulator
from kaizen.journey.state import JourneyStateManager
from kaizen.core.base_agent import BaseAgent


@dataclass
class JourneySession:
    """Active journey session state."""
    session_id: str
    journey_class: Type[Journey]
    current_pathway_id: str
    pathway_stack: List[str] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    accumulated_context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class JourneyResponse:
    """Response from journey processing."""
    message: str
    pathway_id: str
    pathway_changed: bool
    accumulated_context: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class PathwayManager:
    """
    Runtime manager for Journey execution.

    Responsibilities:
    - Manage active sessions
    - Execute pathways
    - Handle transitions
    - Accumulate context
    - Persist state
    """

    def __init__(
        self,
        journey: Journey,
        session_id: str,
        config: "JourneyConfig"
    ):
        self.journey = journey
        self.session_id = session_id
        self.config = config

        # Runtime components
        self._agents: Dict[str, BaseAgent] = {}
        self._intent_detector = IntentDetector(config)
        self._context_accumulator = ContextAccumulator(config)
        self._state_manager = JourneyStateManager(config)

        # Session state
        self._session: Optional[JourneySession] = None
        self._pathway_stack: List[str] = []

    def register_agent(self, agent_id: str, agent: BaseAgent) -> None:
        """Register an agent for use in pathways."""
        self._agents[agent_id] = agent

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get registered agent by ID."""
        return self._agents.get(agent_id)

    async def start_session(
        self,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> JourneySession:
        """Start a new journey session at entry pathway."""
        entry_pathway = self.journey.entry_pathway
        if not entry_pathway:
            raise ValueError("Journey has no entry pathway defined")

        self._session = JourneySession(
            session_id=self.session_id,
            journey_class=type(self.journey),
            current_pathway_id=entry_pathway,
            pathway_stack=[entry_pathway],
            accumulated_context=initial_context or {}
        )

        # Persist initial state
        await self._state_manager.save_session(self._session)

        return self._session

    async def process_message(self, message: str) -> JourneyResponse:
        """
        Process user message in current pathway.

        Flow:
        1. Check for global transitions (intent detection)
        2. If transition triggered, switch pathway
        3. Execute current pathway with message
        4. Accumulate outputs
        5. Handle next pathway (if specified)
        6. Return response
        """
        if self._session is None:
            raise RuntimeError("Session not started. Call start_session() first.")

        # Add message to history
        self._session.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Step 1: Check for global transitions
        transition_result = await self._check_transitions(message)

        if transition_result.triggered:
            # Step 2: Switch pathway
            await self._switch_pathway(
                transition_result.target_pathway,
                transition_result.preserve_context
            )

        # Step 3: Execute current pathway
        pathway_result = await self._execute_current_pathway(message)

        # Step 4: Accumulate outputs
        self._context_accumulator.accumulate(
            self._session.accumulated_context,
            pathway_result.accumulated
        )

        # Step 5: Handle next pathway
        pathway_changed = transition_result.triggered
        if pathway_result.next_pathway and not transition_result.triggered:
            await self._advance_to_pathway(pathway_result.next_pathway)
            pathway_changed = True

        # Step 6: Handle return behavior
        current_pathway = self._get_current_pathway()
        if current_pathway.return_behavior:
            await self._handle_return_behavior(current_pathway, pathway_result)

        # Add assistant response to history
        response_message = pathway_result.outputs.get("response", "")
        self._session.conversation_history.append({
            "role": "assistant",
            "content": response_message,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Update session
        self._session.updated_at = datetime.utcnow()
        await self._state_manager.save_session(self._session)

        return JourneyResponse(
            message=response_message,
            pathway_id=self._session.current_pathway_id,
            pathway_changed=pathway_changed,
            accumulated_context=self._session.accumulated_context.copy(),
            metadata={
                "pathway_stack": self._session.pathway_stack.copy(),
                "transition_triggered": transition_result.triggered,
                "transition_intent": transition_result.matched_intent
            }
        )

    async def _check_transitions(self, message: str) -> TransitionResult:
        """Check if any global transitions should trigger."""
        transitions = self.journey.transitions

        for transition in transitions:
            result = await transition.evaluate(
                message=message,
                context=self._session.accumulated_context,
                intent_detector=self._intent_detector
            )
            if result.triggered:
                return result

        return TransitionResult(triggered=False)

    async def _switch_pathway(
        self,
        target_pathway: str,
        preserve_context: bool = True
    ) -> None:
        """Switch to a different pathway."""
        if target_pathway not in self.journey.pathways:
            raise ValueError(f"Unknown pathway: {target_pathway}")

        # Push current pathway to stack (for return navigation)
        self._session.pathway_stack.append(self._session.current_pathway_id)

        # Switch to target
        self._session.current_pathway_id = target_pathway

        if not preserve_context:
            # Clear accumulated context (rare)
            self._session.accumulated_context = {}

    async def _advance_to_pathway(self, next_pathway: str) -> None:
        """Advance to the next pathway in the flow."""
        if next_pathway not in self.journey.pathways:
            raise ValueError(f"Unknown pathway: {next_pathway}")

        # Don't push to stack for natural progression
        self._session.current_pathway_id = next_pathway

    async def _execute_current_pathway(self, message: str) -> PathwayResult:
        """Execute the current pathway with user message."""
        pathway_class = self.journey.pathways[self._session.current_pathway_id]
        pathway = pathway_class(self)

        context = PathwayContext(
            session_id=self.session_id,
            pathway_id=self._session.current_pathway_id,
            user_message=message,
            accumulated_context=self._session.accumulated_context,
            conversation_history=self._session.conversation_history
        )

        return await pathway.execute(context)

    def _get_current_pathway(self) -> Pathway:
        """Get current pathway instance."""
        pathway_class = self.journey.pathways[self._session.current_pathway_id]
        return pathway_class(self)

    async def _handle_return_behavior(
        self,
        pathway: Pathway,
        result: PathwayResult
    ) -> None:
        """Handle return behavior after pathway completion."""
        from kaizen.journey.behaviors import ReturnToPrevious, ReturnToSpecific

        behavior = pathway.return_behavior

        if isinstance(behavior, ReturnToPrevious):
            if self._session.pathway_stack:
                previous = self._session.pathway_stack.pop()
                self._session.current_pathway_id = previous

        elif isinstance(behavior, ReturnToSpecific):
            if behavior.target_pathway in self.journey.pathways:
                self._session.current_pathway_id = behavior.target_pathway

    async def get_session_state(self) -> Optional[JourneySession]:
        """Get current session state."""
        return self._session

    async def restore_session(self, session_id: str) -> Optional[JourneySession]:
        """Restore session from persistence."""
        self._session = await self._state_manager.load_session(session_id)
        if self._session:
            self._pathway_stack = self._session.pathway_stack.copy()
        return self._session
```

### REQ-PM-002: ContextAccumulator

```python
# File: kaizen/journey/context.py

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MergeStrategy(str, Enum):
    """Strategy for merging accumulated values."""
    REPLACE = "replace"      # New value replaces old
    APPEND = "append"        # Append to list
    MERGE_DICT = "merge"     # Merge dictionaries
    MAX = "max"              # Keep maximum value
    MIN = "min"              # Keep minimum value
    SUM = "sum"              # Sum numeric values
    UNION = "union"          # Set union for lists


@dataclass
class AccumulatedField:
    """Tracked accumulated field with metadata."""
    name: str
    value: Any
    source_pathway: str
    timestamp: datetime
    version: int = 1


@dataclass
class ContextSnapshot:
    """Snapshot of context at a point in time."""
    context: Dict[str, Any]
    pathway_id: str
    timestamp: datetime
    version: int


class ContextAccumulator:
    """
    Manages cross-pathway context accumulation.

    Features:
    - Field-level merge strategies
    - Context versioning
    - Snapshot/restore
    - Size limits
    - Conflict resolution
    """

    def __init__(self, config: "JourneyConfig"):
        self.config = config
        self._merge_strategies: Dict[str, MergeStrategy] = {}
        self._field_history: Dict[str, List[AccumulatedField]] = {}
        self._snapshots: List[ContextSnapshot] = []
        self._version = 0

    def configure_field(
        self,
        field_name: str,
        strategy: MergeStrategy = MergeStrategy.REPLACE
    ) -> None:
        """Configure merge strategy for a specific field."""
        self._merge_strategies[field_name] = strategy

    def accumulate(
        self,
        context: Dict[str, Any],
        new_values: Dict[str, Any],
        source_pathway: str = ""
    ) -> Dict[str, Any]:
        """
        Accumulate new values into context.

        Args:
            context: Current accumulated context (modified in place)
            new_values: New values to accumulate
            source_pathway: Pathway that produced these values

        Returns:
            Updated context
        """
        for field_name, new_value in new_values.items():
            if new_value is None:
                continue

            strategy = self._merge_strategies.get(
                field_name,
                MergeStrategy.REPLACE
            )

            old_value = context.get(field_name)
            merged_value = self._merge_value(old_value, new_value, strategy)

            context[field_name] = merged_value

            # Track field history
            self._track_field(field_name, merged_value, source_pathway)

        self._version += 1
        return context

    def _merge_value(
        self,
        old: Any,
        new: Any,
        strategy: MergeStrategy
    ) -> Any:
        """Merge old and new values based on strategy."""
        if old is None:
            return new

        if strategy == MergeStrategy.REPLACE:
            return new

        elif strategy == MergeStrategy.APPEND:
            if isinstance(old, list):
                if isinstance(new, list):
                    return old + new
                return old + [new]
            return [old, new]

        elif strategy == MergeStrategy.MERGE_DICT:
            if isinstance(old, dict) and isinstance(new, dict):
                merged = old.copy()
                merged.update(new)
                return merged
            return new

        elif strategy == MergeStrategy.MAX:
            try:
                return max(old, new)
            except TypeError:
                return new

        elif strategy == MergeStrategy.MIN:
            try:
                return min(old, new)
            except TypeError:
                return new

        elif strategy == MergeStrategy.SUM:
            try:
                return old + new
            except TypeError:
                return new

        elif strategy == MergeStrategy.UNION:
            if isinstance(old, list) and isinstance(new, list):
                return list(set(old) | set(new))
            return new

        return new

    def _track_field(
        self,
        field_name: str,
        value: Any,
        source_pathway: str
    ) -> None:
        """Track field history for debugging/auditing."""
        if field_name not in self._field_history:
            self._field_history[field_name] = []

        entry = AccumulatedField(
            name=field_name,
            value=value,
            source_pathway=source_pathway,
            timestamp=datetime.utcnow(),
            version=self._version
        )

        self._field_history[field_name].append(entry)

        # Limit history size
        max_history = 100
        if len(self._field_history[field_name]) > max_history:
            self._field_history[field_name] = \
                self._field_history[field_name][-max_history:]

    def snapshot(
        self,
        context: Dict[str, Any],
        pathway_id: str
    ) -> ContextSnapshot:
        """Create a snapshot of current context."""
        snapshot = ContextSnapshot(
            context=context.copy(),
            pathway_id=pathway_id,
            timestamp=datetime.utcnow(),
            version=self._version
        )
        self._snapshots.append(snapshot)

        # Limit snapshots
        max_snapshots = 10
        if len(self._snapshots) > max_snapshots:
            self._snapshots = self._snapshots[-max_snapshots:]

        return snapshot

    def restore_snapshot(self, version: int) -> Optional[Dict[str, Any]]:
        """Restore context from a specific version."""
        for snapshot in reversed(self._snapshots):
            if snapshot.version == version:
                return snapshot.context.copy()
        return None

    def get_field_history(
        self,
        field_name: str
    ) -> List[AccumulatedField]:
        """Get history of a specific field."""
        return self._field_history.get(field_name, []).copy()

    def get_context_size(self, context: Dict[str, Any]) -> int:
        """Calculate approximate size of context in bytes."""
        import json
        try:
            return len(json.dumps(context).encode('utf-8'))
        except (TypeError, ValueError):
            return 0

    def validate_size(self, context: Dict[str, Any]) -> bool:
        """Check if context is within size limits."""
        size = self.get_context_size(context)
        return size <= self.config.max_context_size_bytes
```

### REQ-PM-003: JourneyStateManager

```python
# File: kaizen/journey/state.py

from typing import Any, Dict, Optional
from abc import ABC, abstractmethod
import json
from datetime import datetime

from kaizen.journey.manager import JourneySession


class StateBackend(ABC):
    """Abstract backend for session persistence."""

    @abstractmethod
    async def save(self, session_id: str, data: Dict[str, Any]) -> None:
        """Save session data."""
        pass

    @abstractmethod
    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data."""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete session data."""
        pass

    @abstractmethod
    async def list_sessions(self) -> list[str]:
        """List all session IDs."""
        pass


class MemoryStateBackend(StateBackend):
    """In-memory session storage (for development/testing)."""

    def __init__(self):
        self._storage: Dict[str, Dict[str, Any]] = {}

    async def save(self, session_id: str, data: Dict[str, Any]) -> None:
        self._storage[session_id] = data.copy()

    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._storage.get(session_id, {}).copy() or None

    async def delete(self, session_id: str) -> None:
        self._storage.pop(session_id, None)

    async def list_sessions(self) -> list[str]:
        return list(self._storage.keys())


class DataFlowStateBackend(StateBackend):
    """DataFlow-backed session storage (production)."""

    def __init__(self, db: "DataFlow"):
        self.db = db

    async def save(self, session_id: str, data: Dict[str, Any]) -> None:
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime import AsyncLocalRuntime

        # Check if session exists
        existing = await self.load(session_id)

        workflow = WorkflowBuilder()

        if existing:
            workflow.add_node("JourneySessionUpdateNode", "update", {
                "filter": {"id": session_id},
                "fields": {
                    "data": json.dumps(data),
                    "updated_at": datetime.utcnow().isoformat()
                }
            })
        else:
            workflow.add_node("JourneySessionCreateNode", "create", {
                "id": session_id,
                "data": json.dumps(data)
            })

        runtime = AsyncLocalRuntime()
        await runtime.execute_workflow_async(workflow.build())

    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime import AsyncLocalRuntime

        workflow = WorkflowBuilder()
        workflow.add_node("JourneySessionReadNode", "read", {
            "filter": {"id": session_id}
        })

        runtime = AsyncLocalRuntime()
        results, _ = await runtime.execute_workflow_async(workflow.build())

        record = results.get("read")
        if record and record.get("data"):
            return json.loads(record["data"])
        return None

    async def delete(self, session_id: str) -> None:
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime import AsyncLocalRuntime

        workflow = WorkflowBuilder()
        workflow.add_node("JourneySessionDeleteNode", "delete", {
            "filter": {"id": session_id}
        })

        runtime = AsyncLocalRuntime()
        await runtime.execute_workflow_async(workflow.build())

    async def list_sessions(self) -> list[str]:
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime import AsyncLocalRuntime

        workflow = WorkflowBuilder()
        workflow.add_node("JourneySessionListNode", "list", {
            "filter": {},
            "fields": ["id"]
        })

        runtime = AsyncLocalRuntime()
        results, _ = await runtime.execute_workflow_async(workflow.build())

        records = results.get("list", {}).get("records", [])
        return [r["id"] for r in records]


class JourneyStateManager:
    """
    Manages journey session persistence.

    Features:
    - Multiple backend support (memory, DataFlow, Redis)
    - Session serialization/deserialization
    - TTL-based expiration
    - Recovery from crashes
    """

    def __init__(self, config: "JourneyConfig"):
        self.config = config
        self._backend = self._create_backend()

    def _create_backend(self) -> StateBackend:
        """Create appropriate backend based on config."""
        persistence = self.config.context_persistence

        if persistence == "memory":
            return MemoryStateBackend()

        elif persistence == "dataflow":
            # DataFlow backend requires db instance to be passed
            # This will be injected during runtime setup
            return MemoryStateBackend()  # Fallback

        else:
            return MemoryStateBackend()

    def set_backend(self, backend: StateBackend) -> None:
        """Set a custom backend."""
        self._backend = backend

    async def save_session(self, session: JourneySession) -> None:
        """Save session to backend."""
        data = self._serialize_session(session)
        await self._backend.save(session.session_id, data)

    async def load_session(
        self,
        session_id: str
    ) -> Optional[JourneySession]:
        """Load session from backend."""
        data = await self._backend.load(session_id)
        if data:
            return self._deserialize_session(data)
        return None

    async def delete_session(self, session_id: str) -> None:
        """Delete session from backend."""
        await self._backend.delete(session_id)

    async def list_sessions(self) -> list[str]:
        """List all active session IDs."""
        return await self._backend.list_sessions()

    def _serialize_session(self, session: JourneySession) -> Dict[str, Any]:
        """Serialize session to storable format."""
        return {
            "session_id": session.session_id,
            "journey_class": f"{session.journey_class.__module__}."
                           f"{session.journey_class.__name__}",
            "current_pathway_id": session.current_pathway_id,
            "pathway_stack": session.pathway_stack,
            "conversation_history": session.conversation_history,
            "accumulated_context": session.accumulated_context,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }

    def _deserialize_session(self, data: Dict[str, Any]) -> JourneySession:
        """Deserialize session from stored format."""
        # Note: journey_class restoration requires import machinery
        # For now, we store the class reference separately
        return JourneySession(
            session_id=data["session_id"],
            journey_class=None,  # Will be set by PathwayManager
            current_pathway_id=data["current_pathway_id"],
            pathway_stack=data.get("pathway_stack", []),
            conversation_history=data.get("conversation_history", []),
            accumulated_context=data.get("accumulated_context", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )
```

## Test Scenarios

### Test 1: PathwayManager Session Management
```python
@pytest.mark.asyncio
async def test_start_session_creates_at_entry_pathway():
    journey = create_test_journey()
    manager = PathwayManager(journey, "session-1", JourneyConfig())

    session = await manager.start_session()

    assert session.session_id == "session-1"
    assert session.current_pathway_id == journey.entry_pathway
    assert len(session.pathway_stack) == 1

@pytest.mark.asyncio
async def test_process_message_without_session_raises():
    journey = create_test_journey()
    manager = PathwayManager(journey, "session-1", JourneyConfig())

    with pytest.raises(RuntimeError, match="Session not started"):
        await manager.process_message("Hello")
```

### Test 2: Pathway Transitions
```python
@pytest.mark.asyncio
async def test_intent_triggers_pathway_switch(mock_intent_detector):
    mock_intent_detector.detect.return_value = IntentResult(
        intent="faq",
        confidence=0.95
    )

    journey = create_journey_with_faq_transition()
    manager = PathwayManager(journey, "session-1", JourneyConfig())
    manager._intent_detector = mock_intent_detector

    await manager.start_session()
    response = await manager.process_message("What are your hours?")

    assert response.pathway_id == "faq"
    assert response.pathway_changed is True
    assert "faq" in response.metadata["transition_intent"]
```

### Test 3: Context Accumulation
```python
def test_accumulate_with_replace_strategy():
    accumulator = ContextAccumulator(JourneyConfig())
    context = {"name": "Alice"}

    accumulator.accumulate(context, {"name": "Bob"}, "pathway1")

    assert context["name"] == "Bob"

def test_accumulate_with_append_strategy():
    accumulator = ContextAccumulator(JourneyConfig())
    accumulator.configure_field("rejected_doctors", MergeStrategy.APPEND)

    context = {"rejected_doctors": ["Dr. Smith"]}
    accumulator.accumulate(
        context,
        {"rejected_doctors": ["Dr. Jones"]},
        "booking"
    )

    assert context["rejected_doctors"] == ["Dr. Smith", "Dr. Jones"]

def test_accumulate_with_union_strategy():
    accumulator = ContextAccumulator(JourneyConfig())
    accumulator.configure_field("preferences", MergeStrategy.UNION)

    context = {"preferences": ["morning", "telehealth"]}
    accumulator.accumulate(
        context,
        {"preferences": ["morning", "female_doctor"]},
        "intake"
    )

    assert set(context["preferences"]) == {"morning", "telehealth", "female_doctor"}
```

### Test 4: State Persistence
```python
@pytest.mark.asyncio
async def test_session_persists_across_restore():
    config = JourneyConfig(context_persistence="memory")
    state_manager = JourneyStateManager(config)

    original_session = JourneySession(
        session_id="test-123",
        journey_class=TestJourney,
        current_pathway_id="intake",
        accumulated_context={"name": "Alice"}
    )

    await state_manager.save_session(original_session)
    restored = await state_manager.load_session("test-123")

    assert restored.session_id == "test-123"
    assert restored.current_pathway_id == "intake"
    assert restored.accumulated_context["name"] == "Alice"
```

### Test 5: Return Behavior
```python
@pytest.mark.asyncio
async def test_return_to_previous_after_faq():
    journey = create_journey_with_faq_return()
    manager = PathwayManager(journey, "session-1", JourneyConfig())

    await manager.start_session()  # At "intake"
    await manager.process_message("Help me!")  # Transitions to "faq"
    response = await manager.process_message("Thanks, that answered it")

    # Should return to "intake" after FAQ completion
    assert response.pathway_id == "intake"
```

## Implementation Tasks

| Task | Effort | Dependencies |
|------|--------|--------------|
| Implement PathwayManager core | 2 days | Journey/Pathway, IntentDetector |
| Implement ContextAccumulator | 1.5 days | None |
| Implement MergeStrategy logic | 0.5 day | ContextAccumulator |
| Implement StateBackend interface | 0.5 day | None |
| Implement MemoryStateBackend | 0.25 day | StateBackend |
| Implement DataFlowStateBackend | 1 day | StateBackend, DataFlow |
| Implement JourneyStateManager | 0.5 day | StateBackend |
| Unit tests for PathwayManager | 1 day | All PathwayManager |
| Unit tests for ContextAccumulator | 0.5 day | ContextAccumulator |
| Integration tests with real LLM | 0.75 day | All implementation |

## Error Handling

```python
class JourneyError(Exception):
    """Base exception for journey errors."""
    pass

class PathwayNotFoundError(JourneyError):
    """Raised when pathway doesn't exist."""
    def __init__(self, pathway_id: str, available: List[str]):
        self.pathway_id = pathway_id
        self.available = available
        super().__init__(
            f"Pathway '{pathway_id}' not found. "
            f"Available: {available}"
        )

class SessionNotStartedError(JourneyError):
    """Raised when operating on unstarted session."""
    pass

class ContextSizeExceededError(JourneyError):
    """Raised when context exceeds size limit."""
    def __init__(self, current_size: int, max_size: int):
        self.current_size = current_size
        self.max_size = max_size
        super().__init__(
            f"Context size {current_size} bytes exceeds "
            f"limit of {max_size} bytes"
        )

class MaxPathwayDepthError(JourneyError):
    """Raised when pathway stack exceeds max depth."""
    def __init__(self, depth: int, max_depth: int):
        self.depth = depth
        self.max_depth = max_depth
        super().__init__(
            f"Pathway depth {depth} exceeds max {max_depth}"
        )
```

## Performance Considerations

1. **Intent Detection Caching**: Cache intent results for similar messages
2. **Lazy Pathway Instantiation**: Don't create pathway instances until needed
3. **Batched State Persistence**: Batch multiple updates before persisting
4. **Context Pruning**: Automatically prune old context when approaching limits
5. **Connection Pooling**: Reuse database connections in DataFlowStateBackend
