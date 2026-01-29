# Intent Detection System

> **Priority**: P1
> **Effort**: 4 days
> **Files**: `kaizen/journey/transitions.py`, `kaizen/journey/intent.py`

## Purpose

Implement LLM-powered intent detection for pathway transitions with pattern matching fast-path and caching for performance.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    IntentDetector                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  1. Pattern Matching (Fast Path)                         │    │
│  │     "help" in message.lower() → Match!                   │    │
│  └────────────────────┬────────────────────────────────────┘    │
│                       │ No match                                 │
│                       ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  2. Cache Check                                          │    │
│  │     hash(message + triggers) → Cached result?            │    │
│  └────────────────────┬────────────────────────────────────┘    │
│                       │ Cache miss                               │
│                       ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  3. LLM Classification                                   │    │
│  │     IntentClassificationSignature → BaseAgent.run()      │    │
│  └────────────────────┬────────────────────────────────────┘    │
│                       │                                          │
│                       ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  4. Cache Result                                         │    │
│  │     Store with TTL                                       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Requirements

### REQ-ID-001: Transition Class

```python
# File: kaizen/journey/transitions.py

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class Transition:
    """
    Rule for switching between pathways.

    Attributes:
        trigger: Condition for activation (IntentTrigger, ConditionTrigger)
        from_pathway: Source pathway ("*" for any)
        to_pathway: Destination pathway
        context_update: How to update context on transition
        priority: Higher priority evaluated first (default 0)
    """

    trigger: "BaseTrigger"
    from_pathway: str = "*"
    to_pathway: str = ""
    context_update: Optional[Dict[str, str]] = None
    priority: int = 0

    def matches(
        self,
        current_pathway: str,
        message: str,
        context: Dict[str, Any]
    ) -> bool:
        """Check if transition should activate."""
        # Check pathway match
        if self.from_pathway != "*":
            if isinstance(self.from_pathway, list):
                if current_pathway not in self.from_pathway:
                    return False
            elif self.from_pathway != current_pathway:
                return False

        # Check trigger
        return self.trigger.evaluate(message, context)

    def apply_context_update(
        self,
        context: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply context updates specified in transition.

        Syntax:
        - "append:field_name" - Append current value to list
        - "set:value" - Set literal value
        - "copy:field_name" - Copy from result
        - "remove:field_name" - Remove from context
        - "field_name" - Direct reference (same as copy:)
        """
        if not self.context_update:
            return context

        new_context = context.copy()

        for target_field, update_spec in self.context_update.items():
            if update_spec.startswith("append:"):
                source_field = update_spec.split(":", 1)[1]
                source_value = result.get(source_field)
                if source_value is not None:
                    existing = new_context.get(target_field, [])
                    if not isinstance(existing, list):
                        existing = [existing] if existing else []
                    existing.append(source_value)
                    new_context[target_field] = existing

            elif update_spec.startswith("set:"):
                value = update_spec.split(":", 1)[1]
                new_context[target_field] = value

            elif update_spec.startswith("copy:"):
                source_field = update_spec.split(":", 1)[1]
                if source_field in result:
                    new_context[target_field] = result[source_field]

            elif update_spec.startswith("remove:"):
                field_to_remove = update_spec.split(":", 1)[1]
                new_context.pop(field_to_remove, None)

            else:
                # Direct field reference
                if update_spec in result:
                    new_context[target_field] = result[update_spec]

        return new_context
```

### REQ-ID-002: BaseTrigger and IntentTrigger

```python
class BaseTrigger:
    """Base class for transition triggers."""

    def evaluate(self, message: str, context: Dict[str, Any]) -> bool:
        """Evaluate if trigger condition is met."""
        raise NotImplementedError


@dataclass
class IntentTrigger(BaseTrigger):
    """
    LLM-powered intent detection trigger.

    Uses pattern matching first, with optional LLM fallback.

    Example:
        IntentTrigger(patterns=["help", "question", "what is"])
    """

    patterns: List[str] = field(default_factory=list)
    use_llm_fallback: bool = True
    confidence_threshold: float = 0.7

    # Set by IntentDetector during evaluation
    _detector: Optional["IntentDetector"] = field(default=None, repr=False)

    def evaluate(self, message: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate if message matches intent patterns.

        First checks simple pattern matching, then uses LLM if enabled.
        """
        # Fast path: pattern matching (case-insensitive)
        message_lower = message.lower()
        for pattern in self.patterns:
            pattern_lower = pattern.lower()
            # Check for word boundary match (not just substring)
            import re
            if re.search(r'\b' + re.escape(pattern_lower) + r'\b', message_lower):
                return True

        # Slow path handled by IntentDetector (async)
        # This method only does sync pattern matching
        return False

    def get_intent_name(self) -> str:
        """Get primary intent name from patterns."""
        return self.patterns[0] if self.patterns else "unknown"
```

### REQ-ID-003: ConditionTrigger

```python
@dataclass
class ConditionTrigger(BaseTrigger):
    """
    Condition-based trigger using context values.

    Example:
        ConditionTrigger(
            condition=lambda ctx: ctx.get("retry_count", 0) >= 3
        )
    """

    condition: Callable[[Dict[str, Any]], bool] = None
    description: str = ""  # For debugging/logging

    def evaluate(self, message: str, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context."""
        if self.condition is None:
            return False
        try:
            return bool(self.condition(context))
        except Exception:
            return False
```

### REQ-ID-004: IntentClassificationSignature

```python
# File: kaizen/journey/intent.py

from kaizen.signatures import Signature, InputField, OutputField


class IntentClassificationSignature(Signature):
    """Signature for LLM intent classification."""

    """Classify the user's intent from their message.

    Analyze the message and determine which intent category best matches.
    Be precise and consider the context of the conversation.
    If no intent clearly matches, return 'unknown'.
    """

    __intent__ = "Classify user intent from message with high accuracy"

    __guidelines__ = [
        "Consider the full message context, not just keywords",
        "Match against the provided intent categories only",
        "Return 'unknown' if confidence is below threshold",
        "Explain your reasoning briefly"
    ]

    message: str = InputField(
        description="User message to classify"
    )
    available_intents: str = InputField(
        description="JSON list of possible intent categories"
    )
    conversation_context: str = InputField(
        description="Recent conversation context for disambiguation",
        default=""
    )

    intent: str = OutputField(
        description="Detected intent name or 'unknown'"
    )
    confidence: float = OutputField(
        description="Confidence score from 0.0 to 1.0"
    )
    reasoning: str = OutputField(
        description="Brief explanation of classification decision"
    )
```

### REQ-ID-005: IntentMatch Result

```python
@dataclass
class IntentMatch:
    """Result of intent detection."""
    intent: str
    confidence: float
    reasoning: str
    trigger: Optional["IntentTrigger"] = None
    from_cache: bool = False
    detection_method: str = "pattern"  # "pattern", "llm", "cache"
```

### REQ-ID-006: IntentDetector

```python
class IntentDetector:
    """
    LLM-powered intent detector with caching.

    Provides fast pattern matching with LLM fallback for complex cases.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        cache_ttl_seconds: int = 300,
        confidence_threshold: float = 0.7,
        max_cache_size: int = 1000
    ):
        self.model = model
        self.cache_ttl_seconds = cache_ttl_seconds
        self.confidence_threshold = confidence_threshold
        self.max_cache_size = max_cache_size

        # Cache: message hash -> (IntentMatch, timestamp)
        self._cache: Dict[str, tuple] = {}
        self._agent: Optional["BaseAgent"] = None

    async def detect_intent(
        self,
        message: str,
        available_triggers: List["IntentTrigger"],
        context: Dict[str, Any]
    ) -> Optional[IntentMatch]:
        """
        Detect intent from message.

        Order of operations:
        1. Pattern matching (fast, sync)
        2. Cache lookup
        3. LLM classification (slow, async)

        Args:
            message: User message
            available_triggers: List of IntentTrigger to check
            context: Current conversation context

        Returns:
            IntentMatch if intent detected above threshold, None otherwise
        """
        # Step 1: Fast path - pattern matching
        for trigger in available_triggers:
            if trigger.evaluate(message, context):
                return IntentMatch(
                    intent=trigger.get_intent_name(),
                    confidence=1.0,
                    reasoning="Pattern match",
                    trigger=trigger,
                    from_cache=False,
                    detection_method="pattern"
                )

        # Step 2: Check cache
        cache_key = self._cache_key(message, available_triggers)
        cached = self._get_cached(cache_key)
        if cached:
            cached.from_cache = True
            return cached

        # Step 3: LLM classification (only triggers with use_llm_fallback)
        llm_triggers = [t for t in available_triggers if t.use_llm_fallback]
        if not llm_triggers:
            return None

        result = await self._llm_classify(message, llm_triggers, context)

        # Step 4: Cache result
        if result:
            self._cache_result(cache_key, result)

        return result

    async def _llm_classify(
        self,
        message: str,
        triggers: List["IntentTrigger"],
        context: Dict[str, Any]
    ) -> Optional[IntentMatch]:
        """Use LLM for intent classification."""
        import json
        from kaizen.core.base_agent import BaseAgent

        # Lazy initialize agent
        if self._agent is None:
            from dataclasses import dataclass

            @dataclass
            class IntentConfig:
                llm_provider: str = "openai"
                model: str = self.model
                temperature: float = 0.3  # Low temp for classification

            self._agent = BaseAgent(
                config=IntentConfig(),
                signature=IntentClassificationSignature()
            )

        # Build intent list from triggers
        intent_list = []
        trigger_map = {}
        for t in triggers:
            for pattern in t.patterns:
                intent_list.append(pattern)
                trigger_map[pattern] = t

        # Format context for prompt
        context_str = ""
        if context:
            # Only include relevant context fields
            relevant = {k: v for k, v in context.items()
                       if isinstance(v, (str, int, float, bool))}
            context_str = json.dumps(relevant, indent=2)

        # Execute classification
        try:
            result = await self._agent.run_async(
                message=message,
                available_intents=json.dumps(intent_list),
                conversation_context=context_str
            )

            confidence = float(result.get("confidence", 0.0))
            detected_intent = result.get("intent", "unknown")

            if confidence >= self.confidence_threshold and detected_intent != "unknown":
                # Find matching trigger
                trigger = trigger_map.get(detected_intent)
                if trigger:
                    return IntentMatch(
                        intent=detected_intent,
                        confidence=confidence,
                        reasoning=result.get("reasoning", ""),
                        trigger=trigger,
                        from_cache=False,
                        detection_method="llm"
                    )

        except Exception as e:
            # Log error but don't fail - just return None
            import logging
            logging.warning(f"Intent classification failed: {e}")

        return None

    def _cache_key(
        self,
        message: str,
        triggers: List["IntentTrigger"]
    ) -> str:
        """Generate cache key from message and triggers."""
        import hashlib

        # Normalize message
        msg_normalized = message.lower().strip()

        # Sort patterns for consistent key
        patterns_str = "|".join(
            sorted(p for t in triggers for p in t.patterns)
        )

        content = f"{msg_normalized}:{patterns_str}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cached(self, key: str) -> Optional[IntentMatch]:
        """Get cached result if not expired."""
        import time

        if key not in self._cache:
            return None

        result, timestamp = self._cache[key]
        if time.time() - timestamp > self.cache_ttl_seconds:
            del self._cache[key]
            return None

        return result

    def _cache_result(self, key: str, result: IntentMatch):
        """Cache result with timestamp."""
        import time

        # Evict oldest entries if cache full
        if len(self._cache) >= self.max_cache_size:
            oldest_key = min(
                self._cache.keys(),
                key=lambda k: self._cache[k][1]
            )
            del self._cache[oldest_key]

        self._cache[key] = (result, time.time())

    def clear_cache(self):
        """Clear all cached results."""
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        import time
        now = time.time()

        valid_entries = sum(
            1 for _, (_, ts) in self._cache.items()
            if now - ts <= self.cache_ttl_seconds
        )

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "max_size": self.max_cache_size,
            "ttl_seconds": self.cache_ttl_seconds
        }
```

## Test Scenarios

### Test 1: Pattern Matching
```python
def test_intent_trigger_pattern_match():
    trigger = IntentTrigger(patterns=["help", "question"])

    assert trigger.evaluate("I need help", {})
    assert trigger.evaluate("Can I ask a question?", {})
    assert not trigger.evaluate("Book an appointment", {})

def test_pattern_match_word_boundary():
    """Ensure 'help' doesn't match 'helpful'."""
    trigger = IntentTrigger(patterns=["help"])

    assert trigger.evaluate("I need help", {})
    assert not trigger.evaluate("That was helpful", {})
```

### Test 2: LLM Classification
```python
@pytest.mark.asyncio
async def test_llm_classification_fallback(mock_llm):
    detector = IntentDetector(model="gpt-4o-mini")

    triggers = [
        IntentTrigger(
            patterns=["refund"],
            use_llm_fallback=True
        )
    ]

    # Message doesn't match pattern but is about refunds
    result = await detector.detect_intent(
        "I want my money back",
        triggers,
        {}
    )

    assert result is not None
    assert result.detection_method == "llm"
```

### Test 3: Caching
```python
@pytest.mark.asyncio
async def test_cache_hit():
    detector = IntentDetector(cache_ttl_seconds=300)

    triggers = [IntentTrigger(patterns=["help"])]

    # First call - cache miss
    result1 = await detector.detect_intent("need help", triggers, {})

    # Second call - cache hit
    result2 = await detector.detect_intent("need help", triggers, {})

    assert result2.from_cache
```

### Test 4: Transition Context Update
```python
def test_context_append():
    transition = Transition(
        trigger=IntentTrigger(patterns=["change"]),
        context_update={"rejected_doctors": "append:selected_doctor"}
    )

    context = {"rejected_doctors": ["Dr. A"]}
    result = {"selected_doctor": "Dr. B"}

    new_context = transition.apply_context_update(context, result)

    assert new_context["rejected_doctors"] == ["Dr. A", "Dr. B"]
```

## Implementation Tasks

| Task | Effort | Dependencies |
|------|--------|--------------|
| Implement Transition class | 0.5 day | None |
| Implement BaseTrigger, IntentTrigger | 0.5 day | None |
| Implement ConditionTrigger | 0.25 day | BaseTrigger |
| Implement IntentClassificationSignature | 0.25 day | Layer 2 enhancements |
| Implement IntentDetector | 1.5 days | IntentClassificationSignature |
| Implement caching layer | 0.5 day | IntentDetector core |
| Unit tests for triggers | 0.5 day | All triggers |
| Integration tests with LLM | 1 day | IntentDetector |

## Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Pattern match latency | < 1ms | Direct evaluation |
| Cache lookup latency | < 5ms | Hash + dict access |
| LLM classification latency | < 200ms | API call + processing |
| Cache hit rate | > 80% | Repeated messages |
