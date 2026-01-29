"""
ACGS-2 Core Validator

The main verification interface for AI compliance checking.

Constitutional Hash: cdd01ef066bc6cf2
"""

import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from .hash import constitutional_hash, CONSTITUTIONAL_HASH
from .result import VerificationResult, Violation, ComplianceLevel
from .policy import PolicyEngine, Policy


class Validator:
    """
    The main ACGS-2 validator class.

    Provides cryptographic verification of AI outputs against
    compliance policies.

    Example:
        >>> validator = Validator()
        >>> result = validator.verify("AI generated content")
        >>> print(result.compliant)  # True or False
        >>> print(result.proof_hash)  # Cryptographic proof
    """

    def __init__(
        self,
        include_default_policies: bool = True,
        strict_mode: bool = False
    ):
        """
        Initialize the validator.

        Args:
            include_default_policies: Whether to include default PII/safety policies
            strict_mode: If True, any policy match causes non-compliance
        """
        self.policy_engine = PolicyEngine(include_defaults=include_default_policies)
        self.strict_mode = strict_mode
        self._verification_count = 0

    def verify(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        policies: Optional[List[str]] = None
    ) -> VerificationResult:
        """
        Verify AI content for compliance.

        Args:
            content: The AI-generated content to verify
            context: Optional context information
            policies: Optional list of policy IDs to check (defaults to all)

        Returns:
            VerificationResult with compliance status and cryptographic proof

        Example:
            >>> result = validator.verify("Hello, my SSN is 123-45-6789")
            >>> result.compliant
            False
            >>> result.violations[0].rule_id
            'no-ssn'
        """
        start_time = time.perf_counter()

        # Run policy evaluation
        policy_results = self.policy_engine.evaluate(content)

        # Filter by requested policies if specified
        if policies:
            policy_results = [r for r in policy_results if r.policy_id in policies]

        # Convert policy failures to violations
        violations = []
        for pr in policy_results:
            if not pr.passed:
                policy = self.policy_engine.get_policy(pr.policy_id)
                severity = policy.severity if policy else "medium"

                violations.append(Violation(
                    rule_id=pr.policy_id,
                    description=pr.message or f"Policy {pr.policy_id} violated",
                    severity=severity,
                    suggestion=f"Remove content matching: {pr.matches[:3]}" if pr.matches else None
                ))

        # Determine compliance
        if self.strict_mode:
            compliant = len(violations) == 0
        else:
            # In non-strict mode, only critical violations cause non-compliance
            compliant = not any(v.severity == "critical" for v in violations)

        # Calculate latency
        latency_ms = (time.perf_counter() - start_time) * 1000

        # Generate timestamp
        timestamp = datetime.now(timezone.utc)

        # Generate proof hash
        proof_hash = constitutional_hash(content, timestamp)

        # Increment counter
        self._verification_count += 1

        return VerificationResult(
            compliant=compliant,
            proof_hash=proof_hash,
            constitutional_anchor=CONSTITUTIONAL_HASH,
            timestamp=timestamp,
            latency_ms=latency_ms,
            violations=violations,
            metadata={
                "verification_id": self._verification_count,
                "policies_checked": len(policy_results),
                "context": context or {},
            }
        )

    def add_policy(self, policy: Policy) -> None:
        """Add a custom policy."""
        self.policy_engine.add_policy(policy)

    def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy by ID."""
        return self.policy_engine.remove_policy(policy_id)

    def list_policies(self) -> List[str]:
        """List all active policy IDs."""
        return self.policy_engine.list_policies()

    @property
    def verification_count(self) -> int:
        """Total number of verifications performed."""
        return self._verification_count


# Global validator instance for simple usage
_default_validator: Optional[Validator] = None


def get_validator() -> Validator:
    """Get or create the default validator instance."""
    global _default_validator
    if _default_validator is None:
        _default_validator = Validator()
    return _default_validator


def verify(
    content: str,
    context: Optional[Dict[str, Any]] = None,
    policies: Optional[List[str]] = None
) -> VerificationResult:
    """
    Verify AI content for compliance using the default validator.

    This is the simplest way to use ACGS-2:

        from acgs2_core import verify

        result = verify("AI generated content")
        if result.compliant:
            print("Content is compliant!")
        else:
            print(f"Violations: {len(result.violations)}")

    Args:
        content: The AI-generated content to verify
        context: Optional context information
        policies: Optional list of specific policy IDs to check

    Returns:
        VerificationResult with compliance status and cryptographic proof
    """
    return get_validator().verify(content, context, policies)
