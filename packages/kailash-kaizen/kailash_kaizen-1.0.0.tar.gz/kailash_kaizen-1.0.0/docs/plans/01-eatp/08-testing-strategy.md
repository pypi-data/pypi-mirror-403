# EATP Implementation Plan: Testing Strategy

## Document Control
- **Version**: 1.0
- **Date**: 2025-12-15
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## Overview

This document outlines the comprehensive testing strategy for EATP implementation, following the Kaizen framework's **3-tier testing approach** with **NO MOCKING** policy for Tiers 2 and 3.

---

## Testing Philosophy

### Core Principles

1. **Test Intent, Not Implementation**: Tests verify what the system should do, not how it does it
2. **Real Infrastructure**: Tiers 2-3 use actual databases, services, and systems
3. **Trust Verification**: Every test verifies trust chain integrity
4. **Audit Trail**: Every test verifies audit anchors are created
5. **Security First**: Tests actively try to break trust boundaries

### 3-Tier Testing Structure

| Tier | Scope | Mocking Allowed | Infrastructure |
|------|-------|-----------------|----------------|
| **Tier 1** | Unit Tests | Yes | None |
| **Tier 2** | Integration Tests | **NO** | Docker Compose |
| **Tier 3** | E2E Tests | **NO** | Full Stack |

---

## Tier 1: Unit Tests

### What to Test
- Trust chain data structure operations
- Cryptographic signature verification
- Constraint evaluation logic
- Capability matching algorithms
- Serialization/deserialization

### What NOT to Test
- Database interactions (Tier 2)
- Network communication (Tier 2)
- Cross-agent communication (Tier 2)
- Full workflow execution (Tier 3)

### Unit Test Examples

```python
# tests/unit/trust/test_trust_chain.py

import pytest
from kaizen.trust.chain import (
    TrustLineageChain,
    GenesisRecord,
    CapabilityAttestation,
    ConstraintEnvelope
)
from kaizen.trust.exceptions import InvalidSignatureError

class TestTrustLineageChain:
    """Unit tests for TrustLineageChain."""

    def test_hash_stability(self):
        """Chain hash should be deterministic."""
        genesis = GenesisRecord(
            id="gen-001",
            agent_id="agent-001",
            authority_id="auth-001",
            authority_type=AuthorityType.ORGANIZATION,
            created_at=datetime(2025, 12, 15, 10, 0, 0),
            signature="sig123",
            signature_algorithm="Ed25519"
        )

        chain = TrustLineageChain(
            genesis=genesis,
            capabilities=[],
            delegations=[],
            constraint_envelope=ConstraintEnvelope(agent_id="agent-001"),
            audit_anchors=[]
        )

        # Hash should be same on multiple calls
        assert chain.hash() == chain.hash()

    def test_expiration_detection(self):
        """Expired genesis should be detected."""
        genesis = GenesisRecord(
            id="gen-001",
            agent_id="agent-001",
            authority_id="auth-001",
            authority_type=AuthorityType.ORGANIZATION,
            created_at=datetime(2024, 1, 1),
            expires_at=datetime(2024, 12, 31),  # Expired
            signature="sig123",
            signature_algorithm="Ed25519"
        )

        chain = TrustLineageChain(genesis=genesis, ...)
        assert chain.is_expired() is True

    def test_capability_lookup(self):
        """Should find capabilities by name."""
        cap1 = CapabilityAttestation(
            id="cap-001",
            capability="read_data",
            capability_type=CapabilityType.ACCESS,
            constraints=["read_only"],
            ...
        )
        cap2 = CapabilityAttestation(
            id="cap-002",
            capability="write_data",
            capability_type=CapabilityType.ACTION,
            constraints=["audit_required"],
            ...
        )

        chain = TrustLineageChain(
            genesis=...,
            capabilities=[cap1, cap2],
            ...
        )

        assert chain.has_capability("read_data") is True
        assert chain.has_capability("delete_data") is False

    def test_effective_constraints_aggregation(self):
        """Constraints should aggregate from all sources."""
        # Genesis constraints
        genesis = GenesisRecord(...)

        # Capability constraints
        cap = CapabilityAttestation(
            capability="analyze",
            constraints=["read_only"],
            ...
        )

        # Delegation constraints
        delegation = DelegationRecord(
            capabilities_delegated=["analyze"],
            constraint_subset=["time_limited"],
            ...
        )

        chain = TrustLineageChain(
            genesis=genesis,
            capabilities=[cap],
            delegations=[delegation],
            ...
        )

        effective = chain.get_effective_constraints("analyze")
        assert "read_only" in effective
        assert "time_limited" in effective


class TestConstraintEvaluation:
    """Unit tests for constraint evaluation."""

    def test_time_window_constraint(self):
        """Time window constraint should block outside hours."""
        constraint = Constraint(
            constraint_type=ConstraintType.TIME_WINDOW,
            value={"start": "09:00", "end": "17:00", "timezone": "UTC"}
        )

        # During business hours
        context = {"current_time": datetime(2025, 12, 15, 12, 0, 0)}
        assert evaluate_single_constraint(constraint, "action", None, context) is True

        # Outside business hours
        context = {"current_time": datetime(2025, 12, 15, 22, 0, 0)}
        assert evaluate_single_constraint(constraint, "action", None, context) is False

    def test_resource_scope_constraint(self):
        """Resource scope should limit accessible resources."""
        constraint = Constraint(
            constraint_type=ConstraintType.DATA_SCOPE,
            value={"tables": ["transactions", "accounts"]}
        )

        # Allowed table
        assert evaluate_single_constraint(constraint, "read", "transactions", {}) is True

        # Disallowed table
        assert evaluate_single_constraint(constraint, "read", "users", {}) is False


class TestSignatureVerification:
    """Unit tests for cryptographic operations."""

    def test_valid_signature_verification(self):
        """Valid signatures should verify successfully."""
        # Create key pair
        private_key, public_key = generate_ed25519_keypair()

        payload = b"test payload"
        signature = sign(payload, private_key)

        assert verify(payload, signature, public_key) is True

    def test_invalid_signature_rejection(self):
        """Invalid signatures should be rejected."""
        _, public_key = generate_ed25519_keypair()

        payload = b"test payload"
        invalid_signature = "invalid-signature"

        with pytest.raises(InvalidSignatureError):
            verify(payload, invalid_signature, public_key)

    def test_tampered_payload_detection(self):
        """Tampered payloads should fail verification."""
        private_key, public_key = generate_ed25519_keypair()

        original_payload = b"test payload"
        signature = sign(original_payload, private_key)

        tampered_payload = b"TAMPERED payload"

        assert verify(tampered_payload, signature, public_key) is False
```

---

## Tier 2: Integration Tests

### Infrastructure Setup

```yaml
# tests/integration/docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: eatp_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    ports:
      - "6380:6379"

  mock-legacy-api:
    build: ./mock-legacy-api
    ports:
      - "8081:8080"
```

### Integration Test Examples

```python
# tests/integration/trust/test_trust_operations.py

import pytest
from kaizen.trust.operations import TrustOperations
from kaizen.trust.store import PostgresTrustStore
from kaizen.trust.key_manager import LocalKeyManager

@pytest.fixture
async def trust_ops(postgres_connection):
    """Create TrustOperations with real database."""
    store = PostgresTrustStore(postgres_connection)
    key_manager = LocalKeyManager()
    authority_registry = await create_test_authority_registry(postgres_connection)

    return TrustOperations(
        authority_registry=authority_registry,
        key_manager=key_manager,
        trust_store=store
    )


class TestEstablishOperation:
    """Integration tests for ESTABLISH operation."""

    async def test_establish_creates_complete_chain(self, trust_ops):
        """ESTABLISH should create all chain elements."""
        # Create authority
        authority = await trust_ops.authority_registry.create(
            id="auth-test",
            name="Test Authority",
            authority_type=AuthorityType.ORGANIZATION
        )

        # Establish trust
        chain = await trust_ops.establish(
            agent_id="agent-test",
            authority_id=authority.id,
            capabilities=[
                CapabilityRequest(
                    capability="analyze_data",
                    capability_type=CapabilityType.ACCESS,
                    constraints=["read_only"]
                )
            ],
            constraints=["audit_required"]
        )

        # Verify chain structure
        assert chain.genesis is not None
        assert chain.genesis.authority_id == authority.id
        assert len(chain.capabilities) == 1
        assert chain.capabilities[0].capability == "analyze_data"

        # Verify persisted to database
        stored_chain = await trust_ops.trust_store.get_chain("agent-test")
        assert stored_chain is not None
        assert stored_chain.hash() == chain.hash()

    async def test_establish_rejects_inactive_authority(self, trust_ops):
        """ESTABLISH should reject inactive authority."""
        authority = await trust_ops.authority_registry.create(
            id="auth-inactive",
            name="Inactive Authority",
            is_active=False
        )

        with pytest.raises(AuthorityInactiveError):
            await trust_ops.establish(
                agent_id="agent-test",
                authority_id=authority.id,
                capabilities=[...]
            )

    async def test_establish_creates_audit_anchor(self, trust_ops):
        """ESTABLISH should create audit anchor."""
        authority = await create_active_authority(trust_ops)

        chain = await trust_ops.establish(
            agent_id="agent-audit-test",
            authority_id=authority.id,
            capabilities=[...]
        )

        # Verify audit anchor exists
        anchors = await trust_ops.audit_store.query(agent_id="agent-audit-test")
        assert len(anchors) >= 1
        assert anchors[0].action == "trust_established"


class TestDelegateOperation:
    """Integration tests for DELEGATE operation."""

    async def test_delegate_creates_chain_link(self, trust_ops):
        """DELEGATE should link delegator and delegatee."""
        authority = await create_active_authority(trust_ops)

        # Setup delegator
        delegator_chain = await trust_ops.establish(
            agent_id="delegator",
            authority_id=authority.id,
            capabilities=[
                CapabilityRequest(capability="analyze_data", constraints=["read_only"])
            ]
        )

        # Setup delegatee
        delegatee_chain = await trust_ops.establish(
            agent_id="delegatee",
            authority_id=authority.id,
            capabilities=[]
        )

        # Delegate
        delegation = await trust_ops.delegate(
            delegator_id="delegator",
            delegatee_id="delegatee",
            task_id="task-001",
            capabilities=["analyze_data"],
            additional_constraints=["time_limited"]
        )

        # Verify delegation record
        assert delegation.delegator_id == "delegator"
        assert delegation.delegatee_id == "delegatee"
        assert "analyze_data" in delegation.capabilities_delegated
        assert "time_limited" in delegation.constraint_subset

        # Verify delegatee's chain updated
        updated_chain = await trust_ops.trust_store.get_chain("delegatee")
        assert len(updated_chain.delegations) == 1

    async def test_delegate_prevents_constraint_loosening(self, trust_ops):
        """DELEGATE should not allow loosening constraints."""
        authority = await create_active_authority(trust_ops)

        # Delegator has read_only constraint
        await trust_ops.establish(
            agent_id="strict-delegator",
            authority_id=authority.id,
            capabilities=[
                CapabilityRequest(capability="data_access", constraints=["read_only"])
            ]
        )

        await trust_ops.establish(
            agent_id="delegatee",
            authority_id=authority.id,
            capabilities=[]
        )

        # Trying to delegate without read_only should work (adds more constraints)
        # But we verify the constraint is inherited
        delegation = await trust_ops.delegate(
            delegator_id="strict-delegator",
            delegatee_id="delegatee",
            task_id="task-001",
            capabilities=["data_access"],
            additional_constraints=[]  # Not adding, but inherited
        )

        # Delegatee should inherit read_only
        delegatee_chain = await trust_ops.trust_store.get_chain("delegatee")
        effective = delegatee_chain.get_effective_constraints("data_access")
        assert "read_only" in effective


class TestVerifyOperation:
    """Integration tests for VERIFY operation."""

    async def test_verify_allows_valid_action(self, trust_ops):
        """VERIFY should allow actions within trust bounds."""
        authority = await create_active_authority(trust_ops)

        await trust_ops.establish(
            agent_id="verified-agent",
            authority_id=authority.id,
            capabilities=[
                CapabilityRequest(capability="read_data", constraints=[])
            ]
        )

        result = await trust_ops.verify(
            agent_id="verified-agent",
            action="read_data",
            resource="test_table",
            level=VerificationLevel.STANDARD
        )

        assert result.valid is True

    async def test_verify_blocks_unauthorized_action(self, trust_ops):
        """VERIFY should block actions not in capabilities."""
        authority = await create_active_authority(trust_ops)

        await trust_ops.establish(
            agent_id="limited-agent",
            authority_id=authority.id,
            capabilities=[
                CapabilityRequest(capability="read_data", constraints=[])
            ]
        )

        result = await trust_ops.verify(
            agent_id="limited-agent",
            action="delete_data",  # Not authorized
            resource="test_table",
            level=VerificationLevel.STANDARD
        )

        assert result.valid is False
        assert "No capability found" in result.reason

    async def test_verify_respects_constraints(self, trust_ops):
        """VERIFY should enforce constraint boundaries."""
        authority = await create_active_authority(trust_ops)

        await trust_ops.establish(
            agent_id="constrained-agent",
            authority_id=authority.id,
            capabilities=[
                CapabilityRequest(
                    capability="access_data",
                    constraints=["read_only"],
                    scope={"tables": ["allowed_table"]}
                )
            ]
        )

        # Action on allowed table - should pass
        result = await trust_ops.verify(
            agent_id="constrained-agent",
            action="access_data",
            resource="allowed_table"
        )
        assert result.valid is True

        # Action on disallowed table - should fail
        result = await trust_ops.verify(
            agent_id="constrained-agent",
            action="access_data",
            resource="secret_table"
        )
        assert result.valid is False

    async def test_verify_full_checks_signatures(self, trust_ops):
        """VERIFY FULL should validate all signatures."""
        authority = await create_active_authority(trust_ops)

        chain = await trust_ops.establish(
            agent_id="sig-test-agent",
            authority_id=authority.id,
            capabilities=[
                CapabilityRequest(capability="test_cap", constraints=[])
            ]
        )

        # Tamper with signature (simulate attack)
        chain.genesis.signature = "tampered-signature"
        await trust_ops.trust_store.save_chain(chain)

        # QUICK should still pass (no signature check)
        result = await trust_ops.verify(
            agent_id="sig-test-agent",
            action="test_cap",
            level=VerificationLevel.QUICK
        )
        assert result.valid is True

        # FULL should fail (signature check)
        result = await trust_ops.verify(
            agent_id="sig-test-agent",
            action="test_cap",
            level=VerificationLevel.FULL
        )
        assert result.valid is False
        assert "Invalid genesis signature" in result.reason
```

---

## Tier 3: End-to-End Tests

### E2E Test Examples

```python
# tests/e2e/test_trust_workflow.py

import pytest
from kaizen.trust.agent import TrustedAgent, TrustedSupervisorAgent, TrustedWorkerAgent
from kaizen.orchestration.runtime import TrustAwareOrchestrationRuntime

@pytest.fixture
async def full_eatp_stack():
    """Setup complete EATP stack for E2E testing."""
    # This uses real infrastructure from docker-compose
    async with setup_full_stack() as stack:
        yield stack


class TestSupervisorWorkerTrust:
    """E2E tests for supervisor-worker pattern with trust."""

    async def test_complete_supervised_workflow(self, full_eatp_stack):
        """Test complete supervisor-worker flow with trust verification."""
        trust_ops = full_eatp_stack.trust_ops
        authority = full_eatp_stack.authority

        # Create supervisor
        supervisor = TrustedSupervisorAgent(name="e2e-supervisor")
        await supervisor.establish_trust(
            authority_id=authority.id,
            capabilities=[
                CapabilityRequest(capability="manage_workers", constraints=[]),
                CapabilityRequest(capability="aggregate_results", constraints=[])
            ]
        )

        # Create workers
        worker1 = TrustedWorkerAgent(name="e2e-worker-1")
        await worker1.establish_trust(
            authority_id=authority.id,
            capabilities=[
                CapabilityRequest(capability="analyze_data", constraints=["read_only"])
            ]
        )

        worker2 = TrustedWorkerAgent(name="e2e-worker-2")
        await worker2.establish_trust(
            authority_id=authority.id,
            capabilities=[
                CapabilityRequest(capability="analyze_data", constraints=["read_only"])
            ]
        )

        # Create runtime
        runtime = TrustAwareOrchestrationRuntime(
            agents={"supervisor": supervisor, "worker1": worker1, "worker2": worker2},
            trust_ops=trust_ops
        )

        # Execute workflow
        result = await runtime.execute(
            input={"data": "test data to analyze"},
            pattern="supervisor_worker",
            task_id="e2e-test-001"
        )

        # Verify success
        assert result.success is True

        # Verify delegations were created
        assert len(result.delegations) >= 2  # One per worker

        # Verify audit trail
        assert len(result.audit_trail) >= 4  # Supervisor + workers

        # Verify delegation chain integrity
        for delegation in result.delegations:
            assert delegation.delegator_id == supervisor.id
            assert "read_only" in delegation.constraint_subset  # Constraints propagated

    async def test_worker_constraint_enforcement(self, full_eatp_stack):
        """Test that workers cannot exceed their constraints."""
        trust_ops = full_eatp_stack.trust_ops
        authority = full_eatp_stack.authority

        # Create worker with strict constraints
        worker = TrustedWorkerAgent(name="strict-worker")
        await worker.establish_trust(
            authority_id=authority.id,
            capabilities=[
                CapabilityRequest(
                    capability="query_database",
                    constraints=["read_only", "no_pii"],
                    scope={"tables": ["public_data"]}
                )
            ]
        )

        # Worker tries to access PII table - should fail
        with pytest.raises(ConstraintViolationError):
            await worker.call_tool(
                "database_query",
                query="SELECT * FROM users_pii"
            )

        # Verify audit recorded the failed attempt
        anchors = await trust_ops.audit_store.query(
            agent_id=worker.id,
            result=ActionResult.DENIED
        )
        assert len(anchors) >= 1


class TestA2ATrust:
    """E2E tests for A2A protocol with trust."""

    async def test_a2a_cross_agent_trust(self, full_eatp_stack):
        """Test A2A communication with trust verification."""
        # Start A2A service for agent A
        agent_a = TrustedAgent(name="agent-a")
        await agent_a.establish_trust(...)
        service_a = A2AService(agent=agent_a, trust_ops=full_eatp_stack.trust_ops)

        # Start A2A service for agent B
        agent_b = TrustedAgent(name="agent-b")
        await agent_b.establish_trust(...)
        service_b = A2AService(agent=agent_b, trust_ops=full_eatp_stack.trust_ops)

        async with run_services([service_a, service_b]) as (url_a, url_b):
            # Agent A fetches Agent B's agent card
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url_b}/.well-known/agent.json") as resp:
                    card_b = await resp.json()

            # Verify trust lineage in card
            assert "trust_lineage" in card_b
            assert card_b["trust_lineage"]["genesis"]["authority_id"] is not None

            # Agent A sends task to Agent B
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{url_b}/a2a",
                    json={
                        "jsonrpc": "2.0",
                        "method": "task.create",
                        "params": {"input": {"text": "analyze this"}},
                        "id": 1
                    },
                    headers={
                        "X-Agent-Card-URL": f"{url_a}/.well-known/agent.json"
                    }
                ) as resp:
                    result = await resp.json()

            # Should succeed with trust verification
            assert "result" in result
            assert result["result"]["status"] == "pending"


class TestESATrust:
    """E2E tests for ESA pattern."""

    async def test_esa_database_access(self, full_eatp_stack, postgres_connection):
        """Test ESA-mediated database access."""
        # Create ESA for test database
        esa = DatabaseESA(
            name="test-db-esa",
            connection_string=postgres_connection,
            trust_ops=full_eatp_stack.trust_ops
        )
        await esa.connect_and_inherit_trust(authority_id=full_eatp_stack.authority.id)

        # Create agent that needs database access
        agent = TrustedAgent(name="db-user-agent")
        await agent.establish_trust(
            authority_id=full_eatp_stack.authority.id,
            capabilities=[]  # No direct database capability
        )

        # Delegate database access through ESA
        delegation = await esa.delegate_system_access(
            to_agent=agent,
            capabilities=["read_test_table"],
            constraints=["read_only", "limit_100"]
        )

        # Agent accesses database through ESA
        result = await esa.execute_on_behalf(
            agent=agent,
            capability="read_test_table",
            operation="query:test_table",
            params={"query": "SELECT * FROM test_table LIMIT 10"}
        )

        assert result is not None

        # Verify audit trail through ESA
        anchors = await full_eatp_stack.trust_ops.audit_store.query(
            agent_id=esa.id,
            action_prefix="esa_proxy:"
        )
        assert len(anchors) >= 1
        assert anchors[-1].context["on_behalf_of"] == agent.id
```

---

## Security Testing

### Attack Simulation Tests

```python
# tests/security/test_trust_attacks.py

class TestTrustAttacks:
    """Security tests simulating attacks on trust system."""

    async def test_signature_forgery_attack(self, trust_ops):
        """Attempt to forge genesis signature."""
        # Create legitimate chain
        authority = await create_active_authority(trust_ops)
        chain = await trust_ops.establish(
            agent_id="victim-agent",
            authority_id=authority.id,
            capabilities=[CapabilityRequest(capability="sensitive_action", ...)]
        )

        # Attacker tries to forge new genesis with more capabilities
        forged_genesis = GenesisRecord(
            id="forged-gen",
            agent_id="attacker-agent",
            authority_id=authority.id,
            capabilities=[CapabilityRequest(capability="admin_access", ...)],
            signature="forged-signature"
        )

        forged_chain = TrustLineageChain(genesis=forged_genesis, ...)

        # Verification should fail
        result = await trust_ops.verify(
            agent_id="attacker-agent",
            action="admin_access",
            level=VerificationLevel.FULL
        )
        assert result.valid is False

    async def test_replay_attack(self, trust_ops):
        """Attempt to replay expired delegation."""
        authority = await create_active_authority(trust_ops)

        # Create short-lived delegation
        delegator = await create_trusted_agent(trust_ops, "delegator")
        delegatee = await create_trusted_agent(trust_ops, "delegatee")

        delegation = await trust_ops.delegate(
            delegator_id=delegator.id,
            delegatee_id=delegatee.id,
            task_id="temp-task",
            capabilities=["sensitive_action"],
            expires_at=datetime.utcnow() + timedelta(seconds=1)
        )

        # Wait for expiration
        await asyncio.sleep(2)

        # Attempt to use expired delegation
        result = await trust_ops.verify(
            agent_id=delegatee.id,
            action="sensitive_action",
            level=VerificationLevel.STANDARD
        )
        assert result.valid is False

    async def test_privilege_escalation_attack(self, trust_ops):
        """Attempt to escalate privileges through delegation."""
        authority = await create_active_authority(trust_ops)

        # Limited agent
        limited_agent = await trust_ops.establish(
            agent_id="limited",
            authority_id=authority.id,
            capabilities=[
                CapabilityRequest(capability="read_data", constraints=["read_only"])
            ]
        )

        # Attacker agent
        attacker = await trust_ops.establish(
            agent_id="attacker",
            authority_id=authority.id,
            capabilities=[]
        )

        # Attacker tries to get delegation with write access
        with pytest.raises(ConstraintViolationError):
            await trust_ops.delegate(
                delegator_id="limited",
                delegatee_id="attacker",
                task_id="attack-task",
                capabilities=["read_data"],
                additional_constraints=[]  # Trying to remove read_only
            )

    async def test_chain_tampering_detection(self, trust_ops):
        """Detect tampering in trust chain."""
        authority = await create_active_authority(trust_ops)

        chain = await trust_ops.establish(
            agent_id="target-agent",
            authority_id=authority.id,
            capabilities=[CapabilityRequest(capability="action", ...)]
        )

        original_hash = chain.hash()

        # Tamper with capability
        chain.capabilities[0].constraints = []  # Remove constraints

        # Hash should change
        assert chain.hash() != original_hash

        # Full verification should fail
        result = chain.verify(trust_ops.authority_registry)
        assert result.valid is False
```

---

## Performance Testing

```python
# tests/performance/test_trust_performance.py

class TestTrustPerformance:
    """Performance tests for trust operations."""

    async def test_verify_quick_latency(self, trust_ops, benchmark):
        """VERIFY QUICK should complete under 5ms."""
        # Setup
        await setup_agent_with_chain(trust_ops, "perf-agent")

        # Benchmark
        result = await benchmark(
            trust_ops.verify,
            agent_id="perf-agent",
            action="test_action",
            level=VerificationLevel.QUICK
        )

        assert result.mean < 0.005  # 5ms

    async def test_verify_standard_latency(self, trust_ops, benchmark):
        """VERIFY STANDARD should complete under 50ms."""
        await setup_agent_with_chain(trust_ops, "perf-agent")

        result = await benchmark(
            trust_ops.verify,
            agent_id="perf-agent",
            action="test_action",
            level=VerificationLevel.STANDARD
        )

        assert result.mean < 0.050  # 50ms

    async def test_concurrent_verifications(self, trust_ops):
        """System should handle 100 concurrent verifications."""
        await setup_agent_with_chain(trust_ops, "concurrent-agent")

        tasks = [
            trust_ops.verify(
                agent_id="concurrent-agent",
                action="test_action",
                level=VerificationLevel.STANDARD
            )
            for _ in range(100)
        ]

        start = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        # All should succeed
        assert all(r.valid for r in results)
        # Should complete within 1 second
        assert elapsed < 1.0
```

---

## Test Coverage Requirements

| Component | Required Coverage |
|-----------|-------------------|
| Trust Chain Data Structures | 95% |
| Trust Operations | 90% |
| TrustedAgent | 90% |
| A2A Service | 85% |
| ESA Pattern | 85% |
| Orchestration Integration | 80% |

---

## Next Steps

1. **Document 09**: Phased Implementation Plan
2. Create test fixtures and infrastructure
3. Implement Tier 1 tests first
4. Setup Docker Compose for Tier 2/3
