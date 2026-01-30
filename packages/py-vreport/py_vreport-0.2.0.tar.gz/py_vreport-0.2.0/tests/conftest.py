"""Shared pytest fixtures for py_vreport tests."""

import pytest
from pathlib import Path
from py_vreport.parser import CanoeReportParser
from py_vreport.models import TestModule, TestGroup, TestCase, TestStep, FailureContext


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def minimal_report_xml(fixtures_dir):
    """Path to minimal valid CANoe report."""
    return fixtures_dir / "minimal_report.xml"


@pytest.fixture
def report_with_failures_xml(fixtures_dir):
    """Path to report containing failures."""
    return fixtures_dir / "report_with_failures.xml"


@pytest.fixture
def report_with_diagnostics_xml(fixtures_dir):
    """Path to report containing diagnostic tables."""
    return fixtures_dir / "report_with_diagnostics.xml"


@pytest.fixture
def report_all_pass_xml(fixtures_dir):
    """Path to report where all tests pass."""
    return fixtures_dir / "report_all_pass.xml"


@pytest.fixture
def report_nested_groups_xml(fixtures_dir):
    """Path to report with nested test groups."""
    return fixtures_dir / "report_nested_groups.xml"


@pytest.fixture
def report_skipped_tests_xml(fixtures_dir):
    """Path to report with skipped tests."""
    return fixtures_dir / "report_skipped_tests.xml"


@pytest.fixture
def report_empty_xml(fixtures_dir):
    """Path to report with no tests."""
    return fixtures_dir / "report_empty.xml"


@pytest.fixture
def malformed_xml(fixtures_dir):
    """Path to malformed XML file."""
    return fixtures_dir / "malformed.xml"


# Parsed report fixtures
@pytest.fixture
def parsed_minimal_report(minimal_report_xml):
    """Parsed minimal report object."""
    parser = CanoeReportParser(str(minimal_report_xml))
    return parser.parse()


@pytest.fixture
def parsed_report_with_failures(report_with_failures_xml):
    """Parsed report with failures."""
    parser = CanoeReportParser(str(report_with_failures_xml))
    return parser.parse()


@pytest.fixture
def parsed_report_with_diagnostics(report_with_diagnostics_xml):
    """Parsed report with diagnostic tables."""
    parser = CanoeReportParser(str(report_with_diagnostics_xml))
    return parser.parse()


@pytest.fixture
def parsed_report_all_pass(report_all_pass_xml):
    """Parsed report where all tests pass."""
    parser = CanoeReportParser(str(report_all_pass_xml))
    return parser.parse()


# Model fixtures for direct testing
@pytest.fixture
def sample_test_step():
    """Sample TestStep object."""
    return TestStep(
        timestamp=123.456,
        result="pass",
        level=0,
        type="user",
        ident="TS-001",
        description="Check voltage level",
        diagnostic_data=[{"parameter": "Voltage", "value": "12.5V", "raw": "0x7D"}],
    )


@pytest.fixture
def sample_failure_context():
    """Sample FailureContext object."""
    return FailureContext(
        message="Expected DTC 0x123456, got 0x000000",
        context_logs=[
            "I-001: Starting diagnostic session",
            "I-002: Reading DTC memory",
            "I-003: Request sent: 19 02 FF",
        ],
        diagnostic_table=[
            {"parameter": "Request", "value": "19 02 FF", "raw": "0x1902FF"},
            {"parameter": "Response", "value": "59 02 00", "raw": "0x590200"},
        ],
    )


@pytest.fixture
def sample_test_case(sample_test_step, sample_failure_context):
    """Sample TestCase object with failure."""
    return TestCase(
        title="Check_DTC_Status",
        verdict="fail",
        start_time=100.0,
        end_time=105.5,
        steps=[sample_test_step],
        failure_reason="DTC mismatch",
        rich_failure=[sample_failure_context],
    )


@pytest.fixture
def sample_test_group(sample_test_case):
    """Sample TestGroup object."""
    return TestGroup(title="DTC Tests", test_cases=[sample_test_case])


@pytest.fixture
def sample_test_module(sample_test_group):
    """Sample TestModule object."""
    return TestModule(
        name="ECU_Diagnostics",
        file_path="/path/to/report.xml",
        start_time="2024-01-25T10:00:00",
        root_groups=[sample_test_group],
    )
