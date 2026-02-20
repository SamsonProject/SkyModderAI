---
name: 📝 Pull Request
description: Propose code changes to SkyModderAI
title: ""
labels: ["triage"]
assignees: []
---

## 🎯 Description
Briefly describe the changes in this PR.

> Example: "This PR adds support for detecting conflicts between..."

## 🔗 Related Issue
Link to the issue this PR addresses (if applicable):
- Fixes #[issue number]
- Closes #[issue number]
- Related to #[issue number]

## 🛠️ Type of Change
Select all that apply:
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Test addition/update
- [ ] Configuration change

## 🧪 Testing
Describe how you tested these changes:

### Manual Testing
- [ ] I have manually tested this change
- [ ] I have tested with different mod lists
- [ ] I have tested across multiple games (if applicable)

### Automated Testing
- [ ] I have added/updated tests
- [ ] All existing tests pass
- [ ] Coverage has not decreased

### Test Environment
- **OS:** [e.g., Windows 11, macOS 13, Ubuntu 22.04]
- **Python Version:** [e.g., 3.11.5]
- **Game Version:** [e.g., Skyrim SE 1.6.640]

## 📋 Checklist
Before submitting this PR:
- [ ] My code follows the project's style guidelines (see [CONSISTENCY_GUIDE.md](CONSISTENCY_GUIDE.md))
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have updated the CHANGELOG (if applicable)
- [ ] I have run `pre-commit run --all-files`
- [ ] I have run `pytest tests/` and all tests pass
- [ ] I have run `ruff check .` and `ruff format .`
- [ ] I have run `mypy` for type checking (if applicable)

## 📸 Screenshots (if applicable)
If this changes the UI, include screenshots:

Before:
```
[Screenshot or description]
```

After:
```
[Screenshot or description]
```

## 📝 Additional Notes
Any additional context, concerns, or questions for reviewers:

## 🎮 Modder Impact
How does this change affect end users (modders)?

> Example: "Modders will now be able to detect conflicts between X and Y mods automatically."

## 🔍 Code Changes Summary
Brief summary of files changed:

| File | Changes |
|------|---------|
| `app.py` | Added new endpoint for... |
| `conflict_detector.py` | Updated logic to handle... |
| `tests/test_conflicts.py` | Added test cases for... |

---

**Thank you for contributing!** Your help makes SkyModderAI better for the entire modding community. 🛡️
