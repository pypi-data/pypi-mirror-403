from datetime import datetime, timedelta, timezone

import pytest

# @pytest.fixture
# def fixtures_dir():
#     return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_pyproject(tmp_path):
    content = """
[project]
name = "test-project"
dependencies = [
    "requests>=2.28.0",
    "click[shell]>=8.0",
    "numpy==1.24.0",
]
[dependency-groups]
test = [
    "pytest>=7.0",
    "pytest-cov",
]
dev = [
    "black",
    "ruff",
]

[tool.hatch.envs.docs]
dependencies = [
    "mkdocs",
    "mkdocs-material",
]
"""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(content)
    return pyproject


@pytest.fixture
def sample_pyproject_poetry(tmp_path):
    """Create a Poetry-style pyproject.toml"""
    content = """
[tool.poetry]
name = "poetry-project"

[tool.poetry.dependencies]
python = "^3.9"
requests = "^2.28.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
black = "^23.0"

[tool.poetry.group.test.dependencies]
pytest-cov = "^4.0"
"""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(content)
    return pyproject


@pytest.fixture
def sample_requirements(tmp_path):
    """Create a sample requirements.txt"""
    content = """# Production dependencies
requests>=2.28.0
click[shell]>=8.0
numpy==1.24.0

# Comment line
flask~=2.3.0

# URL-based dependency
git+https://github.com/user/repo.git@main#egg=package
"""
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(content)
    return requirements


@pytest.fixture
def sample_requirements_dev(tmp_path):
    """Create requirements-dev.txt"""
    content = """pytest>=7.0
pytest-cov
black
ruff
"""
    req_dev = tmp_path / "requirements-dev.txt"
    req_dev.write_text(content)
    return req_dev


@pytest.fixture
def mock_pypi_response():
    return {
        "info": {
            "name": "requests",
            "version": "2.31.0",
            "summary": "Python HTTP for Humans.",
            "requires_python": ">=3.7",
            "project_urls": {
                "Homepage": "https://requests.readthedocs.io",
                "Source": "https://github.com/psf/requests",
            },
            "classifiers": [
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
            ],
        },
        "releases": {
            "2.31.0": [
                {
                    "upload_time": "2023-05-22T14:30:00",
                    "upload_time_iso_8601": "2023-05-22T14:30:00Z",
                }
            ]
        },
    }


@pytest.fixture
def mock_pypi_response_no_github():
    return {
        "info": {
            "name": "simple-package",
            "version": "1.0.0",
            "summary": "A simple package",
            "requires_python": ">=3.8",
            "project_urls": {
                "Homepage": "https://example.com",
                "Documentation": "https://docs.example.com",
            },
            "classifiers": [],
        },
        "releases": {
            "1.0.0": [
                {
                    "upload_time_iso_8601": "2024-01-01T00:00:00Z",
                }
            ]
        },
    }


@pytest.fixture
def mock_pypi_response_no_requires():
    return {
        "info": {
            "name": "legacy-package",
            "version": "0.5.0",
            "summary": "Legacy package",
            "project_urls": {},
            "classifiers": [
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
            ],
        },
        "releases": {
            "0.5.0": [
                {
                    "upload_time": "2020-01-01T00:00:00",
                }
            ]
        },
    }


@pytest.fixture
def mock_github_response():
    """Mock GitHub API response for active repository"""
    now = datetime.now(timezone.utc)
    return {
        "name": "requests",
        "full_name": "psf/requests",
        "pushed_at": (now - timedelta(days=30)).isoformat(),
        "updated_at": (now - timedelta(days=30)).isoformat(),
        "created_at": (now - timedelta(days=3650)).isoformat(),
        "archived": False,
        "open_issues_count": 42,
        "stargazers_count": 50000,
        "forks_count": 9000,
        "watchers_count": 2000,
        "default_branch": "main",
    }


@pytest.fixture
def mock_github_response_archived():
    """Mock GitHub response for archived repository"""
    now = datetime.now(timezone.utc)
    return {
        "name": "archived-project",
        "full_name": "user/archived-project",
        "pushed_at": (now - timedelta(days=730)).isoformat(),
        "updated_at": (now - timedelta(days=730)).isoformat(),
        "created_at": (now - timedelta(days=2000)).isoformat(),
        "archived": True,
        "open_issues_count": 15,
        "stargazers_count": 100,
        "forks_count": 10,
        "watchers_count": 5,
        "default_branch": "master",
    }


@pytest.fixture
def mock_github_issues_search():
    """Mock GitHub issues search API response"""
    return {
        "total_count": 1200,
        "incomplete_results": False,
    }
