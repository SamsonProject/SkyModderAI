# SkyModderAI Test Suite

**Professional-grade test suite with 80%+ coverage requirement.**

---

## 📁 Test Structure

```
tests/
├── unit/                    # Unit tests (isolated components)
│   ├── test_conflict_detector.py
│   ├── test_list_builder_options.py
│   ├── test_modding_scenarios.py
│   ├── test_pruning.py
│   ├── test_quickstart_config.py
│   └── test_security_logging.py
│
├── integration/             # Integration tests (component interactions)
│   ├── test_integration.py
│   ├── test_integration_e2e.py
│   ├── test_information_surfaces.py
│   ├── test_modlist_normalize_api.py
│   └── test_profile_dashboard_api.py
│
├── openclaw/               # OpenCLAW-specific tests
│   ├── test_openclaw.py
│   ├── test_openclaw_engine.py
│   └── test_openclaw_safety.py
│
├── conftest.py             # Shared test configuration
├── __init__.py
└── README.md               # This file
```

---

## 🧪 Running Tests

### **Basic Commands**

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_conflict_detector.py -v

# Run test class
pytest tests/unit/test_conflict_detector.py::TestConflictDetector -v

# Run specific test function
pytest tests/unit/test_conflict_detector.py::TestConflictDetector::test_detect_conflicts -v
```

### **Test Categories**

```bash
# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v

# Run OpenCLAW tests only
pytest tests/openclaw/ -v

# Run slow tests (marked with @pytest.mark.slow)
pytest -m slow -v

# Skip slow tests
pytest -m "not slow" -v
```

### **Coverage Reports**

```bash
# HTML report (opens in browser)
pytest --cov=. --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# XML report (for CI/CD)
pytest --cov=. --cov-report=xml

# Terminal report with missing lines
pytest --cov=. --cov-report=term-missing
```

---

## 📝 Writing Tests

### **Test File Naming**

- Files: `test_*.py` (e.g., `test_conflict_detector.py`)
- Classes: `Test*` (e.g., `TestConflictDetector`)
- Functions: `test_*` (e.g., `test_detect_conflicts`)

### **Test Structure**

```python
"""Tests for conflict_detector module."""

import pytest
from conflict_detector import ConflictDetector, parse_mod_list_text


class TestConflictDetector:
    """Tests for ConflictDetector class."""
    
    def test_detect_conflicts(self):
        """Test basic conflict detection."""
        # Arrange
        mod_list = ["USSEP.esp", "SkyUI.esp"]
        
        # Act
        detector = ConflictDetector()
        conflicts = detector.detect(mod_list)
        
        # Assert
        assert len(conflicts) == 0
    
    def test_missing_master(self):
        """Test missing master detection."""
        # Arrange
        mod_list = ["ChildMod.esp"]  # Missing parent
        
        # Act
        detector = ConflictDetector()
        conflicts = detector.detect(mod_list)
        
        # Assert
        assert any(c.type == "missing_master" for c in conflicts)
```

### **Fixtures**

```python
# conftest.py
import pytest

@pytest.fixture
def sample_mod_list():
    """Sample mod list for testing."""
    return [
        "USSEP.esp",
        "SkyUI.esp",
        "Ordinator.esp",
    ]

@pytest.fixture
def conflict_detector():
    """ConflictDetector instance."""
    return ConflictDetector()

# Usage in test file
def test_detect_conflicts(sample_mod_list, conflict_detector):
    conflicts = conflict_detector.detect(sample_mod_list)
    assert len(conflicts) == 0
```

### **Markers**

```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    """Mark slow tests for selective running."""
    pass

@pytest.mark.integration
def test_integration():
    """Mark integration tests."""
    pass

@pytest.mark.openclaw
def test_openclaw_feature():
    """Mark OpenCLAW-specific tests."""
    pass
```

---

## 🎯 Test Coverage

### **Coverage Requirements**

- **Overall:** 80%+ required
- **Critical modules:** 90%+ (conflict_detector, openclaw_engine)
- **Legacy code:** 70%+ (app.py - excluded from coverage)

### **Coverage Exclusions**

```python
# Exclude from coverage in pyproject.toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/venv/*",
    "*/migrations/*",
    "app.py",  # Legacy monolith
    "config.py",
]
```

### **Current Coverage**

Run `pytest --cov=. --cov-report=term-missing` to see current coverage.

---

## 🔧 Test Configuration

### **pyproject.toml**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

addopts = """
    -v
    --tb=short
    --strict-markers
    --cov=.
    --cov-report=term-missing
    --cov-fail-under=80
    --maxfail=5
"""

markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "e2e: marks tests as end-to-end tests",
    "openclaw: marks OpenCLAW-related tests",
    "security: marks security-related tests",
]
```

### **conftest.py**

```python
"""Pytest configuration and shared fixtures."""

import pytest
from app import app as flask_app


@pytest.fixture
def app():
    """Create Flask app for testing."""
    flask_app.config['TESTING'] = True
    flask_app.config['DATABASE_URL'] = 'sqlite:///:memory:'
    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()
```

---

## 🧪 Test Categories

### **Unit Tests** (`tests/unit/`)

Test isolated components:
- `test_conflict_detector.py` — Conflict detection logic
- `test_list_builder_options.py` — List builder preferences
- `test_modding_scenarios.py` — Modding scenario tests
- `test_pruning.py` — Data pruning logic
- `test_security_logging.py` — Security and logging

### **Integration Tests** (`tests/integration/`)

Test component interactions:
- `test_integration.py` — General integration
- `test_integration_e2e.py` — End-to-end flows
- `test_information_surfaces.py` — UI/API integration
- `test_modlist_normalize_api.py` — API endpoint tests
- `test_profile_dashboard_api.py` — Dashboard API tests

### **OpenCLAW Tests** (`tests/openclaw/`)

Test OpenCLAW functionality:
- `test_openclaw.py` — OpenCLAW integration tests
- `test_openclaw_engine.py` — Engine unit tests
- `test_openclaw_safety.py` — Safety validation tests

---

## 🐛 Debugging Tests

### **Verbose Output**

```bash
# Show all output
pytest -v -s

# Show local variables on failure
pytest -l

# Print statements (capture disabled)
pytest -s
```

### **Step-by-Step Debugging**

```bash
# Install pytest-debugger
pip install pytest-debugger

# Run with debugger
pytest --pdb

# Breakpoint in test
def test_something():
    import pdb; pdb.set_trace()
    # ... test code
```

### **Common Issues**

| Issue | Solution |
|-------|----------|
| Import errors | Check `PYTHONPATH`, use absolute imports |
| Database errors | Use in-memory SQLite for tests |
| Flask context errors | Use `app.app_context()` |
| Fixture not found | Check `conftest.py` location |

---

## 📊 CI/CD Integration

### **GitHub Actions**

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 🎯 Best Practices

1. **Test Isolation** — Each test should be independent
2. **Descriptive Names** — `test_missing_master_detection` not `test_1`
3. **AAA Pattern** — Arrange, Act, Assert
4. **Mock External Services** — Don't call real APIs in tests
5. **Fast Tests** — Keep unit tests under 100ms
6. **Coverage Goals** — Aim for 80%+, but focus on critical paths

---

**Last Updated:** February 20, 2026
