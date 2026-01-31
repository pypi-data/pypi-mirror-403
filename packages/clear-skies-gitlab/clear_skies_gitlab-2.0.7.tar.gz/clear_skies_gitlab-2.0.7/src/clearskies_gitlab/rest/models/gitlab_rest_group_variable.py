from __future__ import annotations

from typing import Self

from clearskies.columns import String

from clearskies_gitlab.rest import gitlab_cicd_variable
from clearskies_gitlab.rest.backends import GitlabRestBackend


class GitlabRestGroupVariable(
    gitlab_cicd_variable.GitlabCICDVariable,
):
    """
    Model for GitLab group CI/CD variables.

    This model provides access to the GitLab Group Variables API for managing
    CI/CD variables at the group level. Group variables are available to all
    projects within the group.

    See https://docs.gitlab.com/api/group_level_variables/ for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestGroupVariable


    def my_function(group_variables: GitlabRestGroupVariable):
        # List all variables for a group
        for var in group_variables.where("group_id=123"):
            print(f"Variable: {var.key}")
            print(f"Protected: {var.protected}")
            print(f"Masked: {var.masked}")

        # Create a new variable
        new_var = group_variables.create(
            {
                "group_id": "123",
                "key": "DATABASE_URL",
                "value": "postgres://localhost/mydb",
                "protected": True,
                "masked": True,
            }
        )

        # Find a specific variable
        db_url = group_variables.find("key=DATABASE_URL")
        if db_url:
            print(f"Database URL is {'protected' if db_url.protected else 'not protected'}")
    ```
    """

    id_column_name = "id"
    backend = GitlabRestBackend()

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "groups/:group_id/variables"

    """
    The ID of the group this variable belongs to.

    Used to scope API requests to a specific group.
    """
    group_id = String()
