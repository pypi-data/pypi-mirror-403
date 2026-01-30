"""Unit tests for data models."""

from py_vreport.models import TestStep, FailureContext, TestCase, TestGroup, TestModule


class TestTestStep:
    """Tests for TestStep model."""

    def test_create_test_step(self):
        """Should create TestStep with required fields."""
        step = TestStep(timestamp=123.456, result="pass", level=0, type="user")

        assert step.timestamp == 123.456
        assert step.result == "pass"
        assert step.level == 0
        assert step.type == "user"

    def test_test_step_with_optional_fields(self):
        """Should create TestStep with optional fields."""
        step = TestStep(
            timestamp=123.456,
            result="pass",
            level=0,
            type="user",
            ident="TS-001",
            description="Check voltage",
            diagnostic_data=[{"param": "voltage", "value": "12V"}],
        )

        assert step.ident == "TS-001"
        assert step.description == "Check voltage"
        assert len(step.diagnostic_data) == 1


class TestFailureContext:
    """Tests for FailureContext model."""

    def test_create_failure_context(self):
        """Should create FailureContext with message."""
        ctx = FailureContext(message="Test failed")

        assert ctx.message == "Test failed"
        assert ctx.context_logs == []
        assert ctx.diagnostic_table == []

    def test_failure_context_with_logs(self):
        """Should create FailureContext with context logs."""
        ctx = FailureContext(message="DTC mismatch", context_logs=["Log 1", "Log 2"])

        assert len(ctx.context_logs) == 2
        assert ctx.context_logs[0] == "Log 1"

    def test_failure_context_with_diagnostic_table(self):
        """Should create FailureContext with diagnostic data."""
        ctx = FailureContext(
            message="Request failed",
            diagnostic_table=[
                {"parameter": "Request", "value": "19 02 FF", "raw": "0x1902FF"}
            ],
        )

        assert len(ctx.diagnostic_table) == 1
        assert ctx.diagnostic_table[0]["parameter"] == "Request"


class TestTestCase:
    """Tests for TestCase model."""

    def test_create_test_case(self):
        """Should create TestCase with required fields."""
        case = TestCase(
            title="Check_DTC", verdict="pass", start_time=100.0, end_time=105.0
        )

        assert case.title == "Check_DTC"
        assert case.verdict == "pass"
        assert case.start_time == 100.0
        assert case.end_time == 105.0

    def test_test_case_duration(self):
        """Duration property should calculate correctly."""
        case = TestCase(title="Test", verdict="pass", start_time=100.0, end_time=105.5)

        assert case.duration == 5.5

    def test_test_case_duration_zero(self):
        """Duration should be zero for same start/end time."""
        case = TestCase(title="Test", verdict="pass", start_time=100.0, end_time=100.0)

        assert case.duration == 0.0

    def test_is_failed_returns_true_for_fail(self):
        """is_failed() should return True for failed tests."""
        case = TestCase(title="Test", verdict="fail", start_time=100.0, end_time=105.0)

        assert case.is_failed() is True

    def test_is_failed_returns_true_for_fail_uppercase(self):
        """is_failed() should be case-insensitive."""
        case = TestCase(title="Test", verdict="FAIL", start_time=100.0, end_time=105.0)

        assert case.is_failed() is True

    def test_is_failed_returns_false_for_pass(self):
        """is_failed() should return False for passed tests."""
        case = TestCase(title="Test", verdict="pass", start_time=100.0, end_time=105.0)

        assert case.is_failed() is False

    def test_is_failed_returns_false_for_skipped(self):
        """is_failed() should return False for skipped tests."""
        case = TestCase(
            title="Test", verdict="skipped", start_time=100.0, end_time=105.0
        )

        assert case.is_failed() is False

    def test_to_dict_returns_correct_structure(self):
        """to_dict() should return dict with expected keys."""
        case = TestCase(
            title="Check_Voltage",
            verdict="fail",
            start_time=100.0,
            end_time=105.5,
            failure_reason="Voltage out of range",
        )

        result = case.to_dict()

        assert "title" in result
        assert "verdict" in result
        assert "duration" in result
        assert "failure_reason" in result
        assert "rich_failure_count" in result

        assert result["title"] == "Check_Voltage"
        assert result["verdict"] == "fail"
        assert result["duration"] == 5.5
        assert result["failure_reason"] == "Voltage out of range"

    def test_to_dict_includes_rich_failure_count(self):
        """to_dict() should count rich failures."""
        case = TestCase(
            title="Test",
            verdict="fail",
            start_time=100.0,
            end_time=105.0,
            rich_failure=[
                FailureContext(message="Error 1"),
                FailureContext(message="Error 2"),
            ],
        )

        result = case.to_dict()
        assert result["rich_failure_count"] == 2


class TestTestGroup:
    """Tests for TestGroup model."""

    def test_create_test_group(self):
        """Should create TestGroup with title."""
        group = TestGroup(title="DTC Tests")

        assert group.title == "DTC Tests"
        assert group.groups == []
        assert group.test_cases == []

    def test_get_all_test_cases_empty_group(self):
        """get_all_test_cases() should return empty list for empty group."""
        group = TestGroup(title="Empty Group")

        assert group.get_all_test_cases() == []

    def test_get_all_test_cases_flat_structure(self):
        """get_all_test_cases() should return all cases in flat group."""
        case1 = TestCase("Test 1", "pass", 0.0, 1.0)
        case2 = TestCase("Test 2", "pass", 1.0, 2.0)

        group = TestGroup(title="Group", test_cases=[case1, case2])

        cases = group.get_all_test_cases()
        assert len(cases) == 2
        assert case1 in cases
        assert case2 in cases

    def test_get_all_test_cases_nested_groups(self):
        """get_all_test_cases() should return cases from nested groups."""
        case1 = TestCase("Test 1", "pass", 0.0, 1.0)
        case2 = TestCase("Test 2", "pass", 1.0, 2.0)
        case3 = TestCase("Test 3", "pass", 2.0, 3.0)

        subgroup = TestGroup(title="Subgroup", test_cases=[case2, case3])
        parent = TestGroup(title="Parent", test_cases=[case1], groups=[subgroup])

        cases = parent.get_all_test_cases()
        assert len(cases) == 3
        assert case1 in cases
        assert case2 in cases
        assert case3 in cases

    def test_get_all_test_cases_deeply_nested(self):
        """get_all_test_cases() should handle deep nesting."""
        case1 = TestCase("Test 1", "pass", 0.0, 1.0)
        case2 = TestCase("Test 2", "pass", 1.0, 2.0)
        case3 = TestCase("Test 3", "pass", 2.0, 3.0)

        level2 = TestGroup(title="Level 2", test_cases=[case3])
        level1 = TestGroup(title="Level 1", test_cases=[case2], groups=[level2])
        root = TestGroup(title="Root", test_cases=[case1], groups=[level1])

        cases = root.get_all_test_cases()
        assert len(cases) == 3


class TestTestModule:
    """Tests for TestModule model."""

    def test_create_test_module(self):
        """Should create TestModule with required fields."""
        module = TestModule(
            name="ECU_Tests",
            file_path="/path/to/report.xml",
            start_time="2024-01-25T10:00:00",
        )

        assert module.name == "ECU_Tests"
        assert module.file_path == "/path/to/report.xml"
        assert module.start_time == "2024-01-25T10:00:00"
        assert module.root_groups == []

    def test_get_all_failures_empty_module(self):
        """get_all_failures() should return empty list for empty module."""
        module = TestModule(
            name="Empty", file_path="test.xml", start_time="2024-01-25T10:00:00"
        )

        assert module.get_all_failures() == []

    def test_get_all_failures_no_failures(self):
        """get_all_failures() should return empty list when all pass."""
        case1 = TestCase("Test 1", "pass", 0.0, 1.0)
        case2 = TestCase("Test 2", "pass", 1.0, 2.0)

        group = TestGroup(title="Group", test_cases=[case1, case2])
        module = TestModule(
            name="Module",
            file_path="test.xml",
            start_time="2024-01-25T10:00:00",
            root_groups=[group],
        )

        assert len(module.get_all_failures()) == 0

    def test_get_all_failures_with_failures(self):
        """get_all_failures() should return only failed tests."""
        case1 = TestCase("Test 1", "pass", 0.0, 1.0)
        case2 = TestCase("Test 2", "fail", 1.0, 2.0)
        case3 = TestCase("Test 3", "pass", 2.0, 3.0)
        case4 = TestCase("Test 4", "fail", 3.0, 4.0)

        group = TestGroup(title="Group", test_cases=[case1, case2, case3, case4])
        module = TestModule(
            name="Module",
            file_path="test.xml",
            start_time="2024-01-25T10:00:00",
            root_groups=[group],
        )

        failures = module.get_all_failures()
        assert len(failures) == 2
        assert case2 in failures
        assert case4 in failures

    def test_get_all_failures_across_groups(self):
        """get_all_failures() should find failures in all groups."""
        case1 = TestCase("Test 1", "fail", 0.0, 1.0)
        case2 = TestCase("Test 2", "pass", 1.0, 2.0)
        case3 = TestCase("Test 3", "fail", 2.0, 3.0)

        group1 = TestGroup(title="Group 1", test_cases=[case1])
        group2 = TestGroup(title="Group 2", test_cases=[case2, case3])

        module = TestModule(
            name="Module",
            file_path="test.xml",
            start_time="2024-01-25T10:00:00",
            root_groups=[group1, group2],
        )

        failures = module.get_all_failures()
        assert len(failures) == 2
        assert case1 in failures
        assert case3 in failures

    def test_to_pandas_returns_dataframe(self):
        """to_pandas() should return pandas DataFrame."""
        case1 = TestCase("Test 1", "pass", 0.0, 1.0)
        case2 = TestCase("Test 2", "fail", 1.0, 2.0)

        group = TestGroup(title="Group", test_cases=[case1, case2])
        module = TestModule(
            name="Module",
            file_path="test.xml",
            start_time="2024-01-25T10:00:00",
            root_groups=[group],
        )

        df = module.to_pandas()

        assert len(df) == 2
        assert "title" in df.columns
        assert "verdict" in df.columns
        assert "duration" in df.columns
        assert "module_name" in df.columns
        assert "group" in df.columns

    def test_to_pandas_includes_module_and_group_info(self):
        """to_pandas() should include module name and group title."""
        case = TestCase("Test 1", "pass", 0.0, 1.0)
        group = TestGroup(title="Test Group", test_cases=[case])
        module = TestModule(
            name="Test Module",
            file_path="test.xml",
            start_time="2024-01-25T10:00:00",
            root_groups=[group],
        )

        df = module.to_pandas()

        assert df.iloc[0]["module_name"] == "Test Module"
        assert df.iloc[0]["group"] == "Test Group"
