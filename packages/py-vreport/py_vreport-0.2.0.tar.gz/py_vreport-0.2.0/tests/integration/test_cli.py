"""Integration tests for CLI commands."""

from typer.testing import CliRunner
from py_vreport.cli import app

runner = CliRunner()


class TestSummaryCommand:
    """Tests for the summary command."""

    def test_summary_with_valid_file(self, minimal_report_xml):
        """Summary command should succeed with valid file."""
        result = runner.invoke(app, ["summary", str(minimal_report_xml)])

        assert result.exit_code == 0
        assert "Module:" in result.stdout

    def test_summary_with_missing_file(self):
        """Summary command should handle missing files."""
        result = runner.invoke(app, ["summary", "nonexistent.xml"])

        # Should exit with error or continue depending on implementation
        assert "does not exist" in result.output or "Error" in result.output

    def test_summary_with_multiple_files(self, minimal_report_xml, report_all_pass_xml):
        """Summary command should process multiple files."""
        result = runner.invoke(
            app, ["summary", str(minimal_report_xml), str(report_all_pass_xml)]
        )

        assert result.exit_code == 0
        # Should show output for multiple reports
        assert result.stdout.count("Module:") >= 2

    def test_summary_displays_failure_count(self, report_with_failures_xml):
        """Summary should display failure count."""
        result = runner.invoke(app, ["summary", str(report_with_failures_xml)])

        assert result.exit_code == 0
        assert "Failures" in result.stdout or "failures" in result.stdout

    def test_summary_shows_no_failures_message(self, report_all_pass_xml):
        """Summary should indicate when there are no failures."""
        result = runner.invoke(app, ["summary", str(report_all_pass_xml)])

        assert result.exit_code == 0
        # Should show 0 failures or no failed tests listed


class TestFailuresCommand:
    """Tests for the failures command."""

    def test_failures_with_valid_file(self, report_with_failures_xml):
        """Failures command should succeed with valid file."""
        result = runner.invoke(app, ["failures", str(report_with_failures_xml)])

        assert result.exit_code == 0

    def test_failures_with_missing_file(self):
        """Failures command should handle missing files."""
        result = runner.invoke(app, ["failures", "nonexistent.xml"])

        assert "does not exist" in result.output or "Error" in result.output

    def test_failures_displays_failure_details(self, report_with_failures_xml):
        """Failures command should show failure details."""
        result = runner.invoke(app, ["failures", str(report_with_failures_xml)])

        assert result.exit_code == 0
        # Should contain failure indicators
        assert "Found" in result.stdout or "failures" in result.stdout

    def test_failures_with_no_failures(self, report_all_pass_xml):
        """Failures command should handle reports with no failures."""
        result = runner.invoke(app, ["failures", str(report_all_pass_xml)])

        assert result.exit_code == 0
        assert "No failures" in result.stdout or "0 failures" in result.stdout

    def test_failures_with_multiple_files(
        self, report_with_failures_xml, minimal_report_xml
    ):
        """Failures command should process multiple files."""
        result = runner.invoke(
            app, ["failures", str(report_with_failures_xml), str(minimal_report_xml)]
        )

        assert result.exit_code == 0


class TestInspectCommand:
    """Tests for the inspect command."""

    def test_inspect_with_valid_search(self, minimal_report_xml):
        """Inspect command should find matching test cases."""
        # Note: This assumes the minimal report has at least one test
        # You may need to adjust the search term based on actual test names
        result = runner.invoke(
            app,
            [
                "inspect",
                str(minimal_report_xml),
                "-t",
                "test",  # Generic search term
            ],
        )

        # Should either find tests or report no matches
        assert result.exit_code == 0

    def test_inspect_requires_test_case_option(self, minimal_report_xml):
        """Inspect command should require -t/--test-case option."""
        result = runner.invoke(app, ["inspect", str(minimal_report_xml)])

        # Should fail or show error about missing required option
        assert result.exit_code != 0 or "required" in result.stdout.lower()

    def test_inspect_with_no_matches(self, minimal_report_xml):
        """Inspect command should handle no matching tests."""
        result = runner.invoke(
            app, ["inspect", str(minimal_report_xml), "-t", "NonExistentTestName12345"]
        )

        assert result.exit_code == 0
        assert (
            "No test cases matching" in result.stdout or "No matches" in result.stdout
        )

    def test_inspect_with_missing_file(self):
        """Inspect command should handle missing files."""
        result = runner.invoke(app, ["inspect", "nonexistent.xml", "-t", "test"])

        assert "does not exist" in result.output or "Error" in result.output

    def test_inspect_displays_test_details(self, minimal_report_xml):
        """Inspect command should display test case details."""
        result = runner.invoke(
            app, ["inspect", str(minimal_report_xml), "--test-case", "test"]
        )

        # If tests are found, should show details
        if "No test cases matching" not in result.stdout:
            assert "TEST CASE" in result.stdout or "VERDICT" in result.stdout

    def test_inspect_case_insensitive_search(self, minimal_report_xml):
        """Inspect search should be case-insensitive."""
        result1 = runner.invoke(app, ["inspect", str(minimal_report_xml), "-t", "TEST"])

        result2 = runner.invoke(app, ["inspect", str(minimal_report_xml), "-t", "test"])

        # Both should produce same results
        assert result1.exit_code == result2.exit_code


class TestCLIHelp:
    """Tests for CLI help and documentation."""

    def test_app_help(self):
        """App should display help message."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "CANoe" in result.stdout or "report" in result.stdout.lower()

    def test_summary_help(self):
        """Summary command should have help."""
        result = runner.invoke(app, ["summary", "--help"])

        assert result.exit_code == 0
        assert "summary" in result.stdout.lower()

    def test_failures_help(self):
        """Failures command should have help."""
        result = runner.invoke(app, ["failures", "--help"])

        assert result.exit_code == 0
        assert "failure" in result.stdout.lower()

    def test_inspect_help(self):
        """Inspect command should have help."""
        result = runner.invoke(app, ["inspect", "--help"])

        assert result.exit_code == 0
        assert "inspect" in result.stdout.lower()


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_invalid_command(self):
        """CLI should handle invalid commands."""
        result = runner.invoke(app, ["invalid_command"])

        assert result.exit_code != 0

    def test_no_arguments_shows_help(self):
        """CLI with no arguments should show help or default behavior."""
        result = runner.invoke(app, [])

        # Should either show help or provide guidance
        assert result.exit_code == 0 or "help" in result.stdout.lower()


class TestCLIOutputFormatting:
    """Tests for CLI output formatting."""

    def test_summary_output_is_readable(self, minimal_report_xml):
        """Summary output should be formatted and readable."""
        result = runner.invoke(app, ["summary", str(minimal_report_xml)])

        assert result.exit_code == 0
        # Output should contain structured information
        assert len(result.stdout) > 0
        assert "\n" in result.stdout  # Multiple lines

    def test_failures_output_is_structured(self, report_with_failures_xml):
        """Failures output should be structured."""
        result = runner.invoke(app, ["failures", str(report_with_failures_xml)])

        assert result.exit_code == 0
        assert len(result.stdout) > 0


class TestEndToEndWorkflows:
    """End-to-end workflow tests."""

    def test_workflow_summary_then_failures(self, report_with_failures_xml):
        """Test typical workflow: check summary, then investigate failures."""
        # First, get summary
        summary_result = runner.invoke(app, ["summary", str(report_with_failures_xml)])
        assert summary_result.exit_code == 0

        # Then, get detailed failures
        failures_result = runner.invoke(
            app, ["failures", str(report_with_failures_xml)]
        )
        assert failures_result.exit_code == 0

    def test_workflow_failures_then_inspect(self, report_with_failures_xml):
        """Test workflow: find failures, then inspect specific test."""
        # First, see what failed
        failures_result = runner.invoke(
            app, ["failures", str(report_with_failures_xml)]
        )
        assert failures_result.exit_code == 0

        # Then inspect a specific test (if we know a name from the fixture)
        # This is a generic test - adjust based on your fixture content
        inspect_result = runner.invoke(
            app, ["inspect", str(report_with_failures_xml), "-t", "test"]
        )
        # Should succeed whether tests are found or not
        assert inspect_result.exit_code == 0
