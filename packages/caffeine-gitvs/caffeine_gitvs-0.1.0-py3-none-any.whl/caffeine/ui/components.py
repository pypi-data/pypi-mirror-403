"""Rich UI components for visualizing repository data."""

from datetime import datetime, timezone
from typing import Optional

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from rich.markdown import Markdown
from rich.tree import Tree

from caffeine.models import (
    CommitActivity,
    Contributor,
    FileTreeItem,
    Issue,
    IssueStats,
    LanguageStats,
    RateLimitInfo,
    Release,
    Repository,
    SearchResult,
    TrendingRepo,
)


def format_number(n: int) -> str:
    """Format large numbers with K/M suffix."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def time_ago(dt: Optional[datetime]) -> str:
    """Format datetime as relative time."""
    if not dt:
        return "Unknown"
    
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f"{mins} min{'s' if mins != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 2592000:  # 30 days
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 31536000:  # 365 days
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


def create_header(repo: Repository) -> Panel:
    """Create the main header panel with repo info."""
    # Title with repo name
    title = Text()
    title.append("☕ ", style="bold yellow")
    title.append("CAFFEINE", style="bold #c9a66b")
    title.append("  ", style="")
    title.append(repo.full_name, style="bold white")
    
    # Description
    content = Text()
    if repo.description:
        content.append(repo.description, style="#f5e6d3")
    else:
        content.append("No description provided", style="dim")
    content.append("\n")
    
    # Metadata line
    meta = Text()
    if repo.homepage:
        meta.append("🌐 ", style="")
        meta.append(repo.homepage, style="#61afef underline")
        meta.append("  │  ", style="dim")
    
    if repo.license_name:
        meta.append("📜 ", style="")
        meta.append(repo.license_name, style="#d4a574")
        meta.append("  │  ", style="dim")
    
    if repo.created_at:
        meta.append("Created: ", style="dim")
        meta.append(time_ago(repo.created_at), style="#a0a0a0")
    
    content.append(meta)
    
    # Topics
    if repo.topics:
        content.append("\n")
        topics_text = Text()
        for topic in repo.topics[:5]:  # Limit to 5 topics
            topics_text.append(f" {topic} ", style="on #3d3d3d #c9a66b")
            topics_text.append(" ", style="")
        content.append(topics_text)
    
    return Panel(
        content,
        title=title,
        border_style="#8b6f47",
        padding=(0, 1),
    )


def create_stats_row(repo: Repository) -> Text:
    """Create the stats row with stars, forks, etc."""
    stats = Text()
    stats.append("  ")
    
    # Stars
    stats.append("⭐ ", style="yellow")
    stats.append(format_number(repo.stars), style="bold white")
    stats.append("     ", style="")
    
    # Forks
    stats.append("🍴 ", style="#d4a574")
    stats.append(format_number(repo.forks), style="bold white")
    stats.append("     ", style="")
    
    # Watchers
    stats.append("👁️  ", style="#61afef")
    stats.append(format_number(repo.watchers), style="bold white")
    stats.append("     ", style="")
    
    # Size
    stats.append("📦 ", style="#98c379")
    stats.append(repo.size_human, style="bold white")
    stats.append("     ", style="")
    
    # Default branch
    stats.append("🔀 ", style="#c678dd")
    stats.append(repo.default_branch, style="bold white")
    
    # Flags
    if repo.is_archived:
        stats.append("     ")
        stats.append("📦 ARCHIVED", style="bold #e5c07b")
    
    if repo.is_fork:
        stats.append("     ")
        stats.append("🔱 FORK", style="#a0a0a0")
    
    stats.append("\n")
    return stats


def create_languages_panel(languages: Optional[LanguageStats]) -> Panel:
    """Create the languages panel with progress bars."""
    if not languages or not languages.languages:
        content = Text("No language data available", style="dim")
        return Panel(content, title="[bold #c9a66b]Languages", border_style="#8b6f47")
    
    sorted_langs = languages.get_sorted()
    
    # Create a simple text-based visualization
    lines = []
    
    # Color palette for languages
    lang_colors = [
        "#61afef",  # Blue
        "#98c379",  # Green
        "#e5c07b",  # Yellow
        "#c678dd",  # Purple
        "#e06c75",  # Red
        "#56b6c2",  # Cyan
        "#d19a66",  # Orange
    ]
    
    for i, (lang, _, percent) in enumerate(sorted_langs[:6]):  # Top 6 languages
        color = lang_colors[i % len(lang_colors)]
        
        # Create progress bar manually
        bar_width = 30
        filled = int((percent / 100) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        line = Text()
        line.append(f"  {lang:<12}", style="#f5e6d3")
        line.append(bar, style=color)
        line.append(f"  {percent:>5.1f}%", style="#a0a0a0")
        lines.append(line)
    
    content = Text("\n").join(lines)
    return Panel(content, title="[bold #c9a66b]Languages", border_style="#8b6f47")


def create_sparkline(values: list[int], width: int = 50) -> str:
    """Create a sparkline from values."""
    if not values:
        return ""
    
    # Sparkline characters (8 levels)
    chars = " ▁▂▃▄▅▆▇█"
    
    max_val = max(values) if max(values) > 0 else 1
    
    # Sample values if too many
    if len(values) > width:
        step = len(values) / width
        sampled = [values[int(i * step)] for i in range(width)]
    else:
        sampled = values
    
    # Convert to sparkline
    sparkline = ""
    for val in sampled:
        idx = int((val / max_val) * (len(chars) - 1))
        sparkline += chars[idx]
    
    return sparkline


def create_commits_panel(activity: Optional[CommitActivity]) -> Panel:
    """Create the commit activity panel with sparkline."""
    if not activity or not activity.weekly_commits:
        content = Text("No commit data available (stats may still be computing)", style="dim")
        return Panel(content, title="[bold #c9a66b]Commit Activity (52 weeks)", border_style="#8b6f47")
    
    lines = []
    
    # Sparkline
    sparkline = create_sparkline(activity.weekly_commits, width=52)
    spark_text = Text()
    spark_text.append("  ", style="")
    spark_text.append(sparkline, style="#c9a66b")
    lines.append(spark_text)
    
    # Stats line
    stats = Text()
    stats.append("\n  ")
    stats.append("Total: ", style="dim")
    stats.append(format_number(activity.total), style="bold white")
    stats.append("  │  ", style="dim")
    stats.append("Avg: ", style="dim")
    stats.append(f"{activity.average:.0f}/week", style="#a0a0a0")
    stats.append("  │  ", style="dim")
    stats.append("Peak: ", style="dim")
    stats.append(f"{activity.peak}", style="#98c379")
    stats.append(f" (Week {activity.peak_week})", style="dim")
    lines.append(stats)
    
    content = Text("").join(lines)
    return Panel(content, title="[bold #c9a66b]Commit Activity (52 weeks)", border_style="#8b6f47")


def create_contributors_panel(contributors: list[Contributor]) -> Panel:
    """Create the contributors table."""
    if not contributors:
        content = Text("No contributor data available", style="dim")
        return Panel(content, title="[bold #c9a66b]Top Contributors", border_style="#8b6f47")
    
    table = Table(
        show_header=True,
        header_style="bold #c9a66b",
        border_style="#8b6f47",
        box=None,
        padding=(0, 1),
    )
    
    table.add_column("#", style="#c9a66b", width=3)
    table.add_column("Username", style="#f5e6d3")
    table.add_column("Commits", justify="right", style="#d4a574")
    table.add_column("Contribution", width=20)
    
    max_commits = contributors[0].contributions if contributors else 1
    
    for i, contrib in enumerate(contributors[:5], 1):
        # Create mini progress bar
        bar_width = 15
        percent = (contrib.contributions / max_commits) * 100
        filled = int((percent / 100) * bar_width)
        bar = Text()
        bar.append("█" * filled, style="#61afef")
        bar.append("░" * (bar_width - filled), style="#3d3d3d")
        
        table.add_row(
            str(i),
            f"@{contrib.username}",
            format_number(contrib.contributions),
            bar,
        )
    
    return Panel(table, title="[bold #c9a66b]Top Contributors", border_style="#8b6f47")


def create_issues_panel(stats: Optional[IssueStats]) -> Panel:
    """Create the issues and PRs panel."""
    if not stats:
        content = Text("No issue data available", style="dim")
        return Panel(content, title="[bold #c9a66b]Issues & Pull Requests", border_style="#8b6f47")
    
    lines = []
    
    # Issues section
    issues_line = Text()
    issues_line.append("  Issues        ", style="bold #f5e6d3")
    issues_line.append("Open: ", style="dim")
    issues_line.append(format_number(stats.open_issues), style="#e5c07b")
    issues_line.append("    Closed: ", style="dim")
    issues_line.append(format_number(stats.closed_issues), style="#98c379")
    lines.append(issues_line)
    
    # Issues progress bar
    if stats.total_issues > 0:
        bar_width = 20
        filled = int((stats.issue_close_rate / 100) * bar_width)
        bar_line = Text()
        bar_line.append("                ", style="")
        bar_line.append("█" * filled, style="#98c379")
        bar_line.append("░" * (bar_width - filled), style="#3d3d3d")
        bar_line.append(f" {stats.issue_close_rate:.0f}% closed", style="dim")
        lines.append(bar_line)
    
    lines.append(Text(""))
    
    # PRs section
    prs_line = Text()
    prs_line.append("  Pull Requests ", style="bold #f5e6d3")
    prs_line.append("Open: ", style="dim")
    prs_line.append(format_number(stats.open_prs), style="#61afef")
    prs_line.append("    Merged: ", style="dim")
    prs_line.append(format_number(stats.merged_prs), style="#98c379")
    lines.append(prs_line)
    
    # PRs progress bar
    if stats.total_prs > 0:
        bar_width = 20
        filled = int((stats.pr_merge_rate / 100) * bar_width)
        bar_line = Text()
        bar_line.append("                ", style="")
        bar_line.append("█" * filled, style="#98c379")
        bar_line.append("░" * (bar_width - filled), style="#3d3d3d")
        bar_line.append(f" {stats.pr_merge_rate:.0f}% merged", style="dim")
        lines.append(bar_line)
    
    content = Text("\n").join(lines)
    return Panel(content, title="[bold #c9a66b]Issues & Pull Requests", border_style="#8b6f47")


def create_releases_panel(releases: list[Release]) -> Panel:
    """Create the releases timeline."""
    if not releases:
        content = Text("No releases found", style="dim")
        return Panel(content, title="[bold #c9a66b]Recent Releases", border_style="#8b6f47")
    
    lines = []
    
    for i, release in enumerate(releases[:5]):
        line = Text()
        
        # Timeline marker
        if i == 0:
            line.append("  ● ", style="#98c379")
        else:
            line.append("  ○ ", style="#8b6f47")
        
        # Tag name
        line.append(release.tag_name, style="bold #c9a66b" if i == 0 else "#c9a66b")
        
        # Date
        if release.published_at:
            line.append(f"  {time_ago(release.published_at)}", style="dim")
        
        # Latest badge
        if i == 0:
            line.append("  (Latest)", style="#98c379")
        
        # Prerelease badge
        if release.is_prerelease:
            line.append("  [pre-release]", style="#e5c07b")
        
        lines.append(line)
    
    content = Text("\n").join(lines)
    return Panel(content, title="[bold #c9a66b]Recent Releases", border_style="#8b6f47")


def create_footer(
    rate_limit: RateLimitInfo, 
    fetch_time: float,
    is_authenticated: bool = False,
) -> Text:
    """Create the footer with rate limit and timing info."""
    footer = Text()
    footer.append("\n  ")
    footer.append(f"Fetched in {fetch_time:.1f}s", style="dim")
    footer.append("  │  ", style="dim")
    
    # Show authentication status
    if is_authenticated:
        footer.append("🔑 ", style="")
    
    footer.append("Rate limit: ", style="dim")
    
    # Color based on remaining requests
    if rate_limit.is_exhausted:
        style = "#e06c75"
    elif rate_limit.is_low:
        style = "#e5c07b"
    else:
        style = "#98c379"
    
    footer.append(f"{rate_limit.remaining}/{rate_limit.limit}", style=style)
    footer.append(" remaining", style="dim")
    
    if rate_limit.is_low and rate_limit.reset_at:
        footer.append(f"  (resets {time_ago(rate_limit.reset_at)})", style="dim")
    
    footer.append("\n")
    return footer


# ============================================================================
# New Feature Components
# ============================================================================

def create_issues_panel_with_recent(
    stats: Optional[IssueStats],
    recent_issues: list[Issue],
) -> Panel:
    """Create the issues panel with recent issues list."""
    if not stats:
        content = Text("No issue data available", style="dim")
        return Panel(content, title="[bold #c9a66b]Issues & Pull Requests", border_style="#8b6f47")
    
    lines = []
    
    # Issues section
    issues_line = Text()
    issues_line.append("  Issues        ", style="bold #f5e6d3")
    issues_line.append("Open: ", style="dim")
    issues_line.append(format_number(stats.open_issues), style="#e5c07b")
    issues_line.append("    Closed: ", style="dim")
    issues_line.append(format_number(stats.closed_issues), style="#98c379")
    lines.append(issues_line)
    
    # Issues progress bar
    if stats.total_issues > 0:
        bar_width = 20
        filled = int((stats.issue_close_rate / 100) * bar_width)
        bar_line = Text()
        bar_line.append("                ", style="")
        bar_line.append("█" * filled, style="#98c379")
        bar_line.append("░" * (bar_width - filled), style="#3d3d3d")
        bar_line.append(f" {stats.issue_close_rate:.0f}% closed", style="dim")
        lines.append(bar_line)
    
    lines.append(Text(""))
    
    # PRs section
    prs_line = Text()
    prs_line.append("  Pull Requests ", style="bold #f5e6d3")
    prs_line.append("Open: ", style="dim")
    prs_line.append(format_number(stats.open_prs), style="#61afef")
    prs_line.append("    Merged: ", style="dim")
    prs_line.append(format_number(stats.merged_prs), style="#98c379")
    lines.append(prs_line)
    
    # PRs progress bar
    if stats.total_prs > 0:
        bar_width = 20
        filled = int((stats.pr_merge_rate / 100) * bar_width)
        bar_line = Text()
        bar_line.append("                ", style="")
        bar_line.append("█" * filled, style="#98c379")
        bar_line.append("░" * (bar_width - filled), style="#3d3d3d")
        bar_line.append(f" {stats.pr_merge_rate:.0f}% merged", style="dim")
        lines.append(bar_line)
    
    # Recent issues section
    if recent_issues:
        lines.append(Text(""))
        lines.append(Text("  ─── Recent Open Issues ───", style="dim"))
        lines.append(Text(""))
        
        for issue in recent_issues[:3]:
            issue_line = Text()
            issue_line.append("  ", style="")
            issue_line.append(f"#{issue.number}", style="bold #61afef")
            issue_line.append(" ", style="")
            
            # Truncate title if too long
            title = issue.title[:50] + "..." if len(issue.title) > 50 else issue.title
            issue_line.append(title, style="#f5e6d3")
            
            # Labels
            if issue.labels:
                issue_line.append(" ", style="")
                for label in issue.labels[:2]:
                    issue_line.append(f" {label} ", style="on #3d3d3d #e5c07b")
                    issue_line.append(" ", style="")
            
            lines.append(issue_line)
            
            # Issue metadata
            meta_line = Text()
            meta_line.append(f"     @{issue.author}", style="dim")
            if issue.created_at:
                meta_line.append(f" • {time_ago(issue.created_at)}", style="dim")
            if issue.comments_count > 0:
                meta_line.append(f" • 💬 {issue.comments_count}", style="dim")
            lines.append(meta_line)
    
    content = Text("\n").join(lines)
    return Panel(content, title="[bold #c9a66b]Issues & Pull Requests", border_style="#8b6f47")


def create_readme_panel(readme_content: Optional[str]) -> Panel:
    """Create a panel with README preview."""
    if not readme_content:
        content = Text("No README found", style="dim")
        return Panel(content, title="[bold #c9a66b]📖 README", border_style="#8b6f47")
    
    # Truncate if too long
    max_length = 2000
    if len(readme_content) > max_length:
        readme_content = readme_content[:max_length] + "\n\n... (truncated)"
    
    # Render as markdown
    md = Markdown(readme_content)
    
    return Panel(
        md,
        title="[bold #c9a66b]📖 README",
        border_style="#8b6f47",
        padding=(1, 2),
    )


def create_file_tree_panel(items: list[FileTreeItem], repo_name: str) -> Panel:
    """Create a file tree panel."""
    if not items:
        content = Text("No files found", style="dim")
        return Panel(content, title="[bold #c9a66b]📁 File Tree", border_style="#8b6f47")
    
    # Build tree structure
    tree = Tree(f"[bold #c9a66b]📁 {repo_name}[/]")
    
    # Create a dict to hold tree nodes by path
    nodes: dict[str, Tree] = {"": tree}
    
    # Sort items so directories come first, then by path
    sorted_items = sorted(items, key=lambda x: (not x.is_directory, x.path))
    
    for item in sorted_items[:50]:  # Limit to 50 items for readability
        parts = item.path.split("/")
        
        # Find or create parent node
        parent_path = "/".join(parts[:-1])
        parent = nodes.get(parent_path, tree)
        
        # Create node
        if item.is_directory:
            icon = "📁"
            style = "#c9a66b"
        else:
            # Choose icon based on file extension
            ext = item.name.split(".")[-1].lower() if "." in item.name else ""
            icon_map = {
                "py": "🐍",
                "js": "📜",
                "ts": "📘",
                "json": "📋",
                "md": "📝",
                "txt": "📄",
                "yml": "⚙️",
                "yaml": "⚙️",
                "toml": "⚙️",
                "sh": "🔧",
                "css": "🎨",
                "html": "🌐",
                "rs": "🦀",
                "go": "🐹",
                "java": "☕",
                "rb": "💎",
            }
            icon = icon_map.get(ext, "📄")
            style = "#f5e6d3"
        
        label = f"{icon} [{ style}]{item.name}[/]"
        if not item.is_directory and item.size > 0:
            size_str = f"{item.size / 1024:.1f} KB" if item.size > 1024 else f"{item.size} B"
            label += f" [dim]({size_str})[/]"
        
        node = parent.add(label)
        nodes[item.path] = node
    
    if len(items) > 50:
        tree.add(f"[dim]... and {len(items) - 50} more files[/]")
    
    return Panel(
        tree,
        title="[bold #c9a66b]📁 File Tree",
        border_style="#8b6f47",
        padding=(0, 1),
    )


def create_trending_table(repos: list[TrendingRepo], since: str = "daily") -> Panel:
    """Create a table of trending repositories."""
    period_labels = {
        "daily": "Today",
        "weekly": "This Week",
        "monthly": "This Month",
    }
    period = period_labels.get(since, "Today")
    
    if not repos:
        content = Text("No trending repos found", style="dim")
        return Panel(content, title=f"[bold #c9a66b]🔥 Trending {period}", border_style="#8b6f47")
    
    table = Table(
        show_header=True,
        header_style="bold #c9a66b",
        border_style="#8b6f47",
        box=None,
        padding=(0, 1),
    )
    
    table.add_column("#", style="#c9a66b", width=3)
    table.add_column("Repository", style="#f5e6d3", max_width=35)
    table.add_column("Language", style="#61afef", width=12)
    table.add_column("⭐", justify="right", style="yellow")
    table.add_column("🍴", justify="right", style="#d4a574")
    
    for i, repo in enumerate(repos[:10], 1):
        # Truncate description
        desc = repo.description or ""
        if len(desc) > 40:
            desc = desc[:37] + "..."
        
        name_text = Text()
        name_text.append(repo.full_name, style="bold #f5e6d3")
        if desc:
            name_text.append(f"\n{desc}", style="dim")
        
        table.add_row(
            str(i),
            name_text,
            repo.language or "-",
            format_number(repo.stars),
            format_number(repo.forks),
        )
    
    return Panel(
        table,
        title=f"[bold #c9a66b]🔥 Trending {period}",
        border_style="#8b6f47",
    )


def create_search_results_table(results: SearchResult, query: str) -> Panel:
    """Create a table of search results."""
    if not results.repos:
        content = Text(f"No repositories found for '{query}'", style="dim")
        return Panel(content, title="[bold #c9a66b]🔍 Search Results", border_style="#8b6f47")
    
    header = Text()
    header.append(f"Found ", style="dim")
    header.append(format_number(results.total_count), style="bold white")
    header.append(f" repositories for ", style="dim")
    header.append(f"'{query}'", style="#c9a66b")
    
    table = Table(
        show_header=True,
        header_style="bold #c9a66b",
        border_style="#8b6f47",
        box=None,
        padding=(0, 1),
    )
    
    table.add_column("#", style="#c9a66b", width=3)
    table.add_column("Repository", style="#f5e6d3", max_width=40)
    table.add_column("Language", style="#61afef", width=12)
    table.add_column("⭐", justify="right", style="yellow")
    table.add_column("🍴", justify="right", style="#d4a574")
    
    for i, repo in enumerate(results.repos[:10], 1):
        desc = repo.description or ""
        if len(desc) > 45:
            desc = desc[:42] + "..."
        
        name_text = Text()
        name_text.append(repo.full_name, style="bold #f5e6d3")
        if desc:
            name_text.append(f"\n{desc}", style="dim")
        
        table.add_row(
            str(i),
            name_text,
            repo.language or "-",
            format_number(repo.stars),
            format_number(repo.forks),
        )
    
    from rich.console import Group
    content = Group(header, Text(""), table)
    
    return Panel(
        content,
        title="[bold #c9a66b]🔍 Search Results",
        border_style="#8b6f47",
    )

