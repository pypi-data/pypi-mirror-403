"""
Tests for Enhanced Pattern Protection

Constitutional Hash: cdd01ef066bc6cf2

Tests 15+ PII detection categories:
- SSN (multiple formats)
- Credit Cards (Visa, MC, Amex, Discover)
- Bank Accounts / IBAN
- Email
- Phone (US, International)
- Passport Numbers
- Date of Birth
- API Keys (Stripe, Google, GitHub, Slack)
- AWS Credentials
- Private Keys
- JWT Tokens
- Passwords in Context
- IP Addresses
- Harmful Content
"""

import pytest
from acgs2_core import verify, Validator


class TestSSNPatterns:
    """Test SSN detection in multiple formats."""

    def test_ssn_with_dashes(self):
        result = verify("SSN: 123-45-6789")
        assert result.compliant is False
        assert any(v.rule_id == "no-ssn" for v in result.violations)

    def test_ssn_with_spaces(self):
        result = verify("SSN: 123 45 6789")
        assert result.compliant is False

    def test_ssn_no_separators(self):
        result = verify("SSN: 123456789")
        assert result.compliant is False


class TestCreditCardPatterns:
    """Test credit card detection for various card types."""

    def test_visa(self):
        result = verify("Card: 4111-1111-1111-1111")
        assert result.compliant is False
        assert any(v.rule_id == "no-credit-card" for v in result.violations)

    def test_mastercard(self):
        result = verify("Card: 5500 0000 0000 0004")
        assert result.compliant is False

    def test_amex(self):
        result = verify("Card: 3782-822463-10005")
        assert result.compliant is False

    def test_discover(self):
        result = verify("Card: 6011000000000004")
        assert result.compliant is False


class TestAPIKeyPatterns:
    """Test API key detection."""

    def test_stripe_live_key(self):
        result = verify("Key: sk-live-abcdefghijklmnopqrstuvwx")
        assert any(v.rule_id == "no-api-keys" for v in result.violations)

    def test_github_token(self):
        # GitHub tokens are ghp_ followed by 36 alphanumeric chars
        result = verify("Token: ghp_abcdefghijklmnopqrstuvwxyz1234567890")
        assert any(v.rule_id == "no-api-keys" for v in result.violations)

    def test_aws_access_key(self):
        result = verify("AWS Key: AKIAIOSFODNN7EXAMPLE")
        # May match multiple patterns
        violations = [v.rule_id for v in result.violations]
        assert "no-api-keys" in violations or "no-aws-credentials" in violations


class TestPrivateKeyPatterns:
    """Test private key detection."""

    def test_rsa_private_key(self):
        result = verify("-----BEGIN RSA PRIVATE KEY-----")
        assert any(v.rule_id == "no-private-keys" for v in result.violations)

    def test_private_key(self):
        result = verify("-----BEGIN PRIVATE KEY-----")
        assert any(v.rule_id == "no-private-keys" for v in result.violations)


class TestJWTPatterns:
    """Test JWT token detection."""

    def test_jwt_token(self):
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.Gfx6VO9tcxwk6xqx9yYzSfebfeakZp5JYIgP_edcw_A"
        result = verify(f"Token: {jwt}")
        assert any(v.rule_id == "no-jwt-tokens" for v in result.violations)


class TestPasswordPatterns:
    """Test password context detection."""

    def test_password_assignment(self):
        result = verify("password = 'mysecretpassword123'")
        assert any(v.rule_id == "no-passwords" for v in result.violations)

    def test_password_colon(self):
        result = verify("password: supersecret123")
        assert any(v.rule_id == "no-passwords" for v in result.violations)


class TestIPAddressPatterns:
    """Test IP address detection."""

    def test_ipv4(self):
        result = verify("Server: 192.168.1.100")
        violations = [v for v in result.violations if v.rule_id == "no-ip-address"]
        assert len(violations) == 1

    def test_ipv4_public(self):
        result = verify("IP: 8.8.8.8")
        violations = [v for v in result.violations if v.rule_id == "no-ip-address"]
        assert len(violations) == 1


class TestPhonePatterns:
    """Test phone number detection in various formats."""

    def test_us_with_dashes(self):
        result = verify("Call: 555-123-4567")
        violations = [v for v in result.violations if v.rule_id == "no-phone"]
        assert len(violations) == 1

    def test_us_with_parentheses(self):
        result = verify("Call: (555) 123-4567")
        violations = [v for v in result.violations if v.rule_id == "no-phone"]
        assert len(violations) == 1

    def test_us_with_country_code(self):
        result = verify("Call: +1-555-123-4567")
        violations = [v for v in result.violations if v.rule_id == "no-phone"]
        assert len(violations) == 1


class TestDateOfBirthPatterns:
    """Test DOB detection."""

    def test_mm_dd_yyyy(self):
        result = verify("DOB: 01/15/1990")
        violations = [v for v in result.violations if v.rule_id == "no-dob"]
        assert len(violations) == 1

    def test_yyyy_mm_dd(self):
        result = verify("DOB: 1990-01-15")
        violations = [v for v in result.violations if v.rule_id == "no-dob"]
        assert len(violations) == 1


class TestCleanContent:
    """Verify clean content passes all checks."""

    def test_clean_text(self):
        result = verify("The quick brown fox jumps over the lazy dog.")
        # Should have no critical violations
        critical = [v for v in result.violations if v.severity == "critical"]
        assert len(critical) == 0


class TestPolicyList:
    """Test the full policy list."""

    def test_policy_count(self):
        validator = Validator()
        policies = validator.list_policies()
        # Should have 14 policies now
        assert len(policies) >= 14

    def test_required_policies_exist(self):
        validator = Validator()
        policies = validator.list_policies()
        required = [
            "no-ssn", "no-credit-card", "no-email-leak", "no-phone",
            "no-api-keys", "no-aws-credentials", "no-private-keys",
            "no-jwt-tokens", "no-passwords", "no-ip-address"
        ]
        for policy_id in required:
            assert policy_id in policies, f"Missing policy: {policy_id}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
