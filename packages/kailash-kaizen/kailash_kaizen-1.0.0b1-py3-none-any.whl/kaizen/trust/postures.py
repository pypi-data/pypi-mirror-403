"""Trust posture mapping for Agentic-OS integration.

Maps Kaizen trust verification results to Agentic-OS trust postures.

See: TODO-204 Agentic-OS Streaming Integration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TrustPosture(str, Enum):
    """Trust posture levels for Agentic-OS.

    Determines how an agent's actions are handled:
    - FULL_AUTONOMY: Agent can act freely without approval
    - SUPERVISED: Agent actions are logged but not blocked
    - HUMAN_DECIDES: Each action requires human approval
    - BLOCKED: Action is denied
    """

    FULL_AUTONOMY = "full_autonomy"
    SUPERVISED = "supervised"
    HUMAN_DECIDES = "human_decides"
    BLOCKED = "blocked"


@dataclass
class PostureConstraints:
    """Constraints applied with a trust posture."""

    audit_required: bool = False
    approval_required: bool = False
    log_level: str = "info"  # debug, info, warning, error
    allowed_capabilities: Optional[List[str]] = None
    blocked_capabilities: Optional[List[str]] = None
    max_actions_before_review: Optional[int] = None
    require_human_approval_for: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "audit_required": self.audit_required,
            "approval_required": self.approval_required,
            "log_level": self.log_level,
            "allowed_capabilities": self.allowed_capabilities,
            "blocked_capabilities": self.blocked_capabilities,
            "max_actions_before_review": self.max_actions_before_review,
            "require_human_approval_for": self.require_human_approval_for,
            "metadata": self.metadata,
        }


@dataclass
class PostureResult:
    """Result of trust posture determination.

    Contains the posture and associated constraints.
    """

    posture: TrustPosture
    constraints: PostureConstraints = field(default_factory=PostureConstraints)
    reason: str = ""
    verification_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "posture": self.posture.value,
            "constraints": self.constraints.to_dict(),
            "reason": self.reason,
            "verification_details": self.verification_details,
        }


class TrustPostureMapper:
    """
    Maps Kaizen trust verification results to Agentic-OS trust postures.

    Provides the bridge between Kaizen's VerificationResult and
    Agentic-OS's trust posture system.

    Example:
        >>> mapper = TrustPostureMapper()
        >>> posture_result = mapper.map_verification_result(verification)
        >>> print(posture_result.posture)  # TrustPosture.FULL_AUTONOMY
    """

    def __init__(
        self,
        default_posture: TrustPosture = TrustPosture.SUPERVISED,
        sensitive_capabilities: Optional[List[str]] = None,
        high_risk_tools: Optional[List[str]] = None,
    ):
        """
        Initialize posture mapper.

        Args:
            default_posture: Default posture when no specific mapping applies
            sensitive_capabilities: Capabilities requiring human approval
            high_risk_tools: Tools requiring elevated trust level
        """
        self._default_posture = default_posture
        self._sensitive_capabilities = sensitive_capabilities or [
            "delete",
            "modify_config",
            "execute_code",
            "external_api",
            "financial_transaction",
        ]
        self._high_risk_tools = high_risk_tools or [
            "bash_command",
            "delete_file",
            "write_file",
            "http_post",
            "http_put",
            "http_delete",
        ]

    def map_verification_result(
        self,
        verification_result: Any,
        requested_capability: Optional[str] = None,
        requested_tool: Optional[str] = None,
    ) -> PostureResult:
        """
        Map a VerificationResult to a TrustPosture.

        Args:
            verification_result: Kaizen VerificationResult
            requested_capability: Optional capability being requested
            requested_tool: Optional tool being requested

        Returns:
            PostureResult with posture and constraints
        """
        # Handle None or invalid result
        if verification_result is None:
            return PostureResult(
                posture=TrustPosture.BLOCKED,
                reason="No verification result provided",
            )

        # Check if verification was valid
        is_valid = getattr(verification_result, "valid", False)
        if not is_valid:
            return PostureResult(
                posture=TrustPosture.BLOCKED,
                reason=getattr(verification_result, "reason", "Verification failed"),
                verification_details=self._extract_details(verification_result),
            )

        # Extract constraints from verification result
        constraints_dict = getattr(verification_result, "constraints", {}) or {}

        # Determine posture based on constraints
        audit_required = constraints_dict.get("audit_required", False)
        approval_required = constraints_dict.get("approval_required", False)
        human_in_loop = constraints_dict.get("human_in_loop", False)

        # Check for sensitive capability
        is_sensitive = self._is_sensitive_capability(requested_capability)
        is_high_risk_tool = self._is_high_risk_tool(requested_tool)

        # Determine posture
        if approval_required or human_in_loop:
            posture = TrustPosture.HUMAN_DECIDES
            reason = "Human approval required"
        elif is_sensitive or is_high_risk_tool:
            posture = TrustPosture.SUPERVISED
            reason = "Sensitive capability or high-risk tool"
            audit_required = True
        elif audit_required:
            posture = TrustPosture.SUPERVISED
            reason = "Audit logging required"
        else:
            # Check trust level if available
            trust_level = constraints_dict.get("trust_level", "normal")
            if trust_level == "high" or trust_level == "full":
                posture = TrustPosture.FULL_AUTONOMY
                reason = "High trust level"
            else:
                posture = self._default_posture
                reason = f"Default posture ({self._default_posture.value})"

        # Build constraints
        posture_constraints = PostureConstraints(
            audit_required=audit_required,
            approval_required=approval_required,
            log_level="warning" if is_sensitive else "info",
            require_human_approval_for=self._sensitive_capabilities if is_sensitive else None,
            metadata=constraints_dict,
        )

        return PostureResult(
            posture=posture,
            constraints=posture_constraints,
            reason=reason,
            verification_details=self._extract_details(verification_result),
        )

    def map_to_posture(
        self,
        is_valid: bool,
        trust_level: str = "normal",
        audit_required: bool = False,
        approval_required: bool = False,
        reason: str = "",
    ) -> PostureResult:
        """
        Simplified posture mapping from basic parameters.

        Args:
            is_valid: Whether the action is allowed
            trust_level: Trust level (none, low, normal, high, full)
            audit_required: Whether audit logging is required
            approval_required: Whether human approval is required
            reason: Reason for the posture

        Returns:
            PostureResult with posture and constraints
        """
        if not is_valid:
            return PostureResult(
                posture=TrustPosture.BLOCKED,
                reason=reason or "Access denied",
            )

        if approval_required:
            return PostureResult(
                posture=TrustPosture.HUMAN_DECIDES,
                constraints=PostureConstraints(
                    approval_required=True,
                    audit_required=True,
                ),
                reason=reason or "Human approval required",
            )

        if audit_required or trust_level in ("none", "low"):
            return PostureResult(
                posture=TrustPosture.SUPERVISED,
                constraints=PostureConstraints(
                    audit_required=True,
                ),
                reason=reason or "Audit logging required",
            )

        if trust_level in ("high", "full"):
            return PostureResult(
                posture=TrustPosture.FULL_AUTONOMY,
                reason=reason or "High trust level",
            )

        return PostureResult(
            posture=self._default_posture,
            reason=reason or f"Default posture ({self._default_posture.value})",
        )

    def _is_sensitive_capability(self, capability: Optional[str]) -> bool:
        """Check if capability is sensitive."""
        if not capability:
            return False
        capability_lower = capability.lower()
        return any(
            sensitive in capability_lower
            for sensitive in self._sensitive_capabilities
        )

    def _is_high_risk_tool(self, tool: Optional[str]) -> bool:
        """Check if tool is high risk."""
        if not tool:
            return False
        tool_lower = tool.lower()
        return any(
            risk_tool in tool_lower
            for risk_tool in self._high_risk_tools
        )

    def _extract_details(self, verification_result: Any) -> Dict[str, Any]:
        """Extract details from verification result."""
        details = {}

        # Extract common fields
        for field in ("agent_id", "action", "trust_chain_id", "timestamp"):
            if hasattr(verification_result, field):
                details[field] = getattr(verification_result, field)

        # Extract constraints
        if hasattr(verification_result, "constraints"):
            details["constraints"] = verification_result.constraints

        return details


# Convenience functions
def map_verification_to_posture(
    verification_result: Any,
    capability: Optional[str] = None,
    tool: Optional[str] = None,
) -> PostureResult:
    """
    Convenience function to map verification result to posture.

    Args:
        verification_result: Kaizen VerificationResult
        capability: Optional capability being requested
        tool: Optional tool being requested

    Returns:
        PostureResult
    """
    mapper = TrustPostureMapper()
    return mapper.map_verification_result(verification_result, capability, tool)


def get_posture_for_action(
    is_allowed: bool,
    requires_audit: bool = False,
    requires_approval: bool = False,
) -> TrustPosture:
    """
    Get simple posture for an action.

    Args:
        is_allowed: Whether the action is allowed
        requires_audit: Whether audit logging is required
        requires_approval: Whether human approval is required

    Returns:
        TrustPosture enum value
    """
    if not is_allowed:
        return TrustPosture.BLOCKED
    if requires_approval:
        return TrustPosture.HUMAN_DECIDES
    if requires_audit:
        return TrustPosture.SUPERVISED
    return TrustPosture.FULL_AUTONOMY


__all__ = [
    "TrustPosture",
    "PostureConstraints",
    "PostureResult",
    "TrustPostureMapper",
    "map_verification_to_posture",
    "get_posture_for_action",
]
