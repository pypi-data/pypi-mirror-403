# 01: Audio Support - Executive Summary

## Overview

This plan addresses P1 issue: **GoogleGeminiProvider silently drops audio content** in multimodal messages. The fix adds native audio support to Kaizen AI providers, enabling voice-based AI workflows.

## Problem Statement

| Dimension | Details |
|-----------|---------|
| **Issue** | Audio content silently dropped in `_convert_messages_to_contents()` |
| **Severity** | P1 - Silent data loss affecting all audio-based AI workflows |
| **Scope** | Affects ALL 5 providers (Google, OpenAI, Anthropic, Azure, Ollama) |
| **Root Cause** | Architectural mismatch - audio designed for Whisper pipeline, not native LLM multimodal |

## Fix Strategy

**Phased Approach** (4 phases):

| Phase | Focus | Priority | Duration |
|-------|-------|----------|----------|
| **0** | Infrastructure - Warning for unhandled types | CRITICAL | 1 hour |
| **1** | Core Audio - `audio_utils.py` + GoogleGeminiProvider | HIGH | 1 day |
| **2** | Provider Parity - OpenAI, Azure, AudioField.to_base64() | MEDIUM | 1 day |
| **3** | Testing - 3-tier comprehensive tests | HIGH | 1 day |

## Key Decisions

Based on subagent reviews:

1. **Create `audio_utils.py`** as separate module (mirrors `vision_utils.py` pattern)
2. **Add `to_base64()` to AudioField** - critical missing method
3. **Support `audio_url` type** - for parity with `image_url`
4. **Add warning for unhandled types** - prevent future silent failures
5. **NO MOCKING in Tier 2-3 tests** - real API calls only

## Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| No silent failures | All unhandled types log warnings |
| Audio reaches API | Integration tests verify audio in requests |
| Correct response | LLM acknowledges audio content |
| Backward compatible | Existing workflows unchanged |
| Test coverage | 90%+ for new audio code |
| All tests pass | 100% pass rate |

## Files to Modify

| File | Change | Phase |
|------|--------|-------|
| `kaizen/nodes/ai/ai_providers.py` | Add warning + audio handling | 0, 1, 2 |
| `kaizen/nodes/ai/audio_utils.py` | **NEW** - audio utilities | 1 |
| `kaizen/signatures/multi_modal.py` | Add `AudioField.to_base64()` | 2 |
| `tests/unit/audio/` | Unit tests | 3 |
| `tests/integration/audio/` | Integration tests | 3 |
| `tests/e2e/audio/` | E2E tests | 3 |

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Gemini API format mismatch | Medium | High | Test with real API |
| Large audio OOM | Medium | Medium | Add size validation |
| Breaking changes | Low | Low | Addition only |
