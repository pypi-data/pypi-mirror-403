# Security and Code Quality Plan

**Document**: plans/02-security-code-quality.md
**Created**: 2025-12-29
**Completed**: 2025-12-29
**Status**: ✅ COMPLETED
**Priority**: HIGH
**TODO Reference**: [todos/completed/TODO-SECURITY-002-code-quality-hardening.md](../../todos/completed/TODO-SECURITY-002-code-quality-hardening.md)

---

## Executive Summary

This plan addresses critical code quality and security issues identified in the comprehensive audit:

| Category | Count | Priority |
|----------|-------|----------|
| MUST FIX (Mock Data in Production) | 3 | Critical |
| MUST FIX (Hardcoded URLs) | 3 | Critical |
| SHOULD FIX (Silent Exceptions) | 16+ | High |
| DOCUMENT (Development Features) | 8+ | Medium |

---

## Phase 1: Document Provider Mock Data Prevention (Critical) ✅

### Problem
Document providers (OpenAI Vision, Ollama Vision, Landing AI) return mock data in production without raising errors, causing users to receive fake extraction results.

### Files to Fix
1. `src/kaizen/providers/document/openai_vision_provider.py:151-161`
2. `src/kaizen/providers/document/ollama_vision_provider.py:151-161`
3. `src/kaizen/providers/document/landing_ai_provider.py:166-195`

### Fix Pattern
```python
def extract(self, file_path: str | Path, **kwargs) -> ExtractionResult:
    """Extract text from document."""
    # Check if mock mode is explicitly enabled
    if not os.environ.get("KAIZEN_ALLOW_MOCK_PROVIDERS", "").lower() == "true":
        raise NotImplementedError(
            f"{self.provider_name} document extraction is not yet implemented. "
            "To enable mock responses for development/testing, "
            "set KAIZEN_ALLOW_MOCK_PROVIDERS=true environment variable."
        )

    # Mock implementation for development...
    logger.warning(f"Using mock {self.provider_name} extraction (KAIZEN_ALLOW_MOCK_PROVIDERS=true)")
```

---

## Phase 2: Hardcoded URL Configuration (Critical) ✅

### Problem
Hardcoded localhost URLs prevent proper deployment configuration.

### Files to Fix
1. `src/kaizen/config/providers.py:66` - Ollama health check
2. `src/kaizen/config/providers.py:97` - Docker Model Runner check
3. `src/kaizen/monitoring/dashboard.py:239` - WebSocket URL in JavaScript

### Fix Pattern
```python
# Before:
response = requests.get("http://localhost:11434/api/tags", timeout=1)

# After:
ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
response = requests.get(f"{ollama_url}/api/tags", timeout=1)
```

---

## Phase 3: Silent Exception Handling (High) ✅

### Problem
Bare `except:` clauses silently swallow exceptions without logging.

### Files to Fix (16 locations)

| File | Line | Context |
|------|------|---------|
| `memory/tiers.py` | 384 | Size estimation |
| `memory/signature_integration.py` | 329 | Tier determination |
| `memory/persistent_tiers.py` | 128, 154, 426, 464 | Pickle fallback |
| `orchestration/patterns/handoff.py` | 159, 168, 249, 423 | Value parsing |
| `nodes/ai_nodes.py` | 1397 | Statistical calculation |
| `nodes/rag/realtime.py` | 209, 240 | Calculations |
| `nodes/rag/agentic.py` | 269, 476 | Expression/JSON parsing |
| `nodes/compliance/gdpr.py` | 1364 | Data retention |

### Fix Pattern
```python
# Before:
except:
    return "warm"

# After:
except Exception as e:
    logger.debug(f"Size estimation failed, defaulting to warm tier: {e}")
    return "warm"
```

---

## Phase 4: Token Counting Stub (High) ✅ (Documented)

### Problem
Claude Code agent uses cycle count heuristic instead of actual token counting.

### Files to Fix
- `src/kaizen/agents/autonomous/claude_code.py:495-504` - `_check_context_usage()`
- `src/kaizen/agents/autonomous/claude_code.py:506-527` - `_compact_context()`

### Fix Options
1. **Option A**: Implement using tiktoken library (preferred)
2. **Option B**: Raise NotImplementedError with clear message
3. **Option C**: Document as known limitation with warning log

---

## Test Strategy

### Tier 1 (Unit Tests)
- Verify NotImplementedError raised for mock providers
- Verify environment variable configuration works
- Verify logging added to exception handlers

### Tier 2 (Integration Tests)
- Verify provider selection with environment variables
- Verify WebSocket URL configuration

### Tier 3 (E2E Tests)
- Verify deployment with custom URLs
- Verify mock mode activation

---

## Related TODOs

- TODO-SECURITY-002: Document Provider Mock Prevention
- TODO-SECURITY-003: Hardcoded URL Configuration
- TODO-SECURITY-004: Silent Exception Logging
- TODO-SECURITY-005: Token Counting Implementation
