# py_vreport Test Suite

This directory contains the test suite for py_vreport, organized into three main categories:

## 📁 Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── fixtures/                # Sample XML test data
│   ├── minimal_report.xml
│   ├── report_with_failures.xml
│   ├── report_with_diagnostics.xml
│   ├── report_all_pass.xml
│   ├── report_nested_groups.xml
│   ├── report_skipped_tests.xml
│   ├── report_empty.xml
│   └── malformed.xml
├── unit/                    # Unit tests (60%)
│   ├── test_parser.py       # Parser logic tests
│   └── test_models.py       # Data model tests
├── integration/             # Integration tests (20%)
│   └── test_cli.py          # CLI command tests
└── visual/                  # Snapshot tests (20%)
    └── test_formatters.py   # Formatter output tests
```

## 🚀 Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Visual/snapshot tests only
pytest tests/visual/
```

### Run Tests with Markers
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only visual tests
pytest -m visual

# Skip slow tests
pytest -m "not slow"
```

### Run Specific Test Files
```bash
# Test parser only
pytest tests/unit/test_parser.py

# Test models only
pytest tests/unit/test_models.py

# Test CLI only
pytest tests/integration/test_cli.py
```

### Run Specific Test Classes or Functions
```bash
# Specific test class
pytest tests/unit/test_parser.py::TestParseTestCases

# Specific test function
pytest tests/unit/test_parser.py::TestParseTestCases::test_parse_identifies_failures
```

## 📊 Coverage Reports

### Generate Coverage Report
```bash
# Terminal report
pytest --cov=py_vreport --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov=py_vreport --cov-report=html
open htmlcov/index.html
```

### Coverage Goals
- **Parser**: 90%+ (critical component)
- **Models**: 80%+ (mostly property methods)
- **CLI**: 70%+ (integration level)
- **Formatters**: 60%+ (visual output)

## 📸 Snapshot Testing

### Understanding Snapshots
Snapshot tests capture the output of formatters and compare against stored "golden" outputs.

### Updating Snapshots
When you intentionally change formatter output:

```bash
# Update all snapshots
pytest --snapshot-update

# Update specific snapshot file
pytest tests/visual/test_formatters.py --snapshot-update

# Review changes before updating
pytest tests/visual/test_formatters.py
# Review the diff, then:
pytest tests/visual/test_formatters.py --snapshot-update
```

### Snapshot Locations
Snapshots are stored in `tests/visual/__snapshots__/` and are committed to git.

## 🔧 Test Fixtures

### XML Fixtures
Located in `tests/fixtures/`, these are sample CANoe XML reports:

- **minimal_report.xml**: Smallest valid report (2 passing tests)
- **report_with_failures.xml**: Mixed pass/fail tests (2 failures)
- **report_with_diagnostics.xml**: Failures with UDS diagnostic tables
- **report_all_pass.xml**: All tests pass (3 tests)
- **report_nested_groups.xml**: Deep test group nesting
- **report_skipped_tests.xml**: Contains skipped tests
- **report_empty.xml**: No test cases
- **malformed.xml**: Invalid XML for error handling tests

### Pytest Fixtures
Defined in `conftest.py`:

- **File path fixtures**: `minimal_report_xml`, `report_with_failures_xml`, etc.
- **Parsed object fixtures**: `parsed_minimal_report`, `parsed_report_with_failures`, etc.
- **Model fixtures**: `sample_test_step`, `sample_test_case`, `sample_test_module`, etc.

## 📝 Writing Tests

### Unit Test Example
```python
def test_parse_extracts_module_name(minimal_report_xml):
    """Test that parser extracts the module name correctly."""
    parser = CanoeReportParser(str(minimal_report_xml))
    report = parser.parse()
    
    assert report.name == "Minimal Test Module"
```

### Integration Test Example
```python
def test_summary_command_with_valid_file(minimal_report_xml):
    """Test summary command with valid report file."""
    result = runner.invoke(app, ["summary", str(minimal_report_xml)])
    
    assert result.exit_code == 0
    assert "Module:" in result.stdout
```

### Snapshot Test Example
```python
def test_summary_output(snapshot, sample_test_module):
    """Test summary formatter output matches snapshot."""
    output = capture_console_output(
        SummaryFormatter.print_summary,
        sample_test_module
    )
    
    assert output == snapshot
```

## 🐛 Debugging Tests

### Run Tests in Verbose Mode
```bash
pytest -vv
```

### Show Print Statements
```bash
pytest -s
```

### Drop into Debugger on Failure
```bash
pytest --pdb
```

### Run Last Failed Tests
```bash
pytest --lf
```

### Run Tests Until Failure
```bash
pytest -x  # Stop on first failure
pytest --maxfail=3  # Stop after 3 failures
```

## 🎯 Test Guidelines

### Unit Tests Should:
- Test ONE thing per test
- Use descriptive names: `test_<what>_<condition>_<expected>`
- Be fast (< 0.1s each)
- Not depend on other tests
- Use fixtures for setup

### Integration Tests Should:
- Test complete workflows
- Verify CLI commands work end-to-end
- Test error handling and edge cases
- Check exit codes

### Snapshot Tests Should:
- Focus on visual output
- Be updated when format changes are intentional
- Have clear test names explaining what's being captured
- Use consistent console width (80 chars)

## 📈 Test Metrics

Target test counts:
- **Unit tests**: ~50 tests
- **Integration tests**: ~20 tests
- **Snapshot tests**: ~15 tests
- **Total**: ~85 tests

Target coverage:
- **Overall**: 75%+
- **Parser**: 90%+
- **Models**: 80%+

## 🔄 CI/CD Integration

Tests run automatically on:
- Every push to main
- Every pull request
- Pre-commit hooks (optional)

Required for merge:
- All tests pass
- Coverage doesn't decrease
- No snapshot changes without review

## 📚 Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [syrupy (snapshot testing)](https://github.com/tophat/syrupy)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Typer testing](https://typer.tiangolo.com/tutorial/testing/)