"""
Verification Result Model

Contains the result of a compliance verification, including
cryptographic proof and audit trail information.

Constitutional Hash: cdd01ef066bc6cf2
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum


class ComplianceLevel(Enum):
    """Compliance level categories."""
    FULL = "full"           # 100% compliant
    PARTIAL = "partial"     # Some violations, non-critical
    VIOLATION = "violation" # Critical violations detected
    UNKNOWN = "unknown"     # Unable to determine


@dataclass
class Violation:
    """A single compliance violation."""
    rule_id: str
    description: str
    severity: str  # "low", "medium", "high", "critical"
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class VerificationResult:
    """
    The result of a compliance verification.

    Attributes:
        compliant: Whether the content is compliant
        proof_hash: Cryptographic proof hash
        constitutional_anchor: The constitutional anchor hash
        timestamp: When verification occurred
        latency_ms: Verification latency in milliseconds
        compliance_level: Detailed compliance level
        violations: List of any violations found
        metadata: Additional verification metadata

    Example:
        >>> result = verify("AI content")
        >>> if result.compliant:
        ...     print(f"Verified: {result.proof_hash}")
        ... else:
        ...     for v in result.violations:
        ...         print(f"Violation: {v.description}")
    """

    compliant: bool
    proof_hash: str
    constitutional_anchor: str = "cdd01ef066bc6cf2"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: float = 0.0
    compliance_level: ComplianceLevel = ComplianceLevel.UNKNOWN
    violations: List[Violation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set compliance level based on violations."""
        if not self.violations:
            self.compliance_level = ComplianceLevel.FULL
        elif any(v.severity == "critical" for v in self.violations):
            self.compliance_level = ComplianceLevel.VIOLATION
        else:
            self.compliance_level = ComplianceLevel.PARTIAL

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "compliant": self.compliant,
            "proof_hash": self.proof_hash,
            "constitutional_anchor": self.constitutional_anchor,
            "timestamp": self.timestamp.isoformat(),
            "latency_ms": self.latency_ms,
            "compliance_level": self.compliance_level.value,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "description": v.description,
                    "severity": v.severity,
                    "location": v.location,
                    "suggestion": v.suggestion,
                }
                for v in self.violations
            ],
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        status = "✓ COMPLIANT" if self.compliant else "✗ VIOLATION"
        return (
            f"{status}\n"
            f"  Proof: {self.proof_hash[:16]}...\n"
            f"  Anchor: {self.constitutional_anchor}\n"
            f"  Latency: {self.latency_ms:.2f}ms\n"
            f"  Violations: {len(self.violations)}"
        )
