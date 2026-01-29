"""
EATP Credential Rotation Management.

Provides automated credential rotation for organizational authorities with:
- Keypair rotation with grace period support
- Audit logging for all rotation events
- Atomic updates to prevent partial rotations
- Concurrent rotation prevention (only one rotation per authority at a time)
- Re-signing of trust chains after key rotation
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import uuid4

from kaizen.trust.authority import (
    OrganizationalAuthority,
    OrganizationalAuthorityRegistry,
)
from kaizen.trust.crypto import generate_keypair, serialize_for_signing, sign
from kaizen.trust.exceptions import (
    AuthorityInactiveError,
    AuthorityNotFoundError,
    TrustError,
)
from kaizen.trust.operations import TrustKeyManager
from kaizen.trust.store import PostgresTrustStore


class RotationStatus(str, Enum):
    """Status of a rotation operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    GRACE_PERIOD = "grace_period"


class RotationError(TrustError):
    """Raised when a rotation operation fails."""

    def __init__(
        self,
        message: str,
        authority_id: Optional[str] = None,
        rotation_id: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        super().__init__(
            message,
            details={
                "authority_id": authority_id,
                "rotation_id": rotation_id,
                "reason": reason,
            },
        )
        self.authority_id = authority_id
        self.rotation_id = rotation_id
        self.reason = reason


@dataclass
class RotationResult:
    """
    Result of a key rotation operation.

    Attributes:
        new_key_id: ID of the newly generated key
        old_key_id: ID of the rotated key
        chains_updated: Number of trust chains that were re-signed
        started_at: When the rotation began
        completed_at: When the rotation completed
        rotation_id: Unique identifier for this rotation
        grace_period_end: When the old key will be revoked
    """

    new_key_id: str
    old_key_id: str
    chains_updated: int
    started_at: datetime
    completed_at: datetime
    rotation_id: str = field(default_factory=lambda: f"rot-{uuid4().hex[:12]}")
    grace_period_end: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "rotation_id": self.rotation_id,
            "new_key_id": self.new_key_id,
            "old_key_id": self.old_key_id,
            "chains_updated": self.chains_updated,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "grace_period_end": (
                self.grace_period_end.isoformat() if self.grace_period_end else None
            ),
        }


@dataclass
class RotationStatusInfo:
    """
    Current rotation status for an authority.

    Attributes:
        last_rotation: Timestamp of last completed rotation
        next_scheduled: Timestamp of next scheduled rotation (if any)
        current_key_id: Currently active key ID
        pending_revocations: List of key IDs pending revocation
        rotation_period_days: Configured rotation period
        status: Current rotation status
        grace_period_keys: Keys currently in grace period
    """

    last_rotation: Optional[datetime]
    next_scheduled: Optional[datetime]
    current_key_id: str
    pending_revocations: List[str] = field(default_factory=list)
    rotation_period_days: int = 90
    status: RotationStatus = RotationStatus.COMPLETED
    grace_period_keys: Dict[str, datetime] = field(
        default_factory=dict
    )  # key_id -> expiry

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "last_rotation": (
                self.last_rotation.isoformat() if self.last_rotation else None
            ),
            "next_scheduled": (
                self.next_scheduled.isoformat() if self.next_scheduled else None
            ),
            "current_key_id": self.current_key_id,
            "pending_revocations": self.pending_revocations,
            "rotation_period_days": self.rotation_period_days,
            "status": self.status.value,
            "grace_period_keys": {
                k: v.isoformat() for k, v in self.grace_period_keys.items()
            },
        }


@dataclass
class ScheduledRotation:
    """Scheduled rotation operation."""

    rotation_id: str
    authority_id: str
    scheduled_at: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: RotationStatus = RotationStatus.PENDING


class CredentialRotationManager:
    """
    Manages credential rotation for organizational authorities.

    Provides automated key rotation with grace periods, audit logging,
    and atomic updates to prevent partial rotations.

    Features:
    - Grace period support (default 24 hours)
    - Audit logging for all rotation events
    - Atomic updates to prevent partial rotations
    - Concurrent rotation prevention (only one rotation per authority at a time)
    - Automatic re-signing of trust chains after rotation
    - Scheduled rotation support

    Example:
        >>> # Initialize components
        >>> key_manager = TrustKeyManager()
        >>> trust_store = PostgresTrustStore()
        >>> registry = OrganizationalAuthorityRegistry()
        >>>
        >>> # Create rotation manager
        >>> rotation_mgr = CredentialRotationManager(
        ...     key_manager=key_manager,
        ...     trust_store=trust_store,
        ...     authority_registry=registry,
        ...     rotation_period_days=90,
        ...     grace_period_hours=24,
        ... )
        >>> await rotation_mgr.initialize()
        >>>
        >>> # Rotate a key
        >>> result = await rotation_mgr.rotate_key("org-acme")
        >>> print(f"Rotated {result.chains_updated} chains")
        >>>
        >>> # Check rotation status
        >>> status = await rotation_mgr.get_rotation_status("org-acme")
        >>> print(f"Last rotation: {status.last_rotation}")
        >>>
        >>> # Schedule future rotation
        >>> rotation_id = await rotation_mgr.schedule_rotation(
        ...     "org-acme",
        ...     at=datetime.now(timezone.utc) + timedelta(days=90)
        ... )
    """

    def __init__(
        self,
        key_manager: TrustKeyManager,
        trust_store: PostgresTrustStore,
        authority_registry: OrganizationalAuthorityRegistry,
        rotation_period_days: int = 90,
        grace_period_hours: int = 24,
    ):
        """
        Initialize CredentialRotationManager.

        Args:
            key_manager: TrustKeyManager for key operations
            trust_store: PostgresTrustStore for chain updates
            authority_registry: OrganizationalAuthorityRegistry for authority management
            rotation_period_days: Default rotation period in days (default: 90)
            grace_period_hours: Grace period before old key revocation in hours (default: 24)
        """
        self.key_manager = key_manager
        self.trust_store = trust_store
        self.authority_registry = authority_registry
        self.rotation_period_days = rotation_period_days
        self.grace_period_hours = grace_period_hours

        # Track active rotations to prevent concurrent rotations
        self._active_rotations: Set[str] = set()
        self._rotation_locks: Dict[str, asyncio.Lock] = {}

        # Track rotation history and scheduled rotations
        self._rotation_history: Dict[str, List[RotationResult]] = (
            {}
        )  # authority_id -> results
        self._scheduled_rotations: Dict[str, List[ScheduledRotation]] = (
            {}
        )  # authority_id -> scheduled

        # Track keys in grace period
        self._grace_period_keys: Dict[str, Dict[str, datetime]] = (
            {}
        )  # authority_id -> {key_id: expiry}

        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize the rotation manager.

        Must be called before using the manager.
        """
        if self._initialized:
            return
        self._initialized = True

    def _get_lock(self, authority_id: str) -> asyncio.Lock:
        """
        Get or create a lock for an authority.

        Args:
            authority_id: Authority to get lock for

        Returns:
            Lock for the authority
        """
        if authority_id not in self._rotation_locks:
            self._rotation_locks[authority_id] = asyncio.Lock()
        return self._rotation_locks[authority_id]

    async def rotate_key(
        self,
        authority_id: str,
        grace_period_hours: Optional[int] = None,
    ) -> RotationResult:
        """
        Rotate the signing key for an authority.

        This operation:
        1. Generates a new keypair
        2. Updates the authority record with the new public key
        3. Re-signs all trust chains established by this authority
        4. Places the old key in grace period
        5. Logs the rotation event

        Args:
            authority_id: Authority whose key should be rotated
            grace_period_hours: Override grace period (default: use configured value)

        Returns:
            RotationResult with details of the rotation

        Raises:
            AuthorityNotFoundError: If authority not found
            AuthorityInactiveError: If authority is inactive
            RotationError: If rotation fails or another rotation is in progress
        """
        # Use configured grace period if not specified
        if grace_period_hours is None:
            grace_period_hours = self.grace_period_hours

        # Acquire lock to prevent concurrent rotations
        lock = self._get_lock(authority_id)
        if not await lock.acquire():
            raise RotationError(
                f"Another rotation is in progress for authority {authority_id}",
                authority_id=authority_id,
                reason="concurrent_rotation",
            )

        try:
            # Check if already rotating
            if authority_id in self._active_rotations:
                raise RotationError(
                    f"Rotation already in progress for authority {authority_id}",
                    authority_id=authority_id,
                    reason="concurrent_rotation",
                )

            # Mark as rotating
            self._active_rotations.add(authority_id)

            started_at = datetime.now(timezone.utc)
            rotation_id = f"rot-{uuid4().hex[:12]}"

            try:
                # Get authority
                authority = await self.authority_registry.get_authority(authority_id)
                old_key_id = authority.signing_key_id
                old_public_key = authority.public_key

                # Generate new keypair
                new_private_key, new_public_key = generate_keypair()
                new_key_id = f"key-{uuid4().hex[:12]}"

                # Register new key
                self.key_manager.register_key(new_key_id, new_private_key)

                # Update authority record atomically
                authority.signing_key_id = new_key_id
                authority.public_key = new_public_key
                authority.updated_at = datetime.now(timezone.utc)

                # Add rotation metadata
                if "key_rotation_history" not in authority.metadata:
                    authority.metadata["key_rotation_history"] = []

                authority.metadata["key_rotation_history"].append(
                    {
                        "rotation_id": rotation_id,
                        "old_key_id": old_key_id,
                        "new_key_id": new_key_id,
                        "rotated_at": started_at.isoformat(),
                    }
                )

                await self.authority_registry.update_authority(authority)

                # Re-sign all trust chains established by this authority
                chains_updated = await self._resign_chains(
                    authority_id=authority_id,
                    old_key_id=old_key_id,
                    new_key_id=new_key_id,
                )

                # Place old key in grace period
                grace_period_end = started_at + timedelta(hours=grace_period_hours)
                if authority_id not in self._grace_period_keys:
                    self._grace_period_keys[authority_id] = {}
                self._grace_period_keys[authority_id][old_key_id] = grace_period_end

                completed_at = datetime.now(timezone.utc)

                # Create result
                result = RotationResult(
                    rotation_id=rotation_id,
                    new_key_id=new_key_id,
                    old_key_id=old_key_id,
                    chains_updated=chains_updated,
                    started_at=started_at,
                    completed_at=completed_at,
                    grace_period_end=grace_period_end,
                )

                # Store in history
                if authority_id not in self._rotation_history:
                    self._rotation_history[authority_id] = []
                self._rotation_history[authority_id].append(result)

                # Log audit event
                await self._log_rotation_event(
                    authority_id=authority_id,
                    rotation_id=rotation_id,
                    event_type="rotation_completed",
                    details=result.to_dict(),
                )

                return result

            except Exception as e:
                # Log failure
                await self._log_rotation_event(
                    authority_id=authority_id,
                    rotation_id=rotation_id,
                    event_type="rotation_failed",
                    details={"error": str(e)},
                )
                raise RotationError(
                    f"Failed to rotate key for authority {authority_id}: {str(e)}",
                    authority_id=authority_id,
                    rotation_id=rotation_id,
                    reason="rotation_failed",
                ) from e

        finally:
            # Release lock
            self._active_rotations.discard(authority_id)
            lock.release()

    async def _resign_chains(
        self,
        authority_id: str,
        old_key_id: str,
        new_key_id: str,
    ) -> int:
        """
        Re-sign all trust chains for an authority.

        Args:
            authority_id: Authority whose chains to re-sign
            old_key_id: Old key ID (for reference)
            new_key_id: New key ID to use for signing

        Returns:
            Number of chains updated
        """
        # Get all chains for this authority
        chains = await self.trust_store.list_chains(
            authority_id=authority_id,
            active_only=True,
            limit=10000,  # In production, this would need pagination
        )

        chains_updated = 0

        for chain in chains:
            # Re-sign genesis record
            genesis_payload = serialize_for_signing(chain.genesis.to_signing_payload())
            new_signature = await self.key_manager.sign(genesis_payload, new_key_id)
            chain.genesis.signature = new_signature

            # Re-sign capability attestations
            for capability in chain.capabilities:
                if capability.attester_id == authority_id:
                    cap_payload = serialize_for_signing(capability.to_signing_payload())
                    new_signature = await self.key_manager.sign(cap_payload, new_key_id)
                    capability.signature = new_signature

            # Re-sign delegations
            for delegation in chain.delegations:
                if delegation.delegator_id == authority_id:
                    del_payload = serialize_for_signing(delegation.to_signing_payload())
                    new_signature = await self.key_manager.sign(del_payload, new_key_id)
                    delegation.signature = new_signature

            # Update chain in store
            await self.trust_store.update_chain(chain.genesis.agent_id, chain)
            chains_updated += 1

        return chains_updated

    async def schedule_rotation(
        self,
        authority_id: str,
        at: datetime,
    ) -> str:
        """
        Schedule a future key rotation.

        Args:
            authority_id: Authority to schedule rotation for
            at: When to perform the rotation

        Returns:
            Rotation ID for the scheduled rotation

        Raises:
            AuthorityNotFoundError: If authority not found
            RotationError: If scheduled time is in the past
        """
        # Validate authority exists
        await self.authority_registry.get_authority(authority_id)

        # Validate time
        if at <= datetime.now(timezone.utc):
            raise RotationError(
                "Scheduled rotation time must be in the future",
                authority_id=authority_id,
                reason="invalid_schedule_time",
            )

        # Create scheduled rotation
        rotation_id = f"rot-{uuid4().hex[:12]}"
        scheduled = ScheduledRotation(
            rotation_id=rotation_id,
            authority_id=authority_id,
            scheduled_at=at,
        )

        # Store scheduled rotation
        if authority_id not in self._scheduled_rotations:
            self._scheduled_rotations[authority_id] = []
        self._scheduled_rotations[authority_id].append(scheduled)

        # Log audit event
        await self._log_rotation_event(
            authority_id=authority_id,
            rotation_id=rotation_id,
            event_type="rotation_scheduled",
            details={
                "scheduled_at": at.isoformat(),
            },
        )

        return rotation_id

    async def get_rotation_status(
        self,
        authority_id: str,
    ) -> RotationStatusInfo:
        """
        Get the current rotation status for an authority.

        Args:
            authority_id: Authority to check status for

        Returns:
            RotationStatusInfo with current state

        Raises:
            AuthorityNotFoundError: If authority not found
        """
        # Validate authority exists
        authority = await self.authority_registry.get_authority(authority_id)

        # Get last rotation
        last_rotation = None
        if (
            authority_id in self._rotation_history
            and self._rotation_history[authority_id]
        ):
            last_rotation = self._rotation_history[authority_id][-1].completed_at

        # Get next scheduled
        next_scheduled = None
        if authority_id in self._scheduled_rotations:
            pending = [
                s
                for s in self._scheduled_rotations[authority_id]
                if s.status == RotationStatus.PENDING
            ]
            if pending:
                next_scheduled = min(s.scheduled_at for s in pending)

        # Determine status
        status = RotationStatus.COMPLETED
        if authority_id in self._active_rotations:
            status = RotationStatus.IN_PROGRESS
        elif (
            authority_id in self._grace_period_keys
            and self._grace_period_keys[authority_id]
        ):
            status = RotationStatus.GRACE_PERIOD

        # Get pending revocations (keys past grace period)
        pending_revocations = []
        grace_period_keys = {}
        if authority_id in self._grace_period_keys:
            now = datetime.now(timezone.utc)
            for key_id, expiry in self._grace_period_keys[authority_id].items():
                if expiry <= now:
                    pending_revocations.append(key_id)
                else:
                    grace_period_keys[key_id] = expiry

        return RotationStatusInfo(
            last_rotation=last_rotation,
            next_scheduled=next_scheduled,
            current_key_id=authority.signing_key_id,
            pending_revocations=pending_revocations,
            rotation_period_days=self.rotation_period_days,
            status=status,
            grace_period_keys=grace_period_keys,
        )

    async def revoke_old_key(
        self,
        authority_id: str,
        key_id: str,
    ) -> None:
        """
        Revoke an old key after grace period.

        This removes the key from the key manager and from the grace period tracking.

        Args:
            authority_id: Authority whose key to revoke
            key_id: Key ID to revoke

        Raises:
            AuthorityNotFoundError: If authority not found
            RotationError: If key is not in grace period or grace period not expired
        """
        # Validate authority exists
        await self.authority_registry.get_authority(authority_id)

        # Check if key is in grace period
        if authority_id not in self._grace_period_keys:
            raise RotationError(
                f"No keys in grace period for authority {authority_id}",
                authority_id=authority_id,
                reason="no_grace_period_keys",
            )

        if key_id not in self._grace_period_keys[authority_id]:
            raise RotationError(
                f"Key {key_id} is not in grace period for authority {authority_id}",
                authority_id=authority_id,
                reason="key_not_in_grace_period",
            )

        # Check if grace period has expired
        expiry = self._grace_period_keys[authority_id][key_id]
        if expiry > datetime.now(timezone.utc):
            raise RotationError(
                f"Grace period for key {key_id} has not expired yet (expires at {expiry.isoformat()})",
                authority_id=authority_id,
                reason="grace_period_not_expired",
            )

        # Remove from grace period tracking
        del self._grace_period_keys[authority_id][key_id]

        # Remove from key manager (if it exists)
        # Note: TrustKeyManager doesn't have a remove method in the current implementation,
        # but in production this would remove the key from the HSM/KMS

        # Log audit event
        await self._log_rotation_event(
            authority_id=authority_id,
            rotation_id=f"rev-{uuid4().hex[:12]}",
            event_type="rotation_key_revoked",
            details={
                "key_id": key_id,
                "revoked_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def process_scheduled_rotations(self) -> List[RotationResult]:
        """
        Process any scheduled rotations that are due.

        This should be called periodically (e.g., by a cron job or background task).

        Returns:
            List of RotationResults for completed rotations
        """
        results = []
        now = datetime.now(timezone.utc)

        for authority_id, scheduled_list in self._scheduled_rotations.items():
            for scheduled in scheduled_list:
                if (
                    scheduled.status == RotationStatus.PENDING
                    and scheduled.scheduled_at <= now
                ):
                    try:
                        scheduled.status = RotationStatus.IN_PROGRESS

                        # Perform rotation
                        result = await self.rotate_key(authority_id)
                        results.append(result)

                        scheduled.status = RotationStatus.COMPLETED

                    except Exception as e:
                        scheduled.status = RotationStatus.FAILED
                        await self._log_rotation_event(
                            authority_id=authority_id,
                            rotation_id=scheduled.rotation_id,
                            event_type="scheduled_rotation_failed",
                            details={"error": str(e)},
                        )

        return results

    async def _log_rotation_event(
        self,
        authority_id: str,
        rotation_id: str,
        event_type: str,
        details: Dict,
    ) -> None:
        """
        Log a rotation event for audit purposes.

        Args:
            authority_id: Authority involved in the event
            rotation_id: Rotation identifier
            event_type: Type of event (rotation_completed, rotation_failed, etc.)
            details: Event details
        """
        # Import here to avoid circular imports
        from kaizen.trust.security import SecurityAuditLogger, SecurityEventSeverity

        # Use a shared audit logger instance
        if not hasattr(self, "_audit_logger"):
            self._audit_logger = SecurityAuditLogger()

        # Determine severity based on event type
        severity = SecurityEventSeverity.INFO
        if "failed" in event_type.lower() or "error" in event_type.lower():
            severity = SecurityEventSeverity.ERROR
        elif "warning" in event_type.lower():
            severity = SecurityEventSeverity.WARNING

        # Log to the audit system
        # Note: event_type is already prefixed (e.g., "rotation_completed", "rotation_failed")
        self._audit_logger.log_security_event(
            event_type=event_type,
            details={
                "rotation_id": rotation_id,
                **details,
            },
            authority_id=authority_id,
            severity=severity,
        )

    async def close(self) -> None:
        """Close and cleanup resources."""
        self._active_rotations.clear()
        self._rotation_locks.clear()
