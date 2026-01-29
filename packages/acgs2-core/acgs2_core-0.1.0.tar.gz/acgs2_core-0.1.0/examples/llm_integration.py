"""
LLM Integration Example

Constitutional Hash: cdd01ef066bc6cf2

This example shows how to integrate ACGS-2 Core with LLM applications
to verify AI outputs before returning to users.
"""

from acgs2_core import verify, Validator

# =============================================================================
# Example: LLM Response Wrapper
# =============================================================================

def get_verified_response(llm_output: str) -> dict:
    """
    Wrap LLM output with compliance verification.

    This is the pattern to use in production:
    1. Get response from your LLM (OpenAI, Anthropic, etc.)
    2. Verify with ACGS-2
    3. Only return if compliant, or handle violations

    Args:
        llm_output: The raw output from your LLM

    Returns:
        dict with response and verification metadata
    """
    result = verify(llm_output)

    if result.compliant:
        return {
            "response": llm_output,
            "verified": True,
            "proof_hash": result.proof_hash,
            "constitutional_anchor": result.constitutional_anchor,
        }
    else:
        # In production, you might:
        # - Log the violation
        # - Return a safe fallback response
        # - Re-generate with different prompt
        # - Alert the security team
        return {
            "response": "[CONTENT BLOCKED - COMPLIANCE VIOLATION]",
            "verified": False,
            "violations": [
                {
                    "rule": v.rule_id,
                    "severity": v.severity,
                    "description": v.description
                }
                for v in result.violations
            ],
            "proof_hash": result.proof_hash,
        }


# =============================================================================
# Simulated LLM Outputs
# =============================================================================

print("=" * 60)
print("LLM Integration Pattern Demo")
print("=" * 60)
print()

# Simulate clean LLM response
clean_response = "The capital of France is Paris. It's known for the Eiffel Tower."
print("Test 1: Clean LLM response")
print(f"  Input: {clean_response[:50]}...")
result = get_verified_response(clean_response)
print(f"  Verified: {result['verified']}")
print(f"  Proof: {result['proof_hash'][:16]}...")
print()

# Simulate LLM hallucination with PII
pii_response = "Sure! John's SSN is 123-45-6789 and his credit card is 4111-1111-1111-1111."
print("Test 2: LLM response with PII (hallucination)")
print(f"  Input: {pii_response[:50]}...")
result = get_verified_response(pii_response)
print(f"  Verified: {result['verified']}")
print(f"  Violations: {len(result.get('violations', []))}")
for v in result.get('violations', []):
    print(f"    - {v['rule']}: {v['severity']}")
print()


# =============================================================================
# FastAPI Integration Pattern (pseudocode)
# =============================================================================

print("=" * 60)
print("FastAPI Integration Pattern")
print("=" * 60)
print("""
# In your FastAPI app:

from fastapi import FastAPI, HTTPException
from acgs2_core import verify

app = FastAPI()

@app.post("/chat")
async def chat(message: str):
    # 1. Call your LLM
    llm_response = await call_openai(message)

    # 2. Verify compliance
    result = verify(llm_response)

    if not result.compliant:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "compliance_violation",
                "violations": [v.rule_id for v in result.violations]
            }
        )

    # 3. Return verified response with proof
    return {
        "response": llm_response,
        "proof_hash": result.proof_hash,
        "constitutional_anchor": result.constitutional_anchor
    }
""")

print("=" * 60)
print(f"Constitutional Hash: cdd01ef066bc6cf2")
print("=" * 60)
