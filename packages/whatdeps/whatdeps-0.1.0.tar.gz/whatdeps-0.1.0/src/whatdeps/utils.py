from pathlib import Path

# PEP()
REQUIREMENTS_FILES = {
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-test.txt",
    "dev-requirements.txt",
    "prod-requirements.txt",
    "requirements.txt-prod",
    "test-requirements.txt",
}


def is_valid_dependency_file(path: Path) -> bool:
    if path.name == "pyproject.toml":
        return True

    return path.name in REQUIREMENTS_FILES
