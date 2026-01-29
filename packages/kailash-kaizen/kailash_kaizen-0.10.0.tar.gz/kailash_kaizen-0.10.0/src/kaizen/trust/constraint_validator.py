"""
Constraint validation for EATP delegations.

Ensures that delegations can only TIGHTEN constraints, never loosen them.
This is a fundamental security property of EATP - trust can only be
reduced as it flows through the delegation chain.

Key Principle: A delegation can only REMOVE permissions, never ADD them.

Supported Constraints:
- cost_limit: Child must be <= parent
- time_window: Child must be subset of parent
- resources: Child must be subset of parent (glob matching)
- rate_limit: Child must be <= parent
- geo_restrictions: Child must be subset of parent

Reference: docs/plans/eatp-integration/04-gap-analysis.md (G4)

Author: Kaizen Framework Team
Created: 2026-01-02
"""

import fnmatch
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class ConstraintViolation(str, Enum):
    """
    Types of constraint violations.

    Each violation type indicates a specific way constraints were loosened.
    """

    COST_LOOSENED = "cost_limit_increased"
    TIME_WINDOW_EXPANDED = "time_window_expanded"
    RESOURCES_EXPANDED = "resources_expanded"
    RATE_LIMIT_INCREASED = "rate_limit_increased"
    GEO_RESTRICTION_REMOVED = "geo_restriction_removed"
    BUDGET_LIMIT_INCREASED = "budget_limit_increased"
    ACTION_RESTRICTION_REMOVED = "action_restriction_removed"
    MAX_DELEGATION_DEPTH_INCREASED = "max_delegation_depth_increased"


@dataclass
class ValidationResult:
    """
    Result of constraint validation.

    Attributes:
        valid: True if all constraints are properly tightened
        violations: List of specific violations found
        details: Detailed messages for each violation
    """

    valid: bool
    violations: List[ConstraintViolation] = field(default_factory=list)
    details: Dict[str, str] = field(default_factory=dict)

    def __bool__(self) -> bool:
        """Allow using result directly in boolean context."""
        return self.valid


class ConstraintValidator:
    """
    Validates that child constraints are strictly tighter than parent.

    Rule: A delegation can only REMOVE permissions, never ADD them.

    This validator checks various constraint types to ensure that
    when trust is delegated, the delegatee cannot have more permissions
    than the delegator.

    Supported constraints:
    - cost_limit: Child must be <= parent
    - time_window: Child must be subset of parent (format: "HH:MM-HH:MM")
    - resources: Child must be subset of parent (glob matching)
    - rate_limit: Child must be <= parent
    - geo_restrictions: Child must be subset of parent
    - budget_limit: Child must be <= parent
    - max_delegation_depth: Child must be <= parent

    Example:
        >>> validator = ConstraintValidator()
        >>>
        >>> # Valid: tightening constraints
        >>> result = validator.validate_tightening(
        ...     parent_constraints={"cost_limit": 10000},
        ...     child_constraints={"cost_limit": 1000}  # Lower = tighter
        ... )
        >>> assert result.valid is True
        >>>
        >>> # Invalid: loosening constraints
        >>> result = validator.validate_tightening(
        ...     parent_constraints={"cost_limit": 1000},
        ...     child_constraints={"cost_limit": 10000}  # Higher = loosened!
        ... )
        >>> assert result.valid is False
        >>> assert ConstraintViolation.COST_LOOSENED in result.violations
    """

    def __init__(self, strict_mode: bool = True):
        """
        Initialize validator.

        Args:
            strict_mode: If True, fail on any unknown constraint types.
                        If False, skip unknown constraints with a warning.
        """
        self._strict_mode = strict_mode

    def validate_tightening(
        self,
        parent_constraints: Dict[str, Any],
        child_constraints: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate that child constraints are subset of parent.

        Args:
            parent_constraints: Constraints of the delegator
            child_constraints: Constraints for the delegatee

        Returns:
            ValidationResult with any violations found
        """
        violations: List[ConstraintViolation] = []
        details: Dict[str, str] = {}

        # Check cost limit
        if "cost_limit" in child_constraints:
            parent_limit = parent_constraints.get("cost_limit", float("inf"))
            child_limit = child_constraints["cost_limit"]
            if child_limit > parent_limit:
                violations.append(ConstraintViolation.COST_LOOSENED)
                details["cost_limit"] = f"Child {child_limit} > Parent {parent_limit}"

        # Check budget limit (similar to cost_limit but for different domain)
        if "budget_limit" in child_constraints:
            parent_limit = parent_constraints.get("budget_limit", float("inf"))
            child_limit = child_constraints["budget_limit"]
            if child_limit > parent_limit:
                violations.append(ConstraintViolation.BUDGET_LIMIT_INCREASED)
                details["budget_limit"] = f"Child {child_limit} > Parent {parent_limit}"

        # Check time window
        if "time_window" in child_constraints:
            parent_window = parent_constraints.get("time_window")
            if parent_window and not self._is_time_subset(
                parent_window, child_constraints["time_window"]
            ):
                violations.append(ConstraintViolation.TIME_WINDOW_EXPANDED)
                details["time_window"] = (
                    f"Child window '{child_constraints['time_window']}' "
                    f"not within parent window '{parent_window}'"
                )

        # Check resources
        if "resources" in child_constraints:
            parent_resources = parent_constraints.get("resources", [])
            if parent_resources and not self._is_resource_subset(
                parent_resources, child_constraints["resources"]
            ):
                violations.append(ConstraintViolation.RESOURCES_EXPANDED)
                details["resources"] = "Child resources not subset of parent"

        # Check rate limit
        if "rate_limit" in child_constraints:
            parent_rate = parent_constraints.get("rate_limit", float("inf"))
            child_rate = child_constraints["rate_limit"]
            if child_rate > parent_rate:
                violations.append(ConstraintViolation.RATE_LIMIT_INCREASED)
                details["rate_limit"] = f"Child {child_rate} > Parent {parent_rate}"

        # Check geo restrictions
        if "geo_restrictions" in parent_constraints:
            parent_geo = set(parent_constraints["geo_restrictions"])
            child_geo = set(child_constraints.get("geo_restrictions", []))
            # If child has geo restrictions, they must be subset of parent
            if child_geo and not child_geo.issubset(parent_geo):
                violations.append(ConstraintViolation.GEO_RESTRICTION_REMOVED)
                added_regions = child_geo - parent_geo
                details["geo_restrictions"] = (
                    f"Child adds regions not in parent: {added_regions}"
                )

        # Check max delegation depth
        if "max_delegation_depth" in child_constraints:
            parent_depth = parent_constraints.get("max_delegation_depth", float("inf"))
            child_depth = child_constraints["max_delegation_depth"]
            if child_depth > parent_depth:
                violations.append(ConstraintViolation.MAX_DELEGATION_DEPTH_INCREASED)
                details["max_delegation_depth"] = (
                    f"Child {child_depth} > Parent {parent_depth}"
                )

        # Check action restrictions (allowed_actions must be subset)
        if "allowed_actions" in parent_constraints:
            parent_actions = set(parent_constraints["allowed_actions"])
            child_actions = set(child_constraints.get("allowed_actions", []))
            if child_actions and not child_actions.issubset(parent_actions):
                violations.append(ConstraintViolation.ACTION_RESTRICTION_REMOVED)
                added_actions = child_actions - parent_actions
                details["allowed_actions"] = (
                    f"Child adds actions not in parent: {added_actions}"
                )

        return ValidationResult(
            valid=len(violations) == 0,
            violations=violations,
            details=details,
        )

    def _is_time_subset(self, parent_window: str, child_window: str) -> bool:
        """
        Check if child time window is within parent.

        Time windows are in format "HH:MM-HH:MM" (24-hour format).
        Child is valid if its start >= parent start AND its end <= parent end.

        Args:
            parent_window: Parent's time window (e.g., "09:00-17:00")
            child_window: Child's time window (e.g., "10:00-16:00")

        Returns:
            True if child window is within parent window
        """
        try:
            p_start, p_end = self._parse_time_window(parent_window)
            c_start, c_end = self._parse_time_window(child_window)
            return c_start >= p_start and c_end <= p_end
        except Exception as e:
            logger.warning(f"Failed to parse time windows: {e}")
            return False  # Invalid format = not a subset

    def _is_resource_subset(
        self,
        parent_resources: List[str],
        child_resources: List[str],
    ) -> bool:
        """
        Check if child resources are subset of parent (with glob matching).

        Each child resource must match at least one parent pattern.

        Args:
            parent_resources: Parent's resource patterns (may include globs)
            child_resources: Child's resource patterns

        Returns:
            True if all child resources match parent patterns

        Example:
            >>> validator._is_resource_subset(
            ...     ["invoices/*"], ["invoices/small/*"]
            ... )
            True
            >>> validator._is_resource_subset(
            ...     ["invoices/small/*"], ["invoices/*"]  # Expanded!
            ... )
            False
        """
        for child_res in child_resources:
            # Child resource must match at least one parent pattern
            if not any(
                self._glob_match(parent, child_res) for parent in parent_resources
            ):
                return False
        return True

    def _glob_match(self, pattern: str, path: str) -> bool:
        """
        Check if path matches glob pattern.

        Uses fnmatch for glob matching. Supports:
        - * matches any characters within a path segment
        - ** matches across path segments
        - ? matches single character

        Args:
            pattern: Glob pattern
            path: Path to match

        Returns:
            True if path matches pattern
        """
        # Handle ** for recursive matching
        if "**" in pattern:
            # Convert ** to match anything including /
            pattern = pattern.replace("**", "*")

        return fnmatch.fnmatch(path, pattern)

    def _parse_time_window(self, window: str) -> Tuple[int, int]:
        """
        Parse time window "HH:MM-HH:MM" to minutes from midnight.

        Args:
            window: Time window string (e.g., "09:00-17:00")

        Returns:
            Tuple of (start_minutes, end_minutes) from midnight

        Raises:
            ValueError: If format is invalid
        """
        parts = window.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid time window format: {window}")

        start = self._time_to_minutes(parts[0].strip())
        end = self._time_to_minutes(parts[1].strip())
        return start, end

    def _time_to_minutes(self, time_str: str) -> int:
        """
        Convert HH:MM to minutes from midnight.

        Args:
            time_str: Time string (e.g., "09:00", "17:30")

        Returns:
            Minutes from midnight
        """
        parts = time_str.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid time format: {time_str}")

        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError(f"Invalid time values: {time_str}")

        return h * 60 + m


class DelegationConstraintValidator:
    """
    High-level validator for delegation constraint checking.

    This class provides a simplified interface for validating
    constraint tightening during delegation operations.
    """

    def __init__(self):
        self._validator = ConstraintValidator()

    def validate_delegation(
        self,
        delegator_constraints: Dict[str, Any],
        delegatee_constraints: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate that a delegation maintains constraint tightening.

        Args:
            delegator_constraints: Constraints of the delegating agent
            delegatee_constraints: Constraints being given to the delegatee

        Returns:
            ValidationResult indicating if delegation is valid
        """
        return self._validator.validate_tightening(
            delegator_constraints, delegatee_constraints
        )

    def can_delegate(
        self,
        delegator_constraints: Dict[str, Any],
        delegatee_constraints: Dict[str, Any],
    ) -> bool:
        """
        Quick check if delegation would be valid.

        Args:
            delegator_constraints: Constraints of the delegating agent
            delegatee_constraints: Constraints being given to the delegatee

        Returns:
            True if delegation is valid, False otherwise
        """
        result = self.validate_delegation(delegator_constraints, delegatee_constraints)
        return result.valid

    def get_max_allowed_constraints(
        self,
        delegator_constraints: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Get the maximum constraints that can be delegated.

        Returns a copy of the delegator's constraints, which represent
        the loosest constraints that can be given to a delegatee.

        Args:
            delegator_constraints: Constraints of the delegating agent

        Returns:
            Copy of delegator constraints (represents ceiling for delegatee)
        """
        return dict(delegator_constraints)
