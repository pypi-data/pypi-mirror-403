from __future__ import annotations

from clearskies_gitlab.rest.models import (
    gitlab_rest_advanced_search_blob,
    gitlab_rest_group_search,
)


class GitlabRestGroupSearchBlob(
    gitlab_rest_group_search.GitlabRestGroupSearch,
    gitlab_rest_advanced_search_blob.GitlabRestAdvancedSearchBlob,
):
    """
    Model for GitLab group-scoped blob search results.

    This model combines GitlabRestGroupSearch and GitlabRestAdvancedSearchBlob
    to provide blob (code/file) search functionality scoped to a specific group.
    It includes all the blob-specific fields like path, filename, and line numbers.

    See https://docs.gitlab.com/api/search/#scope-blobs for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestGroupSearchBlob


    def my_function(group_blob_search: GitlabRestGroupSearchBlob):
        # Search for code within a group
        for blob in (
            group_blob_search.where("group_id=123")
            .where("scope=blobs")
            .where("search=def authenticate")
        ):
            print(f"Found in {blob.path} at line {blob.startline}")
            print(f"Project ID: {blob.project_id}")
            print(f"Content: {blob.data}")
    ```
    """
