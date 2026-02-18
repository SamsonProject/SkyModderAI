# SkyModderAI — Professional-Grade Quick Start Guide

**For Developers** — Get up and running with the professional-grade codebase.

---

## Prerequisites

- **Python 3.9+** (3.11+ recommended)
- **Git**
- **pip** (Python package manager)
- **Virtual environment** (venv, virtualenv, or conda)

---

## Quick Setup (5 minutes)

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install all dependencies (including dev tools)
pip install -r requirements.txt
```

### 3. Install Pre-commit Hooks

```bash
# Install pre-commit for automatic linting/formatting
pip install pre-commit
pre-commit install
```

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings (optional for development)
# Minimum for local development:
# SECRET_KEY=dev-secret-key-for-local-testing
# FLASK_ENV=development
```

### 5. Initialize Database

```bash
# Run Alembic migrations
alembic upgrade head
```

### 6. Download LOOT Data

```bash
# Download LOOT masterlist for Skyrim SE
python loot_parser.py skyrimse

# Or download for all games
for game in skyrim skyrimse skyrimvr oblivion fallout3 falloutnv fallout4 starfield; do
    python loot_parser.py $game
done
```

### 7. Run the Application

```bash
# Start Flask development server
python app.py

# Or use the run script
./run.sh
```

Open **http://localhost:5000** in your browser.

---

## Development Workflow

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_integration.py -v

# Run with coverage report
pytest --cov=. --cov-report=term-missing --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Code Quality

```bash
# Lint with Ruff
ruff check .

# Format with Black
black .

# Type check with mypy
mypy blueprints/ services/ exceptions/ --ignore-missing-imports

# Run all pre-commit hooks
pre-commit run --all-files
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

---

## Architecture Overview

### Directory Structure

```
SkyModderAI/
├── app.py                    # Flask application (being refactored)
├── blueprints/               # Flask blueprints (routes)
│   ├── auth.py              # Authentication routes
│   ├── api.py               # REST API routes
│   ├── analysis.py          # Analysis routes
│   ├── community.py         # Community routes
│   └── openclaw.py          # OpenCLAW routes
├── services/                 # Business logic layer
│   ├── auth_service.py      # Auth business logic
│   ├── analysis_service.py  # Analysis logic
│   ├── search_service.py    # Search logic
│   └── community_service.py # Community logic
├── repositories/             # Database access layer (future)
├── models.py                 # SQLAlchemy ORM models
├── exceptions.py             # Custom exceptions
├── sentry_config.py          # Error tracking
├── openapi_spec.py           # API documentation
├── migrations/               # Database migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── tests/                    # Test suite
│   ├── test_integration.py  # Integration tests
│   └── ...
└── requirements.txt          # Dependencies
```

### Request Flow

```
1. HTTP Request
   ↓
2. Flask Blueprint (blueprints/*.py)
   ↓
3. Service Layer (services/*.py)
   ↓
4. Repository/Models (models.py)
   ↓
5. Database (SQLite/PostgreSQL)
```

---

## Using the New Architecture

### Example: Creating a New API Endpoint

**1. Add route to blueprint:**

```python
# blueprints/api.py
@api_bp.route("/mods/<mod_id>", methods=["GET"])
def get_mod(mod_id: str) -> Any:
    """Get mod details by ID."""
    from services import SearchService

    service = SearchService(game="skyrimse")
    mod = service.get_mod_by_id(mod_id)

    if not mod:
        raise ResourceNotFoundError(f"Mod {mod_id} not found")

    return jsonify({"success": True, "mod": mod})
```

**2. Add service method:**

```python
# services/search_service.py
class SearchService:
    def get_mod_by_id(self, mod_id: str) -> Optional[Dict[str, Any]]:
        """Get mod by ID."""
        se = get_search_engine(self.game)
        return se.get_mod(mod_id)
```

**3. Add exception if needed:**

```python
# exceptions.py
class ModNotFoundError(ResourceNotFoundError):
    def __init__(self, message: str = "Mod not found", ...):
        super().__init__(message, "MOD_NOT_FOUND", 404)
```

**4. Write test:**

```python
# tests/test_integration.py
def test_get_mod_endpoint(self, api_client):
    response = api_client.get("/api/v1/mods/ussep")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert "mod" in data
```

---

## API Documentation

### Interactive Swagger UI

Once the app is running, visit:
- **Development**: http://localhost:5000/api/docs
- **Production**: https://skymodderai.onrender.com/api/docs

### OpenAPI Specification

```bash
# View OpenAPI spec
python -c "from openapi_spec import OPENAPI_SPEC; import json; print(json.dumps(OPENAPI_SPEC, indent=2))"
```

### Example API Calls

```bash
# Health check
curl http://localhost:5000/api/v1/health

# Search mods
curl "http://localhost:5000/api/v1/search?q=USSEP&game=skyrimse"

# Analyze mod list (requires API key)
curl -X POST http://localhost:5000/api/v1/analyze \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"mod_list": "Skyrim.esm\nUSSEP.esp", "game": "skyrimse"}'
```

---

## Debugging

### Flask Debug Mode

```bash
# Enable debug mode
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run with debugger
python -m flask run --debug
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error message")
```

### Sentry Testing

```python
from sentry_config import capture_exception

try:
    raise Exception("Test error")
except Exception as e:
    event_id = capture_exception(e, test=True)
    print(f"Error captured: {event_id}")
```

---

## Common Issues

### Issue: "Module not found"

**Solution**: Ensure virtual environment is activated:
```bash
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
```

### Issue: "Database not found"

**Solution**: Run migrations:
```bash
alembic upgrade head
```

### Issue: "LOOT data not available"

**Solution**: Download LOOT data:
```bash
python loot_parser.py skyrimse
```

### Issue: "Coverage threshold not met"

**Solution**: Run tests with coverage report to see what's missing:
```bash
pytest --cov=. --cov-report=term-missing
```

---

## Best Practices

### Code Style

- **Line length**: 100 characters max
- **Imports**: Sorted automatically by Ruff
- **Type hints**: Required for all new code
- **Docstrings**: Google-style for all public functions

### Testing

- **Unit tests**: Test individual functions
- **Integration tests**: Test API endpoints
- **Coverage**: 80%+ required
- **Fixtures**: Use pytest fixtures for setup

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes, commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/your-feature
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: fix bug in analysis
docs: update README
test: add integration tests
refactor: refactor auth service
```

---

## Next Steps

### Learn More

- Read `PHASE1_IMPLEMENTATION_SUMMARY.md` for architecture details
- Review `CONTRIBUTING.md` for contribution guidelines
- Check `ARCHITECTURE_DECISION.md` for design decisions

### Get Involved

- Join the community on GitHub
- Report bugs and suggest features
- Contribute code via pull requests

### Deploy to Production

See `docs/deployment.md` for production deployment guide.

---

**Built by modders, for modders.**
**Professional-grade tools for professional-grade modding.**
