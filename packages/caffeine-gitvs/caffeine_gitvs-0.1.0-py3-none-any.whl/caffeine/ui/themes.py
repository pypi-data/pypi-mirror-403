"""Color themes for caffeine UI."""

from rich.style import Style
from rich.theme import Theme

# Caffeine color palette - warm coffee tones
COLORS = {
    "espresso": "#1a1a2e",      # Dark background
    "latte": "#f5e6d3",         # Light cream
    "caramel": "#d4a574",       # Warm caramel
    "mocha": "#8b6f47",         # Rich mocha
    "foam": "#faf3e0",          # Light foam
    "brew": "#c9a66b",          # Golden brew
    "roast": "#5c4033",         # Dark roast
    "steam": "#a0a0a0",         # Gray steam
    "success": "#98c379",       # Green
    "warning": "#e5c07b",       # Yellow
    "error": "#e06c75",         # Red
    "info": "#61afef",          # Blue
}

# Create the caffeine theme
CAFFEINE_THEME = Theme({
    "header": Style(color=COLORS["brew"], bold=True),
    "header.title": Style(color=COLORS["latte"], bold=True),
    "header.subtitle": Style(color=COLORS["caramel"]),
    
    "stat.label": Style(color=COLORS["steam"]),
    "stat.value": Style(color=COLORS["latte"], bold=True),
    "stat.icon": Style(color=COLORS["brew"]),
    
    "panel.border": Style(color=COLORS["mocha"]),
    "panel.title": Style(color=COLORS["brew"], bold=True),
    
    "language.name": Style(color=COLORS["latte"]),
    "language.bar": Style(color=COLORS["caramel"]),
    "language.percent": Style(color=COLORS["steam"]),
    
    "contributor.rank": Style(color=COLORS["brew"], bold=True),
    "contributor.name": Style(color=COLORS["latte"]),
    "contributor.commits": Style(color=COLORS["caramel"]),
    
    "commit.sparkline": Style(color=COLORS["brew"]),
    "commit.total": Style(color=COLORS["latte"], bold=True),
    "commit.average": Style(color=COLORS["steam"]),
    
    "issue.open": Style(color=COLORS["warning"]),
    "issue.closed": Style(color=COLORS["success"]),
    "pr.open": Style(color=COLORS["info"]),
    "pr.merged": Style(color=COLORS["success"]),
    
    "release.latest": Style(color=COLORS["success"], bold=True),
    "release.tag": Style(color=COLORS["brew"]),
    "release.date": Style(color=COLORS["steam"]),
    
    "success": Style(color=COLORS["success"]),
    "warning": Style(color=COLORS["warning"]),
    "error": Style(color=COLORS["error"]),
    "info": Style(color=COLORS["info"]),
    "muted": Style(color=COLORS["steam"]),
    
    "footer": Style(color=COLORS["steam"]),
    "rate_limit.ok": Style(color=COLORS["success"]),
    "rate_limit.low": Style(color=COLORS["warning"]),
    "rate_limit.exhausted": Style(color=COLORS["error"]),
})

