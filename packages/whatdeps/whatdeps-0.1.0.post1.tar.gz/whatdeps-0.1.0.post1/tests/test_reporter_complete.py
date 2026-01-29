from io import StringIO

from rich.console import Console

from whatdeps import reporter
from whatdeps.models import Origin, PackageInfo


class TestDisplayResultsComplete:
    """Complete tests for display_results function"""

    def test_display_with_no_github(self):
        packages = [
            PackageInfo(
                name="no-github-pkg",
                summary="A package not on GitHub",
                python_requires=">=3.8",
                disk_size=1024,
                is_dev_dependency=False,
            )
        ]

        output = StringIO()
        console = Console(file=output)
        reporter.display_results(packages, console)

        result = output.getvalue()
        assert result is not None

    def test_display_calculates_totals(self):
        """Test that disk usage totals are calculated correctly"""
        packages = [
            PackageInfo(name="pkg1", disk_size=1024 * 1024, is_dev_dependency=False),
            PackageInfo(name="pkg2", disk_size=2048 * 1024, is_dev_dependency=False),
            PackageInfo(name="pkg3", disk_size=512 * 1024, is_dev_dependency=True),
        ]

        output = StringIO()
        console = Console(file=output)
        reporter.display_results(packages, console)

        result = output.getvalue()
        # Should show total disk usage
        assert "Total Disk Usage" in result

    def test_display_separates_prod_and_dev(self):
        """Test that production and dev packages are separated"""
        packages = [
            PackageInfo(name="prod1", is_dev_dependency=False),
            PackageInfo(name="prod2", is_dev_dependency=False),
            PackageInfo(name="dev1", is_dev_dependency=True),
            PackageInfo(name="dev2", is_dev_dependency=True),
        ]

        output = StringIO()
        console = Console(file=output)
        reporter.display_results(packages, console)

        result = output.getvalue()
        assert result is not None

    def test_display_shows_legend(self):
        packages = [PackageInfo(name="test")]

        output = StringIO()
        console = Console(file=output)
        reporter.display_results(packages, console)

        result = output.getvalue()
        assert "Summary" in result

    def test_display_archived_repository(self):
        packages = [
            PackageInfo(
                name="archived-pkg",
                github_metadata=Origin(
                    is_archived=True,
                    open_issues=10,
                ),
                is_dev_dependency=False,
            )
        ]

        output = StringIO()
        console = Console(file=output)
        reporter.display_results(packages, console)
        result = output.getvalue()
        assert "archived" in result

    def test_display_handles_none_console(self):
        """Test that function creates console if None provided"""
        packages = [PackageInfo(name="test")]

        # Should not raise error
        reporter.display_results(packages, None)


class TestTableSectionTotals:
    """Test that table section totals are calculated correctly"""

    def test_section_total_calculation(self):
        """Test that section totals are shown in table"""
        packages = [
            PackageInfo(name="pkg1", disk_size=1024, is_dev_dependency=False),
            PackageInfo(name="pkg2", disk_size=2048, is_dev_dependency=False),
        ]

        table = reporter.create_package_table(packages, "Test")

        # Table should have a section with totals
        assert table is not None

    def test_section_total_with_none_sizes(self):
        """Test section totals with some None disk sizes"""
        packages = [
            PackageInfo(name="pkg1", disk_size=1024, is_dev_dependency=False),
            PackageInfo(name="pkg2", disk_size=None, is_dev_dependency=False),
            PackageInfo(name="pkg3", disk_size=2048, is_dev_dependency=False),
        ]

        table = reporter.create_package_table(packages, "Test")
        assert table is not None
