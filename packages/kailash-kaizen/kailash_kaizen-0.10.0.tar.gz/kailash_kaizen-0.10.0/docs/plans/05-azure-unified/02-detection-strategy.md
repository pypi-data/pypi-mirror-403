# 02: Detection Strategy - Azure Backend Auto-Detection

## Document Control
- **Version**: 1.0
- **Date**: 2026-01-16
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## 1. Detection Algorithm Overview

### Strategy: Hybrid Pattern Match + Smart Default

```
┌─────────────────────────────────────────────────────────────┐
│  1. Check for explicit override (AZURE_BACKEND env var)     │
│     → If set, use specified backend directly                │
├─────────────────────────────────────────────────────────────┤
│  2. Pattern match endpoint URL (95% cases, 0ms)             │
│     *.openai.azure.com → Azure OpenAI                       │
│     *.inference.ai.azure.com → AI Foundry                   │
│     *.services.ai.azure.com → AI Foundry                    │
├─────────────────────────────────────────────────────────────┤
│  3. Unknown Pattern → Default to Azure OpenAI               │
│     (80%+ of enterprise usage)                              │
│     Log warning for visibility                              │
├─────────────────────────────────────────────────────────────┤
│  4. On API Error → Check error signatures                   │
│     "audience is incorrect" → Switch to AI Foundry          │
│     "DeploymentNotFound" → May need different backend       │
├─────────────────────────────────────────────────────────────┤
│  5. Retry with alternate backend (max 1 retry)              │
│     If fallback also fails, raise with diagnostic info      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Endpoint Patterns

### Azure OpenAI Service Patterns

```python
AZURE_OPENAI_PATTERNS = [
    r".*\.openai\.azure\.com",              # Standard
    r".*\.privatelink\.openai\.azure\.com",  # Private endpoint
    r".*\.cognitiveservices\.azure\.com",    # Legacy cognitive services
]
```

**Examples**:
- `https://my-resource.openai.azure.com/`
- `https://my-resource.privatelink.openai.azure.com/`
- `https://westus.api.cognitive.microsoft.com/`

### Azure AI Foundry Patterns

```python
AZURE_AI_FOUNDRY_PATTERNS = [
    r".*\.inference\.ai\.azure\.com",        # Standard inference
    r".*\.services\.ai\.azure\.com",         # AI services
    r".*\.api\.cognitive\.microsoft\.com",   # Regional cognitive
]
```

**Examples**:
- `https://my-model.inference.ai.azure.com/`
- `https://my-resource.services.ai.azure.com/models/`
- `https://southeastasia.api.cognitive.microsoft.com/openai`

---

## 3. Implementation

### AzureBackendDetector Class

```python
import os
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class AzureBackendDetector:
    """
    Intelligent Azure backend detection from endpoint URL.

    Detection Priority:
    1. Explicit AZURE_BACKEND env var
    2. Pattern matching on endpoint URL
    3. Default to Azure OpenAI (most common)
    4. Error-based correction on API failure
    """

    AZURE_OPENAI_PATTERNS = [
        r".*\.openai\.azure\.com",
        r".*\.privatelink\.openai\.azure\.com",
        r".*cognitiveservices\.azure\.com.*openai",
    ]

    AZURE_AI_FOUNDRY_PATTERNS = [
        r".*\.inference\.ai\.azure\.com",
        r".*\.services\.ai\.azure\.com",
        r".*\.api\.cognitive\.microsoft\.com(?!/openai)",
    ]

    # Error signatures indicating wrong backend
    FOUNDRY_ERROR_SIGNATURES = [
        "audience is incorrect",
        "token audience",
        "invalid audience",
    ]

    OPENAI_ERROR_SIGNATURES = [
        "deploymentnotfound",
        "resource not found",
        "the api deployment for this resource does not exist",
    ]

    def __init__(self):
        self._detected_backend: Optional[str] = None
        self._detection_source: Optional[str] = None
        self._endpoint: Optional[str] = None

    def detect(self) -> Tuple[Optional[str], dict]:
        """
        Detect appropriate Azure backend.

        Returns:
            Tuple of (backend_type, config_dict)
            backend_type: "azure_openai", "azure_ai_foundry", or None
        """
        # Priority 1: Explicit override
        explicit = os.getenv("AZURE_BACKEND")
        if explicit:
            backend = self._normalize_backend_name(explicit)
            self._detected_backend = backend
            self._detection_source = "explicit"
            logger.info(f"Azure backend explicitly set: {backend}")
            return backend, self._get_config(backend)

        # Get endpoint for pattern matching
        endpoint = self._get_endpoint()
        if not endpoint:
            return None, {}

        self._endpoint = endpoint

        # Priority 2: Pattern matching
        backend = self._detect_from_pattern(endpoint)
        if backend:
            self._detected_backend = backend
            self._detection_source = "pattern"
            logger.info(f"Azure backend detected from pattern: {backend}")
            return backend, self._get_config(backend)

        # Priority 3: Default to Azure OpenAI
        self._detected_backend = "azure_openai"
        self._detection_source = "default"
        logger.warning(
            f"Unknown Azure endpoint pattern: {endpoint}. "
            "Defaulting to Azure OpenAI. Set AZURE_BACKEND to override."
        )
        return "azure_openai", self._get_config("azure_openai")

    def _detect_from_pattern(self, endpoint: str) -> Optional[str]:
        """Detect backend from endpoint URL pattern."""
        endpoint_lower = endpoint.lower()

        for pattern in self.AZURE_OPENAI_PATTERNS:
            if re.search(pattern, endpoint_lower, re.IGNORECASE):
                return "azure_openai"

        for pattern in self.AZURE_AI_FOUNDRY_PATTERNS:
            if re.search(pattern, endpoint_lower, re.IGNORECASE):
                return "azure_ai_foundry"

        return None

    def handle_error(self, error: Exception) -> Optional[str]:
        """
        Analyze error to detect if wrong backend was used.

        Returns:
            Correct backend if detected from error, None otherwise
        """
        error_str = str(error).lower()

        # Check if error suggests we should switch backends
        if self._detected_backend == "azure_openai":
            for sig in self.FOUNDRY_ERROR_SIGNATURES:
                if sig in error_str:
                    logger.info(
                        f"Error signature suggests Azure AI Foundry: '{sig}'"
                    )
                    self._detected_backend = "azure_ai_foundry"
                    self._detection_source = "error_fallback"
                    return "azure_ai_foundry"

        elif self._detected_backend == "azure_ai_foundry":
            for sig in self.OPENAI_ERROR_SIGNATURES:
                if sig in error_str:
                    logger.info(
                        f"Error signature suggests Azure OpenAI: '{sig}'"
                    )
                    self._detected_backend = "azure_openai"
                    self._detection_source = "error_fallback"
                    return "azure_openai"

        return None

    def _get_endpoint(self) -> Optional[str]:
        """Get endpoint from environment variables."""
        return (
            os.getenv("AZURE_ENDPOINT") or
            os.getenv("AZURE_OPENAI_ENDPOINT") or
            os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
        )

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables."""
        return (
            os.getenv("AZURE_API_KEY") or
            os.getenv("AZURE_OPENAI_API_KEY") or
            os.getenv("AZURE_AI_INFERENCE_API_KEY")
        )

    def _get_config(self, backend: str) -> dict:
        """Get configuration for specified backend."""
        return {
            "endpoint": self._get_endpoint(),
            "api_key": self._get_api_key(),
            "api_version": os.getenv("AZURE_API_VERSION", "2024-10-21"),
            "deployment": os.getenv("AZURE_DEPLOYMENT"),
            "backend": backend,
        }

    def _normalize_backend_name(self, name: str) -> str:
        """Normalize backend name to canonical form."""
        name_lower = name.lower().strip()
        if name_lower in ("openai", "azure_openai", "azureopenai"):
            return "azure_openai"
        if name_lower in ("foundry", "ai_foundry", "azure_ai_foundry", "aifoundry"):
            return "azure_ai_foundry"
        raise ValueError(
            f"Invalid AZURE_BACKEND value: '{name}'. "
            "Use 'openai' or 'foundry'."
        )

    @property
    def detected_backend(self) -> Optional[str]:
        """Return currently detected backend."""
        return self._detected_backend

    @property
    def detection_source(self) -> Optional[str]:
        """Return how backend was detected."""
        return self._detection_source
```

---

## 4. Why Not Probe?

### Probing Analysis

| Factor | Probing | Pattern Match |
|--------|---------|---------------|
| Latency | +100-200ms per first request | 0ms |
| Reliability | 95% (firewalls may block) | 99%+ |
| Network required | Yes (before main request) | No |
| Security | Potential info leak | No concerns |

### Decision: No Probing

Probing adds unacceptable latency for real-time applications. Pattern matching + error-based fallback achieves similar accuracy without the latency cost.

---

## 5. Error Signature Analysis

### Azure OpenAI → Should Use Foundry

```
Error: "audience is incorrect (https://cognitiveservices.azure.com)"
Meaning: Token was generated for wrong service
Action: Switch to AI Foundry backend
```

### Azure AI Foundry → Should Use OpenAI

```
Error: "DeploymentNotFound: The API deployment does not exist"
Meaning: Deployment name format is wrong for this service
Action: Switch to Azure OpenAI backend
```

### Non-Backend Errors (Don't Switch)

```
- 401 Unauthorized → Check API key
- 403 Forbidden → Check RBAC permissions
- 429 Rate Limited → Implement backoff
- 500 Server Error → Retry with backoff
```

---

## 6. Fallback Behavior

### Fallback Flow

```
1. Primary backend fails with error
2. Check if error matches "wrong backend" signatures
3. If yes: switch to alternate backend, retry once
4. If no: propagate original error
5. If fallback also fails: raise comprehensive error with both failures
```

### Comprehensive Error Message

```python
class AzureBackendError(Exception):
    """Raised when both Azure backends fail."""

    def __init__(
        self,
        primary_backend: str,
        primary_error: Exception,
        fallback_backend: Optional[str] = None,
        fallback_error: Optional[Exception] = None,
    ):
        message = f"Azure {primary_backend} error: {primary_error}"

        if fallback_backend and fallback_error:
            message += f"\nFallback to {fallback_backend} also failed: {fallback_error}"

        message += "\n\nTroubleshooting:\n"
        message += "1. Check AZURE_ENDPOINT is correct\n"
        message += "2. Check AZURE_API_KEY is valid\n"
        message += "3. Set AZURE_BACKEND=openai or AZURE_BACKEND=foundry to force backend"

        super().__init__(message)
```

---

## 7. Testing Requirements

### Unit Tests

```python
# tests/unit/providers/azure/test_detection.py

class TestAzureBackendDetector:
    """Unit tests for backend detection."""

    def test_detects_azure_openai_standard(self):
        """*.openai.azure.com → Azure OpenAI"""

    def test_detects_azure_openai_private_endpoint(self):
        """*.privatelink.openai.azure.com → Azure OpenAI"""

    def test_detects_ai_foundry_inference(self):
        """*.inference.ai.azure.com → AI Foundry"""

    def test_detects_ai_foundry_services(self):
        """*.services.ai.azure.com → AI Foundry"""

    def test_unknown_defaults_to_openai(self):
        """Unknown pattern defaults to Azure OpenAI"""

    def test_explicit_override_respected(self):
        """AZURE_BACKEND env var takes precedence"""

    def test_error_fallback_to_foundry(self):
        """'audience is incorrect' triggers switch to Foundry"""

    def test_error_fallback_to_openai(self):
        """'DeploymentNotFound' triggers switch to OpenAI"""
```

### Integration Tests

```python
# tests/integration/providers/azure/test_detection_integration.py

@pytest.mark.integration
class TestAzureDetectionIntegration:
    """Integration tests with real Azure endpoints."""

    def test_auto_detection_azure_openai(self, azure_openai_endpoint):
        """Should correctly detect and use Azure OpenAI."""

    def test_auto_detection_ai_foundry(self, ai_foundry_endpoint):
        """Should correctly detect and use AI Foundry."""

    def test_fallback_on_wrong_backend(self, misconfigured_endpoint):
        """Should fallback when initial backend fails."""
```
