# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.1.2 - 2026-01-30

### Added

- Comprehensive test suite with 55 tests covering all functionality
  - Unit tests for ACMarker and ACsMarker classes
  - Tests for pytest hooks and plugin integration
  - End-to-end integration tests using pytester
- Test coverage reporting (68% coverage)
- Type checking with mypy (strict mode)
- PEP 561 compliance with `py.typed` marker file
- Multi-version testing infrastructure with tox (Python 3.11-3.14)
- Development dependencies: mypy, tox, pytest-cov

### Fixed

- Missing return type annotation on `ACMarker.__hash__()` method
- Optimized regex compilation by moving to module level for better performance

### Changed

- Enhanced development workflow with quality gates (mypy, ruff, pytest)
- Updated development dependencies to include comprehensive testing tools

## 1.1.0

### Added

- `@pytest.mark.acs` for multi-criteria markers.
- Implicit marking from the unit id when `__ac<story_id:int>_<criterion_id:int>` fragments are present.
- Unit marks and keywords are added procedurally. Keywords cann't be used to filter tests; some manual preprocessing is needed in a `conftest.py` script.

### Changed

- `@pytest.mark.ac` now only accepts a single criterion. Existing instances of the multi-criteria marker need to be renamed to `@pytest.mark.acs` (e.g., `@pytest.mark.ac(1, [2, 3])` -> `@pytest.mark.acs(1, [2, 3])`). If only a single criterion existed in the list, replace the list with its only value (e.g., `@pytest.mark.ac(1, [2])` -> `@pytest.mark.ac(1, 2)`).

## 1.0.0

Initial release.
