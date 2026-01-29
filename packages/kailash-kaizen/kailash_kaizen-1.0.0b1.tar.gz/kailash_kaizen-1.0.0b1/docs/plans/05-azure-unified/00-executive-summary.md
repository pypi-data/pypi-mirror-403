# 05-Azure-Unified: Unified Azure Provider for Kaizen SDK

## Document Control
- **Version**: 1.0
- **Date**: 2026-01-16
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## Executive Summary

### Problem Statement

| Dimension | Details |
|-----------|---------|
| **Issue** | Kaizen's Azure support only covers Azure AI Foundry, not Azure OpenAI Service |
| **Severity** | P1 - HIGH (blocks enterprise adoption) |
| **Scope** | All Azure users, especially those using GPT-4o, GPT-5, o-series models |
| **Root Cause** | Microsoft has two separate Azure AI services with different APIs |

### Solution: Unified Azure Provider

Create an intelligent unified provider that:
1. **Auto-detects** the appropriate backend from endpoint URL patterns
2. **Seamlessly handles** both Azure OpenAI Service and Azure AI Foundry
3. **Provides fallback** when primary backend fails with specific errors
4. **Manages feature gaps** with explicit errors for hard gaps, warnings for degradable features

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Detection strategy | Pattern match + smart default | 0ms overhead for 95% of cases |
| Unknown endpoint handling | Default to Azure OpenAI | 80%+ of enterprise usage |
| Fallback mechanism | Error-based auto-fallback | Transparent recovery |
| Feature gap handling | Capability API + contextual behavior | Explicit control with good UX |
| Two providers or one? | **One unified provider** | Don't push Microsoft's complexity to users |

### Architecture Overview

```
User: provider = get_provider("azure")
              │
    ┌─────────▼─────────────────────────┐
    │     UnifiedAzureProvider          │
    │     (Single Entry Point)          │
    └─────────┬─────────────────────────┘
              │
    ┌─────────▼─────────────────────────┐
    │     AzureBackendDetector          │
    │  • Pattern match endpoint URL     │
    │  • Default to OpenAI if unknown   │
    │  • Error-based fallback           │
    └─────────┬─────────────────────────┘
              │
    ┌─────────▼─────────────────────────┐
    │    AzureCapabilityRegistry        │
    │  • supports("audio_input")        │
    │  • check_feature() → error/warn   │
    └─────────┬─────────────────────────┘
              │
         ┌────┴────┐
         ▼         ▼
    ┌─────────┐ ┌─────────┐
    │ OpenAI  │ │ Foundry │
    │ Backend │ │ Backend │
    │(openai) │ │(azure-  │
    │   SDK   │ │inference│
    └─────────┘ └─────────┘
```

### Deliverables Index

| Document | Description |
|----------|-------------|
| [01-architecture-design.md](./01-architecture-design.md) | Detailed architecture and class design |
| [02-detection-strategy.md](./02-detection-strategy.md) | Backend detection algorithm |
| [03-capability-registry.md](./03-capability-registry.md) | Feature gap handling |
| [04-environment-variables.md](./04-environment-variables.md) | Configuration strategy |
| [05-implementation-phases.md](./05-implementation-phases.md) | Phase breakdown with tasks |
| [06-testing-strategy.md](./06-testing-strategy.md) | 3-tier testing approach |
| [07-migration-guide.md](./07-migration-guide.md) | Backward compatibility |

### Success Criteria

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| Auto-detection accuracy | % correct backend on first try | >95% |
| Latency overhead | Detection + routing time | <10ms |
| Backward compatibility | Existing tests passing | 100% |
| Feature gap clarity | User survey on error messages | 90%+ actionable |
| Test coverage | Unit + Integration + E2E | >90% |

### Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1: Foundation | 3 days | Detector, Registry, Backends |
| Phase 2: Integration | 2 days | UnifiedAzureProvider, Provider registration |
| Phase 3: Testing | 2 days | Unit, Integration, E2E tests |
| Phase 4: Documentation | 1 day | Guides, CLAUDE.md updates |

**Total**: ~8 days

### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API version incompatibility | Medium | High | Version-aware client initialization |
| Credential rotation issues | Low | High | Refresh mechanism with TTL |
| Breaking changes for existing users | Medium | High | Deprecation warnings, migration guide |
| Unknown endpoint patterns | Low | Medium | Explicit override via AZURE_BACKEND |

---

## References

- TPC Backend Team Report (2026-01-16): Azure OpenAI integration issues
- Azure AI Foundry vs Azure OpenAI Service distinction
- LiteLLM multi-provider patterns research
