import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

from whatdeps import cli
from whatdeps.models import PackageInfo


@pytest.mark.anyio
class TestAsyncMain:
    async def test_async_main_success(self, sample_pyproject, monkeypatch):
        monkeypatch.chdir(sample_pyproject.parent)

        # Mock args
        args = Mock()
        args.file = None

        # Mock PackageInfo results
        mock_results = [
            PackageInfo(
                name="requests",
                summary="HTTP library",
                python_requires=">=3.7",
                is_dev_dependency=False,
            ),
            PackageInfo(
                name="pytest",
                summary="Testing framework",
                python_requires=">=3.8",
                is_dev_dependency=True,
            ),
        ]

        # Mock inspector
        mock_inspector = Mock()
        mock_inspector.inspect_all = AsyncMock(return_value=mock_results)

        with patch("whatdeps.cli.PackageInspector", return_value=mock_inspector):
            with patch("whatdeps.cli.reporter.display_results"):
                await cli.async_main(args)

        # Verify inspect_all was called
        mock_inspector.inspect_all.assert_called_once()

    async def test_async_main_with_file_pyproject(self, sample_pyproject):
        """Test with explicit pyproject.toml file"""
        args = Mock()
        args.file = str(sample_pyproject)

        mock_inspector = Mock()
        mock_inspector.inspect_all = AsyncMock(return_value=[])

        with patch("whatdeps.cli.PackageInspector", return_value=mock_inspector):
            with patch("whatdeps.cli.reporter.display_results"):
                await cli.async_main(args)

    async def test_async_main_with_file_requirements(self, sample_requirements):
        """Test with explicit requirements.txt file"""
        args = Mock()
        args.file = str(sample_requirements)

        mock_inspector = Mock()
        mock_inspector.inspect_all = AsyncMock(return_value=[])

        with patch("whatdeps.cli.PackageInspector", return_value=mock_inspector):
            with patch("whatdeps.cli.reporter.display_results"):
                await cli.async_main(args)

    async def test_async_main_with_unsupported_file(self, tmp_path):
        bad_file = tmp_path / "random.txt"
        bad_file.write_text("some random content")

        args = Mock()
        args.file = str(bad_file)

        with pytest.raises(ValueError):
            await cli.async_main(args)

    async def test_async_main_progress_tracking(self, sample_pyproject, monkeypatch):
        """Test that progress bar is used correctly"""
        monkeypatch.chdir(sample_pyproject.parent)

        args = Mock()
        args.file = None

        mock_results = [
            PackageInfo(name="pkg1", is_dev_dependency=False),
            PackageInfo(name="pkg2", is_dev_dependency=False),
        ]

        mock_inspector = Mock()
        mock_inspector.inspect_all = AsyncMock(return_value=mock_results)

        with patch("whatdeps.cli.PackageInspector", return_value=mock_inspector):
            with patch("whatdeps.cli.reporter.display_results"):
                await cli.async_main(args)

                # Verify inspect_all was called with progress
                mock_inspector.inspect_all.assert_called_once()


class TestMain:
    """Test main entry point"""

    def test_main_success(self, sample_pyproject, monkeypatch):
        """Test successful main execution"""
        monkeypatch.chdir(sample_pyproject.parent)

        with patch.object(sys, "argv", ["prog"]):
            with patch("whatdeps.cli.asyncio.run") as mock_run:
                cli.main()

                # Verify asyncio.run was called
                mock_run.assert_called_once()

    def test_main_with_file_argument(self, sample_pyproject):
        """Test main with -f/--file argument"""
        with patch.object(sys, "argv", ["prog", "-f", str(sample_pyproject)]):
            with patch("whatdeps.cli.asyncio.run") as mock_run:
                cli.main()

                mock_run.assert_called_once()

    def test_main_file_not_found_error(self):
        """Test main handles FileNotFoundError"""
        args = ["prog"]

        with patch.object(sys, "argv", args):
            with patch(
                "whatdeps.cli.asyncio.run", side_effect=FileNotFoundError("No files")
            ):
                with pytest.raises(SystemExit) as exc_info:
                    cli.main()

                assert exc_info.value.code == 1

    def test_main_value_error(self, tmp_path):
        """Test main handles ValueError (unsupported file)"""
        bad_file = tmp_path / "bad.txt"
        bad_file.write_text("content")

        with patch.object(sys, "argv", ["prog", "-f", str(bad_file)]):
            with patch(
                "whatdeps.cli.asyncio.run", side_effect=ValueError("Unsupported")
            ):
                with pytest.raises(SystemExit) as exc_info:
                    cli.main()

                assert exc_info.value.code == 1

    def test_main_keyboard_interrupt(self):
        """Test main handles KeyboardInterrupt"""
        with patch.object(sys, "argv", ["prog"]):
            with patch("whatdeps.cli.asyncio.run", side_effect=KeyboardInterrupt()):
                with pytest.raises(SystemExit) as exc_info:
                    cli.main()

                assert exc_info.value.code == 130

    def test_main_unexpected_error(self):
        """Test main handles unexpected errors"""
        with patch.object(sys, "argv", ["prog"]):
            with patch("whatdeps.cli.asyncio.run", side_effect=Exception("Boom!")):
                with pytest.raises(SystemExit) as exc_info:
                    cli.main()

                assert exc_info.value.code == 1

    def test_main_creates_argument_parser(self):
        with patch("whatdeps.cli.argparse.ArgumentParser") as mock_parser_class:
            mock_parser = Mock()
            mock_parser.parse_args.return_value = Mock(file=None)
            mock_parser_class.return_value = mock_parser

            with patch("whatdeps.cli.asyncio.run"):
                cli.main()

            # Verify ArgumentParser was created
            mock_parser_class.assert_called_once()

            # Verify it has the right description
            call_kwargs = mock_parser_class.call_args[1]
            assert "description" in call_kwargs

    def test_main_parses_file_argument(self):
        """Test that -f argument is parsed correctly"""
        test_file = "test_requirements.txt"

        with patch.object(sys, "argv", ["prog", "-f", test_file]):
            with patch("whatdeps.cli.asyncio.run") as mock_run:
                cli.main()

                # asyncio.run should be called
                mock_run.assert_called_once()

                # Get the coroutine that was passed
                coro = mock_run.call_args[0][0]

                # Clean up coroutine
                import inspect

                if inspect.iscoroutine(coro):
                    coro.close()
