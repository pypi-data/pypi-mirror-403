"""Main dashboard renderer for caffeine."""

import time
from typing import Optional

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from caffeine.github import GitHubClient, GitHubError, RateLimitError, RepoNotFoundError
from caffeine.models import Issue, RateLimitInfo, Repository
from caffeine.ui.components import (
    create_commits_panel,
    create_contributors_panel,
    create_footer,
    create_header,
    create_issues_panel_with_recent,
    create_languages_panel,
    create_releases_panel,
    create_stats_row,
)
from caffeine.ui.themes import CAFFEINE_THEME


class Dashboard:
    """Main dashboard for displaying repository information."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the dashboard.
        
        Args:
            console: Rich console instance. If None, creates one with theme.
        """
        self.console = console or Console(theme=CAFFEINE_THEME)
    
    def show_logo(self) -> None:
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
        self.console.print(logo)
    
    def show_loading(self, repo_path: str) -> None:
        """Show loading message."""
        self.console.print(f"\n[dim]  Fetching data for[/] [bold #c9a66b]{repo_path}[/][dim]...[/]\n")
    
    def show_error(self, error: Exception, is_authenticated: bool = False) -> None:
        """Display an error message."""
        if isinstance(error, RepoNotFoundError):
            self.console.print(f"\n[bold red]  ✗ Repository not found[/]")
            self.console.print(f"[dim]    Make sure the repository exists and is public.[/]\n")
        elif isinstance(error, RateLimitError):
            self.console.print(f"\n[bold yellow]  ⚠ Rate limit exceeded[/]")
            if is_authenticated:
                self.console.print(f"[dim]    You've used all 5,000 requests/hour.[/]")
            else:
                self.console.print(f"[dim]    GitHub allows 60 requests/hour without authentication.[/]")
                self.console.print(f"[dim]    Set a token for 5,000/hour: caffeine config set-token YOUR_TOKEN[/]")
            self.console.print(f"[dim]    Please wait a while before trying again.[/]\n")
        elif isinstance(error, GitHubError):
            self.console.print(f"\n[bold red]  ✗ GitHub API error:[/] {error}\n")
        else:
            self.console.print(f"\n[bold red]  ✗ Error:[/] {error}\n")
    
    def render(
        self,
        repo: Repository,
        rate_limit: RateLimitInfo,
        fetch_time: float,
        quick: bool = False,
        is_authenticated: bool = False,
        recent_issues: list[Issue] = None,
    ) -> None:
        """Render the full dashboard.
        
        Args:
            repo: Repository data to display.
            rate_limit: Current rate limit info.
            fetch_time: Time taken to fetch data.
            quick: If True, show only essential info.
            is_authenticated: Whether the client is using a token.
            recent_issues: List of recent open issues.
        """
        recent_issues = recent_issues or []
        
        self.console.print()
        
        # Header with basic info
        self.console.print(create_header(repo))
        
        # Stats row
        self.console.print(create_stats_row(repo))
        
        if quick:
            # Quick mode: only show languages
            self.console.print(create_languages_panel(repo.languages))
        else:
            # Full mode: show everything
            self.console.print(create_languages_panel(repo.languages))
            self.console.print()
            self.console.print(create_commits_panel(repo.commit_activity))
            self.console.print()
            self.console.print(create_contributors_panel(repo.contributors))
            self.console.print()
            self.console.print(create_issues_panel_with_recent(repo.issue_stats, recent_issues))
            self.console.print()
            self.console.print(create_releases_panel(repo.releases))
        
        # Footer
        self.console.print(create_footer(rate_limit, fetch_time, is_authenticated))
    
    def fetch_and_render(
        self,
        repo_url: str,
        quick: bool = False,
    ) -> bool:
        """Fetch repository data and render the dashboard.
        
        Args:
            repo_url: GitHub repository URL or owner/repo string.
            quick: If True, fetch and show only essential info.
            
        Returns:
            True if successful, False otherwise.
        """
        start_time = time.time()
        
        with GitHubClient() as client:
            try:
                # Parse the URL first to show in loading message
                owner, repo = client.parse_repo_url(repo_url)
                repo_path = f"{owner}/{repo}"
                
                recent_issues = []
                
                # Show loading with spinner
                with self.console.status(
                    f"[dim]Fetching data for[/] [bold #c9a66b]{repo_path}[/][dim]...[/]",
                    spinner="dots",
                    spinner_style="#c9a66b",
                ):
                    if quick:
                        # Quick mode: only basic info and languages
                        repository = client.get_repository(owner, repo)
                        repository.languages = client.get_languages(owner, repo)
                    else:
                        # Full mode: fetch everything
                        repository = client.fetch_full_repository(repo_url)
                        # Also fetch recent issues for the panel
                        recent_issues = client.get_recent_issues(owner, repo, limit=3)
                
                fetch_time = time.time() - start_time
                
                # Render the dashboard
                self.render(
                    repository, 
                    client.rate_limit, 
                    fetch_time, 
                    quick=quick,
                    is_authenticated=client.is_authenticated,
                    recent_issues=recent_issues,
                )
                return True
                
            except (GitHubError, ValueError) as e:
                self.show_error(e)
                return False

