# Journey and Pathway Core Classes

> **Priority**: P0
> **Effort**: 5 days
> **Files**: `kaizen/journey/core.py`, `kaizen/journey/behaviors.py`

## Purpose

Define the declarative Journey and Pathway classes that form the foundation of Layer 5 orchestration.

## Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Journey (JourneyMeta)                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  __entry_pathway__ = "intake"                            │    │
│  │  __transitions__ = [Transition(...), ...]                │    │
│  │                                                          │    │
│  │  class IntakePath(Pathway):                              │    │
│  │      __signature__ = IntakeSignature                     │    │
│  │      __agents__ = ["agent1", "agent2"]                   │    │
│  │      __pipeline__ = "sequential"                         │    │
│  │      __next__ = "booking"                                │    │
│  │                                                          │    │
│  │  class BookingPath(Pathway): ...                         │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Requirements

### REQ-JC-001: JourneyMeta Metaclass

Process Journey class definitions to extract:
- Nested Pathway classes
- Entry pathway reference
- Global transitions

```python
class JourneyMeta(type):
    """Metaclass for processing Journey class definitions."""

    def __new__(mcs, name, bases, namespace, **kwargs):
        if name == "Journey":
            return super().__new__(mcs, name, bases, namespace)

        # Extract nested Pathway classes
        pathways: Dict[str, Type["Pathway"]] = {}
        for attr_name, attr_value in namespace.items():
            if isinstance(attr_value, type) and issubclass(attr_value, Pathway):
                if attr_value is not Pathway:  # Skip base class
                    pathway_id = mcs._to_pathway_id(attr_name)
                    pathways[pathway_id] = attr_value

        # Validate entry pathway
        entry_pathway = namespace.get("__entry_pathway__")
        if pathways and entry_pathway and entry_pathway not in pathways:
            available = list(pathways.keys())
            raise ValueError(
                f"Entry pathway '{entry_pathway}' not found. "
                f"Available pathways: {available}"
            )

        # Default to first pathway if not specified
        if pathways and not entry_pathway:
            entry_pathway = list(pathways.keys())[0]

        # Store as class variables
        namespace["_pathways"] = pathways
        namespace["_entry_pathway"] = entry_pathway
        namespace["_transitions"] = namespace.get("__transitions__", [])

        return super().__new__(mcs, name, bases, namespace)

    @staticmethod
    def _to_pathway_id(class_name: str) -> str:
        """Convert PathwayClassName to pathway_id (snake_case)."""
        # Remove 'Path' or 'Pathway' suffix
        name = class_name
        for suffix in ("Pathway", "Path"):
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break

        # Convert to snake_case
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
```

### REQ-JC-002: Journey Base Class

```python
class Journey(metaclass=JourneyMeta):
    """
    Base class for declarative journey definition.

    Example:
        class BookingJourney(Journey):
            __entry_pathway__ = "intake"

            class IntakePath(Pathway):
                __signature__ = IntakeSignature
                __agents__ = ["intake_agent"]
                __next__ = "booking"

            __transitions__ = [
                Transition(trigger=IntentTrigger(["help"]), to_pathway="faq")
            ]
    """

    # Class variables (set by JourneyMeta)
    _pathways: ClassVar[Dict[str, Type["Pathway"]]] = {}
    _entry_pathway: ClassVar[Optional[str]] = None
    _transitions: ClassVar[List["Transition"]] = []

    def __init__(
        self,
        session_id: str,
        config: Optional["JourneyConfig"] = None
    ):
        self.session_id = session_id
        self.config = config or JourneyConfig()
        self.manager = PathwayManager(
            journey=self,
            session_id=session_id,
            config=self.config
        )

    @property
    def pathways(self) -> Dict[str, Type["Pathway"]]:
        """Get all registered pathways."""
        return self._pathways.copy()

    @property
    def entry_pathway(self) -> str:
        """Get entry pathway ID."""
        return self._entry_pathway

    @property
    def transitions(self) -> List["Transition"]:
        """Get global transition rules."""
        return self._transitions.copy()

    async def start(
        self,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> "JourneySession":
        """Start journey session at entry pathway."""
        return await self.manager.start_session(initial_context)

    async def process_message(self, message: str) -> "JourneyResponse":
        """Process user message in current pathway."""
        return await self.manager.process_message(message)
```

### REQ-JC-003: PathwayMeta Metaclass

```python
class PathwayMeta(type):
    """Metaclass for processing Pathway class definitions."""

    def __new__(mcs, name, bases, namespace, **kwargs):
        if name == "Pathway":
            return super().__new__(mcs, name, bases, namespace)

        # Extract pathway configuration
        namespace["_signature"] = namespace.get("__signature__")
        namespace["_agents"] = namespace.get("__agents__", [])
        namespace["_pipeline"] = namespace.get("__pipeline__", "sequential")
        namespace["_accumulate"] = namespace.get("__accumulate__", [])
        namespace["_next"] = namespace.get("__next__")
        namespace["_guidelines"] = namespace.get("__guidelines__", [])
        namespace["_return_behavior"] = namespace.get("__return_behavior__")

        # Validate signature
        sig = namespace["_signature"]
        if sig is not None and not (
            isinstance(sig, type) and hasattr(sig, "_signature_inputs")
        ):
            raise TypeError(
                f"__signature__ must be a Signature class, got {type(sig)}"
            )

        return super().__new__(mcs, name, bases, namespace)
```

### REQ-JC-004: Pathway Base Class

```python
class Pathway(metaclass=PathwayMeta):
    """
    A phase in a user journey.

    Pathways define:
    - Signature: I/O contract for this phase
    - Agents: Which agents handle this pathway
    - Pipeline: How agents are coordinated (sequential, parallel, etc.)
    - Accumulate: Which output fields to preserve across pathways
    - Next: Default next pathway (if no transition triggered)
    - Guidelines: Pathway-specific guidelines (merged with signature)
    """

    # Class variables (set by PathwayMeta)
    _signature: ClassVar[Optional[Type[Signature]]] = None
    _agents: ClassVar[List[str]] = []
    _pipeline: ClassVar[str] = "sequential"
    _accumulate: ClassVar[List[str]] = []
    _next: ClassVar[Optional[str]] = None
    _guidelines: ClassVar[List[str]] = []
    _return_behavior: ClassVar[Optional["ReturnBehavior"]] = None

    def __init__(self, manager: "PathwayManager"):
        self.manager = manager
        self._signature_instance = None
        self._pipeline_instance = None

    @property
    def signature(self) -> Optional[Signature]:
        """Get instantiated signature for this pathway."""
        if self._signature_instance is None and self._signature is not None:
            sig = self._signature()

            # Merge pathway guidelines with signature guidelines
            if self._guidelines:
                sig = sig.with_guidelines(self._guidelines)

            self._signature_instance = sig
        return self._signature_instance

    @property
    def agent_ids(self) -> List[str]:
        return self._agents.copy()

    @property
    def pipeline_type(self) -> str:
        return self._pipeline

    @property
    def accumulate_fields(self) -> List[str]:
        return self._accumulate.copy()

    @property
    def next_pathway(self) -> Optional[str]:
        return self._next

    @property
    def return_behavior(self) -> Optional["ReturnBehavior"]:
        return self._return_behavior

    async def execute(self, context: "PathwayContext") -> "PathwayResult":
        """Execute pathway with given context."""
        try:
            agents = self._resolve_agents()
            pipeline = self._build_pipeline(agents)

            # Prepare input from context
            inputs = context.to_input_dict()

            # Add signature fields
            if self.signature:
                for field_name in self.signature._signature_inputs:
                    if field_name in context.accumulated_context:
                        inputs[field_name] = context.accumulated_context[field_name]

            # Execute pipeline
            result = await pipeline.execute(inputs)

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

    def _resolve_agents(self) -> List["BaseAgent"]:
        """Resolve agent IDs to agent instances from registry."""
        agents = []
        for agent_id in self._agents:
            agent = self.manager.get_agent(agent_id)
            if agent is None:
                raise ValueError(f"Agent '{agent_id}' not registered")
            agents.append(agent)
        return agents

    def _build_pipeline(self, agents: List["BaseAgent"]) -> "Pipeline":
        """Build pipeline from agents based on pipeline type."""
        from kaizen.orchestration.pipeline import Pipeline

        if len(agents) == 0:
            raise ValueError("Pathway requires at least one agent")

        if len(agents) == 1:
            # Single agent, wrap in minimal pipeline
            return Pipeline.sequential(agents)

        pipeline_builders = {
            "sequential": Pipeline.sequential,
            "parallel": Pipeline.parallel,
            "router": lambda a: Pipeline.router(a, routing_strategy="semantic"),
            "ensemble": Pipeline.ensemble,
            "supervisor_worker": Pipeline.supervisor_worker,
        }

        builder = pipeline_builders.get(self._pipeline)
        if builder is None:
            raise ValueError(f"Unknown pipeline type: {self._pipeline}")

        return builder(agents)

    def _extract_accumulated_fields(
        self,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract fields to accumulate from result."""
        return {
            field: result.get(field)
            for field in self._accumulate
            if field in result and result.get(field) is not None
        }
```

### REQ-JC-005: Data Classes

```python
@dataclass
class JourneyConfig:
    """Configuration for Journey execution."""

    # Intent detection
    intent_detection_model: str = "gpt-4o-mini"
    intent_confidence_threshold: float = 0.7
    intent_cache_ttl_seconds: int = 300

    # Pathway execution
    max_pathway_depth: int = 10
    pathway_timeout_seconds: float = 60.0

    # Context accumulation
    max_context_size_bytes: int = 1024 * 1024  # 1MB
    context_persistence: str = "memory"  # "memory", "dataflow", "redis"

    # Error handling
    error_recovery: str = "graceful"  # "fail_fast", "graceful", "retry"
    max_retries: int = 3


@dataclass
class PathwayContext:
    """Execution context for a pathway."""
    session_id: str
    pathway_id: str
    user_message: str
    accumulated_context: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]

    def to_input_dict(self) -> Dict[str, Any]:
        """Convert context to pipeline input dictionary."""
        return {
            "message": self.user_message,
            "context": self.accumulated_context,
            "history": self.conversation_history,
        }


@dataclass
class PathwayResult:
    """Result from pathway execution."""
    outputs: Dict[str, Any]
    accumulated: Dict[str, Any]
    next_pathway: Optional[str]
    is_complete: bool
    error: Optional[str] = None
```

### REQ-JC-006: ReturnToPrevious Behavior

```python
# File: kaizen/journey/behaviors.py

from dataclasses import dataclass


@dataclass
class ReturnBehavior:
    """Base class for pathway return behaviors."""
    pass


@dataclass
class ReturnToPrevious(ReturnBehavior):
    """
    Behavior for detour pathways (e.g., FAQ).

    After detour completes, return to previous pathway.

    Example:
        class FAQPath(Pathway):
            __return_behavior__ = ReturnToPrevious()
    """
    preserve_context: bool = True
    max_depth: int = 5


@dataclass
class ReturnToSpecific(ReturnBehavior):
    """Return to a specific pathway after completion."""
    target_pathway: str = ""
    preserve_context: bool = True
```

## Test Scenarios

### Test 1: Journey Definition Parsing
```python
def test_journey_extracts_pathways():
    class TestJourney(Journey):
        __entry_pathway__ = "first"

        class FirstPath(Pathway):
            __signature__ = SimpleSignature
            __agents__ = ["agent1"]

        class SecondPath(Pathway):
            __signature__ = SimpleSignature
            __agents__ = ["agent2"]

    assert "first" in TestJourney._pathways
    assert "second" in TestJourney._pathways
    assert TestJourney._entry_pathway == "first"

def test_invalid_entry_pathway_raises():
    with pytest.raises(ValueError, match="not found"):
        class BadJourney(Journey):
            __entry_pathway__ = "nonexistent"

            class OnlyPath(Pathway):
                __signature__ = SimpleSignature
                __agents__ = ["agent1"]
```

### Test 2: Pathway Configuration
```python
def test_pathway_pipeline_types():
    class ParallelPath(Pathway):
        __signature__ = SimpleSignature
        __agents__ = ["a1", "a2"]
        __pipeline__ = "parallel"

    assert ParallelPath._pipeline == "parallel"

def test_pathway_accumulation():
    class AccumulatingPath(Pathway):
        __signature__ = SimpleSignature
        __agents__ = ["agent1"]
        __accumulate__ = ["field1", "field2"]

    assert AccumulatingPath._accumulate == ["field1", "field2"]
```

### Test 3: Pathway Execution
```python
@pytest.mark.asyncio
async def test_pathway_executes_agents(mock_agent):
    manager = create_test_manager()
    manager.register_agent("test_agent", mock_agent)

    class TestPath(Pathway):
        __signature__ = SimpleSignature
        __agents__ = ["test_agent"]

    pathway = TestPath(manager)
    context = PathwayContext(
        session_id="test",
        pathway_id="test",
        user_message="Hello",
        accumulated_context={},
        conversation_history=[]
    )

    result = await pathway.execute(context)

    assert result.is_complete
    mock_agent.run.assert_called_once()
```

## Implementation Tasks

| Task | Effort | Dependencies |
|------|--------|--------------|
| Implement JourneyMeta | 1 day | None |
| Implement Journey base class | 0.5 day | JourneyMeta |
| Implement PathwayMeta | 0.5 day | None |
| Implement Pathway base class | 1 day | PathwayMeta |
| Implement data classes | 0.5 day | None |
| Implement ReturnBehavior classes | 0.25 day | None |
| Unit tests for metaclasses | 0.5 day | All metaclasses |
| Unit tests for Journey/Pathway | 0.75 day | All implementation |
