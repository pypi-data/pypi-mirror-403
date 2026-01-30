# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


### Added
- Initial release of **py_vreport**
- Modern CLI using Typer and Rich
- Fast XML parsing for Vector CANoe reports
- Detailed failure analysis with context logs
- UDS diagnostic data extraction and display
- Comprehensive test suite with 90%+ coverage
- Multi-file report processing support

## v0.2.0 (2026-01-25)

### Feat

- implement comprehensive test suite and update documentation
- add directory support and improve path validation in CLI
- refactor CLI to use Typer and separate from parser logic
- add detailed test case view and update documentation
- implement detailed report summary and CLI failure filtering

### Fix

- improve error handling and fix formatter method call
- resolve unexpected keyword argument 'err' in console.print calls
- correct syntax and typos in parser and update lockfile

### Refactor

- add new file cli.py to wrapp all logic into it & created new formatter to handle the printing
- fix UV pyproject file & update git ignore
- use explicit re-exports in __init__.py to satisfy linting rules
