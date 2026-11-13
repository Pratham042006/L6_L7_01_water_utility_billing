"""
test_processor.py
Hypothesis Property-Based Fuzz Testing Suite for Water Utility Billing Input Processor.
Exposes, catches, and categorizes unexpected exceptions, malformed delimiter crashes, and null input errors.
"""

from hypothesis import given, strategies as st
from unittest.mock import patch
import runpy
import sys
import os
from processor import sanitize_meter_id, parse_consumption_readings, format_billing_summary, main

# Strategies for combined valid and arbitrary inputs
valid_readings = st.lists(
    st.integers(min_value=-10000, max_value=10000), min_size=1, max_size=10
).map(lambda l: ",".join(map(str, l)))

valid_records = st.tuples(
    st.text(
        alphabet=st.characters(blacklist_categories=('Cs',), blacklist_characters=':'),
        min_size=1,
        max_size=30
    ).filter(lambda x: x.strip() != ""),
    st.integers(min_value=0, max_value=100000),
    st.text(
        alphabet=st.characters(blacklist_categories=('Cs',), blacklist_characters=':'),
        min_size=1,
        max_size=30
    ).filter(lambda x: x.strip() != "")
).map(lambda t: f"{t[0]}:{t[1]}:{t[2]}")


# ============================================================================
# Core Fuzz Testing Functions (Catching unhandled null & malformed inputs)
# ============================================================================

@given(st.text() | st.none())
def test_sanitize_meter_id_no_crash(s):
    """
    Fuzz test for sanitize_meter_id with arbitrary text and None.
    Catches AttributeError when s is None, and validates symbol removal on valid strings.
    """
    try:
        result = sanitize_meter_id(s)
        assert isinstance(result, str)
        assert not any(ch in result for ch in ['!', '@', '#', '$', '%'])
        assert result == result.upper()
    except (AttributeError, TypeError):
        # Expected exception when s is None (NoneType has no attribute 'strip')
        assert s is None or not isinstance(s, str)


@given(valid_readings | st.text() | st.none())
def test_parse_consumption_readings_safe(s):
    """
    Fuzz test for parse_consumption_readings with valid CSV, random text, and None.
    Catches AttributeError on null and ValueError on invalid integer tokens.
    """
    try:
        result = parse_consumption_readings(s)
        assert isinstance(result, list)
        assert all(isinstance(x, int) for x in result)
    except (ValueError, AttributeError, TypeError):
        # Expected exception when s is None or tokens cannot be parsed to integer
        pass


@given(valid_records | st.text() | st.none())
def test_format_billing_summary_safe(s):
    """
    Fuzz test for format_billing_summary with valid records, arbitrary text, and None.
    Catches IndexError on missing delimiters, ValueError on non-integer usage, and AttributeError on null.
    """
    try:
        result = format_billing_summary(s)
        assert isinstance(result, str)
        assert "Customer " in result
        assert " billed " in result
        assert " USD in " in result
    except (IndexError, ValueError, AttributeError, TypeError):
        # Expected exception when delimiter missing or units not int or input is None
        pass


# ============================================================================
# Invariant & Round-Trip Property-Based Tests
# ============================================================================

@given(st.text(alphabet=st.characters(blacklist_categories=('Cs',), blacklist_characters='!@#$%')))
def test_sanitize_meter_id_clean_input(s):
    """When input has no special characters, sanitize should strip whitespace and uppercase."""
    result = sanitize_meter_id(s)
    assert result == s.strip().upper()


@given(st.lists(st.integers(min_value=-1000000, max_value=1000000), min_size=1, max_size=50))
def test_parse_consumption_readings_roundtrip(integers):
    """Valid comma-separated integers should parse accurately back to the original integer list."""
    csv_str = ",".join(map(str, integers))
    result = parse_consumption_readings(csv_str)
    assert result == integers


@given(
    customer_name=st.text(min_size=1, max_size=30).filter(lambda x: ":" not in x and x.strip() != ""),
    units=st.integers(min_value=0, max_value=100000),
    zone=st.text(min_size=1, max_size=20).filter(lambda x: ":" not in x and x.strip() != "")
)
def test_format_billing_summary_valid_record(customer_name, units, zone):
    """Valid Name:Units:Zone record correctly computes units * 2 USD billing summary."""
    record = f"{customer_name}:{units}:{zone}"
    result = format_billing_summary(record)
    expected = f"Customer {customer_name.strip()} billed {units * 2} USD in {zone.strip()}"
    assert result == expected


# ============================================================================
# Interactive CLI Pipeline Execution Tests
# ============================================================================

def test_main_cli_execution():
    """Verify main CLI pipeline executes correctly with interactive input prompts."""
    with patch("builtins.input", side_effect=["!@#MTR101$%", "10,25,30", "Alice:45:North"]), \
         patch("builtins.print") as mock_print:
        main()
        assert mock_print.call_count >= 6


def test_processor_main_module_execution():
    """Execute processor.py directly as __main__ to ensure complete execution coverage."""
    processor_path = os.path.join(os.path.dirname(__file__), "processor.py")
    with patch("builtins.input", side_effect=["!@#MTR999$%", "5,15", "Bob:20:South"]), \
         patch("builtins.print"):
        runpy.run_path(processor_path, run_name="__main__")
