"""
BranchCoverageTest_water_utility_billing.py
Comprehensive test suite targeting 100% Branch Coverage and 100% Code Coverage
for water_utility_billing.py.
"""

import pytest
from water_utility_billing import calculate_water_bill, check_meter_tampering


# ============================================================================
# Tests for calculate_water_bill()
# ============================================================================

def test_invalid_accounts_not_a_list():
    """Branch: not isinstance(accounts, list) is True."""
    with pytest.raises(ValueError, match="Invalid accounts list or base fee"):
        calculate_water_bill("invalid_type", 10.0)


def test_invalid_negative_base_fee():
    """Branch: accounts is list, but base_fee < 0 is True."""
    with pytest.raises(ValueError, match="Invalid accounts list or base fee"):
        calculate_water_bill([], -5.0)


def test_empty_accounts_list_no_activity():
    """Branch: accounts loop does not run (empty list); total_billed == 0.0 -> NO_ACTIVITY."""
    result = calculate_water_bill([], 15.0)
    assert result["total_billed"] == 0.0
    assert result["status"] == "NO_ACTIVITY"


def test_inactive_account_continue_branch():
    """Branch: not account.get('is_active') is True -> continue statement."""
    accounts = [
        {"is_active": False, "usage_blocks": [50]},
        {"usage_blocks": [30]}  # Missing is_active defaults to False
    ]
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 0.0
    assert result["status"] == "NO_ACTIVITY"


def test_active_account_empty_usage_blocks():
    """Branch: active account with empty usage_blocks list (inner loop skipped)."""
    accounts = [
        {
            "is_active": True,
            "usage_blocks": []
        }
    ]
    result = calculate_water_bill(accounts, 25.0)
    assert result["total_billed"] == 25.0
    assert result["status"] == "NORMAL"


def test_usage_zero_and_negative_flags():
    """Branch: usage <= 0 is True (both zero and negative values trigger flagged_accounts and continue)."""
    accounts = [
        {
            "is_active": True,
            "usage_blocks": [0, -15, 20]
        }
    ]
    # base 10 + 20*1.5 = 40.0
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 40.0
    assert result["status"] == "NORMAL"


def test_residential_tier1_low_usage():
    """Branch: usage <= 50 (else branch in tiered rates: usage * 1.5)."""
    accounts = [
        {
            "is_active": True,
            "is_commercial": False,
            "usage_blocks": [30]
        }
    ]
    # base 10 + 30*1.5 = 55.0
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 55.0
    assert result["status"] == "NORMAL"


def test_residential_tier2_medium_usage():
    """Branch: usage > 50 and <= 100 (elif branch: usage * 2.5)."""
    accounts = [
        {
            "is_active": True,
            "is_commercial": False,
            "usage_blocks": [75]
        }
    ]
    # base 10 + 75*2.5 = 197.5
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 197.5
    assert result["status"] == "NORMAL"


def test_residential_high_usage_break_branch():
    """Branch: usage > 100 and not is_commercial is True -> rate 4.5 and break."""
    accounts = [
        {
            "is_active": True,
            "is_commercial": False,
            "usage_blocks": [120, 40]  # block 40 must NOT be billed because residential breaks
        }
    ]
    # base 10 + 120*4.5 = 550.0
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 550.0
    assert result["status"] == "NORMAL"


def test_commercial_high_usage_no_break_branch():
    """Branch: usage > 100 and not is_commercial is False -> rate 3.5 and NO break."""
    accounts = [
        {
            "is_active": True,
            "is_commercial": True,
            "usage_blocks": [110, 40]  # block 40 MUST be billed because commercial continues
        }
    ]
    # base 10 + 110*3.5 (385) + 40*1.5 (60) = 455.0
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 455.0
    assert result["status"] == "NORMAL"


def test_leak_waiver_applied_when_exceeding_200():
    """Branch: has_leak_waiver is True AND acct_total > 200.0 is True -> deducts 50.0."""
    accounts = [
        {
            "is_active": True,
            "has_leak_waiver": True,
            "usage_blocks": [90]  # base 10 + 90*2.5 = 235.0 > 200.0
        }
    ]
    # 235.0 - 50.0 = 185.0
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 185.0
    assert result["status"] == "NORMAL"


def test_leak_waiver_not_applied_when_not_exceeding_200():
    """Branch: has_leak_waiver is True BUT acct_total <= 200.0 is True -> no deduction (covers 33->36)."""
    accounts = [
        {
            "is_active": True,
            "has_leak_waiver": True,
            "usage_blocks": [30]  # base 10 + 30*1.5 = 55.0 <= 200.0
        }
    ]
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 55.0
    assert result["status"] == "NORMAL"


def test_excessive_flags_status():
    """Branch: flagged_accounts > 5 is True -> EXCESSIVE_FLAGS."""
    accounts = [
        {
            "is_active": True,
            "usage_blocks": [-1, -2, -3, -4, -5, -6]  # 6 flags
        }
    ]
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 10.0
    assert result["status"] == "EXCESSIVE_FLAGS"


def test_zero_total_billed_no_activity_status():
    """Branch: flagged_accounts <= 5 AND total_billed == 0.0 -> NO_ACTIVITY."""
    accounts = [
        {
            "is_active": True,
            "usage_blocks": []
        }
    ]
    result = calculate_water_bill(accounts, 0.0)
    assert result["total_billed"] == 0.0
    assert result["status"] == "NO_ACTIVITY"


# ============================================================================
# Tests for check_meter_tampering()
# ============================================================================

def test_tampering_no_data_empty_or_none():
    """Branch: not readings_matrix is True for empty list and None."""
    assert check_meter_tampering([]) == "NO_DATA"
    assert check_meter_tampering(None) == "NO_DATA"


def test_tampering_suspected_consecutive_negative_flow():
    """Branch: delta < 0 twice in succession -> backward_flow_count >= 2 -> TAMPER_SUSPECTED."""
    matrix = [[5, -3, -4, 2]]
    assert check_meter_tampering(matrix) == "TAMPER_SUSPECTED"


def test_tampering_single_negative_flow_reset_and_clear():
    """Branch: delta < 0 once (count=1 < 2), followed by positive delta resetting count -> CLEAR."""
    matrix = [[5, -3, 8, -2, 4]]
    assert check_meter_tampering(matrix) == "CLEAR"


def test_tampering_multiple_meters_tamper_on_subsequent_meter():
    """Branch: first meter is clear, second meter exhibits tampering."""
    matrix = [
        [1, 2, 3],
        [-2, -5, 1]
    ]
    assert check_meter_tampering(matrix) == "TAMPER_SUSPECTED"


def test_tampering_empty_meter_and_all_positive_clear():
    """Branch: meter with empty list and meter with strictly positive values -> CLEAR."""
    matrix = [[], [10, 20, 30]]
    assert check_meter_tampering(matrix) == "CLEAR"
