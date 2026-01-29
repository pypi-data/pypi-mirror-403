from datetime import datetime, timezone

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .models import PackageInfo


def format_size(size_bytes: int | None) -> str:
    """
    >>> format_size(1024)
    '1.0KB'
    >>> format_size(None)
    'N/A'
    """
    if size_bytes is None:
        return "N/A"

    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def format_date(date_str: str | None) -> str:
    if not date_str:
        return "N/A"
    return date_str.split("T")[0] if "T" in date_str else date_str


def days_since(date_str: str | None) -> int | None:
    """Calculate days since a date"""
    if not date_str:
        return None
    try:
        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - date).days
    except (ValueError, AttributeError):
        return None


def create_package_table(packages: list[PackageInfo], title: str) -> Table:
    table = Table(
        title=title,
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        title_style="bold magenta",
    )

    table.add_column("package name", style="cyan", no_wrap=True, width=25)
    table.add_column("supported python version", justify="center", width=30)
    table.add_column("Size on Disk", justify="right", width=20)
    table.add_column("Last Release on PyPi", justify="center", width=25)
    table.add_column("Last Push on GitHub", justify="center", width=25)
    table.add_column("Issues (O/C) on GitHub", justify="center", width=25)
    table.add_column("Stars on GitHub", justify="center", width=20)

    section_total_size = 0

    for pkg in packages:
        if pkg.error:
            table.add_row(
                pkg.name,
                "-",
                "-",
                "-",
                "-",
                f"[red]{pkg.error}[/red]",
                "-",
                "-",
            )
            continue

        py_req = pkg.python_requires or "N/A"

        size = format_size(pkg.disk_size)
        if pkg.disk_size:
            section_total_size += pkg.disk_size

        if pkg.last_release_date:
            days = days_since(pkg.last_release_date)
            release_str = f"{format_date(pkg.last_release_date)}"
            if days is not None:
                if days < 30:
                    release_str = f"[green]{release_str}[/green]"
                elif days < 180:
                    release_str = f"[yellow]{release_str}[/yellow]"
                else:
                    release_str = f"[dim]{release_str}[/dim]"
        else:
            release_str = "N/A"

        if pkg.github_metadata:
            gh = pkg.github_metadata

            if gh.last_push_date:
                days = days_since(gh.last_push_date)
                push_str = f"{format_date(gh.last_push_date)}"
                if days is not None:
                    if days < 90:
                        push_str = f"[green]{push_str}[/green]"
                    elif days < 365:
                        push_str = f"[yellow]{push_str}[/yellow]"
                    else:
                        push_str = f"[red]{push_str}[/red]"
            else:
                push_str = "N/A"
            if gh.total_issues > 0:
                ratio = gh.closed_issues / gh.total_issues
                if ratio > 0.8:
                    issue_color = "green"
                elif ratio > 0.6:
                    issue_color = "yellow"
                else:
                    issue_color = "red"
                issues_str = f"[{issue_color}]{gh.open_issues}/{gh.closed_issues}[/{issue_color}]"
            else:
                issues_str = "[dim]0/0[/dim]"

            if gh.stars > 1000:
                stars_str = f"[bold]{gh.stars:,}[/bold]"
            elif gh.stars > 100:
                stars_str = f"{gh.stars:,}"
            else:
                stars_str = f"[dim]{gh.stars}[/dim]"

        else:
            push_str = "[dim]No GitHub[/dim]"
            issues_str = "-"
            stars_str = "-"

        table.add_row(
            pkg.name,
            py_req,
            size,
            release_str,
            push_str,
            issues_str,
            stars_str,
        )

    if section_total_size > 0:
        table.add_section()
        table.add_row(
            "",
            f"[bold]Total ({len(packages)} packages)[/bold]",
            "",
            f"[bold]{format_size(section_total_size)}[/bold]",
            "",
            "",
            "",
        )

    return table


def display_results(packages: list[PackageInfo], console: Console = None) -> None:
    if console is None:
        console = Console()

    if not packages:
        console.print("[yellow]couldn't find any python package to display![/yellow]")
        return

    prod_deps = [p for p in packages if not p.is_dev_dependency]
    other_deps = [p for p in packages if p.is_dev_dependency]

    if prod_deps:
        console.print()
        console.print(create_package_table(prod_deps, "Production Dependencies"))

    if other_deps:
        console.print()
        console.print(create_package_table(other_deps, "Other Dependencies"))

    total_prod_size = sum(p.disk_size or 0 for p in prod_deps)
    total_dev_size = sum(p.disk_size or 0 for p in other_deps)
    total_size = total_prod_size + total_dev_size

    summary = Panel(
        f"[bold]Total Packages:[/bold]  {len(packages)}\n"
        f"[bold]Total Disk Usage:[/bold] {format_size(total_size)}\n\n"
        f"[dim]Issues shown as Open/Closed ratio",
        title="Summary",
        border_style="green",
    )

    console.print()
    console.print(summary)
