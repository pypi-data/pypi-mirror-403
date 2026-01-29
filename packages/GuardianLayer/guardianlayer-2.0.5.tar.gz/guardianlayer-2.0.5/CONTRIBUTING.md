# Contributing to GuardianLayer

Thank you for your interest in contributing to GuardianLayer! We welcome bug reports, feature requests, documentation improvements, and pull requests. This document explains the project's contribution workflow, coding standards, testing, and release process so that contributions can be reviewed and merged efficiently.

## Table of contents

1. Code of Conduct
2. Ways to contribute
3. Reporting issues
4. Development setup
5. Tests
6. Linting and formatting
7. Pre-commit hooks
8. Branching and pull requests
9. Commit message guidelines
10. Documentation
11. Releasing and publishing to PyPI
12. Security disclosure
13. Maintaining and backporting

---

## 1. Code of Conduct

This project follows a Contributor Covenant-style Code of Conduct. Be respectful and professional. If you believe someone has violated the code of conduct, open an issue and mention the maintainers or contact the project owner directly.

## 2. Ways to contribute

- Report bugs with reproducible steps.
- Propose features and improvements by opening an issue.
- Improve documentation: clarifications, examples, or fixing typos.
- Add or improve tests.
- Submit PRs implementing fixes or features.
- Help triage issues and review PRs.

## 3. Reporting issues

When opening an issue:
- Use a clear, descriptive title.
- Explain the expected behavior vs. actual behavior.
- Provide a minimal reproducible example or test case.
- Include relevant environment information:
  - Python version
  - OS
  - GuardianLayer version (`python -c "import GuardianLayer; print(GuardianLayer.__version__)"`)
- Attach logs or tracebacks if available.

Label issues appropriately (bug, enhancement, question).

## 4. Development setup

Recommended Python: 3.8+

1. Fork the repository and clone your fork:
   [Adjust remote URLs to your fork]
    - Create a virtual environment:
        python -m venv .venv
        source .venv/bin/activate  # Unix/macOS
        .venv\Scripts\Activate     # Windows (PowerShell)
    - Install the package in editable mode with dev extras:
        pip install --upgrade pip
        pip install -e '.[dev]'
    - Alternatively, use the project `pyproject.toml` tooling:
        python -m pip install --upgrade build
        python -m pip install .

2. Run tests to ensure the base is healthy:
    pytest -q

3. Run linters and formatters (see below).

## 5. Tests

- Tests are located in the `tests/` directory.
- Use `pytest` for running tests:
    pytest -q
- For async tests, `pytest-asyncio` is used; ensure it is installed in dev deps.
- Aim for tests that are deterministic and fast. Add tests for bug fixes and new features.

## 6. Linting and formatting

- Prefer black/flake8/isort or the configured tools in the repo. If not present, use:
    python -m pip install flake8 black isort
- Example commands:
    flake8 src tests
    black src tests
    isort src tests

Follow established style and keep diffs minimal and focused.

## 7. Pre-commit hooks

We recommend using pre-commit to run linters/formatters automatically.

- Install:
    python -m pip install pre-commit
    pre-commit install
- Run on all files:
    pre-commit run --all-files

If the project adds a `.pre-commit-config.yaml`, the hooks will run automatically on commit.

## 8. Branching and pull requests

- Create a descriptive branch name:
  - `fix/<short-description>`
  - `feat/<short-description>`
  - `docs/<short-description>`
- Keep PRs small and focused.
- Rebase or squash commits to maintain a tidy history if requested by maintainers.
- Include tests for bug fixes and features.
- Reference related issues in the PR description (e.g., `Closes #123`).
- CI must pass before a PR can be merged.

## 9. Commit message guidelines

Prefer clear, imperative commit messages. Example style:

- `feat: add AdviceGenerator for context-aware suggestions`
- `fix: prevent false-positive loops in LoopDetector.check()`
- `docs: update usage example in README`

If the project follows Conventional Commits or another standard, follow that convention.

## 10. Documentation

Docs are in the `docs/` directory and use Sphinx.

- Build docs locally:
    cd docs
    sphinx-build -b html . _build/html
- Keep docstrings clear, including parameter and return descriptions for public APIs.
- Update `README.md` and `CHANGELOG.md` with user-facing changes.
- Add examples to `examples/` for common usage patterns.

## 11. Releasing and publishing to PyPI

Releases should follow Semantic Versioning. Maintain the changelog (`CHANGELOG.md`) and update the package version in both `pyproject.toml` and `src/__init__.py`.

Manual release steps (recommended to test on TestPyPI first):

1. Update changelog and bump the version:
   - Update `CHANGELOG.md` (move Unreleased entries into the new version).
   - Set the version in `pyproject.toml` and `src/__init__.py`.

2. Tag the release:
    git add -A
    git commit -m "chore(release): vX.Y.Z"
    git tag -a vX.Y.Z -m "Release vX.Y.Z"
    git push origin main --tags

3. Build distribution artifacts:
    python -m pip install --upgrade build
    python -m build

   This creates `dist/` with `.tar.gz` and `.whl`.

4. Upload to TestPyPI (recommended):
   - Create an account on https://test.pypi.org/
   - Create an API token and keep it safe.
   - Upload:
        python -m pip install --upgrade twine
        python -m twine upload --repository testpypi -u __token__ -p <TEST_PYPI_TOKEN> dist/*
   - Test install from TestPyPI:
        pip install -i https://test.pypi.org/simple/ GuardianLayer

5. Publish to PyPI:
   - Create an API token on https://pypi.org/
   - Upload:
        python -m twine upload -u __token__ -p <PYPI_TOKEN> dist/*

Notes:
- Use API tokens (`__token__` with Twine) rather than username/password.
- Store CI secrets (e.g., `PYPI_API_TOKEN`) in repository settings if automating releases via CI.
- Optionally, set up a GitHub Actions workflow to publish when a `v*` tag is pushed.

## 12. Security disclosure

If you discover a security vulnerability, please disclose it privately. Open a private issue or contact the maintainers directly and avoid public disclosure until the issue is addressed.

## 13. Maintaining and backporting

- For urgent fixes, maintainers may backport to supported branches.
- Follow the same testing and review guidelines for backports.
- Keep release notes and changelogs clear about which branches received security or bugfix patches.

---

Thanks for helping make GuardianLayer better. If you'd like, I can also:
- Add a `.github/ISSUE_TEMPLATE` or PR template.
- Add pre-configured `pre-commit` hooks.
- Prepare a GitHub Actions `publish.yml` workflow to automate PyPI releases on tag pushes.

If you want any of these created, tell me which ones and I will prepare them.