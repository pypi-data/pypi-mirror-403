from __future__ import annotations

from typing import Self

from clearskies import Model
from clearskies.columns import BelongsToId, BelongsToModel, Email, Integer, String

from clearskies_gitlab.rest.backends import GitlabRestBackend
from clearskies_gitlab.rest.models import gitlab_rest_project_reference


class GitlabRestProjectRepositoryContributor(
    Model,
):
    """
    Model for GitLab project repository contributors.

    This model provides access to the GitLab Repository Contributors API for
    retrieving statistics about contributors to a project's repository.
    Contributors are identified by their commit email address.

    See https://docs.gitlab.com/api/repositories/#contributors for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestProjectRepositoryContributor


    def my_function(contributors: GitlabRestProjectRepositoryContributor):
        # List all contributors to a project
        for contributor in contributors.where("project_id=123"):
            print(f"Contributor: {contributor.name}")
            print(f"Email: {contributor.email}")
            print(f"Commits: {contributor.commits}")
            print(f"Lines added: {contributor.additions}")
            print(f"Lines deleted: {contributor.deletions}")

        # Get contributors for a specific branch
        for contributor in contributors.where("project_id=123&ref=develop"):
            print(f"{contributor.name}: {contributor.commits} commits")
    ```
    """

    id_column_name = "email"

    backend = GitlabRestBackend()

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "projects/:project_id/repository/contributors"

    """
    The display name of the contributor.

    This is taken from the Git commit author name.
    """
    name = String()

    """
    The email address of the contributor.

    This is taken from the Git commit author email and serves as the unique identifier.
    """
    email = Email()

    """
    The total number of commits by this contributor.
    """
    commits = Integer()

    """
    The total number of lines added by this contributor.
    """
    additions = Integer()

    """
    The total number of lines deleted by this contributor.
    """
    deletions = Integer()

    ### Search params

    """
    The ID of the project to query contributors for.
    """
    project_id = BelongsToId(gitlab_rest_project_reference.GitlabRestProjectReference)

    """
    The project model this contributor belongs to.
    """
    project = BelongsToModel("project_id")

    """
    The branch or tag to get contributors for.

    Defaults to the default branch if not specified.
    """
    ref = String()
