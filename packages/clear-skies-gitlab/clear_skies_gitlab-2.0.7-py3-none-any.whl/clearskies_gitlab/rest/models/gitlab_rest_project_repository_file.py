from __future__ import annotations

from typing import Self

from clearskies import Model
from clearskies.columns import BelongsToId, BelongsToModel, Boolean, Integer, String

from clearskies_gitlab.rest.backends import GitlabRestBackend
from clearskies_gitlab.rest.models import gitlab_rest_project_reference


class GitlabRestProjectRepositoryFile(
    Model,
):
    """
    Model for GitLab project repository files.

    This model provides access to the GitLab Repository Files API for
    retrieving file metadata and content from a project's repository.
    Files are identified by their path within the repository.

    See https://docs.gitlab.com/api/repository_files/ for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestProjectRepositoryFile


    def my_function(files: GitlabRestProjectRepositoryFile):
        # Get a specific file from the repository
        readme = files.find("project_id=123&file_path=README.md")
        if readme:
            print(f"File: {readme.file_name}")
            print(f"Size: {readme.size} bytes")
            print(f"Encoding: {readme.encoding}")
            # Content is base64 encoded by default
            print(f"Content: {readme.content}")

        # Get a file from a specific branch
        config = files.find("project_id=123&file_path=config.yml&ref=develop")
        if config:
            print(f"Last commit: {config.last_commit_id}")
    ```
    """

    id_column_name = "file_path"

    backend = GitlabRestBackend()

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "projects/:project_id/repository/files/:file_path"

    """
    The ID of the project containing the file.
    """
    project_id = BelongsToId(gitlab_rest_project_reference.GitlabRestProjectReference)

    """
    The project model this file belongs to.
    """
    project = BelongsToModel("project_id")

    """
    The path to the file within the repository.

    This serves as the unique identifier for the file.
    """
    file_path = String()

    """
    The branch, tag, or commit SHA to retrieve the file from.

    Defaults to HEAD (the default branch).
    """
    ref = String(default="HEAD")

    """
    The blob SHA of the file content.
    """
    blob_id = String()

    """
    The commit SHA where this file was last modified.
    """
    commit_id = String()

    """
    The file content.

    By default, this is base64 encoded. Use the encoding field
    to determine how to decode it.
    """
    content = String()

    """
    The SHA256 hash of the file content.
    """
    content_sha256 = String()

    """
    The encoding of the content field.

    Typically "base64" for binary-safe transfer.
    """
    encoding = String()

    """
    Whether the file has the executable permission set.
    """
    execute_filemode = Boolean()

    """
    The name of the file (without path).
    """
    file_name = String()

    """
    The commit SHA of the last commit that modified this file.
    """
    last_commit_id = String()

    """
    The size of the file in bytes.
    """
    size = Integer()
