import argparse
import asyncio
import sys
import traceback
from pathlib import Path

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from . import parser, reporter
from .inspector import PackageInspector
from .utils import is_valid_dependency_file

console = Console()


async def async_main(args):
    with console.status("[bold green]Scanning dependency files...", spinner="dots"):
        if args.file:
            path = Path(args.file)
            if not is_valid_dependency_file(path):
                raise ValueError(
                    f"{path.name} is an invalid python dependency specification file, search PEP(735) to learn more!"
                )
            if path.name == "pyproject.toml":
                prod_deps, other_deps = parser.parse_pyproject(path)
            elif path.name == "requirements.txt":
                prod_deps = parser.parse_requirements(path)
                other_deps = {}
        else:
            prod_deps, other_deps = parser.find_and_parse()

    total = len(prod_deps) + len(other_deps)
    if total == 0:
        console.print("[yellow]Couldn't find dependencies[/yellow]")
        return
    all_packages = [(pkg, False) for pkg in prod_deps] + [
        (pkg, True) for pkg in other_deps
    ]
    inspector = PackageInspector()
    console.print(
        f"\n[bold cyan] Inspecting {total} packages[/bold cyan] "
        f"([green]{len(prod_deps)}[/green] production dependencies, [blue]{len(other_deps)}[/blue] other dependencies)"
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            "[cyan]Fetching metadata from PyPI and GitHub...", total=total
        )
        results = await inspector.inspect_all(all_packages, progress, task)
    results.sort(key=lambda x: (x.is_dev_dependency, x.name.lower()))
    reporter.display_results(results, console)


def main():
    parser_obj = argparse.ArgumentParser(
        description="Get to know about your Python project dependency informations from PyPi and GitHub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_obj.add_argument(
        "-f",
        "--file",
        help="Path to pyproject.toml or requirements.txt (will auto-detect if not specified)",
    )

    args = parser_obj.parse_args()
    try:
        asyncio.run(async_main(args))
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Unexpected error Occured:[/red] {e}", style="bold")

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
