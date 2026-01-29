# Layer 2 Signature Enhancements

> **Priority**: P0 (Foundation for Layer 5)
> **Effort**: 3 days
> **File**: `kaizen/signatures/core.py`

## Purpose

Enhance the Signature class to support explicit intent and behavioral guidelines:
1. `__intent__` - High-level purpose (WHY the agent exists)
2. `__guidelines__` - Behavioral constraints (HOW the agent should behave)
3. Immutable composition methods for runtime customization

## Requirements

### REQ-L2-001: Intent Extraction

**Current**: Signature uses `__doc__` (docstring) for instructions
**Enhancement**: Add explicit `__intent__` class attribute

```python
class CustomerSupportSignature(Signature):
    """You are a helpful customer support agent."""  # Still used

    __intent__ = "Resolve customer issues efficiently"  # NEW
```

**SignatureMeta changes**:
```python
def __new__(mcs, name, bases, namespace, **kwargs):
    # ... existing field extraction ...

    # NEW: Extract intent
    intent = namespace.get("__intent__", "")
    namespace["_signature_intent"] = intent
```

### REQ-L2-002: Guidelines Extraction

**Enhancement**: Add `__guidelines__` class attribute for behavioral constraints

```python
class CustomerSupportSignature(Signature):
    __guidelines__ = [
        "Acknowledge concerns before solutions",
        "Use empathetic language",
        "Escalate if unresolved in 3 turns"
    ]
```

**SignatureMeta changes**:
```python
def __new__(mcs, name, bases, namespace, **kwargs):
    # ... existing field extraction ...

    # NEW: Extract guidelines
    guidelines = namespace.get("__guidelines__", [])
    namespace["_signature_guidelines"] = list(guidelines)
```

### REQ-L2-003: Property Accessors

Add instance properties for accessing intent and guidelines:

```python
class Signature(metaclass=SignatureMeta):
    _signature_intent: ClassVar[str] = ""
    _signature_guidelines: ClassVar[List[str]] = []

    @property
    def intent(self) -> str:
        """Get the signature's intent (WHY it exists)."""
        return self._signature_intent

    @property
    def guidelines(self) -> List[str]:
        """Get behavioral guidelines (HOW it should behave)."""
        return self._signature_guidelines.copy()  # Return copy to prevent mutation

    @property
    def instructions(self) -> str:
        """DSPy-compatible: Returns __doc__ (docstring)."""
        return self._signature_description
```

### REQ-L2-004: Immutable Composition - with_instructions()

Create new signature with modified instructions without mutating original:

```python
def with_instructions(self, new_instructions: str) -> "Signature":
    """
    Create new Signature instance with modified instructions.

    Immutable: Returns NEW instance, doesn't modify self.

    Args:
        new_instructions: New instruction text

    Returns:
        New Signature instance with updated instructions
    """
    new_sig = self._clone()
    new_sig._signature_description = new_instructions
    return new_sig
```

### REQ-L2-005: Immutable Composition - with_guidelines()

Create new signature with additional guidelines:

```python
def with_guidelines(self, additional_guidelines: List[str]) -> "Signature":
    """
    Create new Signature instance with additional guidelines.

    Immutable: Returns NEW instance, doesn't modify self.

    Args:
        additional_guidelines: Guidelines to append

    Returns:
        New Signature instance with extended guidelines
    """
    new_sig = self._clone()
    new_sig._signature_guidelines = self._signature_guidelines + list(additional_guidelines)
    return new_sig
```

### REQ-L2-006: Clone Helper

Internal method for immutable operations:

```python
def _clone(self) -> "Signature":
    """Create shallow clone of signature for immutable operations."""
    # Create new instance of same class
    new_sig = object.__new__(self.__class__)

    # Copy class-level attributes
    new_sig._signature_description = self._signature_description
    new_sig._signature_intent = self._signature_intent
    new_sig._signature_guidelines = self._signature_guidelines.copy()
    new_sig._signature_inputs = self._signature_inputs.copy()
    new_sig._signature_outputs = self._signature_outputs.copy()

    return new_sig
```

## Test Scenarios

### Test 1: Intent Extraction
```python
def test_intent_from_class_attribute():
    class MySig(Signature):
        __intent__ = "Test intent"
        question: str = InputField(desc="Q")
        answer: str = OutputField(desc="A")

    sig = MySig()
    assert sig.intent == "Test intent"

def test_missing_intent_defaults_to_empty():
    class MySig(Signature):
        question: str = InputField(desc="Q")
        answer: str = OutputField(desc="A")

    sig = MySig()
    assert sig.intent == ""
```

### Test 2: Guidelines Extraction
```python
def test_guidelines_from_class_attribute():
    class MySig(Signature):
        __guidelines__ = ["G1", "G2"]
        q: str = InputField(desc="Q")
        a: str = OutputField(desc="A")

    sig = MySig()
    assert sig.guidelines == ["G1", "G2"]

def test_guidelines_are_copied():
    """Ensure guidelines property returns copy, not reference."""
    class MySig(Signature):
        __guidelines__ = ["G1"]
        q: str = InputField(desc="Q")
        a: str = OutputField(desc="A")

    sig = MySig()
    guidelines = sig.guidelines
    guidelines.append("G2")
    assert sig.guidelines == ["G1"]  # Original unchanged
```

### Test 3: Immutable Composition
```python
def test_with_instructions_creates_new_instance():
    class MySig(Signature):
        """Original instructions."""
        q: str = InputField(desc="Q")
        a: str = OutputField(desc="A")

    sig1 = MySig()
    sig2 = sig1.with_instructions("New instructions.")

    assert sig1.instructions == "Original instructions."
    assert sig2.instructions == "New instructions."
    assert sig1 is not sig2

def test_with_guidelines_appends():
    class MySig(Signature):
        __guidelines__ = ["G1"]
        q: str = InputField(desc="Q")
        a: str = OutputField(desc="A")

    sig1 = MySig()
    sig2 = sig1.with_guidelines(["G2", "G3"])

    assert sig1.guidelines == ["G1"]
    assert sig2.guidelines == ["G1", "G2", "G3"]
```

### Test 4: Inheritance
```python
def test_intent_inheritance():
    class BaseSig(Signature):
        __intent__ = "Base intent"
        q: str = InputField(desc="Q")
        a: str = OutputField(desc="A")

    class ChildSig(BaseSig):
        pass  # Should inherit intent

    sig = ChildSig()
    assert sig.intent == "Base intent"

def test_intent_override():
    class BaseSig(Signature):
        __intent__ = "Base intent"
        q: str = InputField(desc="Q")
        a: str = OutputField(desc="A")

    class ChildSig(BaseSig):
        __intent__ = "Child intent"

    sig = ChildSig()
    assert sig.intent == "Child intent"
```

## Implementation Tasks

| Task | Effort | Dependencies |
|------|--------|--------------|
| Add `_signature_intent` to SignatureMeta | 0.5 day | None |
| Add `_signature_guidelines` to SignatureMeta | 0.5 day | None |
| Add `intent`, `guidelines`, `instructions` properties | 0.5 day | SignatureMeta changes |
| Implement `with_instructions()` | 0.5 day | Properties |
| Implement `with_guidelines()` | 0.5 day | Properties |
| Implement `_clone()` helper | 0.25 day | None |
| Unit tests (Tier 1) | 0.5 day | All implementation |
| Integration tests with BaseAgent | 0.25 day | Unit tests |

## Backward Compatibility

- Signatures without `__intent__` or `__guidelines__` will have empty defaults
- Existing signatures continue to work without modification
- `__doc__` (docstring) still extracted as `_signature_description`
- No breaking changes to existing API

## Integration with BaseAgent

BaseAgent's WorkflowGenerator should use intent and guidelines in prompt construction:

```python
# In WorkflowGenerator._generate_system_prompt():
parts = []

# Add description (docstring)
if hasattr(self.signature, "description") and self.signature.description:
    parts.append(self.signature.description)

# NEW: Add intent
if hasattr(self.signature, "intent") and self.signature.intent:
    parts.append(f"\nIntent: {self.signature.intent}")

# NEW: Add guidelines
if hasattr(self.signature, "guidelines") and self.signature.guidelines:
    parts.append("\nGuidelines:")
    for g in self.signature.guidelines:
        parts.append(f"- {g}")
```
