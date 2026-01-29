"""UI components for caffeine."""

from caffeine.ui.dashboard import Dashboard
from caffeine.ui.components import (
    create_header,
    create_stats_row,
    create_languages_panel,
    create_commits_panel,
    create_contributors_panel,
    create_issues_panel_with_recent,
    create_releases_panel,
    create_readme_panel,
    create_file_tree_panel,
    create_trending_table,
    create_search_results_table,
)

__all__ = [
    "Dashboard",
    "create_header",
    "create_stats_row",
    "create_languages_panel",
    "create_commits_panel",
    "create_contributors_panel",
    "create_issues_panel_with_recent",
    "create_releases_panel",
    "create_readme_panel",
    "create_file_tree_panel",
    "create_trending_table",
    "create_search_results_table",
]
