# 01: Architecture Design - Unified Azure Provider

## Document Control
- **Version**: 1.0
- **Date**: 2026-01-16
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## 1. Current State Analysis

### Existing Implementation

**File**: `src/kaizen/nodes/ai/ai_providers.py`
**Class**: `AzureAIFoundryProvider` (Lines 2169-2673)

| Component | Status | Location |
|-----------|--------|----------|
| `AzureAIFoundryProvider` | Exists | ai_providers.py:2169-2673 |
| Azure config | Exists | config/providers.py:222-249 |
| Provider registration | Exists | ai_providers.py:4332 |
| Unit tests | Exists | tests/unit/nodes/ai/test_azure_provider.py |
| Integration tests | Exists | tests/integration/nodes/ai/test_azure_integration.py |

### Identified Gaps

| Gap | Description | Impact |
|-----|-------------|--------|
| No Azure OpenAI backend | Only AI Foundry supported | Enterprise users blocked |
| No api_version handling | SDK defaults may fail | json_schema fails |
| No reasoning model support | Temperature sent to o1/o3/GPT-5 | API errors |
| No unified detection | Users must know backend | Poor UX |

---

## 2. Target Architecture

### Class Hierarchy

```python
# Base classes
class AzureBackend(ABC):
    """Abstract base for Azure backends."""

    @abstractmethod
    def is_configured(self) -> bool: ...

    @abstractmethod
    def get_backend_type(self) -> str: ...

    @abstractmethod
    def chat(self, messages, **kwargs) -> dict: ...

    @abstractmethod
    async def chat_async(self, messages, **kwargs) -> dict: ...

    @abstractmethod
    def embed(self, texts, **kwargs) -> list: ...

# Concrete backends
class AzureOpenAIBackend(AzureBackend):
    """Uses openai SDK with AzureOpenAI client."""

class AzureAIFoundryBackend(AzureBackend):
    """Uses azure-ai-inference SDK (wraps existing AzureAIFoundryProvider)."""

# Unified provider (user-facing)
class UnifiedAzureProvider(UnifiedAIProvider):
    """Intelligent unified provider with auto-detection."""
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| `UnifiedAzureProvider` | Single entry point, delegates to backends |
| `AzureBackendDetector` | Pattern matching, smart defaults, error-based fallback |
| `AzureCapabilityRegistry` | Feature support checking, gap handling |
| `AzureOpenAIBackend` | Azure OpenAI Service API calls |
| `AzureAIFoundryBackend` | Azure AI Foundry API calls |
| `CredentialManager` | Unified credential resolution with rotation |

---

## 3. File Structure

```
src/kaizen/
├── providers/
│   └── azure/
│       ├── __init__.py           # Public exports
│       ├── unified.py            # UnifiedAzureProvider
│       ├── detector.py           # AzureBackendDetector
│       ├── capabilities.py       # AzureCapabilityRegistry
│       ├── credentials.py        # CredentialManager
│       ├── errors.py             # Azure-specific errors
│       └── backends/
│           ├── __init__.py
│           ├── base.py           # AzureBackend ABC
│           ├── openai.py         # AzureOpenAIBackend
│           └── foundry.py        # AzureAIFoundryBackend
├── nodes/ai/
│   └── ai_providers.py           # Update PROVIDERS dict
└── config/
    └── providers.py              # Update Azure config
```

### Alternative: In-Place Refactoring

To minimize disruption, we could also refactor within existing files:

```
src/kaizen/nodes/ai/
├── ai_providers.py               # Add UnifiedAzureProvider, backends
├── azure_detection.py            # NEW: AzureBackendDetector
├── azure_capabilities.py         # NEW: AzureCapabilityRegistry
└── azure_backends.py             # NEW: Backend implementations
```

**Recommendation**: Use in-place refactoring for Phase 1, extract to `providers/azure/` in future cleanup.

---

## 4. Key Interfaces

### AzureBackend (Abstract)

```python
from abc import ABC, abstractmethod
from typing import Any, Optional

class AzureBackend(ABC):
    """Abstract base class for Azure service backends."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if backend has valid configuration."""
        pass

    @abstractmethod
    def get_backend_type(self) -> str:
        """Return backend identifier: 'azure_openai' or 'azure_ai_foundry'."""
        pass

    @abstractmethod
    def chat(self, messages: list[dict], **kwargs) -> dict[str, Any]:
        """Synchronous chat completion."""
        pass

    @abstractmethod
    async def chat_async(self, messages: list[dict], **kwargs) -> dict[str, Any]:
        """Asynchronous chat completion."""
        pass

    @abstractmethod
    def embed(self, texts: list[str], **kwargs) -> list[list[float]]:
        """Generate embeddings."""
        pass

    @abstractmethod
    async def embed_async(self, texts: list[str], **kwargs) -> list[list[float]]:
        """Async embedding generation."""
        pass

    def _is_reasoning_model(self, model: str) -> bool:
        """Check if model is a reasoning model (o1, o3, GPT-5)."""
        if not model:
            return False
        reasoning_prefixes = ("o1", "o3", "gpt-5", "gpt5")
        return any(model.lower().startswith(p) for p in reasoning_prefixes)
```

### UnifiedAzureProvider

```python
class UnifiedAzureProvider(UnifiedAIProvider):
    """
    Unified Azure provider with intelligent backend selection.

    Auto-detects Azure OpenAI Service vs Azure AI Foundry from endpoint URL.
    Provides automatic fallback on backend-specific errors.

    Environment Variables:
        AZURE_ENDPOINT: Unified endpoint URL (auto-detected)
        AZURE_API_KEY: Unified API key
        AZURE_API_VERSION: API version (Azure OpenAI only)
        AZURE_DEPLOYMENT: Default deployment/model name
        AZURE_BACKEND: Explicit override ('openai' or 'foundry')

    Legacy (backward compatible):
        AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY
        AZURE_AI_INFERENCE_ENDPOINT, AZURE_AI_INFERENCE_API_KEY
    """

    _capabilities = {
        "chat": True,
        "embeddings": True,
        "streaming": True,
        "tool_calling": True,
    }

    def __init__(
        self,
        preferred_backend: Optional[str] = None,
        fallback_enabled: bool = True,
        use_async: bool = False,
    ):
        super().__init__()
        self._preferred_backend = preferred_backend
        self._fallback_enabled = fallback_enabled
        self._use_async = use_async
        self._detector = AzureBackendDetector()
        self._registry = None  # Lazy init
        self._active_backend: Optional[AzureBackend] = None

    def supports(self, feature: str) -> bool:
        """Check if feature is supported on current backend."""
        if self._registry is None:
            backend_type = self._get_backend().get_backend_type()
            self._registry = AzureCapabilityRegistry(backend_type)
        return self._registry.supports(feature)

    def get_capabilities(self) -> dict[str, bool]:
        """Get all capabilities for current backend."""
        if self._registry is None:
            backend_type = self._get_backend().get_backend_type()
            self._registry = AzureCapabilityRegistry(backend_type)
        return self._registry.get_capabilities()
```

---

## 5. Integration Points

### Provider Registration

Update `ai_providers.py` PROVIDERS dict:

```python
PROVIDERS = {
    # ... existing providers ...
    "azure": UnifiedAzureProvider,      # Unified (recommended)
    "azure_openai": AzureOpenAIBackend,  # Explicit Azure OpenAI
    "azure_foundry": AzureAIFoundryBackend,  # Explicit AI Foundry
    # Legacy alias (deprecated with warning)
    "azure_ai_foundry": AzureAIFoundryBackend,
}
```

### Configuration Integration

Update `config/providers.py`:

```python
def check_azure_available() -> bool:
    """Check if any Azure backend is configured."""
    # Unified
    if os.getenv("AZURE_ENDPOINT") and os.getenv("AZURE_API_KEY"):
        return True
    # Azure OpenAI
    if os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY"):
        return True
    # AI Foundry (legacy)
    if os.getenv("AZURE_AI_INFERENCE_ENDPOINT") and os.getenv("AZURE_AI_INFERENCE_API_KEY"):
        return True
    return False
```

---

## 6. Design Decisions

### Decision 1: Unified vs Separate Providers

**Decision**: Single `UnifiedAzureProvider` with internal backends

**Rationale**:
- Users shouldn't need to understand Azure's service fragmentation
- Automatic detection provides better UX
- Fallback improves reliability
- Internal backends can still be exposed for advanced users

### Decision 2: Refactor vs New Implementation

**Decision**: Wrap existing `AzureAIFoundryProvider` as `AzureAIFoundryBackend`

**Rationale**:
- Preserves existing working code
- Minimizes regression risk
- Faster implementation
- Existing tests continue to work

### Decision 3: Detection Algorithm

**Decision**: Pattern match first, default to OpenAI, error-based fallback

**Rationale**:
- Pattern matching is deterministic and fast (0ms)
- Azure OpenAI is more common (80%+ enterprise usage)
- Error-based fallback handles edge cases without probing

---

## 7. Dependencies

### Required Packages

| Package | Purpose | Status |
|---------|---------|--------|
| `openai` | Azure OpenAI backend | New dependency for Azure OpenAI |
| `azure-ai-inference` | AI Foundry backend | Existing |
| `azure-identity` | Managed identity | Existing |

### Internal Dependencies

| Component | Depends On |
|-----------|-----------|
| `UnifiedAzureProvider` | `AzureBackendDetector`, `AzureCapabilityRegistry`, backends |
| `AzureBackendDetector` | Environment variables |
| `AzureOpenAIBackend` | `openai.AzureOpenAI` |
| `AzureAIFoundryBackend` | Existing `AzureAIFoundryProvider` |

---

## 8. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| SDK version conflicts | Pin openai>=1.0.0, azure-ai-inference>=1.0.0b9 |
| Credential handling differences | Abstract in CredentialManager |
| Response format differences | Normalize in backend classes |
| Breaking existing code | Deprecation warnings, migration period |
