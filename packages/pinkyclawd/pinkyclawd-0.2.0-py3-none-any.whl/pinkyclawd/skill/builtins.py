"""
Built-in skills for common workflows.
"""

BUILTIN_SKILLS: dict = {
    "commit": {
        "description": "Git commit workflow with best practices",
        "instructions": """# Git Commit Skill

Follow these steps when creating a git commit:

## 1. Review Changes
- Run `git status` to see all modified and untracked files
- Run `git diff` to review the actual changes
- Identify what has changed and why

## 2. Stage Changes
- Stage related changes together: `git add <files>`
- Use `git add -p` for partial staging if needed
- Don't stage unrelated changes in the same commit

## 3. Write Commit Message
Follow the Conventional Commits format:
- `feat:` - new feature
- `fix:` - bug fix
- `docs:` - documentation only
- `style:` - formatting, no code change
- `refactor:` - code change that neither fixes nor adds
- `test:` - adding or updating tests
- `chore:` - maintenance tasks

Structure:
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

## 4. Commit
```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <description>

<body explaining what and why>

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## 5. Verify
- Run `git log -1` to verify the commit
- Run `git status` to confirm working tree is clean
""",
    },
    "pr": {
        "description": "Pull request creation and formatting",
        "instructions": """# Pull Request Skill

Follow these steps when creating a pull request:

## 1. Prepare Branch
- Ensure your branch is up to date with main: `git fetch origin && git rebase origin/main`
- Push your branch: `git push -u origin <branch-name>`

## 2. Review Changes
- Run `git log origin/main..HEAD` to see all commits
- Run `git diff origin/main...HEAD` to see all changes
- Summarize what the PR accomplishes

## 3. Create PR
```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<Brief description of changes>

## Changes
- <Change 1>
- <Change 2>
- <Change 3>

## Test Plan
- [ ] <Test 1>
- [ ] <Test 2>

## Screenshots
<If applicable>

---
🤖 Generated with [PinkyClawd](https://github.com/pinkyclawd)
EOF
)"
```

## 4. Link Issues
- If fixing an issue: "Fixes #123"
- If related: "Related to #456"

## 5. Request Review
- Add appropriate reviewers
- Add labels if needed
""",
    },
    "review": {
        "description": "Code review guidelines",
        "instructions": """# Code Review Skill

When reviewing code, follow this checklist:

## 1. Understand Context
- Read the PR description
- Understand what problem is being solved
- Check linked issues for background

## 2. Review for Correctness
- Does the code do what it's supposed to?
- Are edge cases handled?
- Are there any bugs or logic errors?

## 3. Review for Security
- Input validation
- SQL injection / XSS vulnerabilities
- Secrets or credentials in code
- Authentication/authorization issues

## 4. Review for Quality
- Is the code readable and maintainable?
- Are there unnecessary complications?
- Is there code duplication?
- Are variable/function names clear?

## 5. Review for Performance
- Are there obvious performance issues?
- Unnecessary loops or queries?
- Memory leaks?

## 6. Review for Testing
- Are there tests for new functionality?
- Do tests cover edge cases?
- Are tests readable and maintainable?

## 7. Provide Feedback
- Be constructive and specific
- Suggest improvements, don't just criticize
- Distinguish between blocking issues and suggestions
- Praise good patterns and solutions
""",
    },
    "test": {
        "description": "Test writing and running",
        "instructions": """# Test Skill

Guidelines for writing and running tests:

## Test Structure (AAA Pattern)
```python
def test_function_does_something():
    # Arrange - set up test data
    input_data = create_test_data()

    # Act - call the function under test
    result = function_under_test(input_data)

    # Assert - verify the result
    assert result == expected_value
```

## Test Naming
- `test_<function>_<scenario>_<expected_result>`
- Examples:
  - `test_add_positive_numbers_returns_sum`
  - `test_login_invalid_password_raises_error`

## What to Test
- Happy path (normal usage)
- Edge cases (empty input, max values, etc.)
- Error cases (invalid input, exceptions)
- Boundary conditions

## Running Tests
```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_module.py

# Run specific test
pytest tests/test_module.py::test_name

# Run with coverage
pytest --cov=src

# Run with verbose output
pytest -v

# Run matching pattern
pytest -k "pattern"
```

## Test Fixtures
```python
@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```
""",
    },
    "deploy": {
        "description": "Deployment helpers",
        "instructions": """# Deploy Skill

Pre-deployment checklist and helpers:

## Pre-Deployment Checklist
1. [ ] All tests passing
2. [ ] Code reviewed and approved
3. [ ] No security vulnerabilities
4. [ ] Environment variables documented
5. [ ] Database migrations ready
6. [ ] Rollback plan prepared

## Deployment Commands

### Check Status
```bash
# Verify build
npm run build  # or python -m build

# Check for issues
npm audit  # or pip-audit
```

### Tag Release
```bash
# Create release tag
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
```

### Create GitHub Release
```bash
gh release create v1.0.0 --title "Release 1.0.0" --notes "$(cat <<'EOF'
## What's New
- Feature 1
- Feature 2

## Bug Fixes
- Fix 1
- Fix 2

## Breaking Changes
- None
EOF
)"
```

## Post-Deployment
1. Verify deployment succeeded
2. Run smoke tests
3. Monitor logs for errors
4. Verify key functionality
5. Announce release if needed
""",
    },
    "refactor": {
        "description": "Code refactoring patterns",
        "instructions": """# Refactor Skill

Common refactoring patterns and guidelines:

## Refactoring Principles
1. **Make it work, make it right, make it fast** (in that order)
2. **Small, incremental changes** - easier to review and revert
3. **Tests first** - ensure tests pass before and after
4. **One thing at a time** - don't mix refactoring with features

## Common Patterns

### Extract Function
When code is too complex or duplicated:
```python
# Before
def process():
    # 50 lines of complex logic
    pass

# After
def process():
    step1()
    step2()
    step3()
```

### Extract Class
When a class has too many responsibilities:
```python
# Before: one class does everything
# After: separate concerns into focused classes
```

### Rename for Clarity
```python
# Before
def p(d):
    return d * 1.1

# After
def calculate_price_with_tax(base_price):
    TAX_RATE = 0.1
    return base_price * (1 + TAX_RATE)
```

### Replace Conditionals with Polymorphism
When you have repeated type checking.

### Simplify Conditionals
```python
# Before
if x > 0:
    if y > 0:
        if z > 0:
            do_thing()

# After
if x > 0 and y > 0 and z > 0:
    do_thing()
```

## Refactoring Steps
1. Identify the code smell
2. Write tests for existing behavior
3. Make small, safe changes
4. Run tests after each change
5. Review the improved code
""",
    },
    "debug": {
        "description": "Debugging helpers",
        "instructions": """# Debug Skill

Systematic debugging approach:

## 1. Reproduce the Issue
- Get exact steps to reproduce
- Identify minimal reproduction case
- Document expected vs actual behavior

## 2. Gather Information
```python
# Add logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Variable state: {variable}")

# Add print statements (temporary)
print(f"DEBUG: {variable=}")

# Use debugger
import pdb; pdb.set_trace()  # Python
debugger;  // JavaScript
```

## 3. Isolate the Problem
- Binary search through code
- Comment out sections
- Simplify inputs
- Check assumptions

## 4. Common Issues

### Python
- Check for None values
- Verify imports
- Check indentation
- Review exception handling

### JavaScript
- Check for undefined/null
- Verify async/await usage
- Check scope and closures
- Review promise chains

## 5. Fix and Verify
1. Make the smallest possible fix
2. Add a test for the bug
3. Verify the fix works
4. Check for regressions
5. Document the fix

## 6. Prevent Future Issues
- Add validation
- Improve error messages
- Add tests
- Update documentation
""",
    },
}
