# Changelog

All notable changes to this project will be documented in this file.

The format is based on "Keep a Changelog" and this project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
-

### Changed
-

### Fixed
-

---

## [2.0.5] - 2026-01-24

### Added
- Standardized package structure following "src layout" (`src/GuardianLayer/`) for robust PyPI distribution and reliable imports.
- New `generate_async` method in `AdviceGenerator` for non-blocking advice retrieval.

### Fixed
- Resolved critical `RuntimeWarning` in `ExperienceLayer` where async storage callbacks were not being awaited, ensuring data persistence reliability.
- Fixed `ImportError` on fresh installs by ensuring proper package hierarchy.
- Standardized async dispatch logic across all layers (Health, Loop, Experience, Advice).
- Updated comprehensive test suite (31 tests) to reflect new package structure; achieved 100% pass rate with zero warnings.

---

## [2.0.4] - 2026-01-22

### Fixed
- Fixed GitHub Actions permissions to allow automated Release creation.
- (Note: v2.0.3 was published to PyPI but GitHub Release failed).

## [2.0.3] - 2026-01-22

### Fixed
- Critical `IndentationError` in tests (`test_async_flow.py`).
- Comprehensive linting fixes across the codebase (Black/Flake8 compatibility).
- Resolved `asyncio` import issues and bare `except` clauses.

## [2.0.2] - 2026-01-22

### Fixed
- Corrected package metadata (URLs, Author info).

## [2.0.1] - 2026-01-22

### Changed
- Minor package updates and metadata refresh.

## [2.0.0] - 2026-01-20

### Added
- Major refactor and public release of GuardianLayer v2.0.0.
- Core components:
  - `LoopDetector` — loop detection utilities.
  - `GuardianLayer` — high-level orchestration.
  - `ExperienceLayer` — persistence of past interactions and corrections.
  - `MCPFacade` — tool input/output validation facade.
  - `HealthMonitor` — circuit-breaker style error classification and state tracking.
  - `AdviceGenerator` — suggestion generation to recover from failures.
  - Caching implementations: `LRUCache`, `AdviceCache`, `ValidationCache`, `HashCache`.
  - `MetricsCollector` — runtime metrics collection.
- Documentation skeleton (Sphinx) under `docs/`.
- CI workflow for tests (`.github/workflows/ci.yml`).
- Packaging: `pyproject.toml` updated for v2.0.0.
- MIT license added.

### Changed
- Standardized package layout under `src/`.
- Updated imports / `__init__` exports and version.

### Fixed
- Various bugfixes across validation, cache, and tests (see Git history for details).

---

# How to write changelog entries

- Add entries to the `Unreleased` section while developing.
- On release, move entries from `Unreleased` into a new version section and set the release date.
- Use categories: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
- Keep entries concise but descriptive, and reference issues/PR numbers when helpful.

---

# CONTRIBUTING template

Below is a recommended `CONTRIBUTING.md` template. Copy this into `CONTRIBUTING.md` at the repo root and customize if needed.

---
# Contributing to GuardianLayer

Thank you for considering contributing to GuardianLayer! We welcome bug reports, feature requests, documentation improvements, and pull requests.

## Code of Conduct
This project follows a Contributor Covenant Code of Conduct. By participating you agree to abide by its terms.

## Ways to contribute
- Report bugs and provide reproducible steps.
- Suggest features or enhancements by opening an issue.
- Improve documentation (README, docs/).
- Submit pull requests for fixes and features.

## Getting started (development)
1. Fork the repository and clone your fork.
2. Create a virtual environment and install dev dependencies:
   - python >= 3.8
   - pip install -e '.[dev]'
3. Run tests:
   - `pytest -q`
4. Run linters (if configured):
   - `flake8 src tests`

## Branching and pull requests
- Create a descriptive branch name, e.g. `fix/loop-detection-bug` or `feat/advice-generator`.
- Keep PRs small and focused.
- Reference the issue number in the PR description (e.g. `Closes #123`).
- Include tests for new features and bug fixes.
- Add or update documentation when public behavior changes.

## Commit messages
- Use clear, imperative commit messages.
- Prefer conventional commit style (optional): `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, etc.
- Each commit should represent a logical unit of change.

## Tests
- Add unit tests under `tests/`.
- Run the full suite locally before opening a PR:
  - `pytest -q --maxfail=1 --disable-warnings`
- For async tests, `pytest-asyncio` is used.

## Documentation
- Docs live in `docs/` using Sphinx.
- To build docs locally:
  - `pip install -r docs/requirements.txt` (or at least `sphinx` and `sphinx-rtd-theme`)
  - `cd docs`
  - `sphinx-build -b html . _build/html`
- If you update public APIs, update docstrings and regenerate API pages if using `sphinx-apidoc`.

## Security disclosures
If you discover a security issue, please disclose it privately to the maintainers (open a private issue or email the project owner). Do not publicly disclose vulnerabilities until they have been addressed.

## Releasing and versioning
This project follows Semantic Versioning. Releases are created by:
1. Updating `CHANGELOG.md` (move `Unreleased` entries to a new section).
2. Bumping the version in `pyproject.toml` and `src/__init__.py` (`__version__`).
3. Tagging the commit: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
4. Pushing the tag: `git push origin vX.Y.Z`

---

# Publishing to PyPI (manual steps)

1. Ensure you have `build` and `twine`:
   - `pip install --upgrade build twine`
2. Create distributions:
   - `python -m build`
   - Outputs will be placed in `dist/` (sdist and wheel).
3. Test upload to TestPyPI (recommended):
   - Create an account on https://test.pypi.org/
   - Create an API token for TestPyPI and store it securely.
   - Upload:
     - `python -m twine upload --repository testpypi -u __token__ -p <TEST_PYPI_TOKEN> dist/*`
   - Test install:
     - `pip install -i https://test.pypi.org/simple/ GuardianLayer`
4. Publish to PyPI:
   - Create an API token on https://pypi.org/ if you don't have one.
   - Upload:
     - `python -m twine upload -u __token__ -p <PYPI_TOKEN> dist/*`
   - Verify with:
     - `pip install GuardianLayer`

Notes:
- Prefer PyPI API tokens over username/password and store them as CI secrets (`PYPI_API_TOKEN`).
- CI automation can publish on tag pushes (see `.github/workflows/publish.yml` example in documentation).

---

# Release checklist (recommended)

- [ ] All tests pass on CI across supported Python versions.
- [ ] Update `CHANGELOG.md` and set release date.
- [ ] Bump version in `pyproject.toml` and `src/__init__.py`.
- [ ] Tag the release (`vX.Y.Z`) and push tag.
- [ ] Build and upload artifacts to TestPyPI and validate.
- [ ] Upload to PyPI (or let GitHub Actions do it).
- [ ] Create a release entry on GitHub with notes copied from changelog.

---

Thank you for contributing to GuardianLayer! If you want, I can also:
- Create a `CONTRIBUTING.md` file directly in the repo with the template above.
- Add PR/Issue templates under `.github/` directory.
- Set up a `publish.yml` GitHub Actions workflow to automate PyPI releases (trigger on tag).
If you want me to add any of the above automatically, tell me which items and I will add them.