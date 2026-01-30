"""Snapshot tests for formatter output."""

from io import StringIO
from rich.console import Console
from py_vreport.formatters import SummaryFormatter, FailureFormatter, DetailedFormatter
from py_vreport.models import TestModule, TestGroup, TestCase, TestStep, FailureContext


def capture_console_output(func, *args, **kwargs):
    """Capture Rich console output to string."""
    buffer = StringIO()
    console = Console(
        file=buffer,
        force_terminal=True,
        width=80,
        legacy_windows=False,
        force_jupyter=False,
    )

    # Call the function with our console
    func(*args, console=console, **kwargs)

    return buffer.getvalue()


class TestSummaryFormatterSnapshots:
    """Snapshot tests for SummaryFormatter."""

    def test_summary_minimal_report(self, snapshot, sample_test_module):
        """Test summary output for minimal report."""
        output = capture_console_output(
            SummaryFormatter.print_summary, sample_test_module
        )

        assert output == snapshot

    def test_summary_report_with_failures(self, snapshot):
        """Test summary output for report with failures."""
        # Create report with failures
        failed_case = TestCase(
            title="Check_DTC_Status",
            verdict="fail",
            start_time=100.0,
            end_time=105.0,
            failure_reason="Expected DTC 0x123456, got 0x000000",
        )

        passed_case = TestCase(
            title="Check_Voltage", verdict="pass", start_time=105.0, end_time=110.0
        )

        group = TestGroup(
            title="Diagnostic Tests", test_cases=[failed_case, passed_case]
        )

        module = TestModule(
            name="ECU_Diagnostics",
            file_path="/path/to/report.xml",
            start_time="2024-01-25T10:00:00",
            root_groups=[group],
        )

        output = capture_console_output(SummaryFormatter.print_summary, module)

        assert output == snapshot

    def test_summary_report_all_pass(self, snapshot):
        """Test summary output for report with all passing tests."""
        case1 = TestCase("Test 1", "pass", 100.0, 101.0)
        case2 = TestCase("Test 2", "pass", 101.0, 102.0)
        case3 = TestCase("Test 3", "pass", 102.0, 103.0)

        group = TestGroup(title="All Pass Group", test_cases=[case1, case2, case3])

        module = TestModule(
            name="Perfect_Module",
            file_path="/path/to/perfect.xml",
            start_time="2024-01-25T10:00:00",
            root_groups=[group],
        )

        output = capture_console_output(SummaryFormatter.print_summary, module)

        assert output == snapshot

    def test_summary_empty_report(self, snapshot):
        """Test summary output for empty report."""
        module = TestModule(
            name="Empty_Module",
            file_path="/path/to/empty.xml",
            start_time="2024-01-25T10:00:00",
            root_groups=[],
        )

        output = capture_console_output(SummaryFormatter.print_summary, module)

        assert output == snapshot


class TestFailureFormatterSnapshots:
    """Snapshot tests for FailureFormatter."""

    def test_failures_with_context_logs(self, snapshot):
        """Test failure output with context logs."""
        ctx = FailureContext(
            message="Expected DTC 0x123456, got 0x000000",
            context_logs=[
                "I-001: Starting diagnostic session",
                "I-002: Session changed to extended",
                "I-003: Reading DTC memory",
                "I-004: DTC request sent: 19 02 FF",
                "I-005: Response received: 59 02 00",
            ],
        )

        failed_case = TestCase(
            title="Check_DTC_Status",
            verdict="fail",
            start_time=100.0,
            end_time=105.0,
            failure_reason="DTC mismatch",
            rich_failure=[ctx],
        )

        group = TestGroup(title="DTC Tests", test_cases=[failed_case])

        module = TestModule(
            name="ECU_Diagnostics",
            file_path="/path/to/report.xml",
            start_time="2024-01-25T10:00:00",
            root_groups=[group],
        )

        output = capture_console_output(FailureFormatter.print_failures, module)

        assert output == snapshot

    def test_failures_with_diagnostic_table(self, snapshot):
        """Test failure output with diagnostic data table."""
        ctx = FailureContext(
            message="UDS request failed",
            context_logs=["Request: Read DTC"],
            diagnostic_table=[
                {"parameter": "Request", "value": "19 02 FF", "raw": "0x1902FF"},
                {
                    "parameter": "Expected",
                    "value": "59 02 01 23 45 67",
                    "raw": "0x5902012345",
                },
                {"parameter": "Actual", "value": "59 02 00", "raw": "0x590200"},
            ],
        )

        failed_case = TestCase(
            title="UDS_DTC_Read",
            verdict="fail",
            start_time=100.0,
            end_time=105.0,
            failure_reason="Response mismatch",
            rich_failure=[ctx],
        )

        group = TestGroup(title="UDS Tests", test_cases=[failed_case])

        module = TestModule(
            name="Diagnostics",
            file_path="/path/to/report.xml",
            start_time="2024-01-25T10:00:00",
            root_groups=[group],
        )

        output = capture_console_output(FailureFormatter.print_failures, module)

        assert output == snapshot

    def test_failures_no_failures(self, snapshot):
        """Test failure output when there are no failures."""
        passed_case = TestCase(
            title="Check_Voltage", verdict="pass", start_time=100.0, end_time=105.0
        )

        group = TestGroup(title="Tests", test_cases=[passed_case])

        module = TestModule(
            name="Module",
            file_path="/path/to/report.xml",
            start_time="2024-01-25T10:00:00",
            root_groups=[group],
        )

        output = capture_console_output(FailureFormatter.print_failures, module)

        assert output == snapshot

    def test_failures_multiple_failures(self, snapshot):
        """Test failure output with multiple failed tests."""
        ctx1 = FailureContext(
            message="Voltage out of range",
            context_logs=[
                "Measuring voltage",
                "Expected: 12.0V ± 0.5V",
                "Actual: 15.2V",
            ],
        )

        ctx2 = FailureContext(
            message="Timeout waiting for response",
            context_logs=[
                "Sending request",
                "Waiting for response...",
                "Timeout after 5s",
            ],
        )

        fail1 = TestCase(
            title="Check_Voltage_Range",
            verdict="fail",
            start_time=100.0,
            end_time=105.0,
            failure_reason="Voltage too high",
            rich_failure=[ctx1],
        )

        fail2 = TestCase(
            title="Check_ECU_Response",
            verdict="fail",
            start_time=105.0,
            end_time=115.0,
            failure_reason="No response",
            rich_failure=[ctx2],
        )

        group = TestGroup(title="System Tests", test_cases=[fail1, fail2])

        module = TestModule(
            name="System_Check",
            file_path="/path/to/report.xml",
            start_time="2024-01-25T10:00:00",
            root_groups=[group],
        )

        output = capture_console_output(FailureFormatter.print_failures, module)

        assert output == snapshot


class TestDetailedFormatterSnapshots:
    """Snapshot tests for DetailedFormatter."""

    def test_detailed_simple_test_case(self, snapshot):
        """Test detailed output for simple test case."""
        step1 = TestStep(
            timestamp=100.0,
            result="pass",
            level=0,
            type="user",
            ident="TS-001",
            description="Initialize test environment",
        )

        step2 = TestStep(
            timestamp=101.5,
            result="pass",
            level=1,
            type="auto",
            ident="TS-002",
            description="Check initial conditions",
        )

        case = TestCase(
            title="Simple_Test",
            verdict="pass",
            start_time=100.0,
            end_time=105.0,
            steps=[step1, step2],
        )

        output = capture_console_output(
            DetailedFormatter.print_test_case, "Test_Module", [case]
        )

        assert output == snapshot

    def test_detailed_test_case_with_failure(self, snapshot):
        """Test detailed output for test case with failure."""
        step1 = TestStep(
            timestamp=100.0,
            result="pass",
            level=0,
            type="user",
            ident="TS-001",
            description="Send request",
        )

        step2 = TestStep(
            timestamp=101.5,
            result="fail",
            level=0,
            type="auto",
            ident="TS-002",
            description="Verify response",
        )

        case = TestCase(
            title="Request_Response_Test",
            verdict="fail",
            start_time=100.0,
            end_time=102.0,
            steps=[step1, step2],
        )

        output = capture_console_output(
            DetailedFormatter.print_test_case, "Test_Module", [case]
        )

        assert output == snapshot

    def test_detailed_test_case_with_diagnostic_data(self, snapshot):
        """Test detailed output with diagnostic data."""
        step = TestStep(
            timestamp=100.0,
            result="fail",
            level=0,
            type="user",
            ident="TS-001",
            description="UDS Request",
            diagnostic_data=[
                {"parameter": "Request", "value": "22 F1 90", "raw": "0x22F190"},
                {
                    "parameter": "Expected",
                    "value": "62 F1 90 AB CD",
                    "raw": "0x62F190ABCD",
                },
                {"parameter": "Actual", "value": "7F 22 31", "raw": "0x7F2231"},
            ],
        )

        case = TestCase(
            title="UDS_Read_DID",
            verdict="fail",
            start_time=100.0,
            end_time=105.0,
            steps=[step],
        )

        output = capture_console_output(
            DetailedFormatter.print_test_case, "UDS_Tests", [case]
        )

        assert output == snapshot

    def test_detailed_nested_steps(self, snapshot):
        """Test detailed output with nested step levels."""
        steps = [
            TestStep(100.0, "pass", 0, "user", "TS-001", "Main step"),
            TestStep(100.5, "pass", 1, "auto", "TS-002", "Sub-step 1"),
            TestStep(101.0, "pass", 2, "auto", "TS-003", "Sub-sub-step"),
            TestStep(101.5, "pass", 1, "auto", "TS-004", "Sub-step 2"),
            TestStep(102.0, "pass", 0, "user", "TS-005", "Another main step"),
        ]

        case = TestCase(
            title="Nested_Test",
            verdict="pass",
            start_time=100.0,
            end_time=103.0,
            steps=steps,
        )

        output = capture_console_output(
            DetailedFormatter.print_test_case, "Test_Module", [case]
        )

        assert output == snapshot
