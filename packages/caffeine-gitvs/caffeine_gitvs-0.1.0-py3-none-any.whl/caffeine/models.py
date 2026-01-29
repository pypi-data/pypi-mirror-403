"""Data models for GitHub repository information."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Contributor:
    """A repository contributor."""
    
    username: str
    contributions: int
    avatar_url: str = ""
    profile_url: str = ""


@dataclass
class Release:
    """A repository release."""
    
    tag_name: str
    name: str
    published_at: Optional[datetime] = None
    is_prerelease: bool = False
    is_draft: bool = False


@dataclass
class LanguageStats:
    """Language statistics for a repository."""
    
    languages: dict[str, int] = field(default_factory=dict)
    
    @property
    def total_bytes(self) -> int:
        """Total bytes of code."""
        return sum(self.languages.values())
    
    def get_percentages(self) -> dict[str, float]:
        """Get language percentages."""
        total = self.total_bytes
        if total == 0:
            return {}
        return {lang: (bytes_count / total) * 100 
                for lang, bytes_count in self.languages.items()}
    
    def get_sorted(self) -> list[tuple[str, int, float]]:
        """Get languages sorted by percentage (descending)."""
        percentages = self.get_percentages()
        return sorted(
            [(lang, self.languages[lang], percentages[lang]) 
             for lang in self.languages],
            key=lambda x: x[2],
            reverse=True
        )


@dataclass
class CommitActivity:
    """Weekly commit activity for the past year."""
    
    weekly_commits: list[int] = field(default_factory=list)
    
    @property
    def total(self) -> int:
        """Total commits in the past year."""
        return sum(self.weekly_commits)
    
    @property
    def average(self) -> float:
        """Average commits per week."""
        if not self.weekly_commits:
            return 0.0
        return self.total / len(self.weekly_commits)
    
    @property
    def peak(self) -> int:
        """Peak commits in a single week."""
        return max(self.weekly_commits) if self.weekly_commits else 0
    
    @property
    def peak_week(self) -> int:
        """Week number with peak commits."""
        if not self.weekly_commits:
            return 0
        return self.weekly_commits.index(self.peak) + 1


@dataclass
class IssueStats:
    """Issue and PR statistics."""
    
    open_issues: int = 0
    closed_issues: int = 0
    open_prs: int = 0
    merged_prs: int = 0
    closed_prs: int = 0
    
    @property
    def total_issues(self) -> int:
        """Total issues (open + closed)."""
        return self.open_issues + self.closed_issues
    
    @property
    def total_prs(self) -> int:
        """Total PRs."""
        return self.open_prs + self.merged_prs + self.closed_prs
    
    @property
    def issue_close_rate(self) -> float:
        """Percentage of closed issues."""
        if self.total_issues == 0:
            return 0.0
        return (self.closed_issues / self.total_issues) * 100
    
    @property
    def pr_merge_rate(self) -> float:
        """Percentage of merged PRs."""
        if self.total_prs == 0:
            return 0.0
        return (self.merged_prs / self.total_prs) * 100


@dataclass
class Repository:
    """Complete repository information."""
    
    # Basic info
    full_name: str
    name: str
    owner: str
    description: Optional[str] = None
    homepage: Optional[str] = None
    
    # Stats
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    open_issues_count: int = 0
    size: int = 0  # in KB
    
    # Metadata
    default_branch: str = "main"
    license_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    pushed_at: Optional[datetime] = None
    
    # Flags
    is_fork: bool = False
    is_archived: bool = False
    has_issues: bool = True
    has_wiki: bool = True
    
    # Topics/tags
    topics: list[str] = field(default_factory=list)
    
    # Extended data (populated separately)
    languages: Optional[LanguageStats] = None
    contributors: list[Contributor] = field(default_factory=list)
    commit_activity: Optional[CommitActivity] = None
    issue_stats: Optional[IssueStats] = None
    releases: list[Release] = field(default_factory=list)
    
    @property
    def size_human(self) -> str:
        """Human-readable size."""
        size_kb = self.size
        if size_kb < 1024:
            return f"{size_kb} KB"
        elif size_kb < 1024 * 1024:
            return f"{size_kb / 1024:.1f} MB"
        else:
            return f"{size_kb / (1024 * 1024):.1f} GB"
    
    @property
    def age_days(self) -> int:
        """Days since creation."""
        if not self.created_at:
            return 0
        delta = datetime.now(self.created_at.tzinfo) - self.created_at
        return delta.days


@dataclass
class RateLimitInfo:
    """GitHub API rate limit information."""
    
    limit: int = 60
    remaining: int = 60
    reset_at: Optional[datetime] = None
    
    @property
    def is_low(self) -> bool:
        """Check if rate limit is low (< 10)."""
        return self.remaining < 10
    
    @property
    def is_exhausted(self) -> bool:
        """Check if rate limit is exhausted."""
        return self.remaining == 0


@dataclass
class Issue:
    """A repository issue."""
    
    number: int
    title: str
    state: str  # "open" or "closed"
    author: str
    created_at: Optional[datetime] = None
    labels: list[str] = field(default_factory=list)
    comments_count: int = 0
    url: str = ""


@dataclass
class FileTreeItem:
    """An item in the repository file tree."""
    
    path: str
    name: str
    type: str  # "file" or "dir"
    size: int = 0  # in bytes, for files only
    
    @property
    def is_directory(self) -> bool:
        """Check if item is a directory."""
        return self.type == "dir" or self.type == "tree"


@dataclass
class TrendingRepo:
    """A trending repository."""
    
    full_name: str
    description: Optional[str]
    language: Optional[str]
    stars: int
    forks: int
    stars_today: int = 0  # Stars gained today (if available)
    url: str = ""


@dataclass
class SearchResult:
    """Search results container."""
    
    total_count: int
    repos: list["TrendingRepo"] = field(default_factory=list)

