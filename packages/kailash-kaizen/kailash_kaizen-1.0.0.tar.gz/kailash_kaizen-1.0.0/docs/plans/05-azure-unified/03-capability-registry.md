# 03: Capability Registry - Feature Gap Handling

## Document Control
- **Version**: 1.0
- **Date**: 2026-01-16
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## 1. Feature Support Matrix

### Full Comparison

| Feature | Azure OpenAI | AI Foundry | Gap Type | Handling |
|---------|-------------|------------|----------|----------|
| Chat completions | Yes | Yes | None | Direct passthrough |
| Embeddings | Yes | Yes | None | Direct passthrough |
| Streaming | Yes | Yes | None | Direct passthrough |
| Tool calling | Yes | Yes | Format differs | Translation |
| Vision (images) | Yes | Partial | Degradable | Warn + proceed |
| Audio input | Yes | No | Hard gap | Explicit error |
| Reasoning models (o1/o3/GPT-5) | Yes | No | Hard gap | Explicit error |
| Structured output (strict) | Yes | Yes | Format differs | Translation |
| Llama/Mistral models | No | Yes | Inverse gap | Explicit error |
| Custom fine-tuned | Yes | Yes | None | Direct passthrough |

### Gap Type Definitions

| Gap Type | Definition | Handling Strategy |
|----------|------------|-------------------|
| **None** | Feature works identically on both backends | Direct passthrough |
| **Format differs** | Feature exists but requires protocol translation | Silent translation |
| **Degradable** | Feature partially works; can proceed with reduced functionality | Warning + proceed |
| **Hard gap** | Feature completely unavailable; cannot proceed | Explicit error with guidance |
| **Inverse gap** | Feature only available on AI Foundry, not Azure OpenAI | Explicit error with guidance |

---

## 2. Implementation

### AzureCapabilityRegistry Class

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import warnings
import logging

logger = logging.getLogger(__name__)


class GapHandling(Enum):
    """How to handle feature gaps."""
    PASSTHROUGH = "passthrough"      # Feature works on both
    TRANSLATE = "translate"          # Silent format translation
    WARN_PROCEED = "warn_proceed"    # Warn but continue
    ERROR = "error"                  # Raise explicit error


@dataclass
class FeatureInfo:
    """Information about a feature's support status."""
    name: str
    description: str
    azure_openai: bool
    azure_ai_foundry: bool
    gap_handling: GapHandling
    guidance: Optional[str] = None


class FeatureNotSupportedError(Exception):
    """Raised when a feature is not available on the current backend."""

    def __init__(
        self,
        feature: str,
        current_backend: str,
        required_backend: Optional[str] = None,
        guidance: Optional[str] = None,
    ):
        self.feature = feature
        self.current_backend = current_backend
        self.required_backend = required_backend
        self.guidance = guidance

        message = f"Feature '{feature}' is not supported on {current_backend}."
        if required_backend:
            message += f" This feature requires {required_backend}."
        if guidance:
            message += f"\n\n{guidance}"

        super().__init__(message)


class FeatureDegradationWarning(UserWarning):
    """Warning issued when a feature operates in degraded mode."""
    pass


class AzureCapabilityRegistry:
    """
    Registry of feature capabilities for Azure backends.

    Provides:
    - Feature support checking: supports(feature) -> bool
    - Capability enumeration: get_capabilities() -> dict
    - Gap handling: check_feature() raises error or warning as appropriate
    """

    FEATURES = {
        "chat": FeatureInfo(
            name="chat",
            description="Chat completions",
            azure_openai=True,
            azure_ai_foundry=True,
            gap_handling=GapHandling.PASSTHROUGH,
        ),
        "embeddings": FeatureInfo(
            name="embeddings",
            description="Text embeddings",
            azure_openai=True,
            azure_ai_foundry=True,
            gap_handling=GapHandling.PASSTHROUGH,
        ),
        "streaming": FeatureInfo(
            name="streaming",
            description="Streaming responses",
            azure_openai=True,
            azure_ai_foundry=True,
            gap_handling=GapHandling.PASSTHROUGH,
        ),
        "tool_calling": FeatureInfo(
            name="tool_calling",
            description="Function/tool calling",
            azure_openai=True,
            azure_ai_foundry=True,
            gap_handling=GapHandling.TRANSLATE,
            guidance="Tool call format is automatically translated between backends.",
        ),
        "structured_output": FeatureInfo(
            name="structured_output",
            description="JSON schema response format",
            azure_openai=True,
            azure_ai_foundry=True,
            gap_handling=GapHandling.TRANSLATE,
            guidance="Structured output format is automatically translated to Azure format.",
        ),
        "vision": FeatureInfo(
            name="vision",
            description="Image input processing",
            azure_openai=True,
            azure_ai_foundry=True,  # Partial - model dependent
            gap_handling=GapHandling.WARN_PROCEED,
            guidance=(
                "Vision support in AI Foundry depends on deployed model. "
                "Ensure your deployment supports vision input."
            ),
        ),
        "audio_input": FeatureInfo(
            name="audio_input",
            description="Audio file input",
            azure_openai=True,
            azure_ai_foundry=False,
            gap_handling=GapHandling.ERROR,
            guidance=(
                "Audio input requires Azure OpenAI Service. Options:\n"
                "1. Set AZURE_ENDPOINT to *.openai.azure.com\n"
                "2. Use local transcription: from kaizen.audio import transcribe_audio\n"
                "3. Pre-process audio to text before sending"
            ),
        ),
        "reasoning_models": FeatureInfo(
            name="reasoning_models",
            description="o1, o3, GPT-5 reasoning models",
            azure_openai=True,
            azure_ai_foundry=False,
            gap_handling=GapHandling.ERROR,
            guidance=(
                "Reasoning models (o1, o3, GPT-5) require Azure OpenAI Service.\n"
                "Set AZURE_ENDPOINT to your Azure OpenAI resource."
            ),
        ),
        "llama_models": FeatureInfo(
            name="llama_models",
            description="Meta Llama models",
            azure_openai=False,
            azure_ai_foundry=True,
            gap_handling=GapHandling.ERROR,
            guidance=(
                "Llama models are only available through Azure AI Foundry.\n"
                "Set AZURE_ENDPOINT to your AI Foundry endpoint."
            ),
        ),
        "mistral_models": FeatureInfo(
            name="mistral_models",
            description="Mistral AI models",
            azure_openai=False,
            azure_ai_foundry=True,
            gap_handling=GapHandling.ERROR,
            guidance=(
                "Mistral models are only available through Azure AI Foundry.\n"
                "Set AZURE_ENDPOINT to your AI Foundry endpoint."
            ),
        ),
    }

    def __init__(self, backend: str):
        """
        Initialize registry for specific backend.

        Args:
            backend: Either "azure_openai" or "azure_ai_foundry"
        """
        if backend not in ("azure_openai", "azure_ai_foundry"):
            raise ValueError(f"Invalid backend: {backend}")
        self.backend = backend
        self._backend_attr = backend.replace("azure_", "azure_")
        # Map to attribute names
        if backend == "azure_openai":
            self._support_attr = "azure_openai"
        else:
            self._support_attr = "azure_ai_foundry"

    def supports(self, feature: str) -> bool:
        """
        Check if feature is supported on current backend.

        Args:
            feature: Feature name (e.g., "audio_input", "vision")

        Returns:
            True if feature is supported, False otherwise
        """
        info = self.FEATURES.get(feature)
        if not info:
            # Unknown features pass through (assume supported)
            return True
        return getattr(info, self._support_attr, False)

    def get_capabilities(self) -> dict[str, bool]:
        """
        Get all capabilities for current backend.

        Returns:
            Dict mapping feature names to support status
        """
        return {
            name: self.supports(name)
            for name in self.FEATURES
        }

    def get_feature_info(self, feature: str) -> Optional[FeatureInfo]:
        """
        Get detailed information about a feature.

        Args:
            feature: Feature name

        Returns:
            FeatureInfo if feature is known, None otherwise
        """
        return self.FEATURES.get(feature)

    def check_feature(self, feature: str) -> None:
        """
        Check feature and handle gap according to policy.

        For hard gaps: raises FeatureNotSupportedError
        For degradable features: issues FeatureDegradationWarning
        For supported features: returns silently

        Args:
            feature: Feature name to check

        Raises:
            FeatureNotSupportedError: For hard gaps
        """
        info = self.FEATURES.get(feature)
        if not info:
            # Unknown features pass through
            return

        if self.supports(feature):
            # Feature supported, check if translation needed
            if info.gap_handling == GapHandling.TRANSLATE:
                logger.debug(f"Feature '{feature}' requires translation for {self.backend}")
            return

        # Feature not supported on this backend
        if info.gap_handling == GapHandling.ERROR:
            # Determine required backend
            required = None
            if info.azure_openai and not info.azure_ai_foundry:
                required = "Azure OpenAI Service"
            elif info.azure_ai_foundry and not info.azure_openai:
                required = "Azure AI Foundry"

            raise FeatureNotSupportedError(
                feature=feature,
                current_backend=self.backend,
                required_backend=required,
                guidance=info.guidance,
            )

        elif info.gap_handling == GapHandling.WARN_PROCEED:
            warnings.warn(
                f"Feature '{feature}' has limited support on {self.backend}. "
                f"{info.guidance or 'Results may vary.'}",
                FeatureDegradationWarning,
                stacklevel=3,
            )

    def check_model_requirements(self, model: str) -> None:
        """
        Check if model has specific backend requirements.

        Args:
            model: Model name or deployment name

        Raises:
            FeatureNotSupportedError: If model requires different backend
        """
        if not model:
            return

        model_lower = model.lower()

        # Check for reasoning models
        reasoning_prefixes = ("o1", "o3", "gpt-5", "gpt5")
        if any(model_lower.startswith(p) for p in reasoning_prefixes):
            self.check_feature("reasoning_models")

        # Check for Llama models
        if "llama" in model_lower:
            self.check_feature("llama_models")

        # Check for Mistral models
        if "mistral" in model_lower or "mixtral" in model_lower:
            self.check_feature("mistral_models")
```

---

## 3. Usage Examples

### Basic Capability Checking

```python
from kaizen.providers.azure import UnifiedAzureProvider

provider = UnifiedAzureProvider()

# Check single capability
if provider.supports("audio_input"):
    response = provider.chat(audio_messages)
else:
    # Fallback to transcription
    text = transcribe_audio(audio_path)
    response = provider.chat([{"role": "user", "content": text}])

# Get all capabilities
caps = provider.get_capabilities()
print(caps)
# {'chat': True, 'embeddings': True, 'audio_input': False, ...}
```

### Automatic Feature Checking

```python
# Provider automatically checks features based on message content
response = provider.chat([
    {
        "role": "user",
        "content": [
            {"type": "audio", "path": "recording.mp3"}  # Will raise error if unsupported
        ]
    }
])
```

### Error Handling

```python
from kaizen.providers.azure import FeatureNotSupportedError

try:
    response = provider.chat(audio_messages)
except FeatureNotSupportedError as e:
    print(f"Feature not available: {e.feature}")
    print(f"Current backend: {e.current_backend}")
    print(f"Guidance: {e.guidance}")
    # Implement fallback logic
```

---

## 4. Testing Requirements

### Unit Tests

```python
class TestAzureCapabilityRegistry:
    """Unit tests for capability detection."""

    def test_azure_openai_supports_audio(self):
        """Azure OpenAI should support audio input."""
        registry = AzureCapabilityRegistry("azure_openai")
        assert registry.supports("audio_input") is True

    def test_ai_foundry_does_not_support_audio(self):
        """AI Foundry should not support audio input."""
        registry = AzureCapabilityRegistry("azure_ai_foundry")
        assert registry.supports("audio_input") is False

    def test_audio_raises_error_on_ai_foundry(self):
        """Audio check should raise error on AI Foundry."""
        registry = AzureCapabilityRegistry("azure_ai_foundry")
        with pytest.raises(FeatureNotSupportedError) as exc:
            registry.check_feature("audio_input")
        assert "Azure OpenAI Service" in str(exc.value)

    def test_vision_warns_on_ai_foundry(self):
        """Vision check should warn on AI Foundry."""
        registry = AzureCapabilityRegistry("azure_ai_foundry")
        with pytest.warns(FeatureDegradationWarning):
            registry.check_feature("vision")

    def test_llama_raises_error_on_azure_openai(self):
        """Llama models should raise error on Azure OpenAI."""
        registry = AzureCapabilityRegistry("azure_openai")
        with pytest.raises(FeatureNotSupportedError):
            registry.check_feature("llama_models")

    def test_reasoning_model_detection(self):
        """Should detect reasoning models from name."""
        registry = AzureCapabilityRegistry("azure_ai_foundry")
        with pytest.raises(FeatureNotSupportedError):
            registry.check_model_requirements("o1-preview")

    def test_get_capabilities_returns_all(self):
        """Should return all feature capabilities."""
        registry = AzureCapabilityRegistry("azure_openai")
        caps = registry.get_capabilities()
        assert "chat" in caps
        assert "audio_input" in caps
        assert "llama_models" in caps
```

---

## 5. Message Content Detection

### Auto-Detection in Provider

```python
class UnifiedAzureProvider:

    def _detect_required_features(self, messages: list[dict]) -> set[str]:
        """
        Detect features required by message content.

        Scans messages for:
        - Audio content → requires "audio_input"
        - Image content → requires "vision"
        """
        required = set()

        for message in messages:
            content = message.get("content")
            if isinstance(content, list):
                for item in content:
                    item_type = item.get("type", "")
                    if item_type in ("audio", "audio_url", "input_audio"):
                        required.add("audio_input")
                    elif item_type in ("image", "image_url"):
                        required.add("vision")

        return required

    def chat(self, messages: list[dict], **kwargs) -> dict:
        """Chat with automatic feature checking."""
        # Auto-detect required features from message content
        required_features = self._detect_required_features(messages)
        for feature in required_features:
            self._registry.check_feature(feature)

        # Check model requirements
        model = kwargs.get("model")
        if model:
            self._registry.check_model_requirements(model)

        # Proceed with backend call
        return self._get_backend().chat(messages, **kwargs)
```

---

## 6. Future Extensibility

### Adding New Features

```python
# To add a new feature:
FEATURES["new_feature"] = FeatureInfo(
    name="new_feature",
    description="Description of new feature",
    azure_openai=True,
    azure_ai_foundry=False,
    gap_handling=GapHandling.ERROR,
    guidance="Instructions for users when feature unavailable",
)
```

### Version-Specific Features

Future enhancement could include API version checking:

```python
@dataclass
class FeatureInfo:
    # ... existing fields ...
    min_api_version: Optional[str] = None  # e.g., "2024-08-01"

    def is_available(self, backend: str, api_version: str) -> bool:
        """Check availability considering API version."""
        base_support = getattr(self, backend, False)
        if not base_support:
            return False
        if self.min_api_version and api_version < self.min_api_version:
            return False
        return True
```
