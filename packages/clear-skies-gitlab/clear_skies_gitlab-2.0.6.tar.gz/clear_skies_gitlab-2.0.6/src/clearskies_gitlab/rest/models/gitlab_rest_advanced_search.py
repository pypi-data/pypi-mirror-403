from __future__ import annotations

from typing import Self

from clearskies import Model
from clearskies.columns import Boolean, Json, Select, String

from clearskies_gitlab.rest.backends import GitlabRestBackend


class GitlabRestAdvancedSearch(Model):
    """
    Model for GitLab Advanced Search.

    This model provides access to GitLab's Advanced Search API, which allows searching across
    the entire GitLab instance for various types of content including projects, issues,
    merge requests, milestones, snippets, users, wiki content, commits, blobs, and notes.

    Advanced Search requires Elasticsearch to be configured on the GitLab instance.

    See https://docs.gitlab.com/api/search/ for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestAdvancedSearch


    def my_function(search: GitlabRestAdvancedSearch):
        # Search for projects matching a query
        for result in search.where("scope=projects").where("search=my-project"):
            print(f"Found: {result.fields}")

        # Search for blobs (code) containing specific text
        for result in search.where("scope=blobs").where("search=def my_function"):
            print(f"Found code match: {result.fields}")
    ```
    """

    backend = GitlabRestBackend()

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "search"

    """
    The scope of the search.

    Determines what type of content to search for. Available values:
    - `projects`: Search for projects
    - `issues`: Search for issues
    - `merge_requests`: Search for merge requests
    - `milestones`: Search for milestones
    - `snippet_titles`: Search for snippet titles
    - `users`: Search for users
    - `wiki_blobs`: Search for wiki content
    - `commits`: Search for commits
    - `blobs`: Search for code/file content
    - `notes`: Search for comments/notes
    """
    scope = Select(
        allowed_values=[
            "projects",
            "issues",
            "merge_requests",
            "milestones",
            "snippet_titles",
            "users",
            "wiki_blobs",
            "commits",
            "blobs",
            "notes",
        ]
    )

    """
    The search query string.

    The text to search for across the selected scope.
    """
    search = String()

    """
    Filter for confidential issues.

    When searching issues, set to `True` to only return confidential issues,
    or `False` to only return non-confidential issues.
    """
    confidential = Boolean()

    """
    Filter by state.

    When searching issues or merge requests, filter by their state (e.g., "opened", "closed").
    """
    state = String()

    """
    Additional fields returned in the search results.

    Contains extra data specific to the search scope, returned as a JSON object.
    """
    fields = Json()
