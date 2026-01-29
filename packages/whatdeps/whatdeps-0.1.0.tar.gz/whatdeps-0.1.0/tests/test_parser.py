import pytest

from whatdeps import parser


class TestGetPackageName:
    """Test package name extraction from various formats"""

    def test_simple_package_name(self):
        """Test extracting simple package name"""
        assert parser.get_package_name("requests") == "requests"
        assert parser.get_package_name("numpy") == "numpy"

    def test_package_with_version_specifiers(self):
        """Test all version specifier operators"""
        assert parser.get_package_name("requests>=2.28.0") == "requests"
        assert parser.get_package_name("numpy==1.24.0") == "numpy"
        assert parser.get_package_name("flask~=2.3.0") == "flask"
        assert parser.get_package_name("django>4.0") == "django"
        assert parser.get_package_name("pytest<8.0") == "pytest"
        assert parser.get_package_name("click<=8.1.0") == "click"
        assert parser.get_package_name("pydantic!=2.0.0") == "pydantic"

    def test_package_with_extras(self):
        """Test package names with extras"""
        assert parser.get_package_name("click[shell]") == "click"
        assert parser.get_package_name("sqlalchemy[asyncio]") == "sqlalchemy"
        assert parser.get_package_name("requests[security,socks]") == "requests"
        assert parser.get_package_name("pip[testing]>=21.0") == "pip"

    def test_package_with_environment_markers(self):
        """Test package names with environment markers"""
        assert (
            parser.get_package_name("typing-extensions>=4.0; python_version<'3.10'")
            == "typing-extensions"
        )
        assert (
            parser.get_package_name("importlib-metadata; python_version<'3.8'")
            == "importlib-metadata"
        )
        assert (
            parser.get_package_name("colorama>=0.4; sys_platform=='win32'")
            == "colorama"
        )

    def test_package_with_complex_specifiers(self):
        """Test complex dependency specifications"""
        assert parser.get_package_name("django>=3.2,<5.0") == "django"
        assert (
            parser.get_package_name("requests[security]>=2.28.0; python_version>='3.7'")
            == "requests"
        )

    def test_package_with_whitespace(self):
        """Test that whitespace is properly stripped"""
        assert parser.get_package_name("  requests  ") == "requests"
        assert parser.get_package_name("numpy >= 1.20.0") == "numpy"
        assert parser.get_package_name("  click[shell] >= 8.0  ") == "click"

    def test_empty_or_invalid_input(self):
        """Test edge cases with empty or minimal input"""
        assert parser.get_package_name("") == ""
        assert parser.get_package_name("   ") == ""


class TestParsePyproject:
    """Test pyproject.toml parsing"""

    def test_parse_basic_pyproject(self, sample_pyproject):
        """Test parsing standard PEP 621 pyproject.toml"""
        prod, dev = parser.parse_pyproject(sample_pyproject)

        assert "requests" in prod
        assert "click" in prod
        assert "numpy" in prod
        assert len(prod) == 3

        assert "pytest" in dev
        assert "pytest-cov" in dev
        assert "black" in dev
        assert "ruff" in dev
        assert "mkdocs" in dev
        assert "mkdocs-material" in dev

    def test_parse_poetry_pyproject(self, sample_pyproject_poetry):
        """Test parsing Poetry-style pyproject.toml"""
        prod, dev = parser.parse_pyproject(sample_pyproject_poetry)

        assert "requests" in prod
        assert len(prod) == 1

        assert "pytest" in dev
        assert "black" in dev
        assert "pytest-cov" in dev

    def test_parse_empty_dependencies(self, tmp_path):
        """Test parsing pyproject.toml with no dependencies"""
        content = """
[project]
name = "empty-project"
"""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(content)

        prod, dev = parser.parse_pyproject(pyproject)
        assert prod == set()
        assert dev == set()

    def test_parse_only_prod_dependencies(self, tmp_path):
        """Test parsing with only production dependencies"""
        content = """
[project]
dependencies = ["requests", "numpy"]
"""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(content)

        prod, dev = parser.parse_pyproject(pyproject)
        assert len(prod) == 2
        assert len(dev) == 0

    def test_parse_only_dev_dependencies(self, tmp_path):
        """Test parsing with only dev dependencies"""
        content = """
[project]
name = "test"

[dependency-groups]
dev = ["pytest", "black"]
"""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(content)

        prod, dev = parser.parse_pyproject(pyproject)
        assert len(prod) == 0
        assert len(dev) == 2

    def test_parse_malformed_toml(self, tmp_path):
        """Test handling of malformed TOML"""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("this is not valid toml [[[")

        with pytest.raises(Exception):  # tomllib.TOMLDecodeError
            parser.parse_pyproject(pyproject)

    def test_parse_nonexistent_file(self, tmp_path):
        pyproject = tmp_path / "nonexistent.toml"

        with pytest.raises(AssertionError):
            parser.parse_pyproject(pyproject)


class TestParseRequirements:
    """Test requirements.txt parsing"""

    def test_parse_basic_requirements(self, sample_requirements):
        """Test parsing standard requirements.txt"""
        packages = parser.parse_requirements(sample_requirements)

        assert "requests" in packages
        assert "click" in packages
        assert "numpy" in packages
        assert "flask" in packages
        # URL-based dependencies should be skipped or handled
        assert len(packages) >= 4

    def test_parse_with_comments(self, tmp_path):
        """Test that comments are properly ignored"""
        content = """# This is a comment
requests>=2.0
# Another comment
numpy
### Multiple hash marks
flask
"""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text(content)

        packages = parser.parse_requirements(requirements)
        assert len(packages) == 3
        assert "requests" in packages

    def test_parse_with_empty_lines(self, tmp_path):
        """Test that empty lines are ignored"""
        content = """requests

numpy


flask
"""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text(content)

        packages = parser.parse_requirements(requirements)
        assert len(packages) == 3

    def test_parse_with_editable_installs(self, tmp_path):
        """Test that -e flags are ignored"""
        content = """-e git+https://github.com/user/repo.git#egg=package
requests
-e /local/path
numpy
--editable /another/path
"""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text(content)

        packages = parser.parse_requirements(requirements)
        assert "requests" in packages
        assert "numpy" in packages
        # Editable installs should be skipped
        assert len(packages) == 2

    def test_parse_with_flags(self, tmp_path):
        """Test that pip flags are ignored"""
        content = """-r other-requirements.txt
--index-url https://pypi.org/simple
requests
--extra-index-url https://custom.pypi.org
numpy
-c constraints.txt
"""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text(content)

        packages = parser.parse_requirements(requirements)
        assert "requests" in packages
        assert "numpy" in packages

    def test_parse_empty_file(self, tmp_path):
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("")

        packages = parser.parse_requirements(requirements)
        assert packages == set()

    def test_parse_only_comments(self, tmp_path):
        content = """# Comment 1
# Comment 2
### Comment 3
"""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text(content)

        packages = parser.parse_requirements(requirements)
        assert packages == set()


class TestFindAndParse:
    """Test auto-detection and parsing"""

    def test_find_pyproject(self, sample_pyproject, monkeypatch):
        """Test auto-detection of pyproject.toml"""
        monkeypatch.chdir(sample_pyproject.parent)

        prod, dev = parser.find_and_parse()
        assert len(prod) > 0
        assert "requests" in prod

    def test_find_requirements(self, sample_requirements, monkeypatch):
        """Test auto-detection of requirements.txt"""
        monkeypatch.chdir(sample_requirements.parent)

        prod, dev = parser.find_and_parse()
        assert len(prod) > 0
        assert "requests" in prod
        assert len(dev) == 0  # No dev deps in requirements.txt alone

    def test_find_requirements_with_dev(
        self, sample_requirements, sample_requirements_dev, monkeypatch
    ):
        """Test auto-detection of requirements.txt with dev dependencies"""
        monkeypatch.chdir(sample_requirements.parent)

        prod, dev = parser.find_and_parse()
        assert len(prod) > 0
        assert len(dev) > 0
        assert "pytest" in dev

    def test_priority_pyproject_over_requirements(
        self, sample_pyproject, sample_requirements, monkeypatch
    ):
        """Test that pyproject.toml takes priority"""
        # Both files in same directory
        monkeypatch.chdir(sample_pyproject.parent)
        sample_requirements.rename(sample_pyproject.parent / "requirements.txt")

        prod, dev = parser.find_and_parse()
        # Should parse pyproject.toml, not requirements.txt
        assert "numpy" in prod

    def test_find_parse_dependency_file_not_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        with pytest.raises(FileNotFoundError):
            parser.find_and_parse()

    def test_find_multiple_dev_requirement_patterns(self, tmp_path, monkeypatch):
        """Test finding multiple dev requirement file patterns"""
        monkeypatch.chdir(tmp_path)

        # Create requirements.txt
        (tmp_path / "requirements.txt").write_text("requests")

        # Create multiple dev requirement files
        (tmp_path / "requirements-dev.txt").write_text("pytest")
        (tmp_path / "requirements-test.txt").write_text("pytest-cov")
        (tmp_path / "dev-requirements.txt").write_text("black")

        prod, dev = parser.find_and_parse()
        assert "requests" in prod
        assert "pytest" in dev
        assert "pytest-cov" in dev
        assert "black" in dev
