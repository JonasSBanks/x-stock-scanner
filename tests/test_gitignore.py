"""Guardrail: fails if .gitignore ever stops protecting private files."""
from scanner.config import PROJECT_ROOT

MUST_IGNORE = [".env", ".auth/", "data/", "__pycache__/", ".venv/"]


def test_private_files_are_never_committed():
    lines = {line.strip() for line in (PROJECT_ROOT / ".gitignore").read_text().splitlines()}
    missing = [entry for entry in MUST_IGNORE if entry not in lines]
    assert not missing, f".gitignore is missing: {missing}"
