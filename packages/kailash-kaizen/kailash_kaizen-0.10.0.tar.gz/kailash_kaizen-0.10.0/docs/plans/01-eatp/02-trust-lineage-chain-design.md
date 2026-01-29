# EATP Implementation Plan: Trust Lineage Chain Design

## Document Control
- **Version**: 1.0
- **Date**: 2025-12-15
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## Overview

The Trust Lineage Chain is the core data structure of EATP. It provides cryptographically verifiable answers to:

> "Given Agent A attempting Action X on Resource R, why should I permit this?"

This document details the design of the Trust Lineage Chain and its five constituent elements.

---

## Trust Lineage Chain Structure

```
TrustLineageChain
├── GenesisRecord          # Who authorized this agent to exist?
├── CapabilityAttestation[]  # What can this agent do?
├── DelegationRecord[]     # Who delegated work to this agent?
├── ConstraintEnvelope     # What limits apply?
└── AuditAnchor[]          # What has this agent done?
```

### Visual Representation

```
┌─────────────────────────────────────────────────────────────────┐
│                      Trust Lineage Chain                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                               │
│  │GenesisRecord │ ── "I was created by Authority X"             │
│  └──────────────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────┐                                       │
│  │CapabilityAttestation │ ── "I can do A, B, C"                 │
│  │      (multiple)      │                                       │
│  └──────────────────────┘                                       │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────┐                                       │
│  │  DelegationRecord    │ ── "Agent Y delegated task to me"     │
│  │      (multiple)      │                                       │
│  └──────────────────────┘                                       │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────┐                                       │
│  │ ConstraintEnvelope   │ ── "I must follow these limits"       │
│  └──────────────────────┘                                       │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────┐                                       │
│  │    AuditAnchor       │ ── "Here's what I've done"            │
│  │      (multiple)      │                                       │
│  └──────────────────────┘                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Element 1: Genesis Record

### Purpose
Establishes the origin of trust. Every agent must have exactly one Genesis Record that proves its authorization to exist.

### Schema

```python
@dataclass
class GenesisRecord:
    """Cryptographic proof of agent authorization."""

    id: str                          # Unique identifier
    agent_id: str                    # The agent this record authorizes
    authority_id: str                # Who authorized (organization, system, human)
    authority_type: AuthorityType    # ORGANIZATION | SYSTEM | HUMAN
    created_at: datetime             # When authorization occurred
    expires_at: Optional[datetime]   # Optional expiration
    signature: str                   # Cryptographic signature
    signature_algorithm: str         # e.g., "Ed25519", "RSA-SHA256"
    metadata: Dict[str, Any]         # Additional context

class AuthorityType(Enum):
    ORGANIZATION = "organization"    # Enterprise-level authority
    SYSTEM = "system"                # System-level authority (e.g., ESA)
    HUMAN = "human"                  # Individual human authority
```

### Example

```json
{
  "id": "gen-2025-001",
  "agent_id": "data-analyst-agent-001",
  "authority_id": "org-acme-corp",
  "authority_type": "ORGANIZATION",
  "created_at": "2025-12-15T10:00:00Z",
  "expires_at": "2026-12-15T10:00:00Z",
  "signature": "eyJhbGciOiJFZDI1NTE5IiwidHlwIjoiSldUIn0...",
  "signature_algorithm": "Ed25519",
  "metadata": {
    "department": "Finance",
    "cost_center": "CC-1234",
    "approved_by": "user-john-doe"
  }
}
```

### Verification

```python
def verify_genesis(record: GenesisRecord, authority_registry: AuthorityRegistry) -> bool:
    """Verify a genesis record is valid and current."""
    # 1. Check authority exists and is active
    authority = authority_registry.get(record.authority_id)
    if not authority or not authority.is_active:
        return False

    # 2. Check expiration
    if record.expires_at and datetime.utcnow() > record.expires_at:
        return False

    # 3. Verify signature
    public_key = authority.get_public_key()
    payload = serialize_for_signing(record)
    return verify_signature(payload, record.signature, public_key)
```

---

## Element 2: Capability Attestation

### Purpose
Declares what an agent can do. Each capability comes with constraints and cryptographic proof.

### Schema

```python
@dataclass
class CapabilityAttestation:
    """Cryptographic proof of agent capability."""

    id: str                          # Unique identifier
    capability: str                  # What the agent can do
    capability_type: CapabilityType  # ACTION | ACCESS | DELEGATION
    constraints: List[str]           # Limits on this capability
    attester_id: str                 # Who attested this capability
    attested_at: datetime            # When attestation occurred
    expires_at: Optional[datetime]   # Optional expiration
    signature: str                   # Cryptographic signature
    scope: Optional[Dict[str, Any]]  # Resource scope limits

class CapabilityType(Enum):
    ACTION = "action"                # Can perform actions
    ACCESS = "access"                # Can access resources
    DELEGATION = "delegation"        # Can delegate to others
```

### Example

```json
{
  "id": "cap-2025-001",
  "capability": "analyze_financial_data",
  "capability_type": "ACCESS",
  "constraints": ["read_only", "no_pii_export", "audit_required"],
  "attester_id": "org-acme-corp",
  "attested_at": "2025-12-15T10:00:00Z",
  "expires_at": "2026-12-15T10:00:00Z",
  "signature": "eyJhbGciOiJFZDI1NTE5In0...",
  "scope": {
    "databases": ["finance_db"],
    "tables": ["transactions", "accounts"],
    "max_rows": 10000
  }
}
```

### Capability Hierarchy

```
Capability Inheritance:
┌─────────────────────────────────────────────┐
│          Organization Authority              │
│  ┌────────────────────────────────────────┐ │
│  │  analyze_financial_data (full access)  │ │
│  └────────────────────────────────────────┘ │
│                     │                        │
│                     ▼ DELEGATE               │
│  ┌────────────────────────────────────────┐ │
│  │  Supervisor Agent                       │ │
│  │  analyze_financial_data (read_only)    │ │
│  └────────────────────────────────────────┘ │
│                     │                        │
│                     ▼ DELEGATE               │
│  ┌────────────────────────────────────────┐ │
│  │  Worker Agent                          │ │
│  │  analyze_financial_data                │ │
│  │  (read_only, no_pii, single_table)    │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

## Element 3: Delegation Record

### Purpose
Tracks the chain of trust when one agent delegates work to another. Ensures constraints can only be tightened, never loosened.

### Schema

```python
@dataclass
class DelegationRecord:
    """Record of trust delegation between agents."""

    id: str                          # Unique identifier
    delegator_id: str                # Agent delegating trust
    delegatee_id: str                # Agent receiving trust
    task_id: str                     # Associated task
    capabilities_delegated: List[str]  # Which capabilities delegated
    constraint_subset: List[str]     # Additional constraints (tightening only)
    delegated_at: datetime           # When delegation occurred
    expires_at: Optional[datetime]   # Optional expiration
    signature: str                   # Delegator's signature
    parent_delegation_id: Optional[str]  # Link to parent delegation
```

### Example

```json
{
  "id": "del-2025-001",
  "delegator_id": "supervisor-agent-001",
  "delegatee_id": "worker-agent-001",
  "task_id": "task-analyze-q4-2025",
  "capabilities_delegated": ["analyze_financial_data"],
  "constraint_subset": ["q4_data_only", "summary_only"],
  "delegated_at": "2025-12-15T10:30:00Z",
  "expires_at": "2025-12-15T18:00:00Z",
  "signature": "eyJhbGciOiJFZDI1NTE5In0...",
  "parent_delegation_id": null
}
```

### Constraint Tightening Rule

```python
def validate_delegation(
    delegator: TrustLineageChain,
    delegatee: TrustLineageChain,
    record: DelegationRecord
) -> bool:
    """Ensure delegation only tightens constraints, never loosens."""
    # Get delegator's effective constraints for this capability
    delegator_constraints = delegator.get_effective_constraints(
        record.capabilities_delegated[0]
    )

    # New constraints must be a superset (more restrictive)
    new_constraints = set(delegator_constraints) | set(record.constraint_subset)

    # Delegatee cannot have fewer constraints than delegator
    if not new_constraints.issuperset(delegator_constraints):
        return False

    return True
```

---

## Element 4: Constraint Envelope

### Purpose
Defines the complete set of constraints that govern an agent's behavior. Aggregates constraints from genesis, capabilities, and delegations.

### Schema

```python
@dataclass
class ConstraintEnvelope:
    """Aggregated constraints governing agent behavior."""

    id: str                          # Unique identifier
    agent_id: str                    # Agent these constraints apply to
    active_constraints: List[Constraint]  # All active constraints
    computed_at: datetime            # When envelope was computed
    valid_until: datetime            # Recomputation deadline
    constraint_hash: str             # Hash for quick comparison

@dataclass
class Constraint:
    """Individual constraint definition."""

    id: str                          # Unique identifier
    constraint_type: ConstraintType  # Type of constraint
    value: Any                       # Constraint value
    source: str                      # Where this constraint came from
    priority: int                    # Higher = stricter enforcement

class ConstraintType(Enum):
    RESOURCE_LIMIT = "resource_limit"      # e.g., max_api_calls
    TIME_WINDOW = "time_window"            # e.g., business_hours_only
    DATA_SCOPE = "data_scope"              # e.g., department_data_only
    ACTION_RESTRICTION = "action_restriction"  # e.g., read_only
    AUDIT_REQUIREMENT = "audit_requirement"    # e.g., log_all_actions
```

### Example

```json
{
  "id": "env-2025-001",
  "agent_id": "worker-agent-001",
  "active_constraints": [
    {
      "id": "con-001",
      "constraint_type": "ACTION_RESTRICTION",
      "value": "read_only",
      "source": "cap-2025-001",
      "priority": 100
    },
    {
      "id": "con-002",
      "constraint_type": "DATA_SCOPE",
      "value": {"tables": ["transactions"]},
      "source": "del-2025-001",
      "priority": 90
    },
    {
      "id": "con-003",
      "constraint_type": "TIME_WINDOW",
      "value": {"start": "09:00", "end": "17:00", "timezone": "UTC"},
      "source": "gen-2025-001",
      "priority": 80
    }
  ],
  "computed_at": "2025-12-15T10:30:00Z",
  "valid_until": "2025-12-15T11:00:00Z",
  "constraint_hash": "sha256:abc123..."
}
```

### Constraint Evaluation

```python
def evaluate_constraints(
    envelope: ConstraintEnvelope,
    action: str,
    resource: str,
    context: Dict[str, Any]
) -> ConstraintResult:
    """Evaluate if action is permitted under current constraints."""

    violations = []

    for constraint in envelope.active_constraints:
        if not check_constraint(constraint, action, resource, context):
            violations.append(ConstraintViolation(
                constraint_id=constraint.id,
                constraint_type=constraint.constraint_type,
                reason=f"Action '{action}' violates {constraint.constraint_type}"
            ))

    return ConstraintResult(
        permitted=len(violations) == 0,
        violations=violations,
        evaluated_at=datetime.utcnow()
    )
```

---

## Element 5: Audit Anchor

### Purpose
Creates an immutable record of agent actions. Enables post-hoc verification and compliance reporting.

### Schema

```python
@dataclass
class AuditAnchor:
    """Immutable record of agent action."""

    id: str                          # Unique identifier
    agent_id: str                    # Agent that performed action
    action: str                      # What was done
    resource: Optional[str]          # Resource affected
    timestamp: datetime              # When action occurred
    trust_chain_hash: str            # Hash of trust chain at action time
    result: ActionResult             # Outcome of action
    parent_anchor_id: Optional[str]  # Link to triggering action
    signature: str                   # Agent's signature

class ActionResult(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
    PARTIAL = "partial"
```

### Example

```json
{
  "id": "aud-2025-001",
  "agent_id": "worker-agent-001",
  "action": "query_transactions",
  "resource": "finance_db.transactions",
  "timestamp": "2025-12-15T10:35:00Z",
  "trust_chain_hash": "sha256:def456...",
  "result": "SUCCESS",
  "parent_anchor_id": "aud-2025-000",
  "signature": "eyJhbGciOiJFZDI1NTE5In0..."
}
```

### Audit Chain Visualization

```
Audit Chain for Task task-analyze-q4-2025:

aud-001 (Supervisor)          aud-002 (Worker)           aud-003 (Worker)
├─ delegate_task       ──────► receive_delegation ──────► query_transactions
├─ 10:30:00                    10:30:01                    10:35:00
├─ chain_hash: abc...          chain_hash: def...         chain_hash: ghi...
└─ SUCCESS                     SUCCESS                     SUCCESS
                                                                │
                                                                ▼
                               aud-004 (Worker)           aud-005 (Supervisor)
                               └─ analyze_data     ──────► receive_results
                                  10:35:30                 10:36:00
                                  chain_hash: jkl...       chain_hash: mno...
                                  SUCCESS                  SUCCESS
```

---

## Trust Lineage Chain Implementation

### Complete Data Structure

```python
@dataclass
class TrustLineageChain:
    """Complete trust lineage for an agent."""

    genesis: GenesisRecord
    capabilities: List[CapabilityAttestation]
    delegations: List[DelegationRecord]
    constraint_envelope: ConstraintEnvelope
    audit_anchors: List[AuditAnchor]

    def hash(self) -> str:
        """Compute hash of current trust state."""
        payload = {
            "genesis_id": self.genesis.id,
            "capability_ids": [c.id for c in self.capabilities],
            "delegation_ids": [d.id for d in self.delegations],
            "constraint_hash": self.constraint_envelope.constraint_hash
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def get_effective_constraints(self, capability: str) -> List[str]:
        """Get all constraints for a specific capability."""
        constraints = []

        # From capability attestations
        for cap in self.capabilities:
            if cap.capability == capability:
                constraints.extend(cap.constraints)

        # From delegations
        for del_ in self.delegations:
            if capability in del_.capabilities_delegated:
                constraints.extend(del_.constraint_subset)

        return list(set(constraints))

    def verify(self, authority_registry: AuthorityRegistry) -> VerificationResult:
        """Verify entire trust chain is valid."""
        # Verify genesis
        if not verify_genesis(self.genesis, authority_registry):
            return VerificationResult(valid=False, reason="Invalid genesis")

        # Verify capabilities
        for cap in self.capabilities:
            if not verify_capability(cap, authority_registry):
                return VerificationResult(valid=False, reason=f"Invalid capability: {cap.id}")

        # Verify delegation chain
        for del_ in self.delegations:
            if not verify_delegation(del_, self):
                return VerificationResult(valid=False, reason=f"Invalid delegation: {del_.id}")

        return VerificationResult(valid=True)
```

---

## Cryptographic Considerations

### Signature Algorithm Selection

| Algorithm | Use Case | Performance | Security |
|-----------|----------|-------------|----------|
| Ed25519 | Default, fast verification | Excellent | High |
| RSA-2048 | Legacy compatibility | Good | High |
| ECDSA P-256 | Cloud HSM compatibility | Good | High |

### Key Management

```python
class TrustKeyManager:
    """Manages cryptographic keys for trust operations."""

    async def sign(self, payload: bytes, key_id: str) -> str:
        """Sign payload with specified key."""
        pass

    async def verify(self, payload: bytes, signature: str, public_key: str) -> bool:
        """Verify signature against public key."""
        pass

    async def rotate_key(self, key_id: str) -> str:
        """Rotate key, returning new public key."""
        pass
```

---

## Storage Requirements

### Database Schema

```sql
-- Genesis Records
CREATE TABLE genesis_records (
    id VARCHAR(64) PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    authority_id VARCHAR(64) NOT NULL,
    authority_type VARCHAR(32) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    signature TEXT NOT NULL,
    signature_algorithm VARCHAR(32) NOT NULL,
    metadata JSONB,
    UNIQUE(agent_id)
);

-- Capability Attestations
CREATE TABLE capability_attestations (
    id VARCHAR(64) PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL REFERENCES genesis_records(agent_id),
    capability VARCHAR(256) NOT NULL,
    capability_type VARCHAR(32) NOT NULL,
    constraints TEXT[],
    attester_id VARCHAR(64) NOT NULL,
    attested_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    signature TEXT NOT NULL,
    scope JSONB
);

-- Delegation Records
CREATE TABLE delegation_records (
    id VARCHAR(64) PRIMARY KEY,
    delegator_id VARCHAR(64) NOT NULL,
    delegatee_id VARCHAR(64) NOT NULL,
    task_id VARCHAR(64) NOT NULL,
    capabilities_delegated TEXT[],
    constraint_subset TEXT[],
    delegated_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    signature TEXT NOT NULL,
    parent_delegation_id VARCHAR(64) REFERENCES delegation_records(id)
);

-- Audit Anchors
CREATE TABLE audit_anchors (
    id VARCHAR(64) PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    action VARCHAR(256) NOT NULL,
    resource VARCHAR(256),
    timestamp TIMESTAMP NOT NULL,
    trust_chain_hash VARCHAR(64) NOT NULL,
    result VARCHAR(32) NOT NULL,
    parent_anchor_id VARCHAR(64) REFERENCES audit_anchors(id),
    signature TEXT NOT NULL
);

-- Indexes for common queries
CREATE INDEX idx_capabilities_agent ON capability_attestations(agent_id);
CREATE INDEX idx_delegations_delegatee ON delegation_records(delegatee_id);
CREATE INDEX idx_audit_agent_time ON audit_anchors(agent_id, timestamp);
```

---

## Next Steps

1. **Document 03**: Trust Operations (ESTABLISH, DELEGATE, VERIFY, AUDIT)
2. **Document 04**: TrustedAgent Integration with BaseAgent
3. Implement core data structures in `kaizen.trust.chain`
4. Create unit tests for all trust chain operations
