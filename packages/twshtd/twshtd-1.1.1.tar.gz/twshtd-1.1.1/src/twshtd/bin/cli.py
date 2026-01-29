"""twshtd CLI - Git repository synchronization tool."""

import logging
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.table import Table

from twshtd.lib.config import (
    RepoConfig,
    get_default_config_path,
    parse_config,
)
from twshtd.lib.git_ops import GitOperations

_log = logging.getLogger(__name__)

__version__ = "1.1.1"

app = typer.Typer(help="twshtd - Git repository synchronization tool")
console = Console()


@dataclass
class OperationResult:
    """Result of an operation on a repository."""

    repo: RepoConfig
    operation: str
    success: bool
    message: str
    duration: float = 0.0
    skipped: bool = False  # True if repo doesn't exist (warning, not error)


@dataclass
class ResultAggregator:
    """Aggregates results from multiple operations."""

    results: list[OperationResult] = field(default_factory=list)

    def add(self, result: OperationResult) -> None:
        """Add a result."""
        self.results.append(result)

    def has_failures(self) -> bool:
        """Check if any operations failed (skipped repos don't count as failures)."""
        return any(not r.success and not r.skipped for r in self.results)

    def get_failures(self) -> list[OperationResult]:
        """Get all failed operations (excludes skipped repos)."""
        return [r for r in self.results if not r.success and not r.skipped]

    def get_skipped(self) -> list[OperationResult]:
        """Get all skipped operations."""
        return [r for r in self.results if r.skipped]

    def print_summary(self) -> None:
        """Print a summary table of all operations."""
        if not self.results:
            console.print("[dim]No operations performed[/dim]")
            return

        table = Table(title="Summary")
        table.add_column("Repository", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Duration", justify="right")
        table.add_column("Message", style="dim")

        for result in self.results:
            repo_name = result.repo.path.name
            if result.skipped:
                status = "[yellow]○[/yellow]"
            elif result.success:
                status = "[green]✓[/green]"
            else:
                status = "[red]✗[/red]"
            duration = f"{result.duration:.1f}s"
            # Truncate long messages
            message = (
                result.message[:50] + "..."
                if len(result.message) > 50
                else result.message
            )
            table.add_row(repo_name, status, duration, message)

        console.print(table)

        # Print skipped repos (warning)
        skipped = self.get_skipped()
        if skipped:
            console.print(f"\n[yellow]Skipped ({len(skipped)}):[/yellow]")
            for s in skipped:
                console.print(f"  [yellow]○[/yellow] {s.repo.path.name}: {s.message}")

        # Print failures
        failures = self.get_failures()
        if failures:
            console.print(f"\n[red]Failures ({len(failures)}):[/red]")
            for f in failures:
                console.print(f"  [red]•[/red] {f.repo.path.name}: {f.message}")

    def exit_code(self) -> int:
        """Return exit code (0 if all success, 1 if any failures)."""
        return 1 if self.has_failures() else 0


def _run_commands(
    commands: list[str],
    cwd: Path,
    label: str,
    fail_fast: bool = True,
) -> tuple[bool, str]:
    """Run multiple commands sequentially.

    Args:
        commands: List of shell commands to execute
        cwd: Working directory
        label: Label for logging (e.g., "Pre-commands", "Post-commands")
        fail_fast: If True, stop on first failure and return False
                   If False, run all commands, collect warnings

    Returns:
        (all_success, message)
    """
    if not commands:
        return True, ""

    messages: list[str] = []
    all_success = True

    for i, cmd in enumerate(commands, 1):
        try:
            subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True,
            )
            messages.append(f"{label}[{i}] OK: {cmd}")
        except subprocess.CalledProcessError as e:
            all_success = False
            stderr = e.stderr.strip() if e.stderr else "exit code non-zero"
            messages.append(f"{label}[{i}] FAILED: {cmd} ({stderr})")
            if fail_fast:
                return False, "\n".join(messages)

    return all_success, "\n".join(messages)


def _setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level."""
    log_fmt = r"%(asctime)-15s %(levelname)-7s %(message)s"
    if verbose:
        logging.basicConfig(
            format=log_fmt, level=logging.DEBUG, datefmt="%m-%d %H:%M:%S"
        )
    else:
        logging.basicConfig(
            format=log_fmt, level=logging.WARNING, datefmt="%m-%d %H:%M:%S"
        )


def _resolve_workers(workers: str | None, config_workers: int) -> int:
    """Resolve worker count from CLI flag or config.

    Args:
        workers: CLI flag value (None, "auto", or number string)
        config_workers: Default from config file

    Returns:
        Number of workers (1 = sequential)
    """
    if workers is None:
        return max(1, config_workers)
    if workers == "auto":
        return max(1, os.cpu_count() or 1)
    try:
        return max(1, int(workers))
    except ValueError:
        return 1


def _process_push_repo(repo: RepoConfig) -> OperationResult:
    """Process a single repo for push operation (thread-safe)."""
    start_time = time.time()

    # Check if repo exists (missing repos are warnings, not errors)
    if not repo.path.exists():
        duration = time.time() - start_time
        return OperationResult(
            repo, "push", True, f"Repository does not exist: {repo.path}",
            duration, skipped=True
        )

    # Run pre-commands (all must succeed, fail_fast=True)
    pre_success, pre_msg = _run_commands(
        repo.pre_commands, repo.path, "Pre-commands", fail_fast=True
    )
    if not pre_success:
        duration = time.time() - start_time
        return OperationResult(repo, "push", False, pre_msg, duration)

    # Git cleanup
    ops = GitOperations(repo.path)
    result = ops.cleanup()
    duration = time.time() - start_time

    return OperationResult(repo, "push", result.success, result.message, duration)


def _process_pull_repo(repo: RepoConfig) -> OperationResult:
    """Process a single repo for pull operation (thread-safe)."""
    start_time = time.time()

    # Check if repo exists (missing repos are warnings, not errors)
    if not repo.path.exists():
        duration = time.time() - start_time
        return OperationResult(
            repo, repo.pull_mode, True, f"Repository does not exist: {repo.path}",
            duration, skipped=True
        )

    # Git operation based on pull_mode
    ops = GitOperations(repo.path)
    if repo.pull_mode == "fetch":
        result = ops.fetch()
    else:
        result = ops.pull()

    if not result.success:
        duration = time.time() - start_time
        return OperationResult(repo, repo.pull_mode, False, result.message, duration)

    # Run post-commands (warn on failure, don't fail - fail_fast=False)
    post_success, post_msg = _run_commands(
        repo.post_commands, repo.path, "Post-commands", fail_fast=False
    )
    duration = time.time() - start_time

    # Post-command failures are warnings, not failures
    message = result.message
    if not post_success:
        message = f"{result.message} [post-cmd warning: {post_msg}]"

    return OperationResult(repo, repo.pull_mode, True, message, duration)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: Annotated[
        bool, typer.Option("-v", "--verbose", help="Enable debug logging")
    ] = False,
    version: Annotated[
        bool, typer.Option("-V", "--version", help="Show version")
    ] = False,
) -> None:
    """Git repository synchronization tool."""
    _setup_logging(verbose)
    if version:
        typer.echo(f"twshtd version: {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def push(
    config: Annotated[
        Optional[Path], typer.Option("--config", "-c", help="Config file path")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", "-n", help="Show what would be done")
    ] = False,
    workers: Annotated[
        Optional[str],
        typer.Option("--workers", "-w", help="Parallel workers (number or 'auto')"),
    ] = None,
) -> None:
    """Save/Push: Commit and push all configured repositories."""
    # Load config
    config_path = config or get_default_config_path()
    _log.debug("Loading config from %s", config_path)
    try:
        cfg = parse_config(config_path)
    except FileNotFoundError:
        console.print(f"[red]Config file not found: {config_path}[/red]")
        raise typer.Exit(1)

    enabled_repos = [r for r in cfg.repos if r.enabled]
    num_workers = _resolve_workers(workers, cfg.settings.workers)
    _log.debug("Found %d enabled repos, using %d workers", len(enabled_repos), num_workers)

    console.print(
        Panel(
            f"Synchronizing {len(enabled_repos)} repositories, {num_workers} workers",
            title="twshtd push",
        )
    )

    # Run global pre-commands (must all succeed)
    if cfg.settings.pre_commands:
        console.print("\n[bold]Global pre-commands:[/bold]")
        success, msg = _run_commands(
            cfg.settings.pre_commands, Path.cwd(), "Global", fail_fast=True
        )
        if not success:
            console.print(f"  [red]✗[/red] {msg}")
            raise typer.Exit(1)
        console.print("  [green]✓[/green] All global pre-commands passed")

    if dry_run:
        console.print("\n[yellow]Dry run - no changes will be made[/yellow]")
        for i, repo in enumerate(enabled_repos, 1):
            console.print(f"  [{i}/{len(enabled_repos)}] Would push: {repo.path}")
        raise typer.Exit(0)

    # Process repositories
    aggregator = ResultAggregator()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Pushing repos...", total=len(enabled_repos))

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(_process_push_repo, repo): repo
                for repo in enabled_repos
            }
            for future in as_completed(futures):
                result = future.result()
                aggregator.add(result)
                progress.advance(task)

    # Run global post-commands (warn on failure)
    if cfg.settings.post_commands:
        console.print("\n[bold]Global post-commands:[/bold]")
        success, msg = _run_commands(
            cfg.settings.post_commands, Path.cwd(), "Global", fail_fast=False
        )
        if not success:
            console.print(f"  [yellow]⚠[/yellow] {msg}")
        else:
            console.print("  [green]✓[/green] All global post-commands passed")

    # Summary
    console.print()
    aggregator.print_summary()
    raise typer.Exit(aggregator.exit_code())


@app.command()
def pull(
    config: Annotated[
        Optional[Path], typer.Option("--config", "-c", help="Config file path")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", "-n", help="Show what would be done")
    ] = False,
    workers: Annotated[
        Optional[str],
        typer.Option("--workers", "-w", help="Parallel workers (number or 'auto')"),
    ] = None,
) -> None:
    """Load/Pull: Commit local changes and pull from remotes."""
    # Load config
    config_path = config or get_default_config_path()
    _log.debug("Loading config from %s", config_path)
    try:
        cfg = parse_config(config_path)
    except FileNotFoundError:
        console.print(f"[red]Config file not found: {config_path}[/red]")
        raise typer.Exit(1)

    enabled_repos = [r for r in cfg.repos if r.enabled]
    num_workers = _resolve_workers(workers, cfg.settings.workers)
    _log.debug("Found %d enabled repos, using %d workers", len(enabled_repos), num_workers)

    console.print(
        Panel(
            f"Pulling {len(enabled_repos)} repositories, {num_workers} workers",
            title="twshtd pull",
        )
    )

    # Run global pre-commands (must all succeed)
    if cfg.settings.pre_commands:
        console.print("\n[bold]Global pre-commands:[/bold]")
        success, msg = _run_commands(
            cfg.settings.pre_commands, Path.cwd(), "Global", fail_fast=True
        )
        if not success:
            console.print(f"  [red]✗[/red] {msg}")
            raise typer.Exit(1)
        console.print("  [green]✓[/green] All global pre-commands passed")

    if dry_run:
        console.print("\n[yellow]Dry run - no changes will be made[/yellow]")
        for i, repo in enumerate(enabled_repos, 1):
            mode = "fetch" if repo.pull_mode == "fetch" else "pull"
            console.print(f"  [{i}/{len(enabled_repos)}] Would {mode}: {repo.path}")
        raise typer.Exit(0)

    # Process repositories
    aggregator = ResultAggregator()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Pulling repos...", total=len(enabled_repos))

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(_process_pull_repo, repo): repo
                for repo in enabled_repos
            }
            for future in as_completed(futures):
                result = future.result()
                aggregator.add(result)
                progress.advance(task)

    # Run global post-commands (warn on failure)
    if cfg.settings.post_commands:
        console.print("\n[bold]Global post-commands:[/bold]")
        success, msg = _run_commands(
            cfg.settings.post_commands, Path.cwd(), "Global", fail_fast=False
        )
        if not success:
            console.print(f"  [yellow]⚠[/yellow] {msg}")
        else:
            console.print("  [green]✓[/green] All global post-commands passed")

    # Summary
    console.print()
    aggregator.print_summary()
    raise typer.Exit(aggregator.exit_code())


@app.command()
def info(
    config: Annotated[
        Optional[Path], typer.Option("--config", "-c", help="Config file path")
    ] = None,
) -> None:
    """Show configuration and repository status."""
    config_path = config or get_default_config_path()
    try:
        cfg = parse_config(config_path)
    except FileNotFoundError:
        console.print(f"[red]Config file not found: {config_path}[/red]")
        raise typer.Exit(1)

    # Configuration section
    console.print(Panel(f"[bold]Config:[/bold] {config_path}", title="twshtd info"))

    # Settings table
    settings_table = Table(title="Settings", show_header=False)
    settings_table.add_column("Setting", style="cyan")
    settings_table.add_column("Value")
    settings_table.add_row("workers", str(cfg.settings.workers))
    console.print(settings_table)

    # Repository table
    repo_table = Table(title=f"Repositories ({len(cfg.repos)})")
    repo_table.add_column("Repository", style="cyan")
    repo_table.add_column("Path")
    repo_table.add_column("Exists", justify="center")
    repo_table.add_column("Mode")
    repo_table.add_column("Enabled", justify="center")

    for repo in cfg.repos:
        exists = "[green]✓[/green]" if repo.path.exists() else "[red]✗[/red]"
        enabled = "[green]✓[/green]" if repo.enabled else "[dim]○[/dim]"
        repo_table.add_row(
            repo.path.name, str(repo.path), exists, repo.pull_mode, enabled
        )
    console.print(repo_table)

    # Dirty directories table (if any)
    if cfg.dirty:
        dirty_table = Table(title=f"Dirty Directories ({len(cfg.dirty)})")
        dirty_table.add_column("Directory", style="cyan")
        dirty_table.add_column("Exists", justify="center")
        dirty_table.add_column("Enabled", justify="center")

        for d in cfg.dirty:
            exists = "[green]✓[/green]" if d.path.exists() else "[red]✗[/red]"
            enabled = "[green]✓[/green]" if d.enabled else "[dim]○[/dim]"
            dirty_table.add_row(str(d.path), exists, enabled)
        console.print(dirty_table)


@app.command()
def edit(
    config: Annotated[
        Optional[Path], typer.Option("--config", "-c", help="Config file path")
    ] = None,
) -> None:
    """Open configuration file in $EDITOR."""
    config_path = config or get_default_config_path()

    if not config_path.exists():
        console.print(f"[red]Config file not found: {config_path}[/red]")
        console.print("[dim]Create it or specify with --config[/dim]")
        raise typer.Exit(1)

    editor = os.environ.get("EDITOR", "vi")
    try:
        subprocess.run([editor, str(config_path)], check=True)
    except FileNotFoundError:
        console.print(f"[red]Editor not found: {editor}[/red]")
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        raise typer.Exit(e.returncode)


def _find_git_repos(directory: Path) -> list[Path]:
    """Find git repos as direct children of directory."""
    repos = []
    if not directory.exists():
        return repos
    for child in directory.iterdir():
        if child.is_dir() and (child / ".git").is_dir():
            repos.append(child)
    return sorted(repos)


def _format_status_cell(value: int | bool, zero_style: str = "dim") -> str:
    """Format a status cell value."""
    if isinstance(value, bool):
        return "[yellow]✓[/yellow]" if value else f"[{zero_style}]-[/{zero_style}]"
    if value == 0:
        return f"[{zero_style}]0[/{zero_style}]"
    return f"[yellow]{value}[/yellow]"


def _get_dirty_status(repo_path: Path, fetch_first: bool) -> tuple[Path, object]:
    """Get dirty status for a single repo (thread-safe)."""
    ops = GitOperations(repo_path)
    status = ops.get_status(fetch_first=fetch_first)
    return (repo_path, status)


@app.command()
def dirty(
    config: Annotated[
        Optional[Path], typer.Option("--config", "-c", help="Config file path")
    ] = None,
    no_fetch: Annotated[
        bool, typer.Option("--no-fetch", help="Skip git fetch before checking status")
    ] = False,
    workers: Annotated[
        Optional[str],
        typer.Option("--workers", "-w", help="Parallel workers (number or 'auto')"),
    ] = None,
) -> None:
    """Show dirty/behind/ahead status for repos in configured directories."""
    # Load config
    config_path = config or get_default_config_path()
    _log.debug("Loading config from %s", config_path)
    try:
        cfg = parse_config(config_path)
    except FileNotFoundError:
        console.print(f"[red]Config file not found: {config_path}[/red]")
        raise typer.Exit(1)

    enabled_dirs = [d for d in cfg.dirty if d.enabled]
    num_workers = _resolve_workers(workers, cfg.settings.workers)
    _log.debug("Found %d enabled dirty directories, using %d workers", len(enabled_dirs), num_workers)

    if not enabled_dirs:
        console.print("[yellow]No \\[\\[dirty]] directories configured[/yellow]")
        raise typer.Exit(0)

    # Collect all repos to scan
    all_repos: list[tuple[Path, list[Path]]] = []
    total_repo_count = 0
    for dirty_config in enabled_dirs:
        if not dirty_config.path.exists():
            continue
        repos = _find_git_repos(dirty_config.path)
        if repos:
            all_repos.append((dirty_config.path, repos))
            total_repo_count += len(repos)

    if total_repo_count == 0:
        console.print("[dim]No git repositories found[/dim]")
        raise typer.Exit(0)

    console.print(
        Panel(
            f"Scanning {total_repo_count} repos in {len(all_repos)} directories, {num_workers} workers",
            title="twshtd dirty",
        )
    )

    total_repos = 0
    total_dirty = 0
    total_behind = 0
    total_fetch_failed = 0

    # Collect results with progress bar
    results: dict[Path, list[tuple[Path, object]]] = {}
    fetch_first = not no_fetch

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning repos...", total=total_repo_count)

        all_repo_paths = [(dir_path, repo_path) for dir_path, repos in all_repos for repo_path in repos]
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(_get_dirty_status, repo_path, fetch_first): (dir_path, repo_path)
                for dir_path, repo_path in all_repo_paths
            }
            for future in as_completed(futures):
                dir_path, _ = futures[future]
                repo_path, status = future.result()
                if dir_path not in results:
                    results[dir_path] = []
                results[dir_path].append((repo_path, status))
                progress.advance(task)

    # Display tables
    for dir_path, repo_results in results.items():
        table = Table(title=str(dir_path))
        table.add_column("Repository", style="cyan")
        table.add_column("Dirty", justify="center")
        table.add_column("Behind", justify="center")
        table.add_column("Ahead", justify="center")
        table.add_column("Untracked", justify="center")

        for repo_path, status in repo_results:
            # Add warning indicator if fetch failed
            repo_name = repo_path.name
            if status.fetch_failed:
                repo_name = f"{repo_name} [yellow]⚠[/yellow]"
                total_fetch_failed += 1

            if status.error:
                _log.debug("Error getting status for %s: %s", repo_path, status.error)
                table.add_row(
                    repo_name,
                    "[red]?[/red]",
                    "[red]?[/red]",
                    "[red]?[/red]",
                    "[red]?[/red]",
                )
            else:
                table.add_row(
                    repo_name,
                    _format_status_cell(status.dirty),
                    _format_status_cell(status.behind),
                    _format_status_cell(status.ahead),
                    _format_status_cell(status.untracked),
                )

                total_repos += 1
                if status.dirty:
                    total_dirty += 1
                if status.behind > 0:
                    total_behind += 1

        console.print()
        console.print(table)

    # Summary
    console.print()
    console.print(
        f"[bold]Summary:[/bold] {total_repos} repos, "
        f"{total_dirty} dirty, {total_behind} behind"
    )
    if total_fetch_failed > 0:
        console.print(
            f"[yellow]⚠[/yellow] {total_fetch_failed} repo(s) failed to fetch "
            "(remote unreachable)"
        )


if __name__ == "__main__":
    app()
