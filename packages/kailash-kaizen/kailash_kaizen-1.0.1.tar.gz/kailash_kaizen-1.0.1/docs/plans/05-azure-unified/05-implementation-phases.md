# 05: Implementation Phases

## Document Control
- **Version**: 1.0
- **Date**: 2026-01-16
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## Phase Overview

| Phase | Duration | Focus | Deliverables |
|-------|----------|-------|--------------|
| Phase 1 | 3 days | Foundation | Detector, Registry, Backends |
| Phase 2 | 2 days | Integration | UnifiedProvider, Registration |
| Phase 3 | 2 days | Testing | Unit, Integration, E2E |
| Phase 4 | 1 day | Documentation | Guides, CLAUDE.md updates |

**Total**: ~8 days

---

## Phase 1: Foundation (3 days)

### Task 1.1: Create AzureBackendDetector (4 hours)

**Goal**: Implement endpoint pattern detection with smart defaults

**TDD Approach**:
```python
# tests/unit/nodes/ai/test_azure_detection.py

class TestAzureBackendDetector:
    def test_detects_azure_openai_standard(self, monkeypatch):
        """Should detect *.openai.azure.com as Azure OpenAI."""
        monkeypatch.setenv("AZURE_ENDPOINT", "https://my.openai.azure.com")
        detector = AzureBackendDetector()
        backend, _ = detector.detect()
        assert backend == "azure_openai"

    def test_detects_ai_foundry_inference(self, monkeypatch):
        """Should detect *.inference.ai.azure.com as AI Foundry."""
        monkeypatch.setenv("AZURE_ENDPOINT", "https://my.inference.ai.azure.com")
        detector = AzureBackendDetector()
        backend, _ = detector.detect()
        assert backend == "azure_ai_foundry"

    def test_unknown_defaults_to_openai(self, monkeypatch):
        """Should default to Azure OpenAI for unknown patterns."""
        monkeypatch.setenv("AZURE_ENDPOINT", "https://custom.proxy.com")
        detector = AzureBackendDetector()
        backend, _ = detector.detect()
        assert backend == "azure_openai"

    def test_explicit_override(self, monkeypatch):
        """Should respect AZURE_BACKEND override."""
        monkeypatch.setenv("AZURE_ENDPOINT", "https://any.endpoint.com")
        monkeypatch.setenv("AZURE_BACKEND", "foundry")
        detector = AzureBackendDetector()
        backend, _ = detector.detect()
        assert backend == "azure_ai_foundry"

    def test_error_fallback_to_foundry(self):
        """Should detect wrong backend from error signature."""
        detector = AzureBackendDetector()
        detector._detected_backend = "azure_openai"
        error = Exception("audience is incorrect (https://cognitiveservices.azure.com)")
        result = detector.handle_error(error)
        assert result == "azure_ai_foundry"
```

**Implementation**:
- File: `src/kaizen/nodes/ai/azure_detection.py` (NEW)
- See [02-detection-strategy.md](./02-detection-strategy.md) for full implementation

**Verification**:
- [ ] All 5+ unit tests passing
- [ ] Pattern matching covers Azure OpenAI and AI Foundry endpoints
- [ ] Error-based fallback detects wrong backend signatures

---

### Task 1.2: Create AzureCapabilityRegistry (4 hours)

**Goal**: Implement feature gap handling with explicit errors/warnings

**TDD Approach**:
```python
# tests/unit/nodes/ai/test_azure_capabilities.py

class TestAzureCapabilityRegistry:
    def test_azure_openai_supports_audio(self):
        registry = AzureCapabilityRegistry("azure_openai")
        assert registry.supports("audio_input") is True

    def test_ai_foundry_does_not_support_audio(self):
        registry = AzureCapabilityRegistry("azure_ai_foundry")
        assert registry.supports("audio_input") is False

    def test_audio_raises_error_on_ai_foundry(self):
        registry = AzureCapabilityRegistry("azure_ai_foundry")
        with pytest.raises(FeatureNotSupportedError) as exc:
            registry.check_feature("audio_input")
        assert "Azure OpenAI Service" in str(exc.value)
        assert "audio" in exc.value.guidance.lower()

    def test_vision_warns_on_ai_foundry(self):
        registry = AzureCapabilityRegistry("azure_ai_foundry")
        with pytest.warns(FeatureDegradationWarning):
            registry.check_feature("vision")

    def test_reasoning_model_detection(self):
        registry = AzureCapabilityRegistry("azure_ai_foundry")
        with pytest.raises(FeatureNotSupportedError):
            registry.check_model_requirements("o1-preview")

    def test_get_capabilities(self):
        registry = AzureCapabilityRegistry("azure_openai")
        caps = registry.get_capabilities()
        assert caps["chat"] is True
        assert caps["audio_input"] is True
```

**Implementation**:
- File: `src/kaizen/nodes/ai/azure_capabilities.py` (NEW)
- See [03-capability-registry.md](./03-capability-registry.md) for full implementation

**Verification**:
- [ ] All 6+ unit tests passing
- [ ] Hard gaps raise FeatureNotSupportedError with guidance
- [ ] Degradable features issue warnings

---

### Task 1.3: Implement AzureOpenAIBackend (6 hours)

**Goal**: Create backend using native `openai` SDK for Azure OpenAI Service

**TDD Approach**:
```python
# tests/unit/nodes/ai/test_azure_openai_backend.py

class TestAzureOpenAIBackend:
    def test_is_configured_with_env_vars(self, monkeypatch):
        monkeypatch.setenv("AZURE_ENDPOINT", "https://my.openai.azure.com")
        monkeypatch.setenv("AZURE_API_KEY", "test-key")
        backend = AzureOpenAIBackend()
        assert backend.is_configured() is True

    def test_get_backend_type(self):
        backend = AzureOpenAIBackend()
        assert backend.get_backend_type() == "azure_openai"

    def test_reasoning_model_skips_temperature(self):
        backend = AzureOpenAIBackend()
        assert backend._is_reasoning_model("o1-preview") is True
        assert backend._is_reasoning_model("gpt-4o") is False

    def test_build_request_params_standard_model(self):
        backend = AzureOpenAIBackend()
        params = backend._build_request_params(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
            generation_config={"temperature": 0.7}
        )
        assert params["temperature"] == 0.7

    def test_build_request_params_reasoning_model(self):
        backend = AzureOpenAIBackend()
        params = backend._build_request_params(
            model="o1-preview",
            messages=[{"role": "user", "content": "test"}],
            generation_config={"temperature": 0.7, "max_tokens": 100}
        )
        assert "temperature" not in params
        assert params["max_completion_tokens"] == 100
```

**Implementation**:
- File: `src/kaizen/nodes/ai/azure_backends.py` (NEW)
- Uses `openai.AzureOpenAI` client
- Handles reasoning model parameter filtering
- Implements structured output translation

**Verification**:
- [ ] All 5+ unit tests passing
- [ ] Reasoning models don't receive temperature
- [ ] API version correctly passed

---

### Task 1.4: Refactor AzureAIFoundryBackend (4 hours)

**Goal**: Wrap existing AzureAIFoundryProvider as backend

**TDD Approach**:
```python
# tests/unit/nodes/ai/test_azure_foundry_backend.py

class TestAzureAIFoundryBackend:
    def test_is_configured_with_env_vars(self, monkeypatch):
        monkeypatch.setenv("AZURE_AI_INFERENCE_ENDPOINT", "https://my.inference.ai.azure.com")
        monkeypatch.setenv("AZURE_AI_INFERENCE_API_KEY", "test-key")
        backend = AzureAIFoundryBackend()
        assert backend.is_configured() is True

    def test_get_backend_type(self):
        backend = AzureAIFoundryBackend()
        assert backend.get_backend_type() == "azure_ai_foundry"

    def test_api_version_from_env(self, monkeypatch):
        monkeypatch.setenv("AZURE_AI_INFERENCE_API_VERSION", "2025-01-01")
        backend = AzureAIFoundryBackend()
        # API version should be used in client initialization
```

**Implementation**:
- File: `src/kaizen/nodes/ai/azure_backends.py`
- Wraps existing `AzureAIFoundryProvider` methods
- Adds `api_version` support (fixing TPC report issue)
- Preserves all existing functionality

**Verification**:
- [ ] All 3+ unit tests passing
- [ ] Existing AzureAIFoundryProvider tests still pass
- [ ] api_version correctly passed to ChatCompletionsClient

---

## Phase 2: Integration (2 days)

### Task 2.1: Implement UnifiedAzureProvider (6 hours)

**Goal**: Create unified provider with auto-detection and fallback

**TDD Approach**:
```python
# tests/unit/nodes/ai/test_unified_azure_provider.py

class TestUnifiedAzureProvider:
    def test_auto_detects_backend(self, monkeypatch):
        monkeypatch.setenv("AZURE_ENDPOINT", "https://my.openai.azure.com")
        monkeypatch.setenv("AZURE_API_KEY", "test-key")
        provider = UnifiedAzureProvider()
        assert provider._get_backend().get_backend_type() == "azure_openai"

    def test_supports_delegates_to_registry(self, monkeypatch):
        monkeypatch.setenv("AZURE_ENDPOINT", "https://my.inference.ai.azure.com")
        monkeypatch.setenv("AZURE_API_KEY", "test-key")
        provider = UnifiedAzureProvider()
        assert provider.supports("audio_input") is False

    def test_fallback_on_error(self, monkeypatch, mocker):
        monkeypatch.setenv("AZURE_ENDPOINT", "https://custom.endpoint.com")
        monkeypatch.setenv("AZURE_API_KEY", "test-key")

        provider = UnifiedAzureProvider(fallback_enabled=True)
        # Mock primary to fail with wrong backend signature
        mocker.patch.object(
            provider._openai_backend, 'chat',
            side_effect=Exception("audience is incorrect")
        )
        mocker.patch.object(
            provider._foundry_backend, 'chat',
            return_value={"content": "success"}
        )

        result = provider.chat([{"role": "user", "content": "test"}])
        assert result["content"] == "success"

    def test_preferred_backend_override(self, monkeypatch):
        monkeypatch.setenv("AZURE_ENDPOINT", "https://my.openai.azure.com")
        monkeypatch.setenv("AZURE_API_KEY", "test-key")
        provider = UnifiedAzureProvider(preferred_backend="azure_ai_foundry")
        assert provider._get_backend().get_backend_type() == "azure_ai_foundry"
```

**Implementation**:
- File: `src/kaizen/nodes/ai/ai_providers.py` (modify)
- Add UnifiedAzureProvider class
- Implement detection, fallback, capability checking
- Handle both sync and async methods

**Verification**:
- [ ] All 4+ unit tests passing
- [ ] Auto-detection works for both backends
- [ ] Fallback triggers on appropriate errors

---

### Task 2.2: Update Provider Registration (2 hours)

**Goal**: Register UnifiedAzureProvider in PROVIDERS dict

**Implementation**:
- File: `src/kaizen/nodes/ai/ai_providers.py`
- Update PROVIDERS dict:
  ```python
  PROVIDERS = {
      # ... existing ...
      "azure": UnifiedAzureProvider,
      "azure_openai": AzureOpenAIBackend,
      "azure_foundry": AzureAIFoundryBackend,
  }
  ```

**Verification**:
- [ ] `get_provider("azure")` returns UnifiedAzureProvider
- [ ] `get_provider("azure_openai")` returns AzureOpenAIBackend
- [ ] Existing tests still pass

---

### Task 2.3: Update Configuration (2 hours)

**Goal**: Update config/providers.py for unified env vars

**Implementation**:
- File: `src/kaizen/config/providers.py`
- Update `check_azure_available()`
- Update `get_azure_config()`
- Add unified env var support

**Verification**:
- [ ] `check_azure_available()` works with all env var combinations
- [ ] Legacy env vars still work

---

## Phase 3: Testing (2 days)

### Task 3.1: Unit Tests (4 hours)

**Goal**: Comprehensive unit test coverage

**Test Files**:
- `tests/unit/nodes/ai/test_azure_detection.py`
- `tests/unit/nodes/ai/test_azure_capabilities.py`
- `tests/unit/nodes/ai/test_azure_backends.py`
- `tests/unit/nodes/ai/test_unified_azure_provider.py`

**Coverage Targets**:
- Detection logic: 100%
- Capability registry: 100%
- Backend implementations: >90%
- Unified provider: >90%

---

### Task 3.2: Integration Tests (6 hours)

**Goal**: Real Azure endpoint testing

**Test File**: `tests/integration/nodes/ai/test_azure_unified_integration.py`

```python
@pytest.mark.integration
class TestUnifiedAzureIntegration:
    """Integration tests with real Azure endpoints."""

    @pytest.fixture
    def azure_provider(self):
        provider = UnifiedAzureProvider()
        if not provider.is_available():
            pytest.skip("Azure not configured")
        return provider

    def test_chat_completion(self, azure_provider):
        """Should complete chat request successfully."""
        response = azure_provider.chat([
            {"role": "user", "content": "Say 'test' and nothing else"}
        ])
        assert response["content"] is not None
        assert "test" in response["content"].lower()

    def test_embedding(self, azure_provider):
        """Should generate embeddings successfully."""
        embeddings = azure_provider.embed(["Hello world"])
        assert len(embeddings) == 1
        assert len(embeddings[0]) > 0

    def test_auto_detection_correct(self, azure_provider):
        """Should detect correct backend from endpoint."""
        backend_type = azure_provider._get_backend().get_backend_type()
        # Verify detection matches expected endpoint pattern
        endpoint = os.getenv("AZURE_ENDPOINT", "")
        if ".openai.azure.com" in endpoint:
            assert backend_type == "azure_openai"
        elif ".inference.ai.azure.com" in endpoint:
            assert backend_type == "azure_ai_foundry"

    def test_structured_output(self, azure_provider):
        """Should handle structured output format."""
        response = azure_provider.chat(
            messages=[{"role": "user", "content": "Return JSON with name='test'"}],
            generation_config={
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "response",
                        "schema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                            "required": ["name"]
                        }
                    }
                }
            }
        )
        import json
        data = json.loads(response["content"])
        assert "name" in data
```

---

### Task 3.3: E2E Tests (4 hours)

**Goal**: Full workflow testing

**Test File**: `tests/e2e/test_azure_unified_e2e.py`

```python
@pytest.mark.e2e
class TestAzureUnifiedE2E:
    """End-to-end tests for Azure unified provider."""

    def test_agent_with_azure_provider(self):
        """Agent should work with unified Azure provider."""
        from kaizen.agents import BaseAgent

        agent = BaseAgent(
            name="test-agent",
            llm_provider="azure",
            model="gpt-4o",
        )
        response = agent.run("What is 2+2?")
        assert "4" in response

    def test_fallback_scenario(self, azure_openai_env, ai_foundry_env):
        """Should fallback between backends on error."""
        # Configure both backends
        # Trigger error on primary
        # Verify fallback succeeds
```

---

## Phase 4: Documentation (1 day)

### Task 4.1: Update CLAUDE.md (2 hours)

**Goal**: Add unified Azure provider documentation

**Updates**:
- Add Azure unified provider section
- Document environment variables
- Add troubleshooting guidance

---

### Task 4.2: Update kaizen-specialist.md (2 hours)

**Goal**: Update specialist agent documentation

**Updates**:
- Add UnifiedAzureProvider information
- Update Azure configuration examples

---

### Task 4.3: Update User Guides (4 hours)

**Goal**: Create/update user-facing documentation

**Files**:
- `sdk-users/apps/kaizen/guides/azure-provider.md` (NEW)
- `sdk-users/apps/kaizen/README.md` (update)

---

## Success Criteria

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| Unit tests | Pass rate | 100% |
| Integration tests | Pass rate | 100% |
| Auto-detection accuracy | Manual verification | >95% |
| Backward compatibility | Existing tests | 100% pass |
| Documentation | Completeness | All sections covered |
