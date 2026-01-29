# 07: Migration Guide

## Document Control
- **Version**: 1.0
- **Date**: 2026-01-16
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## 1. Overview

This guide helps existing Kaizen users migrate to the new Unified Azure Provider.

**Key Points**:
- Backward compatible - existing code continues to work
- New unified environment variables recommended
- Deprecation warnings for legacy patterns

---

## 2. Environment Variable Migration

### Current (Legacy) Configuration

```bash
# Azure AI Foundry (current)
export AZURE_AI_INFERENCE_ENDPOINT="https://my-resource.inference.ai.azure.com"
export AZURE_AI_INFERENCE_API_KEY="your-api-key"

# Azure OpenAI (if manually configured)
export AZURE_OPENAI_ENDPOINT="https://my-resource.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-api-key"
```

### Recommended Configuration

```bash
# Unified (recommended)
export AZURE_ENDPOINT="https://my-resource.openai.azure.com"
export AZURE_API_KEY="your-api-key"

# Optional
export AZURE_API_VERSION="2024-10-21"
export AZURE_DEPLOYMENT="gpt-4o"
```

### Migration Steps

1. **Identify your current configuration**:
   ```bash
   # Check current env vars
   env | grep -E "AZURE_(AI_INFERENCE|OPENAI)_"
   ```

2. **Set unified variables**:
   ```bash
   # Copy your endpoint
   export AZURE_ENDPOINT="$AZURE_AI_INFERENCE_ENDPOINT"
   # Or for Azure OpenAI:
   # export AZURE_ENDPOINT="$AZURE_OPENAI_ENDPOINT"

   export AZURE_API_KEY="$AZURE_AI_INFERENCE_API_KEY"
   ```

3. **Test the migration**:
   ```python
   from kaizen.nodes.ai.ai_providers import get_provider

   provider = get_provider("azure")
   response = provider.chat([{"role": "user", "content": "Hello"}])
   print(response["content"])
   ```

4. **Remove legacy variables** (optional, after verification):
   ```bash
   unset AZURE_AI_INFERENCE_ENDPOINT
   unset AZURE_AI_INFERENCE_API_KEY
   ```

---

## 3. Code Migration

### Provider Import (No Changes Required)

```python
# Before (still works)
from kaizen.nodes.ai.ai_providers import get_provider
provider = get_provider("azure")

# After (same code)
from kaizen.nodes.ai.ai_providers import get_provider
provider = get_provider("azure")
```

### Direct Provider Usage

```python
# Before (still works, deprecated)
from kaizen.nodes.ai.ai_providers import AzureAIFoundryProvider
provider = AzureAIFoundryProvider()

# After (recommended)
from kaizen.nodes.ai.ai_providers import UnifiedAzureProvider
provider = UnifiedAzureProvider()

# Or via factory (preferred)
from kaizen.nodes.ai.ai_providers import get_provider
provider = get_provider("azure")
```

### Agent Configuration (No Changes Required)

```python
# Before (still works)
from kaizen.agents import BaseAgent
agent = BaseAgent(
    name="my-agent",
    llm_provider="azure",
    model="gpt-4o",
)

# After (same code, now uses UnifiedAzureProvider)
from kaizen.agents import BaseAgent
agent = BaseAgent(
    name="my-agent",
    llm_provider="azure",
    model="gpt-4o",
)
```

---

## 4. Feature Migration

### Audio Input (New Capability)

```python
# Before: Not supported on AI Foundry
# Would fail silently or raise unclear error

# After: Clear error with guidance
from kaizen.nodes.ai.ai_providers import get_provider

provider = get_provider("azure")

# Check before using
if provider.supports("audio_input"):
    response = provider.chat([{
        "role": "user",
        "content": [
            {"type": "audio", "path": "recording.mp3"}
        ]
    }])
else:
    # Clear guidance in exception
    print("Audio requires Azure OpenAI - set AZURE_ENDPOINT to *.openai.azure.com")
```

### Reasoning Models (o1, o3, GPT-5)

```python
# Before: Would fail with cryptic temperature error

# After: Automatic parameter handling
provider = get_provider("azure")

# Temperature automatically skipped for reasoning models
response = provider.chat(
    messages=[{"role": "user", "content": "Think about this problem..."}],
    model="o1-preview",
    generation_config={
        "temperature": 0.7,  # Automatically ignored for o1
        "max_tokens": 4000,  # Translated to max_completion_tokens
    }
)
```

### Structured Output

```python
# Before: Might fail on AI Foundry with schema errors

# After: Automatic format translation
response = provider.chat(
    messages=[{"role": "user", "content": "Extract user info"}],
    generation_config={
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "user",
                "schema": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    }
)
# Format automatically translated to Azure JsonSchemaFormat
```

---

## 5. Handling Deprecation Warnings

### Warning Types

```python
# Import warning (if using deprecated class directly)
from kaizen.nodes.ai.ai_providers import AzureAIFoundryProvider
# DeprecationWarning: AzureAIFoundryProvider is deprecated, use UnifiedAzureProvider

# Config warning (if both legacy env var types set)
# UserWarning: Both AZURE_OPENAI_* and AZURE_AI_INFERENCE_* are set...
```

### Suppressing Warnings (Not Recommended)

```python
import warnings

# Only if you have a specific reason
warnings.filterwarnings("ignore", category=DeprecationWarning, module="kaizen")
```

### Fixing Warnings

```python
# Fix import warning
# Before
from kaizen.nodes.ai.ai_providers import AzureAIFoundryProvider

# After
from kaizen.nodes.ai.ai_providers import UnifiedAzureProvider
# Or use factory
from kaizen.nodes.ai.ai_providers import get_provider
```

---

## 6. Troubleshooting

### Issue: "No Azure backend configured"

**Cause**: No valid Azure environment variables set.

**Solution**:
```bash
# Check what's set
env | grep AZURE

# Set required variables
export AZURE_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_API_KEY="your-api-key"
```

### Issue: "Feature 'audio_input' is not supported"

**Cause**: Using AI Foundry endpoint which doesn't support audio.

**Solution**:
```bash
# Switch to Azure OpenAI endpoint
export AZURE_ENDPOINT="https://your-resource.openai.azure.com"
```

### Issue: "audience is incorrect" error

**Cause**: Backend auto-detection chose wrong backend.

**Solution**:
```bash
# Force specific backend
export AZURE_BACKEND="foundry"  # or "openai"
```

### Issue: Temperature not supported error with o1/o3

**Cause**: Using older code that doesn't filter temperature.

**Solution**: Update to latest Kaizen version - temperature is automatically filtered for reasoning models.

---

## 7. Testing Migration

### Verification Script

```python
#!/usr/bin/env python3
"""Verify Azure migration is working correctly."""

import os
from kaizen.nodes.ai.ai_providers import get_provider, UnifiedAzureProvider

def verify_migration():
    print("=== Azure Migration Verification ===\n")

    # Check environment
    print("1. Environment Variables:")
    for var in ["AZURE_ENDPOINT", "AZURE_API_KEY", "AZURE_BACKEND",
                "AZURE_OPENAI_ENDPOINT", "AZURE_AI_INFERENCE_ENDPOINT"]:
        value = os.getenv(var)
        status = "✓ Set" if value else "✗ Not set"
        print(f"   {var}: {status}")

    # Check provider
    print("\n2. Provider Status:")
    try:
        provider = get_provider("azure")
        print(f"   Type: {type(provider).__name__}")
        print(f"   Available: {provider.is_available()}")

        if provider.is_available():
            backend = provider._get_backend()
            print(f"   Backend: {backend.get_backend_type()}")
            print(f"   Detection: {provider._detector.detection_source}")
    except Exception as e:
        print(f"   Error: {e}")

    # Check capabilities
    print("\n3. Capabilities:")
    if provider.is_available():
        caps = provider.get_capabilities()
        for feature, supported in sorted(caps.items()):
            status = "✓" if supported else "✗"
            print(f"   {status} {feature}")

    # Test basic chat
    print("\n4. Basic Chat Test:")
    if provider.is_available():
        try:
            response = provider.chat([
                {"role": "user", "content": "Say 'migration successful'"}
            ])
            print(f"   Response: {response['content'][:50]}...")
            print("   ✓ Chat working")
        except Exception as e:
            print(f"   ✗ Chat failed: {e}")

    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    verify_migration()
```

### Running Verification

```bash
python verify_azure_migration.py
```

---

## 8. Rollback Plan

If issues occur, rollback to legacy configuration:

```bash
# 1. Unset unified variables
unset AZURE_ENDPOINT
unset AZURE_API_KEY
unset AZURE_BACKEND

# 2. Restore legacy variables
export AZURE_AI_INFERENCE_ENDPOINT="your-old-endpoint"
export AZURE_AI_INFERENCE_API_KEY="your-old-key"

# 3. Use legacy provider directly (temporary)
# In Python:
from kaizen.nodes.ai.ai_providers import AzureAIFoundryProvider
provider = AzureAIFoundryProvider()
```

---

## 9. Timeline

| Phase | Date | Action |
|-------|------|--------|
| Release | TBD | Unified provider available |
| Deprecation | +3 months | Warnings for legacy imports |
| Migration | +6 months | Documentation focuses on unified |
| EOL | +12 months | Legacy code removal (if any) |

**Note**: Legacy environment variables will continue to work indefinitely for backward compatibility.
