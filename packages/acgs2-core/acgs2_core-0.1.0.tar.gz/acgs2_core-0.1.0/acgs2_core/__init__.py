"""
ACGS-2 Core: Cryptographic AI Compliance Verification

Copyright (c) 2024-2025 ACGS-2 Project. All rights reserved.
Licensed under the MIT License. See LICENSE file for details.

Constitutional Hash: cdd01ef066bc6cf2

Verify any AI output is compliant in one line of code.

Usage:
    from acgs2_core import verify
    result = verify("AI generated content here")
    print(result.compliant)  # True
    print(result.proof_hash)  # cdd01ef066bc6cf2...
"""

from .validator import verify, Validator
from .result import VerificationResult
from .policy import Policy, PolicyType, PolicyEngine
from .hash import constitutional_hash, CONSTITUTIONAL_HASH

__version__ = "0.1.0"
__author__ = "ACGS-2 Team"
__license__ = "MIT"

__all__ = [
    "verify",
    "Validator",
    "VerificationResult",
    "Policy",
    "PolicyType",
    "PolicyEngine",
    "constitutional_hash",
    "CONSTITUTIONAL_HASH",
]
