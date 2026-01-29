from dataclasses import dataclass


@dataclass
class Origin:
    last_commit_date: str | None = None
    last_push_date: str | None = None
    updated_at: str | None = None
    is_archived: bool = False
    open_issues: int = 0
    closed_issues: int = 0
    total_issues: int = 0
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    created_at: str | None = None
    default_branch: str | None = None


@dataclass
class PackageInfo:
    name: str
    summary: str | None = None
    homepage: str | None = None
    github_url: str | None = None
    github_metadata: Origin | None = None
    last_release_date: str | None = None
    python_requires: str | None = None
    disk_size: int | None = None
    is_dev_dependency: bool = False
    error: str | None = None
