# 06: Testing Strategy

## Document Control
- **Version**: 1.0
- **Date**: 2026-01-16
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## 1. 3-Tier Testing Approach

Following Kaizen's established testing strategy with NO MOCKING policy for Tiers 2-3.

| Tier | Focus | Infrastructure | Mocking |
|------|-------|----------------|---------|
| Tier 1 | Unit tests | None | Allowed |
| Tier 2 | Integration | Real Azure | **NO MOCKING** |
| Tier 3 | E2E | Real Azure | **NO MOCKING** |

---

## 2. Tier 1: Unit Tests

### Test Files

| File | Tests | Focus |
|------|-------|-------|
| `test_azure_detection.py` | 8+ | Backend detection logic |
| `test_azure_capabilities.py` | 10+ | Feature gap handling |
| `test_azure_backends.py` | 12+ | Backend implementations |
| `test_unified_azure_provider.py` | 10+ | Provider integration |

### Detection Tests

```python
# tests/unit/nodes/ai/test_azure_detection.py

import pytest
import os
from kaizen.nodes.ai.azure_detection import AzureBackendDetector


class TestAzureBackendDetector:
    """Unit tests for Azure backend detection."""

    # Pattern Matching Tests

    @pytest.mark.parametrize("endpoint,expected", [
        ("https://my-resource.openai.azure.com", "azure_openai"),
        ("https://my-resource.openai.azure.com/", "azure_openai"),
        ("https://eastus.api.cognitive.microsoft.com/openai", "azure_openai"),
        ("https://my-resource.privatelink.openai.azure.com", "azure_openai"),
    ])
    def test_detects_azure_openai_patterns(self, monkeypatch, endpoint, expected):
        """Should detect Azure OpenAI from endpoint patterns."""
        monkeypatch.setenv("AZURE_ENDPOINT", endpoint)
        monkeypatch.setenv("AZURE_API_KEY", "test-key")
        detector = AzureBackendDetector()
        backend, _ = detector.detect()
        assert backend == expected

    @pytest.mark.parametrize("endpoint,expected", [
        ("https://my-model.inference.ai.azure.com", "azure_ai_foundry"),
        ("https://my-resource.services.ai.azure.com", "azure_ai_foundry"),
    ])
    def test_detects_ai_foundry_patterns(self, monkeypatch, endpoint, expected):
        """Should detect AI Foundry from endpoint patterns."""
        monkeypatch.setenv("AZURE_ENDPOINT", endpoint)
        monkeypatch.setenv("AZURE_API_KEY", "test-key")
        detector = AzureBackendDetector()
        backend, _ = detector.detect()
        assert backend == expected

    # Default Behavior Tests

    def test_unknown_pattern_defaults_to_openai(self, monkeypatch):
        """Should default to Azure OpenAI for unknown patterns."""
        monkeypatch.setenv("AZURE_ENDPOINT", "https://custom-proxy.company.com/azure")
        monkeypatch.setenv("AZURE_API_KEY", "test-key")
        detector = AzureBackendDetector()
        backend, _ = detector.detect()
        assert backend == "azure_openai"
        assert detector.detection_source == "default"

    # Explicit Override Tests

    @pytest.mark.parametrize("override,expected", [
        ("openai", "azure_openai"),
        ("azure_openai", "azure_openai"),
        ("foundry", "azure_ai_foundry"),
        ("ai_foundry", "azure_ai_foundry"),
    ])
    def test_explicit_override_respected(self, monkeypatch, override, expected):
        """Should respect AZURE_BACKEND override."""
        monkeypatch.setenv("AZURE_ENDPOINT", "https://any.endpoint.com")
        monkeypatch.setenv("AZURE_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_BACKEND", override)
        detector = AzureBackendDetector()
        backend, _ = detector.detect()
        assert backend == expected
        assert detector.detection_source == "explicit"

    # Error Fallback Tests

    def test_error_triggers_fallback_to_foundry(self):
        """Should detect AI Foundry from 'audience' error."""
        detector = AzureBackendDetector()
        detector._detected_backend = "azure_openai"
        error = Exception("audience is incorrect (https://cognitiveservices.azure.com)")
        result = detector.handle_error(error)
        assert result == "azure_ai_foundry"
        assert detector.detection_source == "error_fallback"

    def test_error_triggers_fallback_to_openai(self):
        """Should detect Azure OpenAI from 'DeploymentNotFound' error."""
        detector = AzureBackendDetector()
        detector._detected_backend = "azure_ai_foundry"
        error = Exception("DeploymentNotFound: The API deployment does not exist")
        result = detector.handle_error(error)
        assert result == "azure_openai"

    def test_unrelated_error_no_fallback(self):
        """Should not trigger fallback for unrelated errors."""
        detector = AzureBackendDetector()
        detector._detected_backend = "azure_openai"
        error = Exception("Rate limit exceeded")
        result = detector.handle_error(error)
        assert result is None

    # Configuration Resolution Tests

    def test_no_config_returns_none(self, monkeypatch):
        """Should return None when no config available."""
        monkeypatch.delenv("AZURE_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_AI_INFERENCE_ENDPOINT", raising=False)
        detector = AzureBackendDetector()
        backend, config = detector.detect()
        assert backend is None
        assert config == {}
```

### Capability Tests

```python
# tests/unit/nodes/ai/test_azure_capabilities.py

import pytest
import warnings
from kaizen.nodes.ai.azure_capabilities import (
    AzureCapabilityRegistry,
    FeatureNotSupportedError,
    FeatureDegradationWarning,
)


class TestAzureCapabilityRegistry:
    """Unit tests for capability detection and gap handling."""

    # Support Checking Tests

    @pytest.mark.parametrize("feature,expected", [
        ("chat", True),
        ("embeddings", True),
        ("audio_input", True),
        ("reasoning_models", True),
        ("llama_models", False),
    ])
    def test_azure_openai_capabilities(self, feature, expected):
        """Should correctly report Azure OpenAI capabilities."""
        registry = AzureCapabilityRegistry("azure_openai")
        assert registry.supports(feature) == expected

    @pytest.mark.parametrize("feature,expected", [
        ("chat", True),
        ("embeddings", True),
        ("audio_input", False),
        ("reasoning_models", False),
        ("llama_models", True),
    ])
    def test_ai_foundry_capabilities(self, feature, expected):
        """Should correctly report AI Foundry capabilities."""
        registry = AzureCapabilityRegistry("azure_ai_foundry")
        assert registry.supports(feature) == expected

    # Hard Gap Tests

    def test_audio_raises_error_on_ai_foundry(self):
        """Audio should raise error with guidance on AI Foundry."""
        registry = AzureCapabilityRegistry("azure_ai_foundry")
        with pytest.raises(FeatureNotSupportedError) as exc:
            registry.check_feature("audio_input")
        assert exc.value.feature == "audio_input"
        assert exc.value.current_backend == "azure_ai_foundry"
        assert "Azure OpenAI" in str(exc.value)
        assert exc.value.guidance is not None

    def test_reasoning_raises_error_on_ai_foundry(self):
        """Reasoning models should raise error on AI Foundry."""
        registry = AzureCapabilityRegistry("azure_ai_foundry")
        with pytest.raises(FeatureNotSupportedError):
            registry.check_feature("reasoning_models")

    def test_llama_raises_error_on_azure_openai(self):
        """Llama models should raise error on Azure OpenAI."""
        registry = AzureCapabilityRegistry("azure_openai")
        with pytest.raises(FeatureNotSupportedError) as exc:
            registry.check_feature("llama_models")
        assert "AI Foundry" in str(exc.value)

    # Degradable Feature Tests

    def test_vision_warns_on_ai_foundry(self):
        """Vision should warn but proceed on AI Foundry."""
        registry = AzureCapabilityRegistry("azure_ai_foundry")
        with pytest.warns(FeatureDegradationWarning):
            registry.check_feature("vision")

    def test_supported_feature_no_warning(self):
        """Supported features should not warn."""
        registry = AzureCapabilityRegistry("azure_openai")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            registry.check_feature("chat")
            assert len(w) == 0

    # Model Requirement Tests

    @pytest.mark.parametrize("model", ["o1-preview", "o3-mini", "gpt-5", "GPT-5-turbo"])
    def test_reasoning_model_detection(self, model):
        """Should detect reasoning models and check requirements."""
        registry = AzureCapabilityRegistry("azure_ai_foundry")
        with pytest.raises(FeatureNotSupportedError):
            registry.check_model_requirements(model)

    @pytest.mark.parametrize("model", ["gpt-4o", "gpt-4-turbo", "text-embedding-3-small"])
    def test_standard_model_no_error(self, model):
        """Standard models should not raise errors."""
        registry = AzureCapabilityRegistry("azure_ai_foundry")
        registry.check_model_requirements(model)  # Should not raise

    # Capability Enumeration Tests

    def test_get_capabilities_returns_all_features(self):
        """Should return all feature capabilities."""
        registry = AzureCapabilityRegistry("azure_openai")
        caps = registry.get_capabilities()
        assert "chat" in caps
        assert "audio_input" in caps
        assert "llama_models" in caps
        assert len(caps) >= 10
```

---

## 3. Tier 2: Integration Tests

### Prerequisites

```bash
# Required environment variables for integration tests
export AZURE_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_API_KEY="your-api-key"
export AZURE_DEPLOYMENT="gpt-4o"  # Or your deployment name
```

### Test File

```python
# tests/integration/nodes/ai/test_azure_unified_integration.py

import pytest
import os
from kaizen.nodes.ai.ai_providers import UnifiedAzureProvider


@pytest.mark.integration
class TestUnifiedAzureProviderIntegration:
    """Integration tests with real Azure endpoints - NO MOCKING."""

    @pytest.fixture
    def azure_provider(self):
        """Get configured Azure provider or skip."""
        provider = UnifiedAzureProvider()
        if not provider.is_available():
            pytest.skip("Azure not configured - set AZURE_ENDPOINT and AZURE_API_KEY")
        return provider

    # Basic Functionality Tests

    def test_chat_completion_basic(self, azure_provider):
        """Should complete basic chat request."""
        response = azure_provider.chat([
            {"role": "user", "content": "Say 'hello' and nothing else."}
        ])
        assert response is not None
        assert response.get("content") is not None
        assert "hello" in response["content"].lower()

    def test_chat_completion_with_system_message(self, azure_provider):
        """Should handle system messages."""
        response = azure_provider.chat([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"}
        ])
        assert "4" in response["content"]

    def test_embedding_generation(self, azure_provider):
        """Should generate embeddings."""
        embeddings = azure_provider.embed(["Hello world"])
        assert len(embeddings) == 1
        assert len(embeddings[0]) > 0
        assert isinstance(embeddings[0][0], float)

    def test_embedding_batch(self, azure_provider):
        """Should handle batch embeddings."""
        texts = ["Hello", "World", "Test"]
        embeddings = azure_provider.embed(texts)
        assert len(embeddings) == 3

    # Auto-Detection Tests

    def test_auto_detection_matches_endpoint(self, azure_provider):
        """Detection should match endpoint pattern."""
        backend = azure_provider._get_backend().get_backend_type()
        endpoint = os.getenv("AZURE_ENDPOINT", "")

        if ".openai.azure.com" in endpoint:
            assert backend == "azure_openai"
        elif ".inference.ai.azure.com" in endpoint:
            assert backend == "azure_ai_foundry"

    def test_detection_source_recorded(self, azure_provider):
        """Should record how detection happened."""
        _ = azure_provider._get_backend()  # Trigger detection
        source = azure_provider._detector.detection_source
        assert source in ("pattern", "default", "explicit")

    # Structured Output Tests

    def test_json_mode(self, azure_provider):
        """Should handle JSON mode response format."""
        response = azure_provider.chat(
            messages=[{"role": "user", "content": "Return a JSON object with key 'status' and value 'ok'"}],
            generation_config={
                "response_format": {"type": "json_object"}
            }
        )
        import json
        data = json.loads(response["content"])
        assert "status" in data

    def test_json_schema_mode(self, azure_provider):
        """Should handle JSON schema response format."""
        response = azure_provider.chat(
            messages=[{"role": "user", "content": "Provide a user with name 'Alice' and age 30"}],
            generation_config={
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "user",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "age": {"type": "integer"}
                            },
                            "required": ["name", "age"],
                            "additionalProperties": False
                        },
                        "strict": True
                    }
                }
            }
        )
        import json
        data = json.loads(response["content"])
        assert data["name"] == "Alice"
        assert data["age"] == 30

    # Streaming Tests

    @pytest.mark.asyncio
    async def test_streaming_response(self, azure_provider):
        """Should handle streaming responses."""
        chunks = []
        async for chunk in azure_provider.chat_stream(
            messages=[{"role": "user", "content": "Count from 1 to 5"}]
        ):
            chunks.append(chunk)
        assert len(chunks) > 0
        full_content = "".join(c.get("content", "") for c in chunks)
        assert any(str(i) in full_content for i in range(1, 6))

    # Async Tests

    @pytest.mark.asyncio
    async def test_chat_async(self, azure_provider):
        """Should handle async chat completion."""
        response = await azure_provider.chat_async([
            {"role": "user", "content": "Say 'async' and nothing else."}
        ])
        assert "async" in response["content"].lower()

    @pytest.mark.asyncio
    async def test_embed_async(self, azure_provider):
        """Should handle async embeddings."""
        embeddings = await azure_provider.embed_async(["Test embedding"])
        assert len(embeddings) == 1

    # Capability Tests

    def test_capabilities_match_backend(self, azure_provider):
        """Capabilities should match detected backend."""
        backend = azure_provider._get_backend().get_backend_type()
        caps = azure_provider.get_capabilities()

        if backend == "azure_openai":
            assert caps["audio_input"] is True
            assert caps["reasoning_models"] is True
        else:
            assert caps["audio_input"] is False
```

---

## 4. Tier 3: E2E Tests

### Test File

```python
# tests/e2e/test_azure_unified_e2e.py

import pytest
from kaizen.agents import BaseAgent


@pytest.mark.e2e
class TestAzureUnifiedE2E:
    """End-to-end tests with full Kaizen agent workflows."""

    def test_agent_with_unified_azure_provider(self):
        """Agent should work seamlessly with unified Azure provider."""
        agent = BaseAgent(
            name="test-agent",
            llm_provider="azure",
            model="gpt-4o",
        )
        response = agent.run("What is the capital of France?")
        assert "Paris" in response

    def test_agent_with_tool_calling(self):
        """Agent should handle tool calling via unified provider."""
        def get_weather(city: str) -> str:
            return f"Weather in {city}: Sunny, 25°C"

        agent = BaseAgent(
            name="weather-agent",
            llm_provider="azure",
            model="gpt-4o",
            tools=[get_weather],
        )
        response = agent.run("What's the weather in Tokyo?")
        assert "Tokyo" in response or "Sunny" in response

    def test_agent_with_structured_output(self):
        """Agent should handle structured output signatures."""
        from kaizen.signatures import Signature, Field

        class ExtractInfo(Signature):
            """Extract information from text."""
            text: str = Field(description="Input text")
            name: str = Field(description="Extracted name")
            age: int = Field(description="Extracted age")

        agent = BaseAgent(
            name="extractor",
            llm_provider="azure",
            signature=ExtractInfo,
        )
        result = agent.run(text="John is 25 years old.")
        assert result.name == "John"
        assert result.age == 25

    def test_multi_turn_conversation(self):
        """Agent should maintain conversation context."""
        agent = BaseAgent(
            name="chat-agent",
            llm_provider="azure",
            model="gpt-4o",
        )

        response1 = agent.run("My name is Alice.")
        response2 = agent.run("What is my name?")
        assert "Alice" in response2
```

---

## 5. Test Execution

### Running Tests

```bash
# Run all Azure tests
pytest tests/unit/nodes/ai/test_azure*.py -v

# Run integration tests (requires Azure credentials)
pytest tests/integration/nodes/ai/test_azure*.py -v --integration

# Run E2E tests
pytest tests/e2e/test_azure*.py -v --e2e

# Run with coverage
pytest tests/unit/nodes/ai/test_azure*.py --cov=kaizen.nodes.ai --cov-report=html
```

### CI Configuration

```yaml
# .github/workflows/azure-tests.yml
azure-tests:
  runs-on: ubuntu-latest
  env:
    AZURE_ENDPOINT: ${{ secrets.AZURE_ENDPOINT }}
    AZURE_API_KEY: ${{ secrets.AZURE_API_KEY }}
  steps:
    - uses: actions/checkout@v4
    - name: Run unit tests
      run: pytest tests/unit/nodes/ai/test_azure*.py -v
    - name: Run integration tests
      if: env.AZURE_ENDPOINT != ''
      run: pytest tests/integration/nodes/ai/test_azure*.py -v --integration
```

---

## 6. Coverage Targets

| Component | Target | Measurement |
|-----------|--------|-------------|
| Detection logic | 100% | Line coverage |
| Capability registry | 100% | Line coverage |
| Unified provider | >90% | Line coverage |
| Backend implementations | >90% | Line coverage |
| Integration tests | N/A | Real API success rate |
