from __future__ import annotations

from typing import Self

from clearskies import Model
from clearskies.columns import BelongsToId, BelongsToModel, Boolean, String

from clearskies_gitlab.rest.backends import GitlabRestBackend
from clearskies_gitlab.rest.models import gitlab_rest_project_reference


class GitlabRestProjectRepositoryFileRaw(
    Model,
):
    """
    Model for GitLab project repository raw file content.

    This model provides access to the GitLab Repository Files API for
    retrieving raw file content from a project's repository. Unlike the
    regular file endpoint, this returns the raw file content without
    base64 encoding.

    See https://docs.gitlab.com/api/repository_files/#get-raw-file-from-repository for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestProjectRepositoryFileRaw


    def my_function(raw_files: GitlabRestProjectRepositoryFileRaw):
        # Get raw content of a file
        readme = raw_files.find("project_id=123&file_path=README.md")
        if readme:
            # Content is returned as-is, not base64 encoded
            print(readme.content)

        # Get raw content from a specific branch
        config = raw_files.find("project_id=123&file_path=config.yml&ref=develop")

        # Get LFS pointer content
        large_file = raw_files.find("project_id=123&file_path=data.bin&lfs=true")
    ```
    """

    id_column_name = "file_path"

    backend = GitlabRestBackend()

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "projects/:project_id/repository/files/:file_path/raw"

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
    Whether to return the LFS pointer content.

    When true and the file is stored in Git LFS, returns the
    LFS pointer file content instead of the actual file.
    """
    lfs = Boolean()
