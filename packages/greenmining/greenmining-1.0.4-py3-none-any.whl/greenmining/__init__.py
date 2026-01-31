# Green Microservices Mining - GSF Pattern Analysis Tool.

from greenmining.config import Config
from greenmining.controllers.repository_controller import RepositoryController
from greenmining.gsf_patterns import (
    GREEN_KEYWORDS,
    GSF_PATTERNS,
    get_pattern_by_keywords,
    is_green_aware,
)

__version__ = "1.0.4"


def fetch_repositories(
    github_token: str,
    max_repos: int = None,
    min_stars: int = None,
    languages: list = None,
    keywords: str = None,
):
    # Fetch repositories from GitHub with custom search keywords.
    config = Config()
    config.GITHUB_TOKEN = github_token
    controller = RepositoryController(config)

    return controller.fetch_repositories(
        max_repos=max_repos,
        min_stars=min_stars,
        languages=languages,
        keywords=keywords,
    )


__all__ = [
    "Config",
    "GSF_PATTERNS",
    "GREEN_KEYWORDS",
    "is_green_aware",
    "get_pattern_by_keywords",
    "fetch_repositories",
    "__version__",
]