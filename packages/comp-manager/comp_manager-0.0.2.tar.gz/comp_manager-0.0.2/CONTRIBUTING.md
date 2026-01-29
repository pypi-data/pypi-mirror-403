# Contributing to Comp Manager

Thank you for your interest in contributing to Comp Manager! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Code Review Guidelines](#code-review-guidelines)
- [Community](#community)

---

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

---

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- Python 3.11 or higher
- Git
- MongoDB 7.0+ (local or Docker - alternatively most tests can be done using MongoMock)
- A GitHub account
- A PyPI account (optional for publishing)

### Setting Up Your Development Environment

1. **Fork the repository** on GitHub

2. **Clone your fork locally**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/comp-manager.git
   cd comp-manager
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/fredstro/comp-manager.git
   ```

4. **Initialize Git Flow** (if using git-flow extension):
   ```bash
   git flow init

   # Use default branch names when prompted:
   # - Production branch: main
   # - Development branch: develop
   # - Feature prefix: feature/
   # - Release prefix: release/
   # - Hotfix prefix: hotfix/
   # - Support prefix: support/
   # - Version tag prefix: v
   ```

5. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

6. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

7. **Install pre-commit hooks** (recommended):
   ```bash
   pip install pre-commit
   pre-commit install

   # Test the hooks (optional)
   pre-commit run --all-files
   ```

   The pre-commit hooks will automatically run before each commit and check:
   - Code formatting with Ruff
   - Linting with Ruff
   - Security issues with Bandit
   - YAML, TOML, and JSON syntax
   - Trailing whitespace and end-of-file fixes
   - Large files, merge conflicts, and private keys

   To bypass hooks temporarily (not recommended):
   ```bash
   git commit --no-verify
   ```

8. **Start MongoDB**:
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest

   # Or use your local installation
   mongod --dbpath /path/to/data
   ```

9. **Set environment variables**:
   ```bash
   export MONGO_URI="mongodb://localhost:27017/comp_manager_dev"
   ```

10. **Run tests to verify setup**:
   ```bash
   pytest
   ```

---

## Development Workflow

This project follows the [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/) branching model for a structured and organized development process.

### Understanding Git Flow

Git Flow uses multiple branches to manage development:

- **`main`** - Production-ready code. Only release commits merge here.
- **`develop`** - Integration branch for features. The latest development state.
- **`feature/*`** - New features branch off from `develop`, merge back to `develop`
- **`release/*`** - Release preparation branches from `develop`, merge to both `main` and `develop`
- **`hotfix/*`** - Emergency fixes branch off from `main`, merge to both `main` and `develop`

### Installing Git Flow (Optional)

Git Flow can be used manually or with the `git-flow` extension:

```bash
# macOS
brew install git-flow

# Linux (Debian/Ubuntu)
apt-get install git-flow

# Linux (Fedora)
dnf install git-flow

# Windows (via Git Bash or use manual workflow)
# See: https://github.com/nvie/gitflow/wiki/Windows
```

### 1. Create a Feature Branch

Always create a new branch for your work from `develop`:

```bash
# Update your local develop branch
git checkout develop
git pull upstream develop

# Create and switch to a new feature branch
git checkout -b feature/your-feature-name

# Or using git-flow:
git flow feature start your-feature-name
```

### Branch Naming Conventions

Use descriptive branch names with prefixes:

- `feature/` - New features (e.g., `feature/sage-vector-support`)
- `hotfix/` - Urgent production fixes (e.g., `hotfix/cache-corruption`)
- `release/` - Release preparation (e.g., `release/1.2.0`)

**Note**: Most contributors will primarily work with `feature/` branches.

### 2. Make Your Changes

- Write clean, readable code
- Follow the code style guidelines (see below)
- Add or update tests as needed
- Update documentation if you change APIs or behavior
- Keep commits focused and atomic

### 3. Run Quality Checks

Before committing, ensure your code passes all checks.

**Using Pre-commit Hooks (Recommended):**

If you installed pre-commit hooks, they run automatically before each commit:

```bash
# Pre-commit runs automatically on staged files
git add .
git commit -m "your message"

# Or run manually on all files
pre-commit run --all-files

# Run a specific hook
pre-commit run ruff --all-files
pre-commit run bandit --all-files
```

**Manual Quality Checks:**

You can also run tools manually:

```bash
# Format code
ruff format .

# Run linter
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Run tests
pytest

# Run tests with coverage
pytest --cov=comp_manager --cov-report=term-missing

# Type checking (optional)
mypy src/comp_manager

# Security check
bandit -r src/comp_manager -c pyproject.toml
```

### 4. Commit Your Changes

See [Commit Messages](#commit-messages) section for guidelines.

```bash
git add .
git commit -m "feat: add support for complex number fields"
```

### 5. Keep Your Branch Up-to-Date

Regularly sync your feature branch with the latest `develop`:

```bash
# Fetch latest changes
git fetch upstream

# Rebase your feature branch on develop
git checkout feature/your-feature-name
git rebase upstream/develop

# Or merge develop into your branch (if you prefer merging over rebasing)
git merge upstream/develop
```

### 6. Push and Create Pull Request

```bash
# Push your feature branch to your fork
git push origin feature/your-feature-name

# If you rebased, you may need to force push (be careful!)
git push -f origin feature/your-feature-name
```

Then create a pull request on GitHub targeting the **`develop`** branch (not `main`).

### 7. Finish Your Feature

After your PR is approved and merged:

```bash
# Using git-flow (automatic cleanup)
git flow feature finish your-feature-name

# Or manually
git checkout develop
git pull upstream develop
git branch -d feature/your-feature-name  # Delete local branch
git push origin --delete feature/your-feature-name  # Delete remote branch
```

---

## Git Flow Workflow Details

### Working with Features

**Start a Feature:**
```bash
# Manual
git checkout develop
git pull upstream develop
git checkout -b feature/my-feature

# With git-flow
git flow feature start my-feature
```

**Finish a Feature:**
```bash
# Manual (after PR is merged)
git checkout develop
git pull upstream develop
git branch -d feature/my-feature

# With git-flow (merges locally, then push)
git flow feature finish my-feature
git push upstream develop
```

### Working with Releases

**Start a Release:**
```bash
# Manual
git checkout develop
git pull upstream develop
git checkout -b release/1.2.0

# With git-flow
git flow release start 1.2.0
```

**During Release:**
- Update CHANGELOG.md
- Fix release-specific bugs
- Update documentation

**Finish a Release:**
```bash
# With git-flow (creates tag, merges to main and develop)
git flow release finish 1.2.0
git push upstream main
git push upstream develop
git push upstream --tags

# Manual
git checkout main
git merge --no-ff release/1.2.0
git tag -a v1.2.0 -m "Release version 1.2.0"
git checkout develop
git merge --no-ff release/1.2.0
git branch -d release/1.2.0
git push upstream main develop --tags
```

### Working with Hotfixes

Note: a hotfix is applied to both main and develop.

**Start a Hotfix:**
```bash
# Manual
git checkout main
git pull upstream main
git checkout -b hotfix/1.1.1

# With git-flow
git flow hotfix start 1.1.1
```

**Finish a Hotfix:**
```bash
# With git-flow (merges to main and develop, creates tag)
git flow hotfix finish 1.1.1
git push upstream main develop --tags

# Manual
git checkout main
git merge --no-ff hotfix/1.1.1
git tag -a v1.1.1 -m "Hotfix version 1.1.1"
git checkout develop
git merge --no-ff hotfix/1.1.1
git branch -d hotfix/1.1.1
git push upstream main develop --tags
```

### Branch Lifecycle Summary

```
main ──────●─────────────●─────────────●──────> (production releases)
           ^             ^             ^
           │             │             │
           │  release/   │   hotfix/   │
           │             │             │
develop ───●─────●─────●─●─────────────●──────> (integration)
           │     │     │
           │     │     └──── feature/c
           │     └──────────── feature/b
           └────────────────── feature/a
```

---

## Code Style Guidelines

### General Principles

1. **Readability First**: Code is read more often than written
2. **Consistency**: Follow existing patterns in the codebase
3. **Simplicity**: Prefer simple, clear solutions over clever ones
4. **Documentation**: Document why, not just what

### Python Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting with the following configuration:

- **Line length**: 100 characters
- **Target Python**: 3.12
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Import sorting**: Automatic via Ruff

### Code Structure

```python
# Good: Clear, well-documented function
def calculate_hash(data: dict[str, Any], algorithm: str = "md5") -> str:
    """
    Calculate hash for the given data.

    Args:
        data: Dictionary to hash
        algorithm: Hash algorithm to use (default: "md5")

    Returns:
        Hexadecimal hash string

    Raises:
        ValueError: If algorithm is not supported
    """
    if algorithm not in ["md5", "sha256"]:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    serialized = json.dumps(data, sort_keys=True)
    return hashlib.new(algorithm, serialized.encode()).hexdigest()


# Bad: Unclear, undocumented
def calc(d, a="md5"):
    s = json.dumps(d, sort_keys=True)
    return hashlib.new(a, s.encode()).hexdigest()
```

### Naming Conventions

- **Classes**: `CamelCase` (e.g., `ComputationManager`, `DBObjectBase`)
- **Functions/Methods**: `snake_case` (e.g., `get_by_id`, `calculate_hash`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`, `MAX_CACHE_SIZE`)
- **Private members**: Prefix with `_` (e.g., `_internal_method`, `_cache_key`)
- **Type variables**: Single capital letter or `_t` suffix (e.g., `T`, `P`, `Integer_t`)

### Type Hints

Always include type hints for function signatures:

```python
# Good: Complete type hints
def process_data(
    items: list[dict[str, Any]],
    filter_fn: Callable[[dict[str, Any]], bool] | None = None
) -> list[dict[str, Any]]:
    """Process and filter items."""
    if filter_fn is None:
        return items
    return [item for item in items if filter_fn(item)]


# Bad: Missing type hints
def process_data(items, filter_fn=None):
    """Process and filter items."""
    if filter_fn is None:
        return items
    return [item for item in items if filter_fn(item)]
```

### Docstrings

Use [SageMath-style](https://doc.sagemath.org/html/en/developer/coding_basics.html#documentation-strings) docstrings
with the notable exceptions:
1. The "EXAMPLES" block is optional since we use Pytest instead of doctests.
2. There is no need to include the type of INPUT variables in the docstring since we use typehints.

**All public functions, classes, and methods MUST have docstrings.**

```python
def create_computation(
    name: str,
    function_name: str,
    *args: Any,
    **kwargs: Any
) -> Computation:
    """
    Create a new computation entry in the database and return a Computation instance.

    INPUT:
    - ``name`` -- Display name for the computation
    - ``function_name`` --  Full qualified function name

    EXAMPLES:

        >>> comp = create_computation("my_task", "module.func", 1, 2, timeout=30)
        >>> comp.status
        'started'
    """
    # Implementation
```

For mathematical code (especially Sage-related), use Sage-style docstrings:

```python
def matrix_to_json(m: Matrix) -> MatrixJson:
    r"""
    Convert a Sage matrix to JSON representation.

    INPUT:

    - ``m`` -- a Sage matrix

    OUTPUT:

    A dictionary with the matrix data in JSON-serializable format

    EXAMPLES::

        sage: from comp_manager.utils.json_encoder_sage import matrix_to_json
        sage: m = matrix(ZZ, [[1, 2], [3, 4]])
        sage: matrix_to_json(m)
        {'__type__': 'matrix',
         'base_ring': {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0},
         'entries': [['1', '2'], ['3', '4']]}
    """
    # Implementation
```

#### Checking for Missing Docstrings

We provide multiple tools to ensure all functions have docstrings:

**Method 1: Using Ruff (Recommended)**

Ruff automatically checks for missing docstrings as part of linting:

```bash
# Check all files for missing docstrings
ruff check src/comp_manager --select D

# Only show docstring errors
ruff check src/comp_manager --select D --output-format=concise

# Check a specific file
ruff check src/comp_manager/core/models.py --select D
```

**Method 2: Using Custom Script**

We provide a detailed docstring checker script:

```bash
# Basic check
python scripts/check_docstrings.py

# Show fix suggestions with docstring templates
python scripts/check_docstrings.py --fix-suggestions

# Detailed report
python scripts/check_docstrings.py --detailed
```

**Method 3: Pre-commit Hook**

The pre-commit hook automatically checks for missing docstrings before each commit.
If you need to bypass it temporarily (not recommended):

```bash
git commit --no-verify
```

#### Common Docstring Issues

**D401 - Imperative Mood**: First line should use imperative mood
```python
# Bad
def get_data():
    """Gets the data from database."""

# Good
def get_data():
    """Get data from database."""
```

**D103 - Missing Function Docstring**
```python
# Bad - No docstring
def calculate_total(items):
    return sum(items)

# Good
def calculate_total(items):
    """Calculate the total sum of items."""
    return sum(items)
```

### Imports

Organize imports in three groups, separated by blank lines:

1. Standard library imports
2. Third-party imports
3. Local application imports


---

## Testing

### Test Requirements

- All new features must include tests
- Bug fixes should include regression tests
- Maintain >90% code coverage
- Use `# pragma: no cover` to explicitly ignore ccode that should not be reached.
- Tests should be fast (use mocks for slow operations)

### Writing Tests

```python
import pytest
from comp_manager.core.models import Computation

class TestComputation:
    """Test computation lifecycle management."""

    def test_create_computation(self, db_connection):
        """Test creating a new computation."""
        comp = Computation(
            name="test_task",
            function_name="test_function",
            status="started"
        )
        comp.save()

        assert comp.id is not None
        assert comp.status == "started"

    def test_computation_hash_uniqueness(self, db_connection):
        """Test that identical computations produce the same hash."""
        comp1 = Computation(
            function_name_full="module.func",
            args=[1, 2, 3],
            kwargs={"key": "value"}
        )
        comp2 = Computation(
            function_name_full="module.func",
            args=[1, 2, 3],
            kwargs={"key": "value"}
        )

        assert comp1._get_hash() == comp2._get_hash()
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run specific test
pytest tests/test_models.py::TestComputation::test_create_computation

# Run with coverage
pytest --cov=comp_manager --cov-report=html

# Run only fast tests
pytest -m "not slow"

# Run in verbose mode
pytest -v

# Run with debugging
pytest --pdb
```

### Test Fixtures

Place reusable fixtures in `tests/fixtures`:

---

## Documentation

### Documentation Requirements

When making changes, update relevant documentation:

1. **Code Comments**: Explain complex logic or non-obvious decisions
2. **Docstrings**: Document all public classes, functions, and methods
3. **README.md**: Update if you change installation, usage, or features
4. **API Documentation**: Update OpenAPI specs for API changes
5. **CHANGELOG.md**: Add entry for user-facing changes (maintainer will finalize)

### Documentation Style

- Use clear, concise language
- Include examples for complex features
- Keep documentation up-to-date with code
- Use proper Markdown formatting

---

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification.

NOTE: One of the encouraged uses of ``AI agents`` in contributing to this project is in generating
commit messages as e.g. Claude Code usually generates comprehensive and well-formatted commit messages.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Changes to build process, dependencies, or auxiliary tools
- `ci`: Changes to CI/CD configuration
- `revert`: Reverting a previous commit

### Scope (Optional)

The scope should specify what is being changed:

- `api`: API changes
- `cache`: Caching functionality
- `core`: Core computation management
- `sage`: SageMath integration
- `models`: Database models
- `utils`: Utility functions
- `tests`: Testing infrastructure

### Examples

```
feat(sage): add vector serialization support

Add JSON encoding and decoding for Sage vectors over various rings.
Includes support for integer, rational, real, and number field vectors.

Closes #123
```

```
fix(cache): prevent cache key collision for similar arguments

Previously, arguments with different types but same string representation
could produce the same cache key. Now includes type information in key.

Fixes #456
```

```
docs(readme): add SageMath installation instructions

Add detailed instructions for installing optional SageMath dependencies
and troubleshooting common installation issues.
```

```
refactor(serialization): extract field conversion to separate module

Move field value conversion logic from serialization.py to new
field_converters.py module to improve modularity and testability.
```

### Commit Message Guidelines

- **Subject line**:
  - Keep under 72 characters
  - Use imperative mood ("add" not "added" or "adds")
  - Don't end with a period
  - Capitalize first letter after type/scope

- **Body** (optional):
  - Wrap at 72 characters
  - Explain what and why, not how
  - Separate from subject with blank line

- **Footer** (optional):
  - Reference issues and pull requests
  - Note breaking changes with `BREAKING CHANGE:`

---

## Pull Request Process

### Before Creating a PR

1. **Sync with upstream develop**:
   ```bash
   git checkout develop
   git pull upstream develop
   git checkout your-feature-branch
   git rebase develop
   ```

2. **Run all checks**:
   ```bash
   ruff format .
   ruff check --fix .
   pytest
   ```

3. **Update documentation** if needed

4. **Squash commits** if you have many small commits (optional but recommended)

### Creating a Pull Request

1. Push your branch to your fork
2. Go to the main repository on GitHub
3. Click "New Pull Request"
4. **Important**: Set the base branch to `develop` (not `main`)
5. Select your fork and branch as the compare branch
6. Fill out the PR template (see below)

### PR Template

```markdown
## Description

Brief description of what this PR does.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Related Issues

Closes #123
Related to #456

## Changes Made

- List key changes
- Be specific and clear
- Include any breaking changes

## Testing

Describe the tests you added or modified:
- Unit tests for X
- Integration tests for Y
- Manual testing performed

## Checklist

- [ ] My code follows the code style of this project
- [ ] I have run `ruff format` and `ruff check`
- [ ] I have added tests that prove my fix/feature works
- [ ] All new and existing tests pass
- [ ] I have updated the documentation (with relevant docstrings)
- [ ] My commit messages follow the Conventional Commits specification
```

### After Creating a PR

- Respond to review comments promptly
- Make requested changes in new commits (don't force push during review)
- Re-request review after addressing feedback
- Be patient and respectful with reviewers

---

## Code Review Guidelines

### For Reviewers

**Reviewing Code:**

- Be respectful and constructive
- Focus on the code, not the person
- Explain your reasoning
- Suggest improvements with examples
- Approve when code meets standards, even if you would have done it differently
- Use GitHub's suggestion feature for small fixes

**Review Checklist:**

- [ ] Related issues are resolved (wholly or partially)
- [ ] Code follows project style guidelines
- [ ] Changes are well-tested
- [ ] Documentation is updated
- [ ] No unnecessary complexity
- [ ] Error handling is appropriate
- [ ] Performance considerations are addressed
- [ ] Security implications are considered

**Comment Templates:**


✅ Suggestion: Consider using a dict comprehension here for better readability
```suggestion
return {k: v for k, v in items if condition(v)}
```

🤔 Question: Why did you choose this approach over alternative X?

⚠️ Issue: This could raise an exception if `data` is None

💡 Nit: Minor style issue - extra blank line here (feel free to ignore)

🎉 Nice: Great use of the decorator pattern here!

### For Contributors

**Receiving Feedback:**

- Don't take criticism personally
- Ask for clarification if feedback is unclear
- Explain your reasoning if you disagree
- Be open to alternative approaches
- Thank reviewers for their time and insights

**Addressing Feedback:**

- Address all comments, even if just to acknowledge
- Mark conversations as resolved after addressing
- Add comments to explain your changes
- Update the PR description if scope changes

---

## Community

### Getting Help

- **Documentation**: Check README.md, ARCHITECTURE.md, and code comments
- **GitHub Issues**: Search existing issues for similar problems
- **GitHub Discussions**: Ask questions and discuss ideas
- **Email**: Contact the maintainer at fredrik314@gmail.com

### Reporting Bugs

When reporting bugs, include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Minimal steps to reproduce the issue
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment**: Python version, OS, MongoDB version
6. **Logs**: Relevant error messages or logs

### Suggesting Features

When suggesting features:

1. **Use Case**: Explain the problem you're trying to solve
2. **Proposed Solution**: Describe your suggested approach
3. **Alternatives**: Consider alternative solutions
4. **Impact**: Who would benefit from this feature?

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions, ideas, and general discussion
- **Pull Requests**: Code contributions and reviews
- **Email**: Direct contact with maintainers

---

## Recognition

Contributors will be recognized in:

- CONTRIBUTORS.md file (coming soon)
- Release notes for significant contributions
- Project documentation where appropriate

Thank you for contributing!

---

## Additional Resources

- [Git Flow Model](https://nvie.com/posts/a-successful-git-branching-model/) - Original Git Flow article
- [Git Flow Cheatsheet](https://danielkummer.github.io/git-flow-cheatsheet/) - Quick reference
- [Conventional Commits](https://www.conventionalcommits.org/)
- [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)
- [Python Type Hints Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [SageMath Documentation](https://doc.sagemath.org/)

---

## Frequently Asked Questions

### Q: Should I create PRs against `main` or `develop`?
**A:** Always create PRs against `develop` unless you're a maintainer working on a hotfix.

### Q: What if I accidentally branched from `main`?
**A:** Rebase your branch onto `develop`:
```bash
git checkout your-feature-branch
git rebase --onto develop main your-feature-branch
```

### Q: How do I sync my fork with the upstream repository?
**A:**
```bash
git checkout develop
git fetch upstream
git merge upstream/develop
git push origin develop

git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

### Q: Can I use git-flow commands if the upstream doesn't use them?
**A:** Yes! Git-flow is just a convenience wrapper. You can use it locally even if maintainers use manual commands.

### Q: What happens to my feature branch after the PR is merged?
**A:** Delete it both locally and on your fork to keep your repository clean.

---

*Last Updated: 2025-11-01*
