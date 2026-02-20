# Contributing

This is a community tool. If you use it, you can help improve it.

---

## Setup

```bash
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
```

---

## Making Changes

1. Fork the repo
2. Make your change
3. Run tests: `pytest tests/`
4. Run formatter: `pre-commit run --all-files`
5. Submit a PR

---

## Code Style

See [CONSISTENCY_GUIDE.md](CONSISTENCY_GUIDE.md). Short version:
- Type hints on everything
- 100 char lines
- Explain why in comments
- Log your errors

---

## Reporting Bugs

Open an issue. Include:
- What you were doing
- What happened
- What you expected
- Error messages (if any)

---

## Questions?

Check the existing docs or open an issue.

---

Thanks for helping out.
