# Contributing to Raqib

## Local development
```bash
./setup.sh
source .venv/bin/activate
uvicorn app.main:app --reload --port 8080
```

## PR checklist
- ruff check . passes
- ruff format --check . passes
- pytest passes with >= 85% coverage
- No subprocess, os.system, eval, exec, or shell=True
- No secrets in the diff
