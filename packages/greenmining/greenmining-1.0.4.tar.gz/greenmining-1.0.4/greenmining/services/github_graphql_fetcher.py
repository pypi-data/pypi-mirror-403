"""
GitHub GraphQL API fetcher for faster and more efficient repository fetching.

GraphQL allows fetching exactly the data you need in a single request,
reducing API calls and improving rate limit efficiency.
"""

import json
import time
from typing import Any, Dict, List, Optional

import requests

from greenmining.models.repository import Repository


class GitHubGraphQLFetcher:
    """
    Fetch GitHub repositories using GraphQL API v4.

    Benefits over REST API:
    - Fetch repos + commits in 1 request instead of 100+ REST calls
    - Get exactly the fields you need (no over-fetching)
    - Better rate limit efficiency (5000 points/hour vs 5000 requests/hour)
    - More powerful search capabilities
    """

    GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

    def __init__(self, token: str):
        """
        Initialize GraphQL fetcher.

        Args:
            token: GitHub personal access token
        """
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def search_repositories(
        self,
        keywords: str = "microservices",
        max_repos: int = 100,
        min_stars: int = 100,
        languages: Optional[List[str]] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        pushed_after: Optional[str] = None,
        pushed_before: Optional[str] = None,
    ) -> List[Repository]:
        """
        Search GitHub repositories using GraphQL.

        Args:
            keywords: Search keywords
            max_repos: Maximum number of repositories to fetch
            min_stars: Minimum star count
            languages: Programming languages to filter
            created_after: Created after date (YYYY-MM-DD)
            created_before: Created before date (YYYY-MM-DD)
            pushed_after: Pushed after date (YYYY-MM-DD)
            pushed_before: Pushed before date (YYYY-MM-DD)

        Returns:
            List of Repository objects
        """
        # Build search query
        search_query = self._build_search_query(
            keywords,
            min_stars,
            languages,
            created_after,
            created_before,
            pushed_after,
            pushed_before,
        )

        print(f"GraphQL Search Query: {search_query}")

        # GraphQL query to fetch repositories
        query = """
        query($searchQuery: String!, $first: Int!) {
          search(query: $searchQuery, type: REPOSITORY, first: $first) {
            repositoryCount
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              ... on Repository {
                id
                name
                nameWithOwner
                description
                url
                createdAt
                updatedAt
                pushedAt
                stargazerCount
                forkCount
                watchers {
                  totalCount
                }
                primaryLanguage {
                  name
                }
                languages(first: 5) {
                  nodes {
                    name
                  }
                }
                licenseInfo {
                  name
                }
                isArchived
                isFork
                defaultBranchRef {
                  name
                }
              }
            }
          }
          rateLimit {
            limit
            cost
            remaining
            resetAt
          }
        }
        """

        variables = {"searchQuery": search_query, "first": min(max_repos, 100)}

        # Execute query
        repositories = []
        page_count = 0
        max_pages = (max_repos + 99) // 100  # Round up

        while len(repositories) < max_repos and page_count < max_pages:
            try:
                response = self._execute_query(query, variables)

                if "errors" in response:
                    print(f"GraphQL Errors: {response['errors']}")
                    break

                data = response.get("data", {})
                search = data.get("search", {})
                rate_limit = data.get("rateLimit", {})

                # Print rate limit info
                print(
                    f"Rate Limit: {rate_limit.get('remaining')}/{rate_limit.get('limit')} "
                    f"(cost: {rate_limit.get('cost')})"
                )

                # Parse repositories
                nodes = search.get("nodes", [])
                for node in nodes:
                    if node and len(repositories) < max_repos:
                        repo = self._parse_repository(node)
                        repositories.append(repo)

                # Check pagination
                page_info = search.get("pageInfo", {})
                if not page_info.get("hasNextPage"):
                    break

                # Update cursor for next page
                variables["after"] = page_info.get("endCursor")
                page_count += 1

                # Respect rate limits
                if rate_limit.get("remaining", 0) < 100:
                    print("Approaching rate limit, sleeping...")
                    time.sleep(60)

            except Exception as e:
                print(f"Error fetching repositories: {e}")
                break

        print(f"Fetched {len(repositories)} repositories using GraphQL")
        return repositories

    def _build_search_query(
        self,
        keywords: str,
        min_stars: int,
        languages: Optional[List[str]],
        created_after: Optional[str],
        created_before: Optional[str],
        pushed_after: Optional[str],
        pushed_before: Optional[str],
    ) -> str:
        """Build GitHub search query string."""
        query_parts = [keywords]

        # Star count
        query_parts.append(f"stars:>={min_stars}")

        # Languages
        if languages:
            lang_query = " OR ".join([f"language:{lang}" for lang in languages])
            query_parts.append(f"({lang_query})")

        # Date filters
        if created_after:
            query_parts.append(f"created:>={created_after}")
        if created_before:
            query_parts.append(f"created:<={created_before}")
        if pushed_after:
            query_parts.append(f"pushed:>={pushed_after}")
        if pushed_before:
            query_parts.append(f"pushed:<={pushed_before}")

        return " ".join(query_parts)

    def _execute_query(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GraphQL query."""
        payload = {"query": query, "variables": variables}

        response = requests.post(
            self.GRAPHQL_ENDPOINT, headers=self.headers, json=payload, timeout=30
        )

        response.raise_for_status()
        return response.json()

    def _parse_repository(self, node: Dict[str, Any]) -> Repository:
        """Parse GraphQL repository node to Repository object."""
        # Extract languages
        languages = []
        if node.get("languages") and node["languages"].get("nodes"):
            languages = [lang["name"] for lang in node["languages"]["nodes"]]
        elif node.get("primaryLanguage"):
            languages = [node["primaryLanguage"]["name"]]

        # Extract license
        license_name = None
        if node.get("licenseInfo"):
            license_name = node["licenseInfo"].get("name")

        return Repository(
            name=node.get("name", ""),
            full_name=node.get("nameWithOwner", ""),
            description=node.get("description", ""),
            url=node.get("url", ""),
            stars=node.get("stargazerCount", 0),
            forks=node.get("forkCount", 0),
            watchers=node.get("watchers", {}).get("totalCount", 0),
            language=node.get("primaryLanguage", {}).get("name", ""),
            languages=languages,
            created_at=node.get("createdAt", ""),
            updated_at=node.get("updatedAt", ""),
            pushed_at=node.get("pushedAt", ""),
            license=license_name,
            is_fork=node.get("isFork", False),
            is_archived=node.get("isArchived", False),
            default_branch=node.get("defaultBranchRef", {}).get("name", "main"),
        )

    def get_repository_commits(
        self, owner: str, name: str, max_commits: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch commits for a specific repository using GraphQL.

        This is much faster than REST API as it gets all commits in 1-2 requests
        instead of paginating through 100 individual REST calls.

        Args:
            owner: Repository owner
            name: Repository name
            max_commits: Maximum commits to fetch

        Returns:
            List of commit dictionaries
        """
        query = """
        query($owner: String!, $name: String!, $first: Int!) {
          repository(owner: $owner, name: $name) {
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: $first) {
                    totalCount
                    pageInfo {
                      hasNextPage
                      endCursor
                    }
                    nodes {
                      oid
                      message
                      committedDate
                      author {
                        name
                        email
                        user {
                          login
                        }
                      }
                      additions
                      deletions
                      changedFiles
                    }
                  }
                }
              }
            }
          }
          rateLimit {
            remaining
            cost
          }
        }
        """

        variables = {"owner": owner, "name": name, "first": min(max_commits, 100)}

        commits = []
        try:
            response = self._execute_query(query, variables)

            if "errors" in response:
                print(f"GraphQL Errors: {response['errors']}")
                return commits

            data = response.get("data", {})
            repo = data.get("repository", {})
            branch = repo.get("defaultBranchRef", {})
            target = branch.get("target", {})
            history = target.get("history", {})
            nodes = history.get("nodes", [])

            for node in nodes:
                commit = {
                    "sha": node.get("oid"),
                    "message": node.get("message"),
                    "date": node.get("committedDate"),
                    "author": node.get("author", {}).get("name"),
                    "author_email": node.get("author", {}).get("email"),
                    "additions": node.get("additions", 0),
                    "deletions": node.get("deletions", 0),
                    "changed_files": node.get("changedFiles", 0),
                }
                commits.append(commit)

            print(
                f"Fetched {len(commits)} commits for {owner}/{name} "
                f"(rate limit cost: {data.get('rateLimit', {}).get('cost')})"
            )

        except Exception as e:
            print(f"Error fetching commits for {owner}/{name}: {e}")

        return commits

    def save_results(self, repositories: List[Repository], output_file: str):
        """Save repositories to JSON file."""
        data = {
            "total_repositories": len(repositories),
            "repositories": [repo.to_dict() for repo in repositories],
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(repositories)} repositories to {output_file}")
