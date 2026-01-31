from __future__ import annotations

from clearskies.columns import BelongsToId, BelongsToModel, Integer, String

from clearskies_gitlab.rest.models import gitlab_rest_advanced_search, gitlab_rest_project


class GitlabRestAdvancedSearchBlob(
    gitlab_rest_advanced_search.GitlabRestAdvancedSearch,
):
    """
    Model for GitLab Advanced Search blob results.

    This model extends GitlabRestAdvancedSearch to provide specific fields for blob (code/file)
    search results. When searching with `scope="blobs"`, the results include file content
    and location information.

    See https://docs.gitlab.com/api/search/ for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestAdvancedSearchBlob


    def my_function(blob_search: GitlabRestAdvancedSearchBlob):
        # Search for code containing a specific function
        for blob in blob_search.where("scope=blobs").where("search=def authenticate"):
            print(f"Found in {blob.path} at line {blob.startline}")
            print(f"Project ID: {blob.project_id}")
    ```
    """

    """
    The base filename without the directory path.

    For example, if the full path is "src/utils/helpers.py", the basename would be "helpers.py".
    """
    basename = String()

    """
    The matching content from the file.

    Contains the actual code or text that matched the search query, typically with
    surrounding context.
    """
    data = String()

    """
    The full path to the file within the repository.

    For example: "src/utils/helpers.py".
    """
    path = String()

    """
    The filename of the matched file.

    Similar to basename, contains the name of the file.
    """
    filename = String()

    """
    The unique identifier for this search result.
    """
    id = Integer()

    """
    The Git reference (branch or tag) where the match was found.

    For example: "main", "develop", or "v1.0.0".
    """
    ref = String()

    """
    The starting line number of the matched content.

    Indicates where in the file the matching content begins.
    """
    startline = Integer()

    """
    The ID of the project containing the matched file.
    """
    project_id = BelongsToId(
        gitlab_rest_project.GitlabRestProject,
    )

    """
    The project model containing the matched file.

    Provides access to the full project object via the relationship.
    """
    project = BelongsToModel("project_id")
