# Lab 7: Property-Based Fuzz Testing with Hypothesis

**Student Name:** Pratham P Mudakavi  
**SRN:** PES2UG24CS369  
**Course:** Software Engineering (UE23CS351AA)  
**Assigned Module:** `L6_L7_01_water_utility_billing` — Input Processing & Parsing  
**Upstream Repository:** [SETAPESU26/L6_L7_01_water_utility_billing](https://github.com/SETAPESU26/L6_L7_01_water_utility_billing)  

---

## 1. Overview & Objectives

Property-based testing and fuzz testing with **Hypothesis** systematically explores the input space of functions with pseudo-randomly generated inputs to detect edge-case failures, unhandled exceptions, malformed delimiter crashes, and null input vulnerabilities.

In this laboratory exercise:
1. **Module Under Test (`processor.py`):** The input processing and parsing pipeline of the water utility billing system containing three core routines:
   - `sanitize_meter_id(meter_id)`: Cleans and uppercases meter IDs while removing unwanted characters (`!@#$%`).
   - `parse_consumption_readings(readings_csv)`: Parses comma-separated consumption readings into integer lists.
   - `format_billing_summary(account_record)`: Formats colon-delimited records (`Name:Units:Zone`) into human-readable billing strings.
2. **Fuzz Testing Suite (`test_processor.py` & `FuzzTest_PES2UG24CS369_processor.py`):** Completed using Hypothesis decorators (`@given`) and strategies (`st.text() | st.none()`), wrapped with defensive `try...except` exception handling to safely detect, catch, and categorize expected vs unexpected exceptions, while enforcing invariant properties on valid inputs.
3. **Property Verification & Round-Trip Invariants:** Additional property tests validating round-trip integer parsing, prefix cleaning, format preservation, and end-to-end CLI execution.

---

## 2. File Structure

```text
Lab 7/
├── processor.py                            # Module under test (water utility input processor)
├── test_processor.py                       # Hypothesis fuzz test suite (completed)
├── FuzzTest_PES2UG24CS369_processor.py     # SRN-tagged submission test suite
├── README.md                               # Lab 7 documentation & execution guide
└── reports/
    ├── Lab7_Fuzz_Testing_Report.pdf        # Formal laboratory report for Google Form submission
    ├── test_results_terminal.png           # Pytest verbose terminal execution screenshot
    ├── coverage_report_terminal.png        # 100% statement & branch coverage terminal screenshot
    ├── test_results.txt                    # Pytest verbose terminal execution log
    └── coverage_report.txt                 # Coverage report text log
```

---

## 3. Vulnerability & Fuzzing Failure Modes Analysis

When subjected to arbitrary generated inputs via `st.text() | st.none()`, the starter routines in `processor.py` expose several critical unhandled failure modes:

| Function Under Test | Malformed / Null Fuzz Input | Unhandled Exception | Root Cause Analysis | Defensive Handling in Test |
|---|---|---|---|---|
| `sanitize_meter_id(s)` | `None` | `AttributeError: 'NoneType' has no attribute 'strip'` | Direct method call on null without null-guard | Catch `AttributeError`/`TypeError`; assert input was null |
| `parse_consumption_readings(s)` | `None` | `AttributeError: 'NoneType' has no attribute 'split'` | Null CSV string passed to `.split(',')` | Catch `AttributeError`/`TypeError` |
| `parse_consumption_readings(s)` | `""`, `"abc"`, `"10,,20"` | `ValueError: invalid literal for int()` | Non-numeric or empty tokens cannot convert to `int` | Catch `ValueError`; assert valid integers parse correctly |
| `format_billing_summary(s)` | `None` | `AttributeError: 'NoneType' has no attribute 'split'` | Null record passed to `.split(':')` | Catch `AttributeError`/`TypeError` |
| `format_billing_summary(s)` | `"Alice"`, `"Bob:100"` (< 3 parts) | `IndexError: list index out of range` | Assumes exactly 3 colon-delimited tokens without length check | Catch `IndexError` when tokens < 3 |
| `format_billing_summary(s)` | `"Alice:NaN:North"` | `ValueError: invalid literal for int()` | Units token contains non-integer string | Catch `ValueError` during integer conversion |

---

## 4. Test Suite Implementation

The test suite (`test_processor.py`) implements:
1. **`test_sanitize_meter_id_no_crash(s)`:** Fuzzes with `st.text() | st.none()`. Confirms that valid strings never contain `!`, `@`, `#`, `$`, `%`, are always uppercase, and safely catches `AttributeError` when `s is None`.
2. **`test_parse_consumption_readings_safe(s)`:** Fuzzes with composite strategy `valid_readings | st.text() | st.none()`. Handles `ValueError`, `AttributeError`, and verifies valid integer sequences.
3. **`test_format_billing_summary_safe(s)`:** Fuzzes with `valid_records | st.text() | st.none()`. Verifies formatting tokens (`Customer `, ` billed `, ` USD in `) on valid inputs and catches `IndexError`/`ValueError` on malformed inputs.
4. **`test_sanitize_meter_id_clean_input(s)`:** Property test proving invariance of clean alphanumeric inputs (whitespace stripping & uppercasing).
5. **`test_parse_consumption_readings_roundtrip(integers)`:** Round-trip property test verifying `','.join(integers)` parses identically back to the original integer list.
6. **`test_format_billing_summary_valid_record(customer_name, units, zone)`:** Property test validating billing computation `units * 2 USD` for all valid records.
7. **`test_main_cli_execution()` & `test_processor_main_module_execution()`:** Complete pipeline tests exercising standard CLI input/output interactions.

---

## 5. Verification & Coverage Results

### Pytest Execution
```bash
pytest test_processor.py -v
```

```text
============================= test session starts ==============================
collected 8 items

test_processor.py::test_sanitize_meter_id_no_crash PASSED                [ 12%]
test_processor.py::test_parse_consumption_readings_safe PASSED           [ 25%]
test_processor.py::test_format_billing_summary_safe PASSED               [ 37%]
test_processor.py::test_sanitize_meter_id_clean_input PASSED             [ 50%]
test_processor.py::test_parse_consumption_readings_roundtrip PASSED      [ 62%]
test_processor.py::test_format_billing_summary_valid_record PASSED       [ 75%]
test_processor.py::test_main_cli_execution PASSED                        [ 87%]
test_processor.py::test_processor_main_module_execution PASSED           [100%]

============================== 8 passed in 0.37s ===============================
```

### Coverage Report
```bash
coverage run --branch -m pytest test_processor.py
coverage report -m
```

```text
Name                Stmts   Miss Branch BrPart  Cover   Missing
---------------------------------------------------------------
processor.py           29      0      4      0   100%
test_processor.py      58      0      0      0   100%
---------------------------------------------------------------
TOTAL                  87      0      4      0   100%
```

Both statement coverage and branch coverage achieved **100%** on the module under test and the test suite.
