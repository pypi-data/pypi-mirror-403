# 04: Environment Variables - Configuration Strategy

## Document Control
- **Version**: 1.0
- **Date**: 2026-01-16
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## 1. Environment Variable Overview

### Unified Variables (Recommended)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `AZURE_ENDPOINT` | Yes | Azure endpoint URL | `https://my-resource.openai.azure.com` |
| `AZURE_API_KEY` | Yes* | API key (*or use managed identity) | `abc123...` |
| `AZURE_API_VERSION` | No | API version (defaults to 2024-10-21) | `2024-10-21` |
| `AZURE_DEPLOYMENT` | No | Default deployment/model name | `gpt-4o` |
| `AZURE_BACKEND` | No | Explicit backend override | `openai` or `foundry` |

### Legacy Variables (Backward Compatible)

#### Azure OpenAI Legacy

| Variable | Maps To |
|----------|---------|
| `AZURE_OPENAI_ENDPOINT` | `AZURE_ENDPOINT` |
| `AZURE_OPENAI_API_KEY` | `AZURE_API_KEY` |

#### Azure AI Foundry Legacy

| Variable | Maps To |
|----------|---------|
| `AZURE_AI_INFERENCE_ENDPOINT` | `AZURE_ENDPOINT` |
| `AZURE_AI_INFERENCE_API_KEY` | `AZURE_API_KEY` |

---

## 2. Resolution Priority

### Endpoint Resolution

```python
def _get_endpoint() -> Optional[str]:
    """
    Get Azure endpoint with priority:
    1. AZURE_ENDPOINT (unified)
    2. AZURE_OPENAI_ENDPOINT (legacy Azure OpenAI)
    3. AZURE_AI_INFERENCE_ENDPOINT (legacy AI Foundry)
    """
    return (
        os.getenv("AZURE_ENDPOINT") or
        os.getenv("AZURE_OPENAI_ENDPOINT") or
        os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
    )
```

### API Key Resolution

```python
def _get_api_key() -> Optional[str]:
    """
    Get API key with priority:
    1. AZURE_API_KEY (unified)
    2. AZURE_OPENAI_API_KEY (legacy Azure OpenAI)
    3. AZURE_AI_INFERENCE_API_KEY (legacy AI Foundry)
    """
    return (
        os.getenv("AZURE_API_KEY") or
        os.getenv("AZURE_OPENAI_API_KEY") or
        os.getenv("AZURE_AI_INFERENCE_API_KEY")
    )
```

---

## 3. Conflict Resolution

### When Multiple Variables Are Set

```python
def _resolve_config() -> dict:
    """
    Resolve configuration with conflict handling.

    Rules:
    1. Unified vars (AZURE_*) take precedence
    2. If only legacy vars set, use them
    3. If both legacy types set, prefer Azure OpenAI + warn
    """
    unified_endpoint = os.getenv("AZURE_ENDPOINT")
    unified_key = os.getenv("AZURE_API_KEY")

    openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai_key = os.getenv("AZURE_OPENAI_API_KEY")

    foundry_endpoint = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
    foundry_key = os.getenv("AZURE_AI_INFERENCE_API_KEY")

    # Priority 1: Unified
    if unified_endpoint:
        return {
            "endpoint": unified_endpoint,
            "api_key": unified_key,
            "source": "unified",
        }

    # Check for conflict
    openai_configured = bool(openai_endpoint and openai_key)
    foundry_configured = bool(foundry_endpoint and foundry_key)

    if openai_configured and foundry_configured:
        import warnings
        warnings.warn(
            "Both AZURE_OPENAI_* and AZURE_AI_INFERENCE_* are set. "
            "Using AZURE_OPENAI_*. Set AZURE_ENDPOINT for unified config.",
            UserWarning,
            stacklevel=2
        )
        return {
            "endpoint": openai_endpoint,
            "api_key": openai_key,
            "source": "azure_openai",
            "conflict_detected": True,
        }

    # Priority 2: Azure OpenAI legacy
    if openai_configured:
        return {
            "endpoint": openai_endpoint,
            "api_key": openai_key,
            "source": "azure_openai",
        }

    # Priority 3: AI Foundry legacy
    if foundry_configured:
        return {
            "endpoint": foundry_endpoint,
            "api_key": foundry_key,
            "source": "azure_ai_foundry",
        }

    return {"source": None}
```

---

## 4. Configuration Examples

### Minimal Configuration

```bash
# Just these two are required
export AZURE_ENDPOINT="https://my-resource.openai.azure.com"
export AZURE_API_KEY="your-api-key-here"
```

### Full Configuration

```bash
# Complete configuration
export AZURE_ENDPOINT="https://my-resource.openai.azure.com"
export AZURE_API_KEY="your-api-key-here"
export AZURE_API_VERSION="2024-10-21"
export AZURE_DEPLOYMENT="gpt-4o"
```

### Explicit Backend Override

```bash
# Force specific backend
export AZURE_ENDPOINT="https://custom-proxy.company.com/azure"
export AZURE_API_KEY="your-api-key-here"
export AZURE_BACKEND="openai"  # or "foundry"
```

### Legacy Azure OpenAI

```bash
# These still work (backward compatible)
export AZURE_OPENAI_ENDPOINT="https://my-resource.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-api-key-here"
```

### Legacy AI Foundry

```bash
# These still work (backward compatible)
export AZURE_AI_INFERENCE_ENDPOINT="https://my-resource.inference.ai.azure.com"
export AZURE_AI_INFERENCE_API_KEY="your-api-key-here"
```

---

## 5. Managed Identity Support

### Using DefaultAzureCredential

```bash
# No API key needed when using managed identity
export AZURE_ENDPOINT="https://my-resource.openai.azure.com"
# AZURE_API_KEY not set - will use managed identity
```

### Implementation

```python
def _get_credential(self):
    """
    Get Azure credential.

    Priority:
    1. API key from environment
    2. DefaultAzureCredential (managed identity, CLI, etc.)
    """
    api_key = self._get_api_key()
    if api_key:
        from azure.core.credentials import AzureKeyCredential
        return AzureKeyCredential(api_key)

    try:
        from azure.identity import DefaultAzureCredential
        return DefaultAzureCredential()
    except ImportError:
        raise RuntimeError(
            "No API key found and azure-identity not installed. "
            "Either set AZURE_API_KEY or install azure-identity: "
            "pip install azure-identity"
        )
```

---

## 6. Validation

### Required Variable Checking

```python
def _validate_config(self) -> None:
    """
    Validate Azure configuration.

    Raises:
        ConfigurationError: If required configuration is missing
    """
    endpoint = self._get_endpoint()
    if not endpoint:
        raise ConfigurationError(
            "Azure endpoint not configured. Set one of:\n"
            "  1. AZURE_ENDPOINT (recommended)\n"
            "  2. AZURE_OPENAI_ENDPOINT (Azure OpenAI)\n"
            "  3. AZURE_AI_INFERENCE_ENDPOINT (AI Foundry)"
        )

    # API key is optional if using managed identity
    # Will be validated when credential is retrieved
```

### Endpoint URL Validation

```python
def _validate_endpoint_url(self, endpoint: str) -> str:
    """
    Validate endpoint URL format.

    Checks:
    - Uses HTTPS
    - Valid URL format
    - Warns for non-Azure domains
    """
    from urllib.parse import urlparse

    parsed = urlparse(endpoint)

    # Must use HTTPS
    if parsed.scheme != "https":
        raise ConfigurationError(
            f"Azure endpoint must use HTTPS. Got: {parsed.scheme}"
        )

    # Must have host
    if not parsed.netloc:
        raise ConfigurationError(
            f"Invalid Azure endpoint URL: {endpoint}"
        )

    # Warn for non-Azure domains
    azure_domains = [".azure.com", ".microsoft.com"]
    if not any(parsed.netloc.endswith(d) for d in azure_domains):
        import warnings
        warnings.warn(
            f"Non-standard Azure endpoint domain: {parsed.netloc}. "
            "If this is intentional (proxy, custom domain), you can ignore this warning.",
            UserWarning
        )

    return endpoint
```

---

## 7. Configuration Provider Integration

### Update to config/providers.py

```python
def check_azure_available() -> bool:
    """
    Check if any Azure backend is configured.

    Returns True if either:
    - Unified vars (AZURE_ENDPOINT + AZURE_API_KEY or managed identity)
    - Azure OpenAI vars (AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY)
    - Azure AI Foundry vars (AZURE_AI_INFERENCE_ENDPOINT + AZURE_AI_INFERENCE_API_KEY)
    """
    # Check unified
    if os.getenv("AZURE_ENDPOINT"):
        # Either API key or managed identity can be used
        if os.getenv("AZURE_API_KEY"):
            return True
        try:
            from azure.identity import DefaultAzureCredential
            return True  # Managed identity available
        except ImportError:
            pass

    # Check Azure OpenAI
    if os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY"):
        return True

    # Check AI Foundry
    if os.getenv("AZURE_AI_INFERENCE_ENDPOINT") and os.getenv("AZURE_AI_INFERENCE_API_KEY"):
        return True

    return False


def get_azure_config(model: Optional[str] = None) -> ProviderConfig:
    """
    Get unified Azure provider configuration.

    Automatically resolves configuration from available env vars.
    """
    if not check_azure_available():
        raise ConfigurationError(
            "Azure not configured. Set one of:\n"
            "  1. AZURE_ENDPOINT + AZURE_API_KEY (recommended)\n"
            "  2. AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY\n"
            "  3. AZURE_AI_INFERENCE_ENDPOINT + AZURE_AI_INFERENCE_API_KEY"
        )

    # Get endpoint
    endpoint = (
        os.getenv("AZURE_ENDPOINT") or
        os.getenv("AZURE_OPENAI_ENDPOINT") or
        os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
    )

    # Get API key
    api_key = (
        os.getenv("AZURE_API_KEY") or
        os.getenv("AZURE_OPENAI_API_KEY") or
        os.getenv("AZURE_AI_INFERENCE_API_KEY")
    )

    # Default model
    default_model = os.getenv("AZURE_DEPLOYMENT", "gpt-4o")

    return ProviderConfig(
        provider="azure",
        model=model or os.getenv("KAIZEN_AZURE_MODEL", default_model),
        api_key=api_key,
        base_url=endpoint,
        timeout=int(os.getenv("KAIZEN_TIMEOUT", "60")),
        max_retries=int(os.getenv("KAIZEN_MAX_RETRIES", "3")),
    )
```

---

## 8. Testing Requirements

### Unit Tests

```python
class TestAzureConfiguration:
    """Unit tests for Azure configuration resolution."""

    def test_unified_vars_take_precedence(self, monkeypatch):
        """AZURE_ENDPOINT should override legacy vars."""
        monkeypatch.setenv("AZURE_ENDPOINT", "https://unified.openai.azure.com")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://legacy.openai.azure.com")

        config = _resolve_config()
        assert config["endpoint"] == "https://unified.openai.azure.com"
        assert config["source"] == "unified"

    def test_azure_openai_legacy_works(self, monkeypatch):
        """Legacy Azure OpenAI vars should work."""
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://legacy.openai.azure.com")
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "key123")

        config = _resolve_config()
        assert config["source"] == "azure_openai"

    def test_ai_foundry_legacy_works(self, monkeypatch):
        """Legacy AI Foundry vars should work."""
        monkeypatch.setenv("AZURE_AI_INFERENCE_ENDPOINT", "https://foundry.inference.ai.azure.com")
        monkeypatch.setenv("AZURE_AI_INFERENCE_API_KEY", "key123")

        config = _resolve_config()
        assert config["source"] == "azure_ai_foundry"

    def test_conflict_prefers_azure_openai_with_warning(self, monkeypatch):
        """When both legacy types set, prefer Azure OpenAI and warn."""
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://openai.azure.com")
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "key1")
        monkeypatch.setenv("AZURE_AI_INFERENCE_ENDPOINT", "https://foundry.azure.com")
        monkeypatch.setenv("AZURE_AI_INFERENCE_API_KEY", "key2")

        with pytest.warns(UserWarning, match="Both AZURE_OPENAI"):
            config = _resolve_config()

        assert config["source"] == "azure_openai"
        assert config["conflict_detected"] is True

    def test_https_required(self):
        """Endpoint must use HTTPS."""
        with pytest.raises(ConfigurationError, match="HTTPS"):
            _validate_endpoint_url("http://insecure.azure.com")

    def test_warns_non_azure_domain(self):
        """Should warn for non-Azure domains."""
        with pytest.warns(UserWarning, match="Non-standard"):
            _validate_endpoint_url("https://custom-proxy.company.com")
```
