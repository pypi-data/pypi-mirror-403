# Changelog

All notable changes to the Kaizen AI Agent Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2025-12-16

### Added

#### Enterprise Agent Trust Protocol (EATP)

Complete implementation of cryptographically verifiable trust chains for AI agents.

**Phase 1: Foundation & Single Agent Trust (Weeks 1-4)**
- `TrustLineageChain`: Complete trust chain data structure
- `GenesisRecord`: Cryptographic proof of agent authorization
- `CapabilityAttestation`: What agents are authorized to do
- `DelegationRecord`: Trust transfer between agents
- `ConstraintEnvelope`: Limits on agent behavior
- `AuditAnchor`: Tamper-proof action records
- `TrustOperations`: ESTABLISH, DELEGATE, VERIFY, AUDIT operations
- `PostgresTrustStore`: Persistent trust chain storage
- `OrganizationalAuthorityRegistry`: Authority lifecycle management
- `TrustKeyManager`: Ed25519 key management
- `TrustedAgent`: BaseAgent with automatic trust verification
- `TrustedSupervisorAgent`: Delegation to worker agents

**Phase 2: Multi-Agent Trust (Weeks 5-8)**
- `AgentRegistry`: Central registry for agent discovery
- `AgentHealthMonitor`: Background health monitoring
- `SecureChannel`: End-to-end encrypted messaging
- `MessageVerifier`: Multi-step message verification
- `InMemoryReplayProtection`: Replay attack prevention
- `TrustExecutionContext`: Trust state propagation
- `TrustPolicyEngine`: Policy-based trust evaluation
- `TrustAwareOrchestrationRuntime`: Trust-aware workflow execution

**Phase 3: Enterprise Features (Weeks 9-12)**
- `A2AService`: FastAPI A2A protocol service
- `AgentCardGenerator`: A2A Agent Card with trust extensions
- `JsonRpcHandler`: JSON-RPC 2.0 handler
- `A2AAuthenticator`: JWT-based authentication
- `EnterpriseSystemAgent` (ESA): Proxy for legacy systems
- `DatabaseESA`: SQL database ESA (PostgreSQL, MySQL, SQLite)
- `APIESA`: REST API ESA with OpenAPI support (see details below)
- `ESARegistry`: ESA discovery and management
- `TrustChainCache`: LRU cache with TTL (100x+ speedup)
- `CredentialRotationManager`: Periodic key rotation
- `TrustSecurityValidator`: Input validation and sanitization
- `SecureKeyStorage`: Encrypted key storage (Fernet)
- `TrustRateLimiter`: Per-authority rate limiting
- `SecurityAuditLogger`: Security event logging

**APIESA - REST API Enterprise System Agent (2025-12-15)**

Production-ready ESA for trust-aware REST API integration:

*Core Features:*
- OpenAPI/Swagger spec parsing with automatic capability generation
- HTTP operations: GET, POST, PUT, DELETE, PATCH with full async support
- Rate limiting: per-second, per-minute, per-hour with sliding window
- Request/response audit logging with circular buffer (last 1000 requests)
- Flexible authentication: Bearer tokens, API keys, custom headers

*Trust Integration:*
- Full `EnterpriseSystemAgent` inheritance
- `discover_capabilities()`, `execute_operation()`, `validate_connection()`
- Trust establishment and capability delegation support

*Error Handling:*
- Timeout, request, and connection error handling
- Missing parameter validation
- Rate limit exceeded errors with detailed context

*Documentation:*
- API Reference: `docs/trust/esa/APIESA.md`
- Quick Reference: `docs/trust/esa/APIESA_QUICK_REFERENCE.md`
- Example: `examples/trust/esa_api_example.py`
- 33 unit tests in `tests/unit/trust/esa/test_apiesa.py`

**Performance Targets Met**
- VERIFY QUICK: <1ms (target <5ms)
- VERIFY STANDARD: <5ms (target <50ms)
- VERIFY FULL: <50ms (target <100ms)
- Cache hit: <0.5ms (100x+ speedup)

**Testing**
- 691 total tests (548 unit + 143 integration)
- NO MOCKING policy for Tier 2-3 tests
- Real PostgreSQL infrastructure testing

**Documentation**
- API Reference: `docs/api/trust.md`
- Migration Guide: `docs/guides/eatp-migration-guide.md`
- Security Best Practices: `docs/guides/eatp-security-best-practices.md`
- 10 usage examples in `examples/trust/`

### Changed

- `BaseAgent` now supports optional trust verification via `TrustedAgent` subclass
- Orchestration runtime can be trust-aware via `TrustAwareOrchestrationRuntime`

### Fixed

- SecurityEventType enum now includes rotation events
- APIESA capability name generation fixed for path parameters
- Integration tests now use real implementations (NO MOCKING)

---

## [0.1.x] - Previous Releases

See individual release notes for earlier versions.

---

## Migration

To upgrade from 0.7.x to 0.8.0, see the [EATP Migration Guide](docs/guides/eatp-migration-guide.md).

Key changes:
- New `kaizen.trust` module with all EATP components
- Optional trust verification for existing agents
- Backward compatible - existing `BaseAgent` code works unchanged

## Links

- [Documentation](https://docs.kailash.dev/kaizen)
- [GitHub](https://github.com/Integrum-Global/kailash_python_sdk)
- [Issues](https://github.com/Integrum-Global/kailash_python_sdk/issues)
