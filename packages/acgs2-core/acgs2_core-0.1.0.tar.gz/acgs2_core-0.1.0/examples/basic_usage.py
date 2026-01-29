"""
Basic ACGS-2 Core Usage Examples

Constitutional Hash: cdd01ef066bc6cf2

This example demonstrates the simplest ways to use ACGS-2 Core
for AI compliance verification.
"""

from acgs2_core import verify, Validator, Policy, PolicyType

# =============================================================================
# Example 1: One-Line Verification
# =============================================================================

print("=" * 60)
print("Example 1: One-Line Verification")
print("=" * 60)

# The simplest way to verify AI output
result = verify("The weather today is sunny and 72°F.")

print(f"Content: 'The weather today is sunny and 72°F.'")
print(f"Compliant: {result.compliant}")
print(f"Proof Hash: {result.proof_hash[:16]}...")
print(f"Constitutional Anchor: {result.constitutional_anchor}")
print(f"Latency: {result.latency_ms:.2f}ms")
print()

# =============================================================================
# Example 2: Detecting PII (Personal Identifiable Information)
# =============================================================================

print("=" * 60)
print("Example 2: Detecting PII")
print("=" * 60)

# SSN detection
result_ssn = verify("Contact John at SSN 123-45-6789 for more info.")
print(f"Content with SSN:")
print(f"  Compliant: {result_ssn.compliant}")
print(f"  Violations: {len(result_ssn.violations)}")
if result_ssn.violations:
    v = result_ssn.violations[0]
    print(f"    - Rule: {v.rule_id}")
    print(f"    - Severity: {v.severity}")
print()

# Credit card detection
result_cc = verify("Please charge card 4111-1111-1111-1111")
print(f"Content with Credit Card:")
print(f"  Compliant: {result_cc.compliant}")
print(f"  Violations: {len(result_cc.violations)}")
if result_cc.violations:
    v = result_cc.violations[0]
    print(f"    - Rule: {v.rule_id}")
    print(f"    - Severity: {v.severity}")
print()

# =============================================================================
# Example 3: Custom Validator with Strict Mode
# =============================================================================

print("=" * 60)
print("Example 3: Custom Validator with Strict Mode")
print("=" * 60)

# Strict mode: any violation (regardless of severity) = non-compliant
validator = Validator(strict_mode=True)

result_strict = validator.verify("Contact us at test@example.com")
print(f"Content with email (strict mode):")
print(f"  Compliant: {result_strict.compliant}")
print(f"  Violations: {len(result_strict.violations)}")
print()

# Non-strict mode (default): only critical severity = non-compliant
validator_normal = Validator(strict_mode=False)
result_normal = validator_normal.verify("Contact us at test@example.com")
print(f"Content with email (normal mode):")
print(f"  Compliant: {result_normal.compliant}")  # True because email is high, not critical
print(f"  Violations: {len(result_normal.violations)}")
print()

# =============================================================================
# Example 4: Custom Policies
# =============================================================================

print("=" * 60)
print("Example 4: Custom Policies")
print("=" * 60)

# Create validator without default policies
custom_validator = Validator(include_default_policies=False)

# Add custom policy to block competitor mentions
custom_validator.add_policy(Policy(
    id="no-competitor",
    name="No Competitor Mentions",
    description="Prevent mentioning competitor names",
    policy_type=PolicyType.PATTERN,
    rule=r"\b(CompetitorX|RivalCorp)\b",
    severity="medium"
))

# Test the custom policy
result_competitor = custom_validator.verify("Our product is better than CompetitorX.")
print(f"Content mentioning competitor:")
print(f"  Compliant: {result_competitor.compliant}")
print(f"  Violations: {len(result_competitor.violations)}")
print()

# =============================================================================
# Example 5: Result Serialization
# =============================================================================

print("=" * 60)
print("Example 5: Result Serialization")
print("=" * 60)

result = verify("Clean AI output without any PII")
result_dict = result.to_dict()

print("Result as dictionary:")
for key in ['compliant', 'proof_hash', 'constitutional_anchor', 'timestamp', 'latency_ms']:
    value = result_dict[key]
    if key == 'proof_hash':
        value = f"{value[:16]}..."
    print(f"  {key}: {value}")
print()

# =============================================================================
# Example 6: Verification Statistics
# =============================================================================

print("=" * 60)
print("Example 6: Verification Statistics")
print("=" * 60)

stats_validator = Validator()
print(f"Initial verification count: {stats_validator.verification_count}")

# Run some verifications
for i in range(5):
    stats_validator.verify(f"Test content {i}")

print(f"After 5 verifications: {stats_validator.verification_count}")
print(f"Available policies: {stats_validator.list_policies()}")
print()

print("=" * 60)
print("All examples completed successfully!")
print(f"Constitutional Hash: cdd01ef066bc6cf2")
print("=" * 60)
