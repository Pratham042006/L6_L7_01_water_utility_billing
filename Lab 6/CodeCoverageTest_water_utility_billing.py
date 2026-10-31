"""
CodeCoverageTest_water_utility_billing.py
Test suite designed to achieve full Line Coverage (Code Coverage >= 90%)
for water_utility_billing.py.
"""

import pytest
from water_utility_billing import calculate_water_bill, check_meter_tampering


def test_single_active_residential():
    """Baseline test: Single active residential account with tier 1 usage."""
    accounts = [
        {
            "is_active": True,
            "is_commercial": False,
            "has_leak_waiver": False,
            "usage_blocks": [30]
        }
    ]
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 55.0
    assert result["status"] == "NORMAL"


def test_invalid_accounts_type():
    """Test ValueError raised when accounts argument is not a list."""
    with pytest.raises(ValueError, match="Invalid accounts list or base fee"):
        calculate_water_bill("not_a_list", 10.0)


def test_inactive_account_skipped():
    """Test inactive account is skipped via continue."""
    accounts = [
        {
            "is_active": False,
            "usage_blocks": [50]
        }
    ]
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 0.0
    assert result["status"] == "NO_ACTIVITY"


def test_zero_or_negative_usage_flagged():
    """Test zero or negative usage triggers flagged count and continues."""
    accounts = [
        {
            "is_active": True,
            "usage_blocks": [0, -10, 20]
        }
    ]
    # base 10 + 20*1.5 = 40.0
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 40.0
    assert result["status"] == "NORMAL"


def test_residential_high_usage_break():
    """Test residential usage > 100 triggers 4.5 rate and break."""
    accounts = [
        {
            "is_active": True,
            "is_commercial": False,
            "usage_blocks": [120, 25]  # 25 should be skipped due to break
        }
    ]
    # base 10 + 120*4.5 = 10 + 540 = 550.0
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 550.0
    assert result["status"] == "NORMAL"


def test_commercial_high_usage():
    """Test commercial usage > 100 triggers 3.5 rate without break."""
    accounts = [
        {
            "is_active": True,
            "is_commercial": True,
            "usage_blocks": [110, 40]
        }
    ]
    # base 10 + 110*3.5 (385) + 40*1.5 (60) = 455.0
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 455.0
    assert result["status"] == "NORMAL"


def test_tier_two_usage():
    """Test usage between 50 and 100 triggers 2.5 rate."""
    accounts = [
        {
            "is_active": True,
            "usage_blocks": [80]
        }
    ]
    # base 10 + 80*2.5 = 210.0
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 210.0
    assert result["status"] == "NORMAL"


def test_leak_waiver_reduction():
    """Test leak waiver deduction when account total > 200."""
    accounts = [
        {
            "is_active": True,
            "has_leak_waiver": True,
            "usage_blocks": [80]  # total without waiver = 210.0
        }
    ]
    # 210.0 - 50.0 = 160.0
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 160.0
    assert result["status"] == "NORMAL"


def test_excessive_flags_status():
    """Test excessive flagged accounts status when flags > 5."""
    accounts = [
        {
            "is_active": True,
            "usage_blocks": [-1, -2, -3, -4, -5, -6]
        }
    ]
    result = calculate_water_bill(accounts, 10.0)
    assert result["total_billed"] == 10.0
    assert result["status"] == "EXCESSIVE_FLAGS"


def test_no_activity_empty_accounts():
    """Test no activity status when total billed is 0.0 with empty list."""
    result = calculate_water_bill([], 10.0)
    assert result["total_billed"] == 0.0
    assert result["status"] == "NO_ACTIVITY"


def test_meter_tampering_no_data():
    """Test check_meter_tampering with empty matrix returns NO_DATA."""
    assert check_meter_tampering([]) == "NO_DATA"


def test_meter_tampering_suspected():
    """Test check_meter_tampering with consecutive negative readings returns TAMPER_SUSPECTED."""
    readings = [[10, -5, -8, 2]]
    assert check_meter_tampering(readings) == "TAMPER_SUSPECTED"


def test_meter_tampering_clear():
    """Test check_meter_tampering with reset counter returns CLEAR."""
    readings = [[10, -5, 12, -4, 8]]
    assert check_meter_tampering(readings) == "CLEAR"
