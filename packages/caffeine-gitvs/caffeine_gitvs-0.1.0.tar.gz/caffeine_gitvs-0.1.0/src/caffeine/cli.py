"""Command-line interface for caffeine."""

import sys
import time
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from caffeine import __version__
from caffeine.config import get_config_info, get_token, remove_token, set_token
from caffeine.github import GitHubClient, GitHubError
from caffeine.ui.components import (
    create_file_tree_panel,
    create_footer,
    create_readme_panel,
    create_search_results_table,
    create_trending_table,
)
from caffeine.ui.dashboard import Dashboard
from caffeine.ui.themes import CAFFEINE_THEME

# Create console with theme
console = Console(theme=CAFFEINE_THEME)


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"[bold #c9a66b]caffeine[/] version [bold white]{__version__}[/]")
        raise typer.Exit()


def show_logo() -> None:
    """Display the caffeine ASCII logo."""
    logo = """
[bold #c9a66b]    ██████╗ █████╗ ███████╗███████╗███████╗██╗███╗   ██╗███████╗
   ██╔════╝██╔══██╗██╔════╝██╔════╝██╔════╝██║████╗  ██║██╔════╝
   ██║     ███████║█████╗  █████╗  █████╗  ██║██╔██╗ ██║█████╗  
   ██║     ██╔══██║██╔══╝  ██╔══╝  ██╔══╝  ██║██║╚██╗██║██╔══╝  
   ╚██████╗██║  ██║██║     ██║     ███████╗██║██║ ╚████║███████╗
    ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝     ╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝[/]
[dim]                    GitHub Repository Visualizer ☕[/]
"""
    console.print(logo)


# ============================================================================
# Config App (subcommand)
# ============================================================================

config_app = typer.Typer(
    name="config",
    help="Manage caffeine configuration (GitHub token, etc.)",
    no_args_is_help=True,
)


@config_app.command("set-token")
def config_set_token(
    token: str = typer.Argument(
        ...,
        help="GitHub Personal Access Token (starts with ghp_...)",
    ),
) -> None:
    """
    Save a GitHub token for authenticated API access.
    
    With a token, you get 5,000 API requests/hour instead of 60.
    
    To create a token:
    
    1. Go to GitHub → Settings → Developer Settings → Personal Access Tokens
    
    2. Create a new token (classic) - no scopes needed for public repos
    
    3. Run: caffeine config set-token YOUR_TOKEN
    """
    if not token.startswith(("ghp_", "github_pat_")):
        console.print("[yellow]⚠ Warning:[/] Token doesn't look like a GitHub PAT")
        console.print("[dim]  Expected format: ghp_... or github_pat_...[/]")
        console.print()
    
    set_token(token)
    console.print("[green]✓[/] Token saved successfully!")
    console.print(f"[dim]  Token: {token[:4]}...{token[-4:]}[/]")
    console.print()
    console.print("[dim]You now have 5,000 API requests/hour instead of 60.[/]")


@config_app.command("remove-token")
def config_remove_token() -> None:
    """Remove the saved GitHub token."""
    if remove_token():
        console.print("[green]✓[/] Token removed successfully!")
    else:
        console.print("[yellow]No token was saved.[/]")


@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    info = get_config_info()
    
    console.print()
    console.print("[bold #c9a66b]☕ Caffeine Configuration[/]")
    console.print()
    
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value")
    
    if info["has_token"]:
        table.add_row("Token", f"[green]✓ Configured[/] ({info['token_preview']})")
        table.add_row("Token source", info["token_source"])
        table.add_row("Rate limit", "[green]5,000 requests/hour[/]")
    else:
        table.add_row("Token", "[yellow]Not configured[/]")
        table.add_row("Rate limit", "[yellow]60 requests/hour[/] (unauthenticated)")
    
    table.add_row("Config file", info["config_file"])
    
    console.print(table)
    console.print()
    
    if not info["has_token"]:
        console.print("[dim]Tip: Run 'caffeine config set-token YOUR_TOKEN' to increase rate limit[/]")
        console.print()


# ============================================================================
# Main App
# ============================================================================

app = typer.Typer(
    name="caffeine",
    help="☕ Beautiful GitHub repository visualizer for terminal",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# Add config as subcommand
app.add_typer(config_app, name="config")


@app.command()
def visualize(
    repository: str = typer.Argument(
        ...,
        help="GitHub repository URL or owner/repo (e.g., python/cpython)",
        metavar="REPOSITORY",
    ),
    quick: bool = typer.Option(
        False,
        "--quick",
        "-q",
        help="Quick mode: show only essential info (faster, fewer API calls)",
    ),
    readme: bool = typer.Option(
        False,
        "--readme",
        "-r",
        help="Show README preview",
    ),
    tree: bool = typer.Option(
        False,
        "--tree",
        "-t",
        help="Show file tree structure",
    ),
    no_logo: bool = typer.Option(
        False,
        "--no-logo",
        help="Don't show the ASCII logo",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """
    Visualize a GitHub repository in your terminal.
    
    Examples:
    
        caffeine python/cpython
        
        caffeine facebook/react --quick
        
        caffeine rust-lang/rust --readme
        
        caffeine torvalds/linux --tree
    """
    dashboard = Dashboard(console=console)
    
    if not no_logo:
        dashboard.show_logo()
    
    token = get_token()
    if not token:
        console.print("[dim]  Tip: Set a GitHub token for 5,000 requests/hour → caffeine config set-token[/]\n")
    
    # Handle --readme flag
    if readme:
        start_time = time.time()
        with GitHubClient() as client:
            try:
                owner, repo = client.parse_repo_url(repository)
                with console.status(f"[dim]Fetching README for[/] [bold #c9a66b]{owner}/{repo}[/][dim]...[/]"):
                    readme_content = client.get_readme(owner, repo)
                
                fetch_time = time.time() - start_time
                console.print()
                console.print(create_readme_panel(readme_content))
                console.print(create_footer(client.rate_limit, fetch_time, client.is_authenticated))
            except GitHubError as e:
                dashboard.show_error(e)
                raise typer.Exit(code=1)
        return
    
    # Handle --tree flag
    if tree:
        start_time = time.time()
        with GitHubClient() as client:
            try:
                owner, repo = client.parse_repo_url(repository)
                with console.status(f"[dim]Fetching file tree for[/] [bold #c9a66b]{owner}/{repo}[/][dim]...[/]"):
                    items = client.get_file_tree(owner, repo)
                
                fetch_time = time.time() - start_time
                console.print()
                console.print(create_file_tree_panel(items, f"{owner}/{repo}"))
                console.print(create_footer(client.rate_limit, fetch_time, client.is_authenticated))
            except GitHubError as e:
                dashboard.show_error(e)
                raise typer.Exit(code=1)
        return
    
    # Default: show full dashboard
    success = dashboard.fetch_and_render(repository, quick=quick)
    
    if not success:
        raise typer.Exit(code=1)


@app.command()
def trending(
    language: Optional[str] = typer.Option(
        None,
        "--lang",
        "-l",
        help="Filter by programming language (e.g., python, javascript, rust)",
    ),
    since: str = typer.Option(
        "daily",
        "--since",
        "-s",
        help="Time period: daily, weekly, or monthly",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Number of repos to show (max 25)",
    ),
    no_logo: bool = typer.Option(
        False,
        "--no-logo",
        help="Don't show the ASCII logo",
    ),
) -> None:
    """
    Show trending GitHub repositories.
    
    Examples:
    
        caffeine trending
        
        caffeine trending --lang python
        
        caffeine trending --since weekly --limit 20
    """
    if not no_logo:
        show_logo()
    
    # Validate since
    if since not in ("daily", "weekly", "monthly"):
        console.print(f"[red]Invalid period: {since}. Use daily, weekly, or monthly.[/]")
        raise typer.Exit(code=1)
    
    limit = min(limit, 25)  # Cap at 25
    
    start_time = time.time()
    
    with GitHubClient() as client:
        try:
            lang_label = f" ({language})" if language else ""
            with console.status(f"[dim]Fetching trending repos{lang_label}...[/]"):
                repos = client.get_trending_repos(
                    language=language,
                    since=since,
                    limit=limit,
                )
            
            fetch_time = time.time() - start_time
            
            console.print()
            console.print(create_trending_table(repos, since))
            console.print(create_footer(client.rate_limit, fetch_time, client.is_authenticated))
            
        except GitHubError as e:
            console.print(f"[red]Error:[/] {e}")
            raise typer.Exit(code=1)


@app.command()
def search(
    query: str = typer.Argument(
        ...,
        help="Search query",
    ),
    language: Optional[str] = typer.Option(
        None,
        "--lang",
        "-l",
        help="Filter by programming language",
    ),
    min_stars: Optional[int] = typer.Option(
        None,
        "--stars",
        help="Minimum number of stars",
    ),
    sort: str = typer.Option(
        "stars",
        "--sort",
        help="Sort by: stars, forks, updated",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Number of results to show (max 25)",
    ),
    no_logo: bool = typer.Option(
        False,
        "--no-logo",
        help="Don't show the ASCII logo",
    ),
) -> None:
    """
    Search for GitHub repositories.
    
    Examples:
    
        caffeine search "machine learning"
        
        caffeine search cli --lang rust --stars 1000
        
        caffeine search "web framework" --lang python --sort stars
    """
    if not no_logo:
        show_logo()
    
    # Validate sort
    if sort not in ("stars", "forks", "updated"):
        console.print(f"[red]Invalid sort: {sort}. Use stars, forks, or updated.[/]")
        raise typer.Exit(code=1)
    
    limit = min(limit, 25)
    
    start_time = time.time()
    
    with GitHubClient() as client:
        try:
            with console.status(f"[dim]Searching for '{query}'...[/]"):
                results = client.search_repos(
                    query=query,
                    language=language,
                    min_stars=min_stars,
                    sort=sort,
                    limit=limit,
                )
            
            fetch_time = time.time() - start_time
            
            console.print()
            console.print(create_search_results_table(results, query))
            console.print(create_footer(client.rate_limit, fetch_time, client.is_authenticated))
            
        except GitHubError as e:
            console.print(f"[red]Error:[/] {e}")
            raise typer.Exit(code=1)


def main():
    """Main entry point that handles smart argument parsing."""
    args = sys.argv[1:]
    
    # Commands that should not trigger auto-insert of "visualize"
    subcommands = ("config", "trending", "search", "--help", "-h", "--version", "-v")
    
    if args and args[0] not in subcommands:
        # User is trying to visualize a repo directly
        sys.argv.insert(1, "visualize")
    
    app()


if __name__ == "__main__":
    main()
