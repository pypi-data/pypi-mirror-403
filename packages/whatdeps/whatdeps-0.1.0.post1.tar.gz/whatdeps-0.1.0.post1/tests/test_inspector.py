from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from whatdeps.inspector import PackageInspector
from whatdeps.models import PackageInfo


class TestPackageInspector:
    """Test PackageInspector class"""

    def test_init(self):
        inspector = PackageInspector()
        assert hasattr(inspector, "venv_site_packages")

    def test_find_site_packages_in_venv(self, tmp_path, monkeypatch):
        """Test finding site-packages in virtual environment"""
        site_packages = tmp_path / "lib" / "python3.14" / "site-packages"
        site_packages.mkdir(parents=True)
        # Mock sys.prefix to simulate venv
        monkeypatch.setattr("sys.prefix", str(tmp_path))
        monkeypatch.setattr("sys.base_prefix", "/usr")

        inspector = PackageInspector()
        assert inspector.venv_site_packages == site_packages

    def test_find_site_packages_not_in_venv(self, monkeypatch):
        """Test behavior when not in virtual environment"""
        # Mock sys.prefix == sys.base_prefix (not in venv)
        monkeypatch.setattr("sys.prefix", "/usr")
        monkeypatch.setattr("sys.base_prefix", "/usr")

        inspector = PackageInspector()
        assert inspector.venv_site_packages is None


class TestGetGithubUrl:
    """Test GitHub URL extraction"""

    def test_extract_github_url_from_source(self, mock_pypi_response):
        """Test extracting GitHub URL from Source link"""
        inspector = PackageInspector()
        url = inspector._get_github_url(mock_pypi_response)
        assert url == "https://github.com/psf/requests"

    def test_extract_github_url_from_repository(self):
        """Test extracting from Repository link"""
        data = {
            "info": {"project_urls": {"Repository": "https://github.com/user/repo"}}
        }
        inspector = PackageInspector()
        url = inspector._get_github_url(data)
        assert url == "https://github.com/user/repo"

    def test_extract_github_url_case_insensitive(self):
        """Test case-insensitive label matching"""
        data = {
            "info": {"project_urls": {"SOURCE CODE": "https://github.com/user/repo"}}
        }
        inspector = PackageInspector()
        url = inspector._get_github_url(data)
        assert url == "https://github.com/user/repo"

    def test_no_github_url(self, mock_pypi_response_no_github):
        """Test when no GitHub URL exists"""
        inspector = PackageInspector()
        url = inspector._get_github_url(mock_pypi_response_no_github)
        assert url is None

    def test_no_project_urls(self):
        """Test when project_urls is missing"""
        data = {"info": {}}
        inspector = PackageInspector()
        url = inspector._get_github_url(data)
        assert url is None

    def test_strip_trailing_slash(self):
        """Test that trailing slashes are removed"""
        data = {"info": {"project_urls": {"Source": "https://github.com/user/repo/"}}}
        inspector = PackageInspector()
        url = inspector._get_github_url(data)
        assert url == "https://github.com/user/repo"


class TestParseGithubRepoPath:
    """Test GitHub repo path parsing"""

    def test_parse_standard_url(self):
        """Test parsing standard GitHub URL"""
        inspector = PackageInspector()
        path = inspector._parse_github_repo_path("https://github.com/psf/requests")
        assert path == "psf/requests"

    def test_parse_url_with_git_extension(self):
        """Test parsing URL with .git extension"""
        inspector = PackageInspector()
        path = inspector._parse_github_repo_path("https://github.com/user/repo.git")
        assert path == "user/repo"

    def test_parse_url_with_trailing_slash(self):
        """Test parsing URL with trailing slash"""
        inspector = PackageInspector()
        path = inspector._parse_github_repo_path("https://github.com/user/repo/")
        assert path == "user/repo"

    def test_parse_url_with_subpaths(self):
        """Test parsing URL with subpaths (tree/main, issues, etc.)"""
        inspector = PackageInspector()

        path = inspector._parse_github_repo_path(
            "https://github.com/user/repo/tree/main"
        )
        assert path == "user/repo"

        path = inspector._parse_github_repo_path("https://github.com/user/repo/issues")
        assert path == "user/repo"

    def test_parse_invalid_url(self):
        """Test parsing invalid GitHub URL"""
        inspector = PackageInspector()
        path = inspector._parse_github_repo_path("https://example.com/not-github")
        assert path is None

    def test_parse_url_without_repo(self):
        """Test parsing URL without repo path"""
        inspector = PackageInspector()
        path = inspector._parse_github_repo_path("https://github.com/")
        # Should return None or handle gracefully
        assert path is None or path == ""


class TestGetPythonRequires:
    """Test Python version requirement extraction"""

    def test_extract_from_requires_python(self, mock_pypi_response):
        """Test extracting from requires_python field"""
        inspector = PackageInspector()
        req = inspector._get_python_requires(mock_pypi_response)
        assert req == ">=3.7"

    def test_extract_complex_requirement(self):
        """Test extracting complex version requirement"""
        data = {"info": {"requires_python": ">=3.8,<4.0"}}
        inspector = PackageInspector()
        req = inspector._get_python_requires(data)
        assert req == ">=3.8,<4.0"

    def test_fallback_to_classifiers(self, mock_pypi_response_no_requires):
        """Test fallback to classifiers when requires_python missing"""
        inspector = PackageInspector()
        req = inspector._get_python_requires(mock_pypi_response_no_requires)
        assert req == ">=3.6"

    def test_no_python_info(self):
        """Test when no Python version info available"""
        data = {"info": {"classifiers": []}}
        inspector = PackageInspector()
        req = inspector._get_python_requires(data)
        assert req is None

    def test_whitespace_in_requires(self):
        """Test that whitespace is properly handled"""
        data = {"info": {"requires_python": "  >=3.9  "}}
        inspector = PackageInspector()
        req = inspector._get_python_requires(data)
        assert req == ">=3.9"


class TestGetLastReleaseDate:
    """Test release date extraction"""

    def test_extract_release_date(self, mock_pypi_response):
        """Test extracting release date from latest version"""
        inspector = PackageInspector()
        date = inspector._get_last_release_date(mock_pypi_response)
        assert date == "2023-05-22T14:30:00Z"

    def test_no_releases(self):
        """Test when no releases exist"""
        data = {"releases": {}}
        inspector = PackageInspector()
        date = inspector._get_last_release_date(data)
        assert date is None

    def test_no_version_info(self):
        """Test when version info is missing"""
        data = {"info": {}, "releases": {"1.0.0": []}}
        inspector = PackageInspector()
        date = inspector._get_last_release_date(data)
        assert date is None

    def test_version_not_in_releases(self):
        """Test when listed version doesn't exist in releases"""
        data = {
            "info": {"version": "2.0.0"},
            "releases": {"1.0.0": [{"upload_time": "2020-01-01"}]},
        }
        inspector = PackageInspector()
        date = inspector._get_last_release_date(data)
        assert date is None

    def test_empty_release_files(self):
        """Test when release has no files"""
        data = {"info": {"version": "1.0.0"}, "releases": {"1.0.0": []}}
        inspector = PackageInspector()
        date = inspector._get_last_release_date(data)
        assert date is None

    def test_fallback_to_upload_time(self):
        """Test fallback to upload_time when iso_8601 missing"""
        data = {
            "info": {"version": "1.0.0"},
            "releases": {"1.0.0": [{"upload_time": "2023-01-01T00:00:00"}]},
        }
        inspector = PackageInspector()
        date = inspector._get_last_release_date(data)
        assert date == "2023-01-01T00:00:00"


class TestFindFileSizes:
    """Test disk size calculation"""

    def test_find_sizes_no_venv(self):
        """Test when not in virtual environment"""
        inspector = PackageInspector()
        inspector.venv_site_packages = None

        sizes = inspector.find_file_sizes_in_bytes("my-package")
        assert len(sizes) == 0

    def test_find_sizes_single_file(self, tmp_path):
        """Test finding single .py file"""
        inspector = PackageInspector()
        site_packages = tmp_path / "site-packages"
        site_packages.mkdir()
        inspector.venv_site_packages = site_packages

        # Single file package
        (site_packages / "single_module.py").write_text("# single module code here")

        sizes = inspector.find_file_sizes_in_bytes("single-module")
        assert len(sizes) > 0


@pytest.mark.anyio
class TestAsyncMethods:
    """Test async methods with mocked HTTP"""

    async def test_fetch_json_success(self):
        """Test successful JSON fetch"""
        inspector = PackageInspector()

        mock_response = Mock()
        mock_response.content = b'{"key": "value"}'

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await inspector._fetch_json(mock_client, "https://example.com")
        assert result == {"key": "value"}

    async def test_fetch_json_http_error(self):
        inspector = PackageInspector()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPError("Network error"))

        result = await inspector._fetch_json(mock_client, "https://example.com")
        assert result is None

    async def test_fetch_json_invalid_json(self):
        """Test handling invalid JSON"""
        inspector = PackageInspector()

        mock_response = Mock()
        mock_response.content = b"invalid json {"

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await inspector._fetch_json(mock_client, "https://example.com")
        assert result is None

    async def test_get_github_metadata_success(
        self, mock_github_response, mock_github_issues_search
    ):
        """Test successful GitHub metadata fetch"""
        inspector = PackageInspector()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock()

        async def mock_fetch(client, url):
            if "search/issues" in url:
                return mock_github_issues_search
            return mock_github_response

        with patch.object(inspector, "_fetch_json", side_effect=mock_fetch):
            result = await inspector._get_github_metadata(
                mock_client, "https://github.com/psf/requests"
            )

        assert result is not None
        assert result.open_issues == 42
        assert result.closed_issues == 1200
        assert result.stars == 50000
        assert result.is_archived is False

    async def test_get_github_metadata_archived(
        self, mock_github_response_archived, mock_github_issues_search
    ):
        """Test GitHub metadata for archived repo"""
        inspector = PackageInspector()

        mock_client = AsyncMock()

        async def mock_fetch(client, url):
            if "search/issues" in url:
                return {"total_count": 0}
            return mock_github_response_archived

        with patch.object(inspector, "_fetch_json", side_effect=mock_fetch):
            result = await inspector._get_github_metadata(
                mock_client, "https://github.com/user/archived-project"
            )

        assert result is not None
        assert result.is_archived is True

    async def test_get_github_metadata_invalid_url(self):
        """Test GitHub metadata with invalid URL"""
        inspector = PackageInspector()

        result = await inspector._get_github_metadata(
            client=None, github_url="https://not-github.com/user/repo"
        )

        assert result is None

    async def test_get_github_metadata_api_error(self):
        """Test GitHub metadata when API returns error"""
        inspector = PackageInspector()

        mock_client = AsyncMock()

        with patch.object(inspector, "_fetch_json", return_value=None):
            result = await inspector._get_github_metadata(
                mock_client, "https://github.com/user/repo"
            )

        assert result is None

    async def test_inspect_package_not_found(self):
        inspector = PackageInspector()

        mock_client = AsyncMock()

        with patch.object(inspector, "_fetch_json", return_value=None):
            result = await inspector.inspect(mock_client, "nonexistent-package")

        assert result.error is not None
        assert result.name == "nonexistent-package"

    async def test_inspect_invalid_pypi_response(self):
        inspector = PackageInspector()
        mock_client = AsyncMock()

        with patch.object(
            inspector, "_fetch_json", return_value={"invalid": "response"}
        ):
            result = await inspector.inspect(mock_client, "some-package")

        assert result.error is not None

    async def test_inspect_full_success(
        self, mock_pypi_response, mock_github_response, mock_github_issues_search
    ):
        """Test successful complete package inspection"""
        inspector = PackageInspector()
        inspector.venv_site_packages = None  # Skip disk size check

        mock_client = AsyncMock()

        call_count = 0

        async def mock_fetch(client, url):
            nonlocal call_count
            call_count += 1
            if "pypi.org" in url:
                return mock_pypi_response
            elif "search/issues" in url:
                return mock_github_issues_search
            else:
                return mock_github_response

        with patch.object(inspector, "_fetch_json", side_effect=mock_fetch):
            result = await inspector.inspect(mock_client, "requests", is_dev=False)

        assert result.error is None
        assert result.name == "requests"
        assert result.summary == "Python HTTP for Humans."
        assert result.python_requires == ">=3.7"
        assert result.github_url == "https://github.com/psf/requests"
        assert result.github_metadata is not None
        assert result.is_dev_dependency is False

    async def test_inspect_no_github(self, mock_pypi_response_no_github):
        """Test inspecting package without GitHub"""
        inspector = PackageInspector()
        inspector.venv_site_packages = None

        mock_client = AsyncMock()

        with patch.object(
            inspector, "_fetch_json", return_value=mock_pypi_response_no_github
        ):
            result = await inspector.inspect(mock_client, "simple-package")

        assert result.error is None
        assert result.github_url is None
        assert result.github_metadata is None

    async def test_inspect_dev_dependency(self, mock_pypi_response):
        """Test marking as dev dependency"""
        inspector = PackageInspector()
        inspector.venv_site_packages = None

        mock_client = AsyncMock()

        with patch.object(inspector, "_fetch_json", return_value=mock_pypi_response):
            result = await inspector.inspect(mock_client, "pytest", is_dev=True)

        assert result.is_dev_dependency is True

    async def test_inspect_all_packages(self, mock_pypi_response):
        """Test inspecting multiple packages concurrently"""
        inspector = PackageInspector()
        inspector.venv_site_packages = None

        packages = [
            ("requests", False),
            ("pytest", True),
            ("numpy", False),
        ]

        with patch.object(inspector, "_fetch_json", return_value=mock_pypi_response):
            results = await inspector.inspect_all(packages)

        assert len(results) == 3
        assert all(isinstance(r, PackageInfo) for r in results)

        # Check dev dependency marking
        dev_results = [r for r in results if r.is_dev_dependency]
        assert len(dev_results) == 1
