"""
indian_backtest.analytics.auditor_assert
========================================
Automated Standing Rule R-3 accounting identity and Rule R-6 reproducibility assertions.
"""

import hashlib

def assert_rule_r3_accounting_identity(acc_result: dict):
    """
    Standing Rule R-3:
        initial_capital + realized_pnl - tax + dividends + unrealized_pnl == final_value
    Asserts residual < 1e-6 (strictly 0.00).
    """
    res = acc_result.get("residual", 999.0)
    assert abs(res) < 1e-6, (
        f"Standing Rule R-3 VIOLATION: Accounting residual {res:.10f} != 0.00! "
        f"Initial: {acc_result.get('initial_capital')}, Realized: {acc_result.get('realized_pnl')}, "
        f"Unrealized: {acc_result.get('unrealized_pnl')}, Final: {acc_result.get('final_value')}"
    )

def assert_rule_r6_reproducibility(text_pass1: str, text_pass2: str):
    """
    Standing Rule R-6:
        Both runs must produce bit-for-bit identical output logs and matching SHA-256 digests.
    """
    hash1 = hashlib.sha256(text_pass1.encode("utf-8")).hexdigest()
    hash2 = hashlib.sha256(text_pass2.encode("utf-8")).hexdigest()
    assert hash1 == hash2, (
        f"Standing Rule R-6 VIOLATION: Execution logs differ across independent passes!\n"
        f"Pass 1 SHA-256: {hash1}\n"
        f"Pass 2 SHA-256: {hash2}"
    )
    return hash1
