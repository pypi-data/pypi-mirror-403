"""Unit tests for the CANoe report parser."""

import pytest
from pathlib import Path
from py_vreport.parser import CanoeReportParser


class TestCanoeReportParserInit:
    """Tests for parser initialization."""

    def test_init_with_valid_file(self, minimal_report_xml):
        """Parser should initialize with valid file path."""
        parser = CanoeReportParser(str(minimal_report_xml))
        assert parser.file_path == minimal_report_xml

    def test_init_with_missing_file(self):
        """Parser should raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError, match="does not exist"):
            CanoeReportParser("nonexistent.xml")

    def test_init_converts_string_to_path(self, minimal_report_xml):
        """Parser should convert string paths to Path objects."""
        parser = CanoeReportParser(str(minimal_report_xml))
        assert isinstance(parser.file_path, Path)


class TestCanoeReportParserParse:
    """Tests for the main parse method."""

    def test_parse_returns_test_module(self, minimal_report_xml):
        """Parse should return a TestModule object."""
        parser = CanoeReportParser(str(minimal_report_xml))
        report = parser.parse()

        assert report is not None
        assert hasattr(report, "name")
        assert hasattr(report, "root_groups")

    def test_parse_extracts_module_name(self, minimal_report_xml):
        """Parse should extract the test module name."""
        parser = CanoeReportParser(str(minimal_report_xml))
        report = parser.parse()

        assert report.name is not None
        assert isinstance(report.name, str)

    def test_parse_extracts_start_time(self, minimal_report_xml):
        """Parse should extract the start time."""
        parser = CanoeReportParser(str(minimal_report_xml))
        report = parser.parse()

        assert report.start_time is not None
        assert isinstance(report.start_time, str)

    def test_parse_stores_file_path(self, minimal_report_xml):
        """Parse should store the file path in the report."""
        parser = CanoeReportParser(str(minimal_report_xml))
        report = parser.parse()

        assert report.file_path == str(minimal_report_xml)

    def test_parse_invalid_xml(self, malformed_xml):
        """Parse should raise ValueError for malformed XML."""
        parser = CanoeReportParser(str(malformed_xml))
        with pytest.raises(ValueError, match="Failed to parse XML"):
            parser.parse()

    def test_parse_empty_report(self, report_empty_xml):
        """Parse should handle reports with no tests."""
        parser = CanoeReportParser(str(report_empty_xml))
        report = parser.parse()

        assert report is not None
        assert len(report.root_groups) == 0


class TestParseTestGroups:
    """Tests for parsing test groups."""

    def test_parse_creates_test_groups(self, minimal_report_xml):
        """Parse should create test groups from XML."""
        parser = CanoeReportParser(str(minimal_report_xml))
        report = parser.parse()

        assert len(report.root_groups) > 0
        assert all(hasattr(g, "title") for g in report.root_groups)

    def test_parse_nested_groups(self, report_nested_groups_xml):
        """Parse should handle nested test groups."""
        parser = CanoeReportParser(str(report_nested_groups_xml))
        report = parser.parse()

        # Check for nested structure
        for group in report.root_groups:
            if group.groups:
                assert len(group.groups) > 0
                assert all(hasattr(g, "title") for g in group.groups)

    def test_parse_group_titles(self, minimal_report_xml):
        """Parse should extract group titles."""
        parser = CanoeReportParser(str(minimal_report_xml))
        report = parser.parse()

        for group in report.root_groups:
            assert group.title is not None
            assert isinstance(group.title, str)
            assert len(group.title) > 0


class TestParseTestCases:
    """Tests for parsing test cases."""

    def test_parse_extracts_test_cases(self, minimal_report_xml):
        """Parse should extract test cases from groups."""
        parser = CanoeReportParser(str(minimal_report_xml))
        report = parser.parse()

        all_cases = []
        for group in report.root_groups:
            all_cases.extend(group.get_all_test_cases())

        assert len(all_cases) > 0

    def test_parse_test_case_has_required_fields(self, minimal_report_xml):
        """Test cases should have all required fields."""
        parser = CanoeReportParser(str(minimal_report_xml))
        report = parser.parse()

        cases = report.root_groups[0].get_all_test_cases()
        for case in cases:
            assert hasattr(case, "title")
            assert hasattr(case, "verdict")
            assert hasattr(case, "start_time")
            assert hasattr(case, "end_time")
            assert case.end_time >= case.start_time

    def test_parse_identifies_failures(self, report_with_failures_xml):
        """Parse should correctly identify failed tests."""
        parser = CanoeReportParser(str(report_with_failures_xml))
        report = parser.parse()

        failures = report.get_all_failures()
        assert len(failures) > 0
        assert all(case.is_failed() for case in failures)

    def test_parse_identifies_passes(self, report_all_pass_xml):
        """Parse should correctly identify passed tests."""
        parser = CanoeReportParser(str(report_all_pass_xml))
        report = parser.parse()

        all_cases = []
        for group in report.root_groups:
            all_cases.extend(group.get_all_test_cases())

        assert all(case.verdict.lower() == "pass" for case in all_cases)

    def test_parse_skipped_tests(self, report_skipped_tests_xml):
        """Parse should handle skipped tests."""
        parser = CanoeReportParser(str(report_skipped_tests_xml))
        report = parser.parse()

        all_cases = []
        for group in report.root_groups:
            all_cases.extend(group.get_all_test_cases())

        skipped = [c for c in all_cases if c.verdict.lower() == "skipped"]
        assert len(skipped) > 0


class TestParseTestSteps:
    """Tests for parsing test steps."""

    def test_parse_extracts_test_steps(self, minimal_report_xml):
        """Parse should extract test steps from test cases."""
        parser = CanoeReportParser(str(minimal_report_xml))
        report = parser.parse()

        cases = report.root_groups[0].get_all_test_cases()
        for case in cases:
            if case.steps:
                assert len(case.steps) > 0
                break

    def test_parse_step_has_required_fields(self, minimal_report_xml):
        """Test steps should have all required fields."""
        parser = CanoeReportParser(str(minimal_report_xml))
        report = parser.parse()

        cases = report.root_groups[0].get_all_test_cases()
        for case in cases:
            for step in case.steps:
                assert hasattr(step, "timestamp")
                assert hasattr(step, "result")
                assert hasattr(step, "level")
                assert isinstance(step.timestamp, float)
                assert isinstance(step.level, int)


class TestParseDiagnosticData:
    """Tests for parsing diagnostic tables."""

    def test_parse_extracts_diagnostic_tables(self, report_with_diagnostics_xml):
        """Parse should extract diagnostic data from test steps."""
        parser = CanoeReportParser(str(report_with_diagnostics_xml))
        report = parser.parse()

        failures = report.get_all_failures()
        assert len(failures) > 0

        # Find a failure with diagnostic data
        has_diagnostics = False
        for failure in failures:
            for step in failure.steps:
                if step.diagnostic_data:
                    has_diagnostics = True
                    assert len(step.diagnostic_data) > 0
                    break

        assert has_diagnostics, "No diagnostic data found in report"

    def test_diagnostic_data_structure(self, report_with_diagnostics_xml):
        """Diagnostic data should have correct structure."""
        parser = CanoeReportParser(str(report_with_diagnostics_xml))
        report = parser.parse()

        failures = report.get_all_failures()
        for failure in failures:
            for step in failure.steps:
                for diag in step.diagnostic_data:
                    assert "parameter" in diag
                    assert "value" in diag
                    assert "raw" in diag


class TestParseFailureContext:
    """Tests for parsing failure context."""

    def test_parse_extracts_failure_context(self, report_with_failures_xml):
        """Parse should extract rich failure context."""
        parser = CanoeReportParser(str(report_with_failures_xml))
        report = parser.parse()

        failures = report.get_all_failures()
        assert len(failures) > 0

        for failure in failures:
            assert failure.rich_failure is not None
            if failure.rich_failure:
                assert len(failure.rich_failure) > 0

    def test_failure_context_has_message(self, report_with_failures_xml):
        """Failure context should have error message."""
        parser = CanoeReportParser(str(report_with_failures_xml))
        report = parser.parse()

        failures = report.get_all_failures()
        for failure in failures:
            for ctx in failure.rich_failure:
                assert ctx.message is not None
                assert isinstance(ctx.message, str)
                assert len(ctx.message) > 0

    def test_failure_context_has_logs(self, report_with_failures_xml):
        """Failure context should capture context logs."""
        parser = CanoeReportParser(str(report_with_failures_xml))
        report = parser.parse()

        failures = report.get_all_failures()
        has_logs = False
        for failure in failures:
            for ctx in failure.rich_failure:
                if ctx.context_logs:
                    has_logs = True
                    assert isinstance(ctx.context_logs, list)
                    assert all(isinstance(log, str) for log in ctx.context_logs)

        assert has_logs, "No context logs found in failures"

    def test_legacy_failure_reason(self, report_with_failures_xml):
        """Parse should set legacy failure_reason field."""
        parser = CanoeReportParser(str(report_with_failures_xml))
        report = parser.parse()

        failures = report.get_all_failures()
        for failure in failures:
            assert failure.failure_reason is not None
            assert isinstance(failure.failure_reason, str)
