"""GitHub API client for fetching repository information."""

import re
from datetime import datetime, timezone
from typing import Optional

import httpx

from caffeine.config import get_token
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


class GitHubError(Exception):
    """Base exception for GitHub API errors."""
    pass


class RepoNotFoundError(GitHubError):
    """Repository not found."""
    pass


class RateLimitError(GitHubError):
    """Rate limit exceeded."""
    pass


class GitHubClient:
    """Client for interacting with GitHub API."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None, timeout: float = 30.0):
        """Initialize the client.
        
        Args:
            token: GitHub personal access token. If None, will try to get from
                   environment variable or config file.
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
        self._token = token if token is not None else get_token()
        self._rate_limit = RateLimitInfo()
        self._client: Optional[httpx.Client] = None
    
    @property
    def is_authenticated(self) -> bool:
        """Check if client has a token configured."""
        return self._token is not None
    
    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Caffeine-GitVS/0.1.0",
            }
            
            # Add authorization header if token is available
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"
            
            self._client = httpx.Client(
                base_url=self.BASE_URL,
                timeout=self.timeout,
                headers=headers,
                follow_redirects=True,
            )
        return self._client
    
    @property
    def rate_limit(self) -> RateLimitInfo:
        """Get current rate limit info."""
        return self._rate_limit
    
    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    @staticmethod
    def parse_repo_url(url_or_path: str) -> tuple[str, str]:
        """Parse a GitHub URL or owner/repo string.
        
        Args:
            url_or_path: GitHub URL or "owner/repo" string.
            
        Returns:
            Tuple of (owner, repo).
            
        Raises:
            ValueError: If the URL/path is invalid.
        """
        # Try full URL patterns
        patterns = [
            r"github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",  # https://github.com/owner/repo
            r"^([^/]+)/([^/]+)$",  # owner/repo
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_path.strip())
            if match:
                owner, repo = match.groups()
                # Clean up repo name (remove .git if present)
                repo = repo.rstrip("/").removesuffix(".git")
                return owner, repo
        
        raise ValueError(
            f"Invalid GitHub repository: {url_or_path}\n"
            "Use format: owner/repo or https://github.com/owner/repo"
        )
    
    def _update_rate_limit(self, response: httpx.Response) -> None:
        """Update rate limit info from response headers."""
        self._rate_limit.limit = int(response.headers.get("X-RateLimit-Limit", 60))
        self._rate_limit.remaining = int(response.headers.get("X-RateLimit-Remaining", 60))
        
        reset_timestamp = response.headers.get("X-RateLimit-Reset")
        if reset_timestamp:
            self._rate_limit.reset_at = datetime.fromtimestamp(
                int(reset_timestamp), tz=timezone.utc
            )
    
    def _request(self, endpoint: str) -> dict | list | None:
        """Make a GET request to the GitHub API.
        
        Args:
            endpoint: API endpoint (e.g., "/repos/owner/repo").
            
        Returns:
            JSON response data.
            
        Raises:
            RepoNotFoundError: If the repository doesn't exist.
            RateLimitError: If rate limit is exceeded.
            GitHubError: For other API errors.
        """
        try:
            response = self.client.get(endpoint)
            self._update_rate_limit(response)
            
            if response.status_code == 404:
                raise RepoNotFoundError(f"Repository not found: {endpoint}")
            
            if response.status_code == 403:
                if self._rate_limit.remaining == 0:
                    raise RateLimitError(
                        f"Rate limit exceeded. Resets at {self._rate_limit.reset_at}"
                    )
                raise GitHubError(f"Access forbidden: {endpoint}")
            
            if response.status_code == 202:
                # GitHub is computing stats, data not ready yet
                return None
            
            response.raise_for_status()
            return response.json()
            
        except httpx.TimeoutException:
            raise GitHubError(f"Request timed out: {endpoint}")
        except httpx.RequestError as e:
            raise GitHubError(f"Request failed: {e}")
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 datetime string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return None
    
    def get_repository(self, owner: str, repo: str) -> Repository:
        """Fetch basic repository information.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            
        Returns:
            Repository object with basic info.
        """
        data = self._request(f"/repos/{owner}/{repo}")
        
        return Repository(
            full_name=data["full_name"],
            name=data["name"],
            owner=data["owner"]["login"],
            description=data.get("description"),
            homepage=data.get("homepage") or None,
            stars=data.get("stargazers_count", 0),
            forks=data.get("forks_count", 0),
            watchers=data.get("subscribers_count", 0),
            open_issues_count=data.get("open_issues_count", 0),
            size=data.get("size", 0),
            default_branch=data.get("default_branch", "main"),
            license_name=data.get("license", {}).get("spdx_id") if data.get("license") else None,
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
            pushed_at=self._parse_datetime(data.get("pushed_at")),
            is_fork=data.get("fork", False),
            is_archived=data.get("archived", False),
            has_issues=data.get("has_issues", True),
            has_wiki=data.get("has_wiki", True),
            topics=data.get("topics", []),
        )
    
    def get_languages(self, owner: str, repo: str) -> LanguageStats:
        """Fetch language statistics.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            
        Returns:
            LanguageStats object.
        """
        data = self._request(f"/repos/{owner}/{repo}/languages")
        return LanguageStats(languages=data or {})
    
    def get_contributors(
        self, owner: str, repo: str, limit: int = 10
    ) -> list[Contributor]:
        """Fetch top contributors.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            limit: Maximum number of contributors to fetch.
            
        Returns:
            List of Contributor objects.
        """
        data = self._request(f"/repos/{owner}/{repo}/contributors?per_page={limit}")
        
        if not data:
            return []
        
        return [
            Contributor(
                username=c["login"],
                contributions=c["contributions"],
                avatar_url=c.get("avatar_url", ""),
                profile_url=c.get("html_url", ""),
            )
            for c in data[:limit]
        ]
    
    def get_commit_activity(self, owner: str, repo: str) -> CommitActivity:
        """Fetch commit activity for the past year.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            
        Returns:
            CommitActivity object.
        """
        data = self._request(f"/repos/{owner}/{repo}/stats/commit_activity")
        
        if not data:
            return CommitActivity(weekly_commits=[])
        
        # Each item has a "total" field with total commits for that week
        weekly_commits = [week.get("total", 0) for week in data]
        return CommitActivity(weekly_commits=weekly_commits)
    
    def get_releases(self, owner: str, repo: str, limit: int = 5) -> list[Release]:
        """Fetch recent releases.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            limit: Maximum number of releases to fetch.
            
        Returns:
            List of Release objects.
        """
        data = self._request(f"/repos/{owner}/{repo}/releases?per_page={limit}")
        
        if not data:
            return []
        
        return [
            Release(
                tag_name=r["tag_name"],
                name=r.get("name") or r["tag_name"],
                published_at=self._parse_datetime(r.get("published_at")),
                is_prerelease=r.get("prerelease", False),
                is_draft=r.get("draft", False),
            )
            for r in data[:limit]
        ]
    
    def get_issue_stats(self, owner: str, repo: str) -> IssueStats:
        """Fetch issue and PR statistics.
        
        Note: This uses the search API which counts against rate limit.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            
        Returns:
            IssueStats object.
        """
        stats = IssueStats()
        
        # Get open issues (excluding PRs)
        open_issues_data = self._request(
            f"/search/issues?q=repo:{owner}/{repo}+type:issue+state:open&per_page=1"
        )
        if open_issues_data:
            stats.open_issues = open_issues_data.get("total_count", 0)
        
        # Get closed issues
        closed_issues_data = self._request(
            f"/search/issues?q=repo:{owner}/{repo}+type:issue+state:closed&per_page=1"
        )
        if closed_issues_data:
            stats.closed_issues = closed_issues_data.get("total_count", 0)
        
        # Get open PRs
        open_prs_data = self._request(
            f"/search/issues?q=repo:{owner}/{repo}+type:pr+state:open&per_page=1"
        )
        if open_prs_data:
            stats.open_prs = open_prs_data.get("total_count", 0)
        
        # Get merged PRs
        merged_prs_data = self._request(
            f"/search/issues?q=repo:{owner}/{repo}+type:pr+is:merged&per_page=1"
        )
        if merged_prs_data:
            stats.merged_prs = merged_prs_data.get("total_count", 0)
        
        # Get closed (not merged) PRs
        closed_prs_data = self._request(
            f"/search/issues?q=repo:{owner}/{repo}+type:pr+state:closed+is:unmerged&per_page=1"
        )
        if closed_prs_data:
            stats.closed_prs = closed_prs_data.get("total_count", 0)
        
        return stats
    
    def fetch_full_repository(self, url_or_path: str) -> Repository:
        """Fetch complete repository information.
        
        Args:
            url_or_path: GitHub URL or "owner/repo" string.
            
        Returns:
            Repository object with all available data.
        """
        owner, repo = self.parse_repo_url(url_or_path)
        
        # Fetch basic info first
        repository = self.get_repository(owner, repo)
        
        # Fetch additional data
        repository.languages = self.get_languages(owner, repo)
        repository.contributors = self.get_contributors(owner, repo)
        repository.commit_activity = self.get_commit_activity(owner, repo)
        repository.releases = self.get_releases(owner, repo)
        repository.issue_stats = self.get_issue_stats(owner, repo)
        
        return repository
    
    def get_recent_issues(
        self, owner: str, repo: str, limit: int = 3
    ) -> list[Issue]:
        """Fetch recent open issues.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            limit: Maximum number of issues to fetch.
            
        Returns:
            List of Issue objects.
        """
        # Fetch more items since some might be PRs that we filter out
        fetch_limit = limit * 5  # Fetch 5x to ensure we get enough actual issues
        
        data = self._request(
            f"/repos/{owner}/{repo}/issues?state=open&sort=created&direction=desc&per_page={fetch_limit}"
        )
        
        if not data:
            return []
        
        issues = []
        for item in data:
            # Skip pull requests (they also appear in issues endpoint)
            if "pull_request" in item:
                continue
            
            issues.append(Issue(
                number=item["number"],
                title=item["title"],
                state=item["state"],
                author=item["user"]["login"],
                created_at=self._parse_datetime(item.get("created_at")),
                labels=[label["name"] for label in item.get("labels", [])],
                comments_count=item.get("comments", 0),
                url=item.get("html_url", ""),
            ))
            
            if len(issues) >= limit:
                break
        
        return issues
    
    def get_readme(self, owner: str, repo: str) -> Optional[str]:
        """Fetch repository README content.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            
        Returns:
            README content as string, or None if not found.
        """
        try:
            # Get README metadata
            data = self._request(f"/repos/{owner}/{repo}/readme")
            
            if not data:
                return None
            
            # Content is base64 encoded
            import base64
            content = data.get("content", "")
            if content:
                # Remove newlines from base64 string
                content = content.replace("\n", "")
                return base64.b64decode(content).decode("utf-8")
            
            return None
            
        except RepoNotFoundError:
            return None
        except Exception:
            return None
    
    def get_file_tree(
        self, owner: str, repo: str, branch: Optional[str] = None, max_items: int = 100
    ) -> list[FileTreeItem]:
        """Fetch repository file tree.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            branch: Branch name. If None, uses default branch.
            max_items: Maximum number of items to return.
            
        Returns:
            List of FileTreeItem objects.
        """
        # Get default branch if not specified
        if not branch:
            repo_data = self._request(f"/repos/{owner}/{repo}")
            branch = repo_data.get("default_branch", "main") if repo_data else "main"
        
        # Get the tree (recursive)
        data = self._request(f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
        
        if not data or "tree" not in data:
            return []
        
        items = []
        for item in data["tree"][:max_items]:
            items.append(FileTreeItem(
                path=item["path"],
                name=item["path"].split("/")[-1],
                type="dir" if item["type"] == "tree" else "file",
                size=item.get("size", 0),
            ))
        
        return items
    
    def get_trending_repos(
        self,
        language: Optional[str] = None,
        since: str = "daily",
        limit: int = 10,
    ) -> list[TrendingRepo]:
        """Fetch trending repositories using GitHub Search API.
        
        Note: GitHub doesn't have an official trending API, so we use
        the search API with stars and recent creation/push as proxy.
        
        Args:
            language: Filter by programming language.
            since: Time period - "daily", "weekly", or "monthly".
            limit: Maximum number of repos to return.
            
        Returns:
            List of TrendingRepo objects.
        """
        from datetime import timedelta
        
        # Calculate date threshold based on 'since'
        now = datetime.now(timezone.utc)
        if since == "daily":
            threshold = now - timedelta(days=1)
        elif since == "weekly":
            threshold = now - timedelta(days=7)
        else:  # monthly
            threshold = now - timedelta(days=30)
        
        date_str = threshold.strftime("%Y-%m-%d")
        
        # Build search query
        query_parts = [f"pushed:>{date_str}"]
        if language:
            query_parts.append(f"language:{language}")
        
        query = "+".join(query_parts)
        
        data = self._request(
            f"/search/repositories?q={query}&sort=stars&order=desc&per_page={limit}"
        )
        
        if not data or "items" not in data:
            return []
        
        return [
            TrendingRepo(
                full_name=item["full_name"],
                description=item.get("description"),
                language=item.get("language"),
                stars=item.get("stargazers_count", 0),
                forks=item.get("forks_count", 0),
                url=item.get("html_url", ""),
            )
            for item in data["items"][:limit]
        ]
    
    def search_repos(
        self,
        query: str,
        language: Optional[str] = None,
        min_stars: Optional[int] = None,
        sort: str = "stars",
        limit: int = 10,
    ) -> SearchResult:
        """Search for repositories.
        
        Args:
            query: Search query string.
            language: Filter by programming language.
            min_stars: Minimum number of stars.
            sort: Sort by - "stars", "forks", "updated", "help-wanted-issues".
            limit: Maximum number of repos to return.
            
        Returns:
            SearchResult object with matching repos.
        """
        # Build search query
        query_parts = [query]
        if language:
            query_parts.append(f"language:{language}")
        if min_stars:
            query_parts.append(f"stars:>={min_stars}")
        
        search_query = "+".join(query_parts)
        
        data = self._request(
            f"/search/repositories?q={search_query}&sort={sort}&order=desc&per_page={limit}"
        )
        
        if not data:
            return SearchResult(total_count=0, repos=[])
        
        repos = [
            TrendingRepo(
                full_name=item["full_name"],
                description=item.get("description"),
                language=item.get("language"),
                stars=item.get("stargazers_count", 0),
                forks=item.get("forks_count", 0),
                url=item.get("html_url", ""),
            )
            for item in data.get("items", [])[:limit]
        ]
        
        return SearchResult(
            total_count=data.get("total_count", 0),
            repos=repos,
        )

