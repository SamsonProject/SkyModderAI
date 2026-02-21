# Contributing to SkyModderAI

> **Built by modders, for modders.** 🎮

Welcome! SkyModderAI is an AI-powered mod compatibility checker for Bethesda games. Whether you're fixing bugs, adding features, or improving documentation, your contributions help make modding easier for everyone.

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Where to Contribute](#-where-to-contribute)
- [Development Workflow](#-development-workflow)
- [Code Style & Standards](#-code-style--standards)
- [Code Review Checklist](#-code-review-checklist)
- [Getting Help](#-getting-help)
- [Recognition](#-recognition)

---

## 🚀 Quick Start

Get up and running in under 5 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python3 app.py
```

**→ Visit:** http://localhost:5000

---

## 🎯 Where to Contribute

### Pick Your Path

| Experience Level | Where to Start | Impact |
|-----------------|----------------|--------|
| **First Time** | [`good first issue`](https://github.com/SamsonProject/SkyModderAI/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) | Quick wins, learn the codebase |
| **Experienced Dev** | [`help wanted`](https://github.com/SamsonProject/SkyModderAI/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) | Core features, big impact |
| **Documentation** | [`documentation`](https://github.com/SamsonProject/SkyModderAI/issues?q=is%3Aissue+is%3Aopen+label%3Adocumentation) | Guides, tutorials, translations |

### Priority Areas

#### 🔥 Good First Issues
- UI improvements for compatibility database
- Load order share frontend
- Mod author verification flow
- SEO landing pages for mod pairs
- Test coverage improvements
- Accessibility enhancements

#### 🚀 Advanced Contributions
- Compatibility algorithm improvements
- Performance optimization (caching, indexing)
- Mod manager integrations (MO2, Vortex plugins)

### Development Guidelines

All contributions should follow these principles:

- ✅ **Deterministic first, AI only when necessary** (90/10 split)
- ✅ **Privacy by default** (no PII in telemetry)
- ✅ **User data rights** (export/delete endpoints for all features)

---

## 📊 Telemetry System

SkyModderAI collects anonymized usage data to improve the tool. Transparency is core to our design.

### What We Track

| Category | Examples | Purpose |
|----------|----------|---------|
| **Feature Usage** | Which tools, how often | Prioritize development |
| **Compatibility Patterns** | What conflicts with what | Improve detection |
| **Community Engagement** | Votes, reports, shares | Understand user needs |

### What We DON'T Track

- ❌ Personal identifiers (email, IP—hashed only)
- ❌ Full mod lists (unless explicitly shared)
- ❌ Session duration (we don't optimize for addiction)
- ❌ Third-party cookies or ads

### Contributing to Telemetry

1. Read [`samson_telemetry.py`](samson_telemetry.py)
2. Ensure all new features have telemetry hooks
3. Test export/delete endpoints

---

## 🔄 Development Workflow

### Step 1: Setup Environment

```bash
# Clone repository
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks (recommended)
pre-commit install
```

### Step 2: Make Changes

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ...

# Format code
black --line-length 100 .
ruff check --fix .

# Run tests
pytest --cov=. --cov-report=html

# Check test coverage (80% required)
open htmlcov/index.html  # Or open in browser
```

### Step 3: Commit Changes

```bash
# Stage changes
git add .

# Commit with clear message
git commit -m "feat: add your feature description

- What changed
- Why it changed
- Testing done"

# Push to branch
git push origin feature/your-feature-name
```

### Step 4: Open Pull Request

1. Go to [GitHub repository](https://github.com/SamsonProject/SkyModderAI)
2. Click **Pull Requests** → **New Pull Request**
3. Select your branch
4. Fill out PR template:
   - **What** does this PR do?
   - **Why** is this needed?
   - **How** was it tested?
   - **Screenshots** (if UI changes)
5. Request review from maintainers
6. Address feedback
7. Merge when approved

---

## 💻 Code Style & Standards

### Python

| Standard | Requirement | Example |
|----------|-------------|---------|
| **Type Hints** | Required for all functions | `def foo(x: int) -> str:` |
| **Docstrings** | Required for public methods | `"""Process mod list."""` |
| **90/10 Rule** | Deterministic first, AI second | Rules before LLMs |
| **Formatting** | Black (100 char line length) | `black --line-length 100` |
| **Linting** | Ruff | `ruff check .` |
| **Imports** | Auto-sorted with Ruff isort | `ruff check --select I` |
| **Logging** | `logging` module, never `print()` | `logger.info("Done")` |

**Type Hint Style:** Use `X \| None` for Python 3.10+ or `Optional[X]` for compatibility.

### JavaScript

| Standard | Requirement | Notes |
|----------|-------------|-------|
| **ES6+** | `const` and `let`, never `var` | Modern syntax only |
| **Logging** | `Logger` utility | Not direct `console.*` calls |
| **Formatting** | 4-space indentation, semicolons | Consistent style |
| **Modules** | IIFE or ES6 modules | Encapsulation required |

### CSS

| Standard | Requirement | Reference |
|----------|-------------|-----------|
| **Variables** | Design tokens from `:root` | `design-system.css` |
| **Naming** | BEM-style (`.block__element--modifier`) | Consistent patterns |
| **No SCSS** | Plain CSS only | No nested selectors with `&` |
| **Responsive** | Mobile-first | `mobile-accessibility.css` |

### Privacy Requirements

- ✅ No PII in logs or telemetry
- ✅ Hash user emails before storage
- ✅ Implement export/delete for all user data
- ✅ Local-first storage (browser localStorage)

### Testing Requirements

- ✅ Unit tests for all new features
- ✅ Integration tests for API endpoints
- ✅ Privacy tests (verify no PII leakage)
- ✅ Run before PR: `pytest --cov=. --cov-report=html`
- ✅ **80% coverage required**

---

## ✅ Code Review Checklist

Before submitting your PR, verify all items:

### Code Quality
- [ ] Code is formatted with Black and Ruff
- [ ] All tests pass (`pytest`)
- [ ] Test coverage is 80%+ for new code
- [ ] No `console.log` or `print` statements
- [ ] No hardcoded secrets (use environment variables)

### Documentation
- [ ] Docstrings added for public methods
- [ ] Type hints added for all functions
- [ ] Documentation updated
- [ ] Changelog entry added (if applicable)

### Privacy & Security
- [ ] No PII in logs or telemetry
- [ ] Export/delete endpoints implemented (if applicable)

---

## 📚 Common Contribution Patterns

### Adding a New Feature

```
1. Create blueprint → blueprints/your_feature.py
2. Add service → services/your_service.py
3. Add repository (if DB needed) → repositories/your_repository.py
4. Add tests → tests/test_your_feature.py
5. Update docs → docs/ directory
6. Add telemetry hooks → samson_telemetry.py
```

### Fixing a Bug

```
1. Reproduce the bug locally
2. Write a test that fails due to the bug
3. Fix the bug
4. Verify test passes
5. Run full test suite (no regressions)
6. Document the fix (if common issue)
```

### Improving Documentation

```
1. Find relevant doc file → docs/
2. Update with clear, concise information
3. Add examples where helpful
4. Check links are not broken
5. Update "Last Updated" date
6. Run pytest (ensure code examples work)
```

---

## 🆘 Getting Help

Need assistance? We're here to help.

| Channel | Best For | Response Time |
|---------|----------|---------------|
| **Discord** | Quick questions, community chat | [Join Server](https://discord.gg/skyrimmods) |
| **Reddit** | Discussions, showcases | r/skyrimmods (tag: [SkyModderAI]) |
| **GitHub Issues** | Bug reports, feature requests | Use labels: `good first issue`, `help wanted`, `ethics review` |
| **Email** | Sensitive issues, private matters | [support@skymodderai.com](mailto:support@skymodderai.com) |

---

## 🏆 Recognition

Contributors are recognized in multiple ways:

| Recognition | Description | Status |
|------------|-------------|--------|
| **README.md** | Top contributors section | ✅ Active |
| **Release Notes** | Major contributors mentioned | ✅ Active |
| **Website** | Contributors page | 🚧 Coming Soon |

### Notable Contributors

Want to see your name here? Submit your first PR!

**[Your name here!]** ← Add your first PR

---

## 🎯 Project Principles

By contributing to SkyModderAI, you agree to uphold these principles:

| Principle | What It Means |
|-----------|---------------|
| **Build for Autonomy** | Tools that make users independent, not dependent |
| **Respect Privacy** | User data belongs to users. Period. |
| **Design for Obsolescence** | If your feature solves a problem, celebrate when it's no longer needed |
| **Reject Extraction** | No dark patterns, no addiction optimization, no extractive data practices |
| **Serve the Commons** | What we build belongs to the community, not shareholders |

---

## 📄 License

**MIT License** — Free to use, modify, and distribute.

See [LICENSE](LICENSE) for full terms.

---

**Last Updated:** February 21, 2026  
**Version:** 2.0 (Modernized)

---

**Ready to contribute?** [Browse Good First Issues →](https://github.com/SamsonProject/SkyModderAI/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
