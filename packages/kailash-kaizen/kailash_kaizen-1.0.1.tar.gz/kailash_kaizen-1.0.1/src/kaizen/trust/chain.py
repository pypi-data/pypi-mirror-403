"""
EATP Trust Lineage Chain Data Structures.

Defines the core data structures for the Enterprise Agent Trust Protocol:
- GenesisRecord: Who authorized this agent to exist?
- CapabilityAttestation: What can this agent do?
- DelegationRecord: Who delegated work to this agent?
- ConstraintEnvelope: What limits apply?
- AuditAnchor: What has this agent done?
- TrustLineageChain: Complete trust chain for an agent
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from kaizen.trust.crypto import hash_trust_chain_state, serialize_for_signing

if TYPE_CHECKING:
    from kaizen.trust.execution_context import HumanOrigin


class AuthorityType(Enum):
    """Type of authority that can establish trust."""

    ORGANIZATION = "organization"  # Enterprise-level authority
    SYSTEM = "system"  # System-level authority (e.g., ESA)
    HUMAN = "human"  # Individual human authority


class CapabilityType(Enum):
    """Type of capability an agent can have."""

    ACCESS = "access"  # Can access resources
    ACTION = "action"  # Can perform actions
    DELEGATION = "delegation"  # Can delegate to others


class ActionResult(Enum):
    """Result of an agent action."""

    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
    PARTIAL = "partial"


class ConstraintType(Enum):
    """Type of constraint on agent behavior."""

    RESOURCE_LIMIT = "resource_limit"  # e.g., max_api_calls
    TIME_WINDOW = "time_window"  # e.g., business_hours_only
    DATA_SCOPE = "data_scope"  # e.g., department_data_only
    ACTION_RESTRICTION = "action_restriction"  # e.g., read_only
    AUDIT_REQUIREMENT = "audit_requirement"  # e.g., log_all_actions


class VerificationLevel(Enum):
    """Level of trust verification thoroughness."""

    QUICK = "quick"  # Hash + expiration only (~1ms)
    STANDARD = "standard"  # + Capability match, constraints (~5ms)
    FULL = "full"  # + Signature verification (~50ms)


@dataclass
class GenesisRecord:
    """
    Cryptographic proof of agent authorization.

    The genesis record establishes the origin of trust for an agent.
    Every agent must have exactly one genesis record that proves
    its authorization to exist.

    Attributes:
        id: Unique identifier for this record
        agent_id: The agent this record authorizes
        authority_id: Who authorized (organization, system, human)
        authority_type: Type of authority
        created_at: When authorization occurred
        expires_at: Optional expiration datetime
        signature: Cryptographic signature from authority
        signature_algorithm: Algorithm used (e.g., "Ed25519")
        metadata: Additional context (department, owner, etc.)
    """

    id: str
    agent_id: str
    authority_id: str
    authority_type: AuthorityType
    created_at: datetime
    signature: str
    signature_algorithm: str = "Ed25519"
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if this genesis record has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def to_signing_payload(self) -> dict:
        """Get payload for signature verification."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "authority_id": self.authority_id,
            "authority_type": self.authority_type.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }


@dataclass
class CapabilityAttestation:
    """
    Cryptographic proof of agent capability.

    Declares what an agent can do. Each capability comes with
    constraints and cryptographic proof from an attester.

    Attributes:
        id: Unique identifier
        capability: What the agent can do (e.g., "analyze_financial_data")
        capability_type: ACCESS, ACTION, or DELEGATION
        constraints: Limits on this capability (e.g., ["read_only", "no_pii"])
        attester_id: Who attested this capability
        attested_at: When attestation occurred
        expires_at: Optional expiration
        signature: Cryptographic signature from attester
        scope: Resource scope limits (e.g., {"tables": ["transactions"]})
    """

    id: str
    capability: str
    capability_type: CapabilityType
    constraints: List[str]
    attester_id: str
    attested_at: datetime
    signature: str
    expires_at: Optional[datetime] = None
    scope: Optional[Dict[str, Any]] = None

    def is_expired(self) -> bool:
        """Check if this capability attestation has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def to_signing_payload(self) -> dict:
        """Get payload for signature verification."""
        return {
            "id": self.id,
            "capability": self.capability,
            "capability_type": self.capability_type.value,
            "constraints": sorted(self.constraints),
            "attester_id": self.attester_id,
            "attested_at": self.attested_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scope": self.scope,
        }


@dataclass
class DelegationRecord:
    """
    Record of trust delegation between agents.

    Tracks the chain of trust when one agent delegates work to another.
    Ensures constraints can only be tightened, never loosened.

    EATP Enhancement: Now includes human_origin to trace back to
    the human who ultimately authorized this delegation chain.

    Attributes:
        id: Unique identifier
        delegator_id: Agent delegating trust
        delegatee_id: Agent receiving trust
        task_id: Associated task identifier
        capabilities_delegated: Which capabilities are delegated
        constraint_subset: Additional constraints (tightening only)
        delegated_at: When delegation occurred
        expires_at: Optional expiration
        signature: Delegator's signature
        parent_delegation_id: Link to parent delegation (for chains)
        human_origin: [EATP] The human who ultimately authorized this chain
        delegation_chain: [EATP] Full path from human to current agent
        delegation_depth: [EATP] Distance from human (0 = direct)
    """

    id: str
    delegator_id: str
    delegatee_id: str
    task_id: str
    capabilities_delegated: List[str]
    constraint_subset: List[str]
    delegated_at: datetime
    signature: str
    expires_at: Optional[datetime] = None
    parent_delegation_id: Optional[str] = None

    # EATP Enhancement Fields - Human Origin Tracing
    human_origin: Optional["HumanOrigin"] = None  # Who ultimately authorized
    delegation_chain: List[str] = field(default_factory=list)  # Full path from human
    delegation_depth: int = 0  # Distance from human (0 = direct)

    def is_expired(self) -> bool:
        """Check if this delegation has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def to_signing_payload(self) -> dict:
        """Get payload for signature verification."""
        return {
            "id": self.id,
            "delegator_id": self.delegator_id,
            "delegatee_id": self.delegatee_id,
            "task_id": self.task_id,
            "capabilities_delegated": sorted(self.capabilities_delegated),
            "constraint_subset": sorted(self.constraint_subset),
            "delegated_at": self.delegated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "parent_delegation_id": self.parent_delegation_id,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary including EATP fields.

        Returns:
            Dictionary representation with all fields
        """
        d = {
            "id": self.id,
            "delegator_id": self.delegator_id,
            "delegatee_id": self.delegatee_id,
            "task_id": self.task_id,
            "capabilities_delegated": self.capabilities_delegated,
            "constraint_subset": self.constraint_subset,
            "delegated_at": self.delegated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "signature": self.signature,
            "parent_delegation_id": self.parent_delegation_id,
            # EATP fields
            "delegation_chain": self.delegation_chain,
            "delegation_depth": self.delegation_depth,
        }
        if self.human_origin:
            d["human_origin"] = self.human_origin.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DelegationRecord":
        """
        Deserialize from dictionary including EATP fields.

        Backward compatible - handles records without EATP fields.

        Args:
            data: Dictionary with DelegationRecord fields

        Returns:
            DelegationRecord instance
        """
        # Import here to avoid circular imports at module level
        from kaizen.trust.execution_context import HumanOrigin

        human_origin = None
        if data.get("human_origin"):
            human_origin = HumanOrigin.from_dict(data["human_origin"])

        return cls(
            id=data["id"],
            delegator_id=data["delegator_id"],
            delegatee_id=data["delegatee_id"],
            task_id=data["task_id"],
            capabilities_delegated=data["capabilities_delegated"],
            constraint_subset=data.get("constraint_subset", []),
            delegated_at=datetime.fromisoformat(data["delegated_at"]),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
            signature=data.get("signature", ""),
            parent_delegation_id=data.get("parent_delegation_id"),
            # EATP fields with backward-compatible defaults
            human_origin=human_origin,
            delegation_chain=data.get("delegation_chain", []),
            delegation_depth=data.get("delegation_depth", 0),
        )


@dataclass
class Constraint:
    """
    Individual constraint definition.

    Represents a single constraint on agent behavior, with its type,
    value, source, and enforcement priority.

    Attributes:
        id: Unique identifier
        constraint_type: Type of constraint
        value: Constraint value (type depends on constraint_type)
        source: Where this constraint came from (e.g., "cap-001")
        priority: Higher = stricter enforcement
    """

    id: str
    constraint_type: ConstraintType
    value: Any
    source: str
    priority: int = 0


@dataclass
class ConstraintEnvelope:
    """
    Aggregated constraints governing agent behavior.

    Combines constraints from genesis, capabilities, and delegations
    into a single envelope for efficient constraint evaluation.

    Attributes:
        id: Unique identifier
        agent_id: Agent these constraints apply to
        active_constraints: All active constraints
        computed_at: When envelope was computed
        valid_until: Recomputation deadline
        constraint_hash: Hash for quick comparison
    """

    id: str
    agent_id: str
    active_constraints: List[Constraint] = field(default_factory=list)
    computed_at: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    constraint_hash: str = ""

    def __post_init__(self):
        """Compute hash if not provided."""
        if not self.constraint_hash and self.active_constraints:
            self.constraint_hash = self._compute_hash()
        if not self.computed_at:
            self.computed_at = datetime.now(timezone.utc)

    def _compute_hash(self) -> str:
        """Compute hash of constraints for quick comparison."""
        from kaizen.trust.crypto import hash_chain

        constraint_data = [
            {"id": c.id, "type": c.constraint_type.value, "value": str(c.value)}
            for c in sorted(self.active_constraints, key=lambda x: x.id)
        ]
        return hash_chain({"constraints": constraint_data})

    def get_all_constraints(self) -> List[str]:
        """Get list of all constraint values as strings."""
        return [str(c.value) for c in self.active_constraints]

    def get_constraints_by_type(
        self, constraint_type: ConstraintType
    ) -> List[Constraint]:
        """Get constraints of a specific type."""
        return [
            c for c in self.active_constraints if c.constraint_type == constraint_type
        ]

    def is_valid(self) -> bool:
        """Check if this envelope is still valid."""
        if self.valid_until is None:
            return True
        return datetime.now(timezone.utc) <= self.valid_until


@dataclass
class AuditAnchor:
    """
    Immutable record of agent action.

    Creates an audit trail for agent actions, enabling post-hoc
    verification and compliance reporting.

    EATP Enhancement: Now includes human_origin for complete traceability.
    Every audit record can answer "which human authorized this action?"

    Attributes:
        id: Unique identifier
        agent_id: Agent that performed action
        action: What was done
        resource: Resource affected (optional)
        timestamp: When action occurred
        trust_chain_hash: Hash of trust chain at action time
        result: Outcome of action
        parent_anchor_id: Link to triggering action (for chains)
        signature: Agent's signature
        context: Additional context
        human_origin: [EATP] The human who ultimately authorized this action
    """

    id: str
    agent_id: str
    action: str
    timestamp: datetime
    trust_chain_hash: str
    result: ActionResult
    signature: str
    resource: Optional[str] = None
    parent_anchor_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    # EATP Enhancement Field - Human Origin
    human_origin: Optional["HumanOrigin"] = None  # Who ultimately authorized

    def to_signing_payload(self) -> dict:
        """Get payload for signature verification."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "action": self.action,
            "resource": self.resource,
            "timestamp": self.timestamp.isoformat(),
            "trust_chain_hash": self.trust_chain_hash,
            "result": self.result.value,
            "parent_anchor_id": self.parent_anchor_id,
            "context": self.context,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary including EATP fields.

        Returns:
            Dictionary representation with all fields
        """
        d = {
            "id": self.id,
            "agent_id": self.agent_id,
            "action": self.action,
            "resource": self.resource,
            "timestamp": self.timestamp.isoformat(),
            "trust_chain_hash": self.trust_chain_hash,
            "result": self.result.value,
            "signature": self.signature,
            "parent_anchor_id": self.parent_anchor_id,
            "context": self.context,
        }
        if self.human_origin:
            d["human_origin"] = self.human_origin.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditAnchor":
        """
        Deserialize from dictionary including EATP fields.

        Backward compatible - handles records without EATP fields.

        Args:
            data: Dictionary with AuditAnchor fields

        Returns:
            AuditAnchor instance
        """
        # Import here to avoid circular imports at module level
        from kaizen.trust.execution_context import HumanOrigin

        human_origin = None
        if data.get("human_origin"):
            human_origin = HumanOrigin.from_dict(data["human_origin"])

        return cls(
            id=data["id"],
            agent_id=data["agent_id"],
            action=data["action"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            trust_chain_hash=data["trust_chain_hash"],
            result=ActionResult(data["result"]),
            signature=data.get("signature", ""),
            resource=data.get("resource"),
            parent_anchor_id=data.get("parent_anchor_id"),
            context=data.get("context", {}),
            # EATP field with backward-compatible default
            human_origin=human_origin,
        )


@dataclass
class VerificationResult:
    """
    Result of trust verification.

    Contains the outcome of a VERIFY operation with details
    about what capability was used and any violations.
    """

    valid: bool
    level: VerificationLevel = VerificationLevel.STANDARD
    reason: Optional[str] = None
    capability_used: Optional[str] = None
    effective_constraints: List[str] = field(default_factory=list)
    violations: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class TrustLineageChain:
    """
    Complete trust lineage for an agent.

    The Trust Lineage Chain is the core data structure of EATP,
    containing all trust information for an agent in a cryptographically
    verifiable sequence.

    Attributes:
        genesis: The genesis record (authorization proof)
        capabilities: List of capability attestations
        delegations: List of delegation records
        constraint_envelope: Aggregated constraints
        audit_anchors: List of audit records
    """

    genesis: GenesisRecord
    capabilities: List[CapabilityAttestation] = field(default_factory=list)
    delegations: List[DelegationRecord] = field(default_factory=list)
    constraint_envelope: Optional[ConstraintEnvelope] = None
    audit_anchors: List[AuditAnchor] = field(default_factory=list)

    def __post_init__(self):
        """Initialize constraint envelope if not provided."""
        if self.constraint_envelope is None:
            self.constraint_envelope = ConstraintEnvelope(
                id=f"env-{self.genesis.agent_id}", agent_id=self.genesis.agent_id
            )

    def hash(self) -> str:
        """
        Compute hash of current trust state.

        This hash changes when any component of the trust chain changes,
        enabling quick verification of chain integrity.
        """
        return hash_trust_chain_state(
            genesis_id=self.genesis.id,
            capability_ids=[c.id for c in self.capabilities],
            delegation_ids=[d.id for d in self.delegations],
            constraint_hash=(
                self.constraint_envelope.constraint_hash
                if self.constraint_envelope
                else ""
            ),
        )

    def is_expired(self) -> bool:
        """Check if the trust chain has expired."""
        # Genesis expired
        if self.genesis.is_expired():
            return True

        # All capabilities expired
        if self.capabilities and all(c.is_expired() for c in self.capabilities):
            return True

        return False

    def has_capability(self, capability: str) -> bool:
        """
        Check if agent has a specific capability.

        Args:
            capability: The capability to check for

        Returns:
            True if agent has the capability and it's not expired
        """
        for cap in self.capabilities:
            if cap.capability == capability and not cap.is_expired():
                return True
        return False

    def get_capability(self, capability: str) -> Optional[CapabilityAttestation]:
        """
        Get a specific capability attestation.

        Args:
            capability: The capability to get

        Returns:
            The capability attestation if found and not expired, None otherwise
        """
        for cap in self.capabilities:
            if cap.capability == capability and not cap.is_expired():
                return cap
        return None

    def get_effective_constraints(self, capability: str) -> List[str]:
        """
        Get all constraints for a specific capability.

        Aggregates constraints from:
        1. Capability attestations
        2. Delegations that include this capability

        Args:
            capability: The capability to get constraints for

        Returns:
            List of constraint strings
        """
        constraints = set()

        # From capability attestations
        for cap in self.capabilities:
            if cap.capability == capability and not cap.is_expired():
                constraints.update(cap.constraints)

        # From delegations
        for delegation in self.delegations:
            if (
                capability in delegation.capabilities_delegated
                and not delegation.is_expired()
            ):
                constraints.update(delegation.constraint_subset)

        return list(constraints)

    def verify_basic(self) -> VerificationResult:
        """
        Perform basic (QUICK) verification.

        Checks:
        1. Genesis exists
        2. Not expired

        Returns:
            VerificationResult with valid=True if basic checks pass
        """
        # Check genesis exists
        if not self.genesis:
            return VerificationResult(
                valid=False, level=VerificationLevel.QUICK, reason="No genesis record"
            )

        # Check not expired
        if self.is_expired():
            return VerificationResult(
                valid=False, level=VerificationLevel.QUICK, reason="Trust chain expired"
            )

        return VerificationResult(valid=True, level=VerificationLevel.QUICK)

    def get_active_delegations(self) -> List[DelegationRecord]:
        """Get all non-expired delegations."""
        return [d for d in self.delegations if not d.is_expired()]

    def get_delegation_chain(self) -> List[DelegationRecord]:
        """
        Get delegation chain in order from root to leaf.

        Follows parent_delegation_id links to build ordered chain.
        """
        if not self.delegations:
            return []

        # Build delegation map
        delegation_map = {d.id: d for d in self.delegations}

        # Find leaf delegations (no other delegation references them as parent)
        parent_ids = {
            d.parent_delegation_id for d in self.delegations if d.parent_delegation_id
        }
        leaves = [d for d in self.delegations if d.id not in parent_ids]

        if not leaves:
            return list(self.delegations)

        # Build chain from most recent leaf
        chain = []
        current = leaves[0]
        while current:
            chain.append(current)
            if current.parent_delegation_id:
                current = delegation_map.get(current.parent_delegation_id)
            else:
                current = None

        return list(reversed(chain))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "genesis": {
                "id": self.genesis.id,
                "agent_id": self.genesis.agent_id,
                "authority_id": self.genesis.authority_id,
                "authority_type": self.genesis.authority_type.value,
                "created_at": self.genesis.created_at.isoformat(),
                "expires_at": (
                    self.genesis.expires_at.isoformat()
                    if self.genesis.expires_at
                    else None
                ),
                "signature_algorithm": self.genesis.signature_algorithm,
                "metadata": self.genesis.metadata,
            },
            "capabilities": [
                {
                    "id": cap.id,
                    "capability": cap.capability,
                    "capability_type": cap.capability_type.value,
                    "constraints": cap.constraints,
                    "attester_id": cap.attester_id,
                    "attested_at": cap.attested_at.isoformat(),
                    "expires_at": (
                        cap.expires_at.isoformat() if cap.expires_at else None
                    ),
                    "scope": cap.scope,
                }
                for cap in self.capabilities
            ],
            "delegations": [
                {
                    "id": d.id,
                    "delegator_id": d.delegator_id,
                    "delegatee_id": d.delegatee_id,
                    "task_id": d.task_id,
                    "capabilities_delegated": d.capabilities_delegated,
                    "constraint_subset": d.constraint_subset,
                    "delegated_at": d.delegated_at.isoformat(),
                    "expires_at": d.expires_at.isoformat() if d.expires_at else None,
                    "parent_delegation_id": d.parent_delegation_id,
                }
                for d in self.delegations
            ],
            "constraint_envelope": (
                {
                    "id": self.constraint_envelope.id,
                    "agent_id": self.constraint_envelope.agent_id,
                    "constraint_hash": self.constraint_envelope.constraint_hash,
                    "active_constraints": [
                        {
                            "id": c.id,
                            "constraint_type": c.constraint_type.value,
                            "value": c.value,
                            "source": c.source,
                            "priority": c.priority,
                        }
                        for c in self.constraint_envelope.active_constraints
                    ],
                }
                if self.constraint_envelope
                else None
            ),
            "chain_hash": self.hash(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrustLineageChain":
        """Create TrustLineageChain from dictionary."""
        genesis_data = data["genesis"]
        genesis = GenesisRecord(
            id=genesis_data["id"],
            agent_id=genesis_data["agent_id"],
            authority_id=genesis_data["authority_id"],
            authority_type=AuthorityType(genesis_data["authority_type"]),
            created_at=datetime.fromisoformat(genesis_data["created_at"]),
            expires_at=(
                datetime.fromisoformat(genesis_data["expires_at"])
                if genesis_data.get("expires_at")
                else None
            ),
            signature=genesis_data.get("signature", ""),
            signature_algorithm=genesis_data.get("signature_algorithm", "Ed25519"),
            metadata=genesis_data.get("metadata", {}),
        )

        capabilities = [
            CapabilityAttestation(
                id=cap["id"],
                capability=cap["capability"],
                capability_type=CapabilityType(cap["capability_type"]),
                constraints=cap["constraints"],
                attester_id=cap["attester_id"],
                attested_at=datetime.fromisoformat(cap["attested_at"]),
                expires_at=(
                    datetime.fromisoformat(cap["expires_at"])
                    if cap.get("expires_at")
                    else None
                ),
                signature=cap.get("signature", ""),
                scope=cap.get("scope"),
            )
            for cap in data.get("capabilities", [])
        ]

        delegations = [
            DelegationRecord(
                id=d["id"],
                delegator_id=d["delegator_id"],
                delegatee_id=d["delegatee_id"],
                task_id=d["task_id"],
                capabilities_delegated=d["capabilities_delegated"],
                constraint_subset=d["constraint_subset"],
                delegated_at=datetime.fromisoformat(d["delegated_at"]),
                expires_at=(
                    datetime.fromisoformat(d["expires_at"])
                    if d.get("expires_at")
                    else None
                ),
                signature=d.get("signature", ""),
                parent_delegation_id=d.get("parent_delegation_id"),
            )
            for d in data.get("delegations", [])
        ]

        constraint_envelope = None
        if data.get("constraint_envelope"):
            env_data = data["constraint_envelope"]
            constraint_envelope = ConstraintEnvelope(
                id=env_data["id"],
                agent_id=env_data["agent_id"],
                constraint_hash=env_data.get("constraint_hash", ""),
                active_constraints=[
                    Constraint(
                        id=c["id"],
                        constraint_type=ConstraintType(c["constraint_type"]),
                        value=c["value"],
                        source=c["source"],
                        priority=c.get("priority", 0),
                    )
                    for c in env_data.get("active_constraints", [])
                ],
            )

        return cls(
            genesis=genesis,
            capabilities=capabilities,
            delegations=delegations,
            constraint_envelope=constraint_envelope,
        )
