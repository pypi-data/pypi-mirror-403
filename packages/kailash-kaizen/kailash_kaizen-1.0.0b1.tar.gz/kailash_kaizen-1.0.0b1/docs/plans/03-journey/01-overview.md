# Journey Orchestration - Overview

> **Target Version**: v0.9.0
> **Status**: Implementation Ready
> **ADR**: ADR-025-journey-orchestration-layer.md

## Executive Summary

This plan details the implementation of Kaizen's Layer 5 (Journey Orchestration) and Layer 2 enhancements (Signature intent/guidelines). The implementation enables declarative user journey definition with intent-driven pathway transitions.

## Goals

1. **Layer 2 Enhancements**: Add `__intent__` and `__guidelines__` to Signature classes
2. **Layer 5 Implementation**: Create complete Journey Orchestration module
3. **Healthcare Use Case**: Implement reference healthcare referral journey
4. **100% Test Coverage**: Comprehensive testing following 3-tier strategy

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYER 5: JOURNEY ORCHESTRATION                      │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │     Journey     │  │    Pathway      │  │       Transition            │  │
│  │  (declarative)  │  │   (phase)       │  │  (switching rules)          │  │
│  └────────┬────────┘  └────────┬────────┘  └──────────────┬──────────────┘  │
│           │                    │                          │                  │
│           ▼                    ▼                          ▼                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                       PathwayManager (Runtime)                          ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  ││
│  │  │IntentDetector│  │PathwayStack  │  │   ContextAccumulator         │  ││
│  │  │(LLM-powered) │  │(return nav)  │  │   (cross-pathway state)      │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

## Implementation Phases

| Phase | Focus | Duration | Deliverables |
|-------|-------|----------|--------------|
| **Phase 1** | Layer 2 + Journey/Pathway core | 2 weeks | Signature enhancements, Journey, Pathway |
| **Phase 2** | Intent Detection | 1.5 weeks | IntentDetector, caching, LLM integration |
| **Phase 3** | PathwayManager | 2 weeks | Runtime, ContextAccumulator, persistence |
| **Phase 4** | Healthcare Use Case | 1 week | Complete example, documentation |

## Dependencies

| Component | Depends On | Status |
|-----------|------------|--------|
| Signature enhancements | SignatureMeta (existing) | Ready |
| Journey/Pathway | Signature, Pipeline | Ready |
| IntentDetector | BaseAgent, LLMAgentNode | Ready |
| PathwayManager | DataFlow, Pipeline patterns | Ready |
| ContextAccumulator | None | Ready |

## Success Criteria

1. All unit tests pass (Tier 1)
2. All integration tests pass with real Ollama (Tier 2)
3. E2E tests pass with OpenAI (Tier 3)
4. Healthcare use case works end-to-end
5. Documentation complete with examples

## File Structure

```
kaizen/
├── signatures/
│   └── core.py                  # MODIFY: Add __intent__, __guidelines__
│
└── journey/                     # NEW MODULE
    ├── __init__.py              # Public exports
    ├── core.py                  # Journey, Pathway, metaclasses
    ├── transitions.py           # Transition, triggers
    ├── intent.py                # IntentDetector
    ├── manager.py               # PathwayManager
    ├── context.py               # ContextAccumulator
    ├── state.py                 # JourneyStateManager
    └── behaviors.py             # ReturnToPrevious
```

## Related Documents

- [02-layer2-enhancements.md](./02-layer2-enhancements.md) - Signature enhancements
- [03-journey-core.md](./03-journey-core.md) - Journey and Pathway classes
- [04-intent-detection.md](./04-intent-detection.md) - IntentTrigger and IntentDetector
- [05-runtime.md](./05-runtime.md) - PathwayManager and ContextAccumulator
- [06-integration.md](./06-integration.md) - Integration with existing Kaizen
- [07-healthcare-usecase.md](./07-healthcare-usecase.md) - Reference implementation
