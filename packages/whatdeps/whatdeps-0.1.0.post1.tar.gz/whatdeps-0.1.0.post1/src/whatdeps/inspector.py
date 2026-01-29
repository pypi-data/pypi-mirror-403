import asyncio
import sys
from pathlib import Path

import httpx
import orjson
from rich.progress import Progress

from .models import Origin, PackageInfo


class PackageInspector:
    PYPI_API = "https://pypi.org/pypi/{}/json"
    GITHUB_API = "https://api.github.com/repos/{}"

    def __init__(self):
        self.venv_site_packages = self._find_site_packages()

    @staticmethod
    def _find_site_packages() -> Path | None:
        if sys.prefix == sys.base_prefix:
            return None

        site_packages = Path(sys.prefix) / "lib"
        for path in site_packages.rglob("site-packages"):
            return path
        return None

    async def _fetch_json(self, client: httpx.AsyncClient, url: str) -> dict | None:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return orjson.loads(response.content)
        except (httpx.HTTPError, orjson.JSONDecodeError):
            return None

    def _get_github_url(self, pypi_data: dict) -> str | None:
        pypi_info = pypi_data.get("info", {})
        home_page_url = pypi_info.get("home_page")
        if home_page_url and "github.com" in home_page_url:
            return home_page_url.rstrip("/")
        urls = pypi_info.get("project_urls")
        if not urls:
            return None
        targets = {"source", "repository", "code", "github", "source code", "homepage"}
        for label, url in urls.items():
            label_lower = label.lower()
            if any(t in label_lower for t in targets) and "github.com" in url:
                return url.rstrip("/")
        return None

    def _parse_github_repo_path(self, github_url: str) -> str | None:
        """get owner/repo from GitHub URL"""
        parts = github_url.rstrip("/").split("github.com/")
        if len(parts) < 2:
            return None

        repo_path = parts[1].replace(".git", "").strip("/")
        repo_path = "/".join(repo_path.split("/")[:2])
        return repo_path

    async def _get_github_metadata(
        self, client: httpx.AsyncClient, github_url: str
    ) -> Origin | None:
        if not client:
            return None
        repo_path = self._parse_github_repo_path(github_url)
        if not repo_path:
            return None

        repo_api_url = self.GITHUB_API.format(repo_path)
        repo_data = await self._fetch_json(client, repo_api_url)
        if not repo_data:
            return None

        # GitHub API's open_issues_count including pull requests
        open_issues = repo_data.get("open_issues_count", 0)

        # Fetch closed issues count
        issues_search_url = f"https://api.github.com/search/issues?q=repo:{repo_path}+type:issue+state:closed"
        issues_data = await self._fetch_json(client, issues_search_url)
        closed_issues = issues_data.get("total_count", 0) if issues_data else 0

        pushed_at = repo_data.get("pushed_at")
        return Origin(
            updated_at=repo_data.get("updated_at"),
            last_push_date=pushed_at,
            last_commit_date=pushed_at,
            is_archived=repo_data.get("archived", False),
            open_issues=open_issues,
            closed_issues=closed_issues,
            total_issues=open_issues + closed_issues,
            stars=repo_data.get("stargazers_count", 0),
            forks=repo_data.get("forks_count", 0),
            watchers=repo_data.get("watchers_count", 0),
            created_at=repo_data.get("created_at"),
            default_branch=repo_data.get("default_branch", "main"),
        )

    def _get_python_requires(self, pypi_data: dict) -> str | None:
        """
        get minimum Python version requirement
        Returns a supported version string e.g: '>=3.8' or '>=3.9,<4.0'
        """
        pypi_info = pypi_data.get("info", {})
        requires_python = pypi_info.get("requires_python")

        if requires_python:
            return requires_python.strip()
        classifiers = pypi_info.get("classifiers", [])
        versions = []
        for classifier in classifiers:
            if classifier.startswith("Programming Language :: Python :: "):
                version = classifier.replace("Programming Language :: Python :: ", "")
                if version and version[0].isdigit() and "." in version:
                    versions.append(version)

        if versions:
            min_version = min(versions)
            return f">={min_version}"

        return None

    def _get_last_release_date(self, pypi_data: dict) -> str | None:
        releases = pypi_data.get("releases", {})
        if not releases:
            return None
        latest_version = pypi_data.get("info", {}).get("version")
        if not latest_version or latest_version not in releases:
            return None

        release_files = releases.get(latest_version, [])
        if release_files and len(release_files) > 0:
            return release_files[0].get("upload_time_iso_8601") or release_files[0].get(
                "upload_time"
            )

        return None

    def find_file_sizes_in_bytes(self, package_name: str) -> dict[str, int]:
        if not self.venv_site_packages:
            return {}

        sizes = {}
        normalized = package_name.lower().replace("-", "_")
        alt_name = package_name.lower().replace("_", "-")
        matching_paths = []
        for path in self.venv_site_packages.iterdir():
            path_lower = path.name.lower()
            if path_lower.startswith(normalized) or path_lower.startswith(alt_name):
                matching_paths.append(path)

        if not matching_paths:
            return {}

        for path in matching_paths:
            if path.is_dir():
                size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            else:
                size = path.stat().st_size
            sizes[path.name.lower()] = size

        return sizes

    async def inspect(
        self, client: httpx.AsyncClient, package_name: str, is_dev: bool = False
    ) -> PackageInfo:
        info = PackageInfo(name=package_name, is_dev_dependency=is_dev)

        pypi_data = await self._fetch_json(client, self.PYPI_API.format(package_name))
        if not pypi_data:
            info.error = f"I couldn't find {package_name} package on PyPI"
            return info

        pypi_info = pypi_data.get("info", {})
        if not pypi_info:
            info.error = "Response from PyPI is Invalid"
            return info

        info.summary = (
            pypi_info.get("summary")
            or pypi_info.get("description", "").split("\n")[0][:100]
        )
        if pypi_info.get("project_urls"):
            info.homepage = pypi_info.get("project_urls").get("Homepage")

        info.python_requires = self._get_python_requires(pypi_data)
        info.last_release_date = self._get_last_release_date(pypi_data)

        github_url = self._get_github_url(pypi_data)
        if github_url:
            info.github_url = github_url
            info.github_metadata = await self._get_github_metadata(client, github_url)

        size_map = self.find_file_sizes_in_bytes(package_name)
        info.disk_size = sum(size_map.values()) if size_map else None
        return info

    async def inspect_all(
        self, packages: list[tuple[str, bool]], progress: Progress = None, task_id=None
    ) -> list[PackageInfo]:
        results = []
        async with httpx.AsyncClient(
            headers={"User-Agent": "whatdeps/1.0", "Accept": "application/json"},
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        ) as client:
            tasks = [
                self.inspect(client, pkg_name, is_dev) for pkg_name, is_dev in packages
            ]
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
                if progress and task_id is not None:
                    progress.update(task_id, advance=1)

        return results
