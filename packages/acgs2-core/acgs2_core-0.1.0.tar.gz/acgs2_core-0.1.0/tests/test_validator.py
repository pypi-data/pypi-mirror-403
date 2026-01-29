"""
Tests for ACGS-2 Core Validator

Constitutional Hash: cdd01ef066bc6cf2
"""

import pytest
from acgs2_core import verify, Validator, VerificationResult
from acgs2_core.hash import CONSTITUTIONAL_HASH
from acgs2_core.policy import Policy, PolicyType


class TestVerify:
    """Tests for the verify() function."""

    def test_verify_clean_content(self):
        """Clean content should be compliant."""
        result = verify("The weather today is sunny.")
        assert result.compliant is True
        assert len(result.violations) == 0

    def test_verify_returns_result(self):
        """verify() should return VerificationResult."""
        result = verify("Test content")
        assert isinstance(result, VerificationResult)

    def test_verify_has_proof_hash(self):
        """Result should contain proof hash."""
        result = verify("Test content")
        assert result.proof_hash is not None
        assert len(result.proof_hash) == 64  # SHA-256 hex

    def test_verify_has_constitutional_anchor(self):
        """Result should contain constitutional anchor."""
        result = verify("Test content")
        assert result.constitutional_anchor == CONSTITUTIONAL_HASH

    def test_verify_has_timestamp(self):
        """Result should contain timestamp."""
        result = verify("Test content")
        assert result.timestamp is not None

    def test_verify_has_latency(self):
        """Result should contain latency measurement."""
        result = verify("Test content")
        assert result.latency_ms >= 0


class TestPIIDetection:
    """Tests for PII detection policies."""

    def test_detect_ssn(self):
        """Should detect SSN patterns."""
        result = verify("My SSN is 123-45-6789")
        assert result.compliant is False
        assert any(v.rule_id == "no-ssn" for v in result.violations)

    def test_detect_credit_card(self):
        """Should detect credit card patterns."""
        result = verify("Card: 4111-1111-1111-1111")
        assert result.compliant is False
        assert any(v.rule_id == "no-credit-card" for v in result.violations)

    def test_detect_email(self):
        """Should detect email patterns."""
        result = verify("Contact: john@example.com")
        # Email is high severity, not critical, so compliant in non-strict
        violations = [v for v in result.violations if v.rule_id == "no-email-leak"]
        assert len(violations) == 1

    def test_detect_phone(self):
        """Should detect phone patterns."""
        result = verify("Call 555-123-4567")
        violations = [v for v in result.violations if v.rule_id == "no-phone"]
        assert len(violations) == 1


class TestValidator:
    """Tests for Validator class."""

    def test_validator_creation(self):
        """Should create validator."""
        validator = Validator()
        assert validator is not None

    def test_validator_without_defaults(self):
        """Should work without default policies."""
        validator = Validator(include_default_policies=False)
        result = validator.verify("SSN: 123-45-6789")
        assert result.compliant is True  # No policies to check

    def test_strict_mode(self):
        """Strict mode should fail on any violation."""
        validator = Validator(strict_mode=True)
        # Email is medium severity
        result = validator.verify("Contact: test@test.com")
        assert result.compliant is False

    def test_add_custom_policy(self):
        """Should support custom policies."""
        validator = Validator(include_default_policies=False)
        validator.add_policy(Policy(
            id="no-foo",
            name="No Foo",
            description="Detect foo",
            policy_type=PolicyType.PATTERN,
            rule=r"\bfoo\b",
            severity="critical"
        ))

        result = validator.verify("This has foo in it")
        assert result.compliant is False
        assert result.violations[0].rule_id == "no-foo"

    def test_remove_policy(self):
        """Should remove policies."""
        validator = Validator()
        assert validator.remove_policy("no-ssn") is True

        result = validator.verify("SSN: 123-45-6789")
        assert "no-ssn" not in [v.rule_id for v in result.violations]

    def test_list_policies(self):
        """Should list policy IDs."""
        validator = Validator()
        policies = validator.list_policies()
        assert "no-ssn" in policies
        assert "no-credit-card" in policies

    def test_verification_count(self):
        """Should track verification count."""
        validator = Validator()
        assert validator.verification_count == 0

        validator.verify("Test 1")
        assert validator.verification_count == 1

        validator.verify("Test 2")
        assert validator.verification_count == 2


class TestResultSerialization:
    """Tests for result serialization."""

    def test_to_dict(self):
        """Should convert to dictionary."""
        result = verify("Test content")
        d = result.to_dict()

        assert "compliant" in d
        assert "proof_hash" in d
        assert "timestamp" in d

    def test_str_representation(self):
        """Should have string representation."""
        result = verify("Test content")
        s = str(result)

        assert "COMPLIANT" in s or "VIOLATION" in s


class TestConstitutionalHash:
    """Tests for constitutional hash functionality."""

    def test_hash_is_stable(self):
        """Constitutional hash should be stable."""
        assert CONSTITUTIONAL_HASH == "cdd01ef066bc6cf2"

    def test_different_content_different_hash(self):
        """Different content should produce different hashes."""
        result1 = verify("Content A")
        result2 = verify("Content B")

        assert result1.proof_hash != result2.proof_hash

    def test_same_content_same_timestamp_same_hash(self):
        """Same content and timestamp should produce same hash."""
        from acgs2_core.hash import constitutional_hash
        from datetime import datetime, timezone

        ts = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        hash1 = constitutional_hash("Test", ts)
        hash2 = constitutional_hash("Test", ts)

        assert hash1 == hash2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
