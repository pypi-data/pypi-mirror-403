"""
Policy Engine

Define and evaluate compliance policies against AI outputs.

Constitutional Hash: cdd01ef066bc6cf2
"""

import re
from dataclasses import dataclass, field
from typing import List, Callable, Optional, Any
from enum import Enum


class PolicyType(Enum):
    """Types of policies."""
    CONTENT = "content"       # Content-based rules
    PATTERN = "pattern"       # Regex pattern matching
    SEMANTIC = "semantic"     # Semantic analysis
    CUSTOM = "custom"         # Custom function


@dataclass
class Policy:
    """
    A compliance policy definition.

    Attributes:
        id: Unique policy identifier
        name: Human-readable name
        description: Policy description
        policy_type: Type of policy
        rule: The policy rule (pattern, function, etc.)
        severity: Violation severity if triggered
        enabled: Whether policy is active

    Example:
        >>> policy = Policy(
        ...     id="no-pii",
        ...     name="No PII",
        ...     description="Prevent PII in outputs",
        ...     policy_type=PolicyType.PATTERN,
        ...     rule=r"\\b\\d{3}-\\d{2}-\\d{4}\\b",  # SSN pattern
        ...     severity="critical"
        ... )
    """

    id: str
    name: str
    description: str
    policy_type: PolicyType
    rule: Any  # Pattern string or callable
    severity: str = "medium"
    enabled: bool = True


# =============================================================================
# Enhanced Pattern Definitions (15+ PII Categories)
# =============================================================================

# SSN: Multiple formats (XXX-XX-XXXX, XXX XX XXXX, XXXXXXXXX)
_SSN_PATTERN = r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"

# Credit Cards: Visa, MasterCard, Amex, Discover, etc.
_CREDIT_CARD_PATTERNS = [
    r"\b4\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # Visa
    r"\b5[1-5]\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # MasterCard
    r"\b3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}\b",  # Amex
    r"\b6(?:011|5\d{2})[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # Discover
    r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # Generic 16-digit
]
_CREDIT_CARD_PATTERN = "|".join(f"(?:{p})" for p in _CREDIT_CARD_PATTERNS)

# Phone: US, International, various formats
_PHONE_PATTERNS = [
    r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # US: 123-456-7890
    r"\(\d{3}\)\s*\d{3}[-.\s]?\d{4}",  # US: (123) 456-7890
    r"\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}",  # US: +1-123-456-7890
    r"\+\d{1,3}[-.\s]?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}",  # International
]
_PHONE_PATTERN = "|".join(f"(?:{p})" for p in _PHONE_PATTERNS)

# Email: Standard pattern
_EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

# IP Addresses: IPv4 and IPv6
_IP_PATTERNS = [
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",  # IPv4
    r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b",  # IPv6 full
]
_IP_PATTERN = "|".join(f"(?:{p})" for p in _IP_PATTERNS)

# API Keys and Secrets (common patterns)
_API_KEY_PATTERNS = [
    r"\b[A-Za-z0-9]{32,}\b",  # Generic long alphanumeric
    r"\bsk[-_]live[-_][A-Za-z0-9]{24,}\b",  # Stripe live key
    r"\bsk[-_]test[-_][A-Za-z0-9]{24,}\b",  # Stripe test key
    r"\bAKIA[0-9A-Z]{16}\b",  # AWS Access Key ID
    r"\bAIza[0-9A-Za-z\-_]{35}\b",  # Google API Key
    r"\bghp_[A-Za-z0-9]{36}\b",  # GitHub Personal Access Token
    r"\bgho_[A-Za-z0-9]{36}\b",  # GitHub OAuth Token
    r"\bxox[baprs]-[0-9A-Za-z\-]{10,}\b",  # Slack Token
]
_API_KEY_PATTERN = "|".join(f"(?:{p})" for p in _API_KEY_PATTERNS)

# AWS Credentials
_AWS_PATTERNS = [
    r"\bAKIA[0-9A-Z]{16}\b",  # AWS Access Key
    r"\b[A-Za-z0-9/+=]{40}\b",  # AWS Secret Key (context dependent)
    r"\barn:aws:[a-z0-9-]+:[a-z0-9-]*:\d{12}:[a-zA-Z0-9-_/]+\b",  # AWS ARN
]
_AWS_PATTERN = "|".join(f"(?:{p})" for p in _AWS_PATTERNS)

# Passport Numbers (various countries)
_PASSPORT_PATTERNS = [
    r"\b[A-Z]{1,2}\d{6,9}\b",  # US, UK, etc.
    r"\b[A-Z]\d{8}\b",  # China
]
_PASSPORT_PATTERN = "|".join(f"(?:{p})" for p in _PASSPORT_PATTERNS)

# Bank Account / Routing Numbers
_BANK_PATTERNS = [
    r"\b\d{9}\b",  # US Routing Number (9 digits)
    r"\b\d{10,17}\b",  # Account Numbers (10-17 digits)
    r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}(?:[A-Z0-9]?){0,16}\b",  # IBAN
]
_BANK_PATTERN = "|".join(f"(?:{p})" for p in _BANK_PATTERNS)

# Date of Birth Patterns
_DOB_PATTERNS = [
    r"\b(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])/(?:19|20)\d{2}\b",  # MM/DD/YYYY
    r"\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b",  # YYYY-MM-DD
]
_DOB_PATTERN = "|".join(f"(?:{p})" for p in _DOB_PATTERNS)

# Private Keys and Certificates
_PRIVATE_KEY_PATTERN = r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----"

# JWT Tokens
_JWT_PATTERN = r"\beyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b"

# Passwords in common contexts
_PASSWORD_CONTEXT_PATTERN = r"(?:password|passwd|pwd|secret|token)\s*[=:]\s*['\"]?[^\s'\"]{8,}['\"]?"


# =============================================================================
# Default Policies (15 Protection Categories)
# =============================================================================

DEFAULT_POLICIES = [
    # Critical PII
    Policy(
        id="no-ssn",
        name="No Social Security Numbers",
        description="Detect SSN patterns (XXX-XX-XXXX, XXX XX XXXX)",
        policy_type=PolicyType.PATTERN,
        rule=_SSN_PATTERN,
        severity="critical"
    ),
    Policy(
        id="no-credit-card",
        name="No Credit Card Numbers",
        description="Detect Visa, MasterCard, Amex, Discover patterns",
        policy_type=PolicyType.PATTERN,
        rule=_CREDIT_CARD_PATTERN,
        severity="critical"
    ),
    Policy(
        id="no-bank-account",
        name="No Bank Account Numbers",
        description="Detect routing numbers, account numbers, IBAN",
        policy_type=PolicyType.PATTERN,
        rule=_BANK_PATTERN,
        severity="critical"
    ),

    # High Severity PII
    Policy(
        id="no-email-leak",
        name="No Email Addresses",
        description="Detect email address patterns",
        policy_type=PolicyType.PATTERN,
        rule=_EMAIL_PATTERN,
        severity="high"
    ),
    Policy(
        id="no-passport",
        name="No Passport Numbers",
        description="Detect passport number patterns",
        policy_type=PolicyType.PATTERN,
        rule=_PASSPORT_PATTERN,
        severity="high"
    ),
    Policy(
        id="no-dob",
        name="No Date of Birth",
        description="Detect date of birth patterns",
        policy_type=PolicyType.PATTERN,
        rule=_DOB_PATTERN,
        severity="high"
    ),

    # Security Credentials
    Policy(
        id="no-api-keys",
        name="No API Keys",
        description="Detect API keys (Stripe, Google, GitHub, Slack)",
        policy_type=PolicyType.PATTERN,
        rule=_API_KEY_PATTERN,
        severity="critical"
    ),
    Policy(
        id="no-aws-credentials",
        name="No AWS Credentials",
        description="Detect AWS access keys and ARNs",
        policy_type=PolicyType.PATTERN,
        rule=_AWS_PATTERN,
        severity="critical"
    ),
    Policy(
        id="no-private-keys",
        name="No Private Keys",
        description="Detect RSA/PEM private key headers",
        policy_type=PolicyType.PATTERN,
        rule=_PRIVATE_KEY_PATTERN,
        severity="critical"
    ),
    Policy(
        id="no-jwt-tokens",
        name="No JWT Tokens",
        description="Detect JSON Web Tokens",
        policy_type=PolicyType.PATTERN,
        rule=_JWT_PATTERN,
        severity="critical"
    ),
    Policy(
        id="no-passwords",
        name="No Passwords in Context",
        description="Detect password assignments in text",
        policy_type=PolicyType.PATTERN,
        rule=_PASSWORD_CONTEXT_PATTERN,
        severity="critical"
    ),

    # Network Information
    Policy(
        id="no-ip-address",
        name="No IP Addresses",
        description="Detect IPv4 and IPv6 addresses",
        policy_type=PolicyType.PATTERN,
        rule=_IP_PATTERN,
        severity="medium"
    ),
    Policy(
        id="no-phone",
        name="No Phone Numbers",
        description="Detect US and international phone formats",
        policy_type=PolicyType.PATTERN,
        rule=_PHONE_PATTERN,
        severity="medium"
    ),

    # Harmful Content
    Policy(
        id="no-harmful-content",
        name="No Harmful Content",
        description="Detect security threat keywords",
        policy_type=PolicyType.PATTERN,
        rule=r"\b(hack|exploit|attack|malware|virus|ransomware|phishing|keylogger)\b",
        severity="high"
    ),
]


@dataclass
class PolicyResult:
    """Result of a single policy evaluation."""
    policy_id: str
    passed: bool
    matches: List[str] = field(default_factory=list)
    message: Optional[str] = None


class PolicyEngine:
    """
    Engine for evaluating content against policies.

    Example:
        >>> engine = PolicyEngine()
        >>> engine.add_policy(my_policy)
        >>> results = engine.evaluate("Some AI content")
        >>> for r in results:
        ...     print(f"{r.policy_id}: {'PASS' if r.passed else 'FAIL'}")
    """

    def __init__(self, include_defaults: bool = True):
        """
        Initialize the policy engine.

        Args:
            include_defaults: Whether to include default policies
        """
        self.policies: List[Policy] = []
        if include_defaults:
            self.policies.extend(DEFAULT_POLICIES)

    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the engine."""
        self.policies.append(policy)

    def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy by ID. Returns True if found and removed."""
        for i, p in enumerate(self.policies):
            if p.id == policy_id:
                self.policies.pop(i)
                return True
        return False

    def evaluate(self, content: str) -> List[PolicyResult]:
        """
        Evaluate content against all enabled policies.

        Args:
            content: The content to evaluate

        Returns:
            List of PolicyResult for each policy
        """
        results = []

        for policy in self.policies:
            if not policy.enabled:
                continue

            result = self._evaluate_policy(content, policy)
            results.append(result)

        return results

    def _evaluate_policy(self, content: str, policy: Policy) -> PolicyResult:
        """Evaluate a single policy."""
        if policy.policy_type == PolicyType.PATTERN:
            return self._evaluate_pattern(content, policy)
        elif policy.policy_type == PolicyType.CUSTOM:
            return self._evaluate_custom(content, policy)
        else:
            return PolicyResult(
                policy_id=policy.id,
                passed=True,
                message=f"Policy type {policy.policy_type} not implemented"
            )

    def _evaluate_pattern(self, content: str, policy: Policy) -> PolicyResult:
        """Evaluate a regex pattern policy."""
        try:
            pattern = re.compile(policy.rule, re.IGNORECASE)
            matches = pattern.findall(content)

            return PolicyResult(
                policy_id=policy.id,
                passed=len(matches) == 0,
                matches=matches,
                message=f"Found {len(matches)} matches" if matches else None
            )
        except re.error as e:
            return PolicyResult(
                policy_id=policy.id,
                passed=False,
                message=f"Invalid pattern: {e}"
            )

    def _evaluate_custom(self, content: str, policy: Policy) -> PolicyResult:
        """Evaluate a custom function policy."""
        if not callable(policy.rule):
            return PolicyResult(
                policy_id=policy.id,
                passed=False,
                message="Custom policy rule is not callable"
            )

        try:
            result = policy.rule(content)
            if isinstance(result, bool):
                return PolicyResult(policy_id=policy.id, passed=result)
            elif isinstance(result, PolicyResult):
                return result
            else:
                return PolicyResult(
                    policy_id=policy.id,
                    passed=bool(result)
                )
        except Exception as e:
            return PolicyResult(
                policy_id=policy.id,
                passed=False,
                message=f"Policy evaluation error: {e}"
            )

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a policy by ID."""
        for p in self.policies:
            if p.id == policy_id:
                return p
        return None

    def list_policies(self) -> List[str]:
        """List all policy IDs."""
        return [p.id for p in self.policies]
