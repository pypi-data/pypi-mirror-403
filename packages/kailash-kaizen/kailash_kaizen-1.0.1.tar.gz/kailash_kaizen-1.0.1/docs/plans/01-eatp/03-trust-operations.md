# EATP Implementation Plan: Trust Operations

## Document Control
- **Version**: 1.0
- **Date**: 2025-12-15
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## Overview

EATP defines four core operations that manipulate and verify the Trust Lineage Chain:

| Operation | Purpose | When Used |
|-----------|---------|-----------|
| **ESTABLISH** | Create initial trust | Agent creation |
| **DELEGATE** | Transfer trust | Task assignment |
| **VERIFY** | Validate trust | Before any action |
| **AUDIT** | Record actions | After any action |

---

## Operation 1: ESTABLISH

### Purpose
Creates the initial Trust Lineage Chain for an agent. This is the genesis operation that makes an agent "trusted."

### Preconditions
1. Authority must exist and be active
2. Authority must have permission to create agents
3. Agent must not already have a Genesis Record

### Implementation

```python
class TrustOperations:
    """Core EATP trust operations."""

    def __init__(
        self,
        authority_registry: OrganizationalAuthorityRegistry,
        key_manager: TrustKeyManager,
        trust_store: TrustStore
    ):
        self.authority_registry = authority_registry
        self.key_manager = key_manager
        self.trust_store = trust_store

    async def establish(
        self,
        agent_id: str,
        authority_id: str,
        capabilities: List[CapabilityRequest],
        constraints: List[str] = None,
        metadata: Dict[str, Any] = None,
        expires_at: Optional[datetime] = None
    ) -> TrustLineageChain:
        """
        ESTABLISH: Create initial trust for an agent.

        Args:
            agent_id: Unique identifier for the agent
            authority_id: Authority granting trust
            capabilities: Requested capabilities
            constraints: Initial constraints
            metadata: Additional context
            expires_at: Optional expiration

        Returns:
            TrustLineageChain: Complete trust chain for agent

        Raises:
            AuthorityNotFoundError: If authority doesn't exist
            AuthorityInactiveError: If authority is not active
            AgentAlreadyEstablishedError: If agent already has trust
        """
        # 1. Validate authority
        authority = await self.authority_registry.get(authority_id)
        if not authority:
            raise AuthorityNotFoundError(authority_id)
        if not authority.is_active:
            raise AuthorityInactiveError(authority_id)

        # 2. Check agent doesn't already exist
        existing = await self.trust_store.get_chain(agent_id)
        if existing:
            raise AgentAlreadyEstablishedError(agent_id)

        # 3. Create Genesis Record
        genesis = GenesisRecord(
            id=f"gen-{uuid4()}",
            agent_id=agent_id,
            authority_id=authority_id,
            authority_type=authority.authority_type,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            signature="",  # Will be signed below
            signature_algorithm="Ed25519",
            metadata=metadata or {}
        )

        # 4. Sign genesis record
        genesis.signature = await self.key_manager.sign(
            serialize_for_signing(genesis),
            authority.signing_key_id
        )

        # 5. Create Capability Attestations
        capability_attestations = []
        for cap_request in capabilities:
            attestation = CapabilityAttestation(
                id=f"cap-{uuid4()}",
                capability=cap_request.capability,
                capability_type=cap_request.capability_type,
                constraints=cap_request.constraints + (constraints or []),
                attester_id=authority_id,
                attested_at=datetime.utcnow(),
                expires_at=expires_at,
                signature="",
                scope=cap_request.scope
            )
            attestation.signature = await self.key_manager.sign(
                serialize_for_signing(attestation),
                authority.signing_key_id
            )
            capability_attestations.append(attestation)

        # 6. Create initial Constraint Envelope
        constraint_envelope = self._compute_constraint_envelope(
            agent_id,
            genesis,
            capability_attestations,
            []  # No delegations yet
        )

        # 7. Create Trust Lineage Chain
        chain = TrustLineageChain(
            genesis=genesis,
            capabilities=capability_attestations,
            delegations=[],
            constraint_envelope=constraint_envelope,
            audit_anchors=[]
        )

        # 8. Store and return
        await self.trust_store.save_chain(chain)

        # 9. Create audit anchor for establishment
        await self.audit(
            agent_id=agent_id,
            action="trust_established",
            resource=None,
            result=ActionResult.SUCCESS,
            context={"authority_id": authority_id}
        )

        return chain
```

### Usage Example

```python
# Create a trusted data analyst agent
chain = await trust_ops.establish(
    agent_id="data-analyst-001",
    authority_id="org-acme-corp",
    capabilities=[
        CapabilityRequest(
            capability="analyze_financial_data",
            capability_type=CapabilityType.ACCESS,
            constraints=["read_only", "no_pii_export"],
            scope={"databases": ["finance_db"]}
        ),
        CapabilityRequest(
            capability="generate_reports",
            capability_type=CapabilityType.ACTION,
            constraints=["internal_only"],
            scope={"formats": ["pdf", "xlsx"]}
        )
    ],
    constraints=["audit_required", "business_hours_only"],
    metadata={"department": "Finance", "owner": "john.doe@acme.com"},
    expires_at=datetime(2026, 12, 15)
)
```

---

## Operation 2: DELEGATE

### Purpose
Transfers trust from one agent to another for a specific task. Constraints can only be tightened, never loosened.

### Preconditions
1. Delegator must have valid trust chain
2. Delegator must have the capabilities being delegated
3. Delegatee must have valid genesis (or will be established)
4. New constraints must be subset of delegator's constraints

### Implementation

```python
async def delegate(
    self,
    delegator_id: str,
    delegatee_id: str,
    task_id: str,
    capabilities: List[str],
    additional_constraints: List[str] = None,
    expires_at: Optional[datetime] = None
) -> DelegationRecord:
    """
    DELEGATE: Transfer trust from one agent to another.

    Args:
        delegator_id: Agent delegating trust
        delegatee_id: Agent receiving trust
        task_id: Associated task identifier
        capabilities: Capabilities to delegate
        additional_constraints: Extra constraints (tightening)
        expires_at: Optional expiration

    Returns:
        DelegationRecord: Record of the delegation

    Raises:
        TrustChainNotFoundError: If delegator has no trust
        CapabilityNotFoundError: If delegator lacks capability
        ConstraintViolationError: If trying to loosen constraints
    """
    # 1. Get delegator's trust chain
    delegator_chain = await self.trust_store.get_chain(delegator_id)
    if not delegator_chain:
        raise TrustChainNotFoundError(delegator_id)

    # 2. Verify delegator's chain is valid
    verification = delegator_chain.verify(self.authority_registry)
    if not verification.valid:
        raise InvalidTrustChainError(delegator_id, verification.reason)

    # 3. Check delegator has all requested capabilities
    for cap in capabilities:
        if not delegator_chain.has_capability(cap):
            raise CapabilityNotFoundError(delegator_id, cap)

    # 4. Verify constraint tightening (not loosening)
    for cap in capabilities:
        delegator_constraints = set(delegator_chain.get_effective_constraints(cap))
        new_constraints = delegator_constraints | set(additional_constraints or [])

        # This check ensures we only add constraints, never remove
        if not new_constraints.issuperset(delegator_constraints):
            raise ConstraintViolationError(
                f"Cannot loosen constraints for capability '{cap}'"
            )

    # 5. Get or verify delegatee's chain
    delegatee_chain = await self.trust_store.get_chain(delegatee_id)
    if not delegatee_chain:
        raise TrustChainNotFoundError(delegatee_id)

    # 6. Create delegation record
    delegation = DelegationRecord(
        id=f"del-{uuid4()}",
        delegator_id=delegator_id,
        delegatee_id=delegatee_id,
        task_id=task_id,
        capabilities_delegated=capabilities,
        constraint_subset=additional_constraints or [],
        delegated_at=datetime.utcnow(),
        expires_at=expires_at or self._compute_delegation_expiry(delegator_chain),
        signature="",
        parent_delegation_id=self._find_parent_delegation(delegator_chain, capabilities)
    )

    # 7. Sign delegation with delegator's key
    delegation.signature = await self.key_manager.sign(
        serialize_for_signing(delegation),
        f"agent-{delegator_id}"
    )

    # 8. Update delegatee's chain
    delegatee_chain.delegations.append(delegation)
    delegatee_chain.constraint_envelope = self._compute_constraint_envelope(
        delegatee_id,
        delegatee_chain.genesis,
        delegatee_chain.capabilities,
        delegatee_chain.delegations
    )

    # 9. Store updated chain
    await self.trust_store.save_chain(delegatee_chain)

    # 10. Create audit anchors for both parties
    await self.audit(
        agent_id=delegator_id,
        action="trust_delegated",
        resource=delegatee_id,
        result=ActionResult.SUCCESS,
        context={"task_id": task_id, "capabilities": capabilities}
    )

    await self.audit(
        agent_id=delegatee_id,
        action="trust_received",
        resource=delegator_id,
        result=ActionResult.SUCCESS,
        context={"task_id": task_id, "capabilities": capabilities}
    )

    return delegation
```

### Usage Example

```python
# Supervisor delegates analysis task to worker
delegation = await trust_ops.delegate(
    delegator_id="supervisor-agent-001",
    delegatee_id="worker-agent-001",
    task_id="task-q4-analysis",
    capabilities=["analyze_financial_data"],
    additional_constraints=["q4_data_only", "summary_output_only"],
    expires_at=datetime.utcnow() + timedelta(hours=8)
)
```

---

## Operation 3: VERIFY

### Purpose
Validates that an agent has the trust required to perform a specific action. Called before every action.

### Verification Levels

| Level | Checks | Performance | Use Case |
|-------|--------|-------------|----------|
| **QUICK** | Chain hash, expiration | ~1ms | Frequent operations |
| **STANDARD** | + Capability match, constraints | ~5ms | Normal operations |
| **FULL** | + Signature verification | ~50ms | Sensitive operations |

### Implementation

```python
async def verify(
    self,
    agent_id: str,
    action: str,
    resource: Optional[str] = None,
    level: VerificationLevel = VerificationLevel.STANDARD,
    context: Dict[str, Any] = None
) -> VerificationResult:
    """
    VERIFY: Check if agent has trust to perform action.

    Args:
        agent_id: Agent requesting to act
        action: Action to perform
        resource: Optional resource being accessed
        level: Verification thoroughness
        context: Additional context for constraint evaluation

    Returns:
        VerificationResult: Whether action is permitted

    Note:
        This operation is designed for high performance as it's
        called before every agent action.
    """
    context = context or {}

    # 1. Get agent's trust chain (with caching)
    chain = await self.trust_store.get_chain(agent_id, use_cache=True)
    if not chain:
        return VerificationResult(
            valid=False,
            reason="No trust chain found",
            level=level
        )

    # QUICK: Just check hash and expiration
    if level == VerificationLevel.QUICK:
        if chain.is_expired():
            return VerificationResult(valid=False, reason="Trust chain expired")
        return VerificationResult(valid=True, level=level)

    # STANDARD: Check capabilities and constraints
    # 2. Find matching capability
    capability = self._match_capability(chain, action)
    if not capability:
        return VerificationResult(
            valid=False,
            reason=f"No capability found for action '{action}'",
            level=level
        )

    # 3. Evaluate constraints
    constraint_result = evaluate_constraints(
        chain.constraint_envelope,
        action,
        resource,
        context
    )

    if not constraint_result.permitted:
        return VerificationResult(
            valid=False,
            reason="Constraint violation",
            violations=constraint_result.violations,
            level=level
        )

    # FULL: Also verify all signatures
    if level == VerificationLevel.FULL:
        # 4. Verify genesis signature
        if not await self._verify_genesis_signature(chain.genesis):
            return VerificationResult(
                valid=False,
                reason="Invalid genesis signature",
                level=level
            )

        # 5. Verify capability signatures
        for cap in chain.capabilities:
            if not await self._verify_capability_signature(cap):
                return VerificationResult(
                    valid=False,
                    reason=f"Invalid capability signature: {cap.id}",
                    level=level
                )

        # 6. Verify delegation chain
        for del_ in chain.delegations:
            if not await self._verify_delegation_signature(del_):
                return VerificationResult(
                    valid=False,
                    reason=f"Invalid delegation signature: {del_.id}",
                    level=level
                )

    return VerificationResult(
        valid=True,
        level=level,
        capability_used=capability.id,
        effective_constraints=chain.get_effective_constraints(capability.capability)
    )

def _match_capability(
    self,
    chain: TrustLineageChain,
    action: str
) -> Optional[CapabilityAttestation]:
    """Match action to capability using semantic matching."""
    # Direct match
    for cap in chain.capabilities:
        if cap.capability == action:
            return cap

    # Hierarchical match (e.g., "read_users" matches "read_*")
    for cap in chain.capabilities:
        if self._capability_matches(cap.capability, action):
            return cap

    # Semantic match (using embeddings if available)
    if self.semantic_matcher:
        return self.semantic_matcher.find_capability(chain.capabilities, action)

    return None
```

### Usage Example

```python
# Before executing an action
result = await trust_ops.verify(
    agent_id="worker-agent-001",
    action="query_transactions",
    resource="finance_db.transactions",
    level=VerificationLevel.STANDARD,
    context={"current_time": datetime.utcnow()}
)

if result.valid:
    # Proceed with action
    data = await execute_query(...)
else:
    # Deny action
    raise TrustVerificationError(result.reason, result.violations)
```

---

## Operation 4: AUDIT

### Purpose
Creates an immutable record of agent actions. Enables compliance reporting and forensic analysis.

### Implementation

```python
async def audit(
    self,
    agent_id: str,
    action: str,
    resource: Optional[str] = None,
    result: ActionResult = ActionResult.SUCCESS,
    context: Dict[str, Any] = None,
    parent_anchor_id: Optional[str] = None
) -> AuditAnchor:
    """
    AUDIT: Record agent action for compliance.

    Args:
        agent_id: Agent that performed action
        action: What was done
        resource: Resource affected
        result: Outcome of action
        context: Additional context
        parent_anchor_id: Triggering action (for chains)

    Returns:
        AuditAnchor: Immutable record of action
    """
    # 1. Get agent's current trust chain
    chain = await self.trust_store.get_chain(agent_id)
    if not chain:
        raise TrustChainNotFoundError(agent_id)

    # 2. Create audit anchor
    anchor = AuditAnchor(
        id=f"aud-{uuid4()}",
        agent_id=agent_id,
        action=action,
        resource=resource,
        timestamp=datetime.utcnow(),
        trust_chain_hash=chain.hash(),
        result=result,
        parent_anchor_id=parent_anchor_id,
        signature=""
    )

    # 3. Sign audit anchor
    anchor.signature = await self.key_manager.sign(
        serialize_for_signing(anchor),
        f"agent-{agent_id}"
    )

    # 4. Store anchor (append-only)
    await self.audit_store.append(anchor)

    # 5. Update chain's audit anchors (for quick access)
    chain.audit_anchors.append(anchor)
    await self.trust_store.save_chain(chain)

    # 6. Emit audit event (for real-time monitoring)
    await self.event_emitter.emit("audit.action", {
        "anchor_id": anchor.id,
        "agent_id": agent_id,
        "action": action,
        "result": result.value
    })

    return anchor
```

### Audit Query API

```python
class AuditQueryService:
    """Query and analyze audit records."""

    async def get_agent_history(
        self,
        agent_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        actions: Optional[List[str]] = None
    ) -> List[AuditAnchor]:
        """Get audit history for an agent."""
        pass

    async def get_action_chain(
        self,
        anchor_id: str
    ) -> List[AuditAnchor]:
        """Get full chain of related actions."""
        anchors = []
        current = await self.audit_store.get(anchor_id)

        while current:
            anchors.append(current)
            if current.parent_anchor_id:
                current = await self.audit_store.get(current.parent_anchor_id)
            else:
                break

        return list(reversed(anchors))

    async def generate_compliance_report(
        self,
        start_time: datetime,
        end_time: datetime,
        authority_id: Optional[str] = None
    ) -> ComplianceReport:
        """Generate compliance report for time period."""
        pass
```

---

## Operation Integration: Complete Flow

### Example: Supervisor-Worker Task Execution

```python
async def execute_supervised_task(
    supervisor: TrustedAgent,
    worker: TrustedAgent,
    task: Task
):
    """Complete trust-aware task execution flow."""

    # 1. VERIFY supervisor can delegate
    verify_result = await trust_ops.verify(
        agent_id=supervisor.id,
        action="delegate_task",
        resource=worker.id,
        level=VerificationLevel.STANDARD
    )
    if not verify_result.valid:
        raise TrustError(f"Supervisor cannot delegate: {verify_result.reason}")

    # 2. DELEGATE task to worker
    delegation = await trust_ops.delegate(
        delegator_id=supervisor.id,
        delegatee_id=worker.id,
        task_id=task.id,
        capabilities=task.required_capabilities,
        additional_constraints=task.constraints
    )

    # 3. VERIFY worker can execute task
    for action in task.actions:
        verify_result = await trust_ops.verify(
            agent_id=worker.id,
            action=action.name,
            resource=action.resource,
            level=VerificationLevel.STANDARD
        )
        if not verify_result.valid:
            raise TrustError(f"Worker cannot execute {action.name}: {verify_result.reason}")

    # 4. Execute with AUDIT
    results = []
    for action in task.actions:
        try:
            result = await worker.execute(action)
            await trust_ops.audit(
                agent_id=worker.id,
                action=action.name,
                resource=action.resource,
                result=ActionResult.SUCCESS,
                parent_anchor_id=delegation.id
            )
            results.append(result)
        except Exception as e:
            await trust_ops.audit(
                agent_id=worker.id,
                action=action.name,
                resource=action.resource,
                result=ActionResult.FAILURE,
                context={"error": str(e)},
                parent_anchor_id=delegation.id
            )
            raise

    return results
```

---

## Performance Considerations

### Caching Strategy

```python
class TrustCache:
    """Cache for trust verification performance."""

    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds

    async def get_chain(self, agent_id: str) -> Optional[TrustLineageChain]:
        """Get cached chain if valid."""
        entry = self.cache.get(agent_id)
        if entry and not self._is_expired(entry):
            return entry["chain"]
        return None

    async def invalidate(self, agent_id: str):
        """Invalidate cache entry (on delegation, etc.)."""
        self.cache.pop(agent_id, None)
```

### Lazy Verification

```python
class LazyVerifier:
    """Defer expensive verification until needed."""

    async def verify_on_demand(
        self,
        chain: TrustLineageChain,
        action: str
    ) -> VerificationResult:
        """Start with quick check, escalate if needed."""

        # Quick check first
        result = await self.verify(chain, action, VerificationLevel.QUICK)
        if not result.valid:
            return result

        # Standard check for sensitive actions
        if self._is_sensitive(action):
            result = await self.verify(chain, action, VerificationLevel.STANDARD)
            if not result.valid:
                return result

        # Full check only for critical actions
        if self._is_critical(action):
            result = await self.verify(chain, action, VerificationLevel.FULL)

        return result
```

---

## Error Handling

### Trust Exception Hierarchy

```python
class TrustError(Exception):
    """Base class for trust-related errors."""
    pass

class AuthorityNotFoundError(TrustError):
    """Authority does not exist."""
    pass

class AuthorityInactiveError(TrustError):
    """Authority is not active."""
    pass

class TrustChainNotFoundError(TrustError):
    """Agent has no trust chain."""
    pass

class InvalidTrustChainError(TrustError):
    """Trust chain failed verification."""
    pass

class CapabilityNotFoundError(TrustError):
    """Agent lacks required capability."""
    pass

class ConstraintViolationError(TrustError):
    """Action violates constraints."""
    pass

class DelegationError(TrustError):
    """Delegation operation failed."""
    pass
```

---

## Next Steps

1. **Document 04**: TrustedAgent Integration with BaseAgent
2. **Document 06**: Orchestration Integration
3. Implement trust operations in `kaizen.trust.operations`
4. Create integration tests for operation flows
