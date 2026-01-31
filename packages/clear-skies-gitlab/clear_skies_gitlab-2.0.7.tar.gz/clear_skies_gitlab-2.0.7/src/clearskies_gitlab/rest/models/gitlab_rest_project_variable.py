from __future__ import annotations

from typing import Self

from clearskies.columns import BelongsToId, BelongsToModel

from clearskies_gitlab.rest import gitlab_cicd_variable
from clearskies_gitlab.rest.backends import GitlabRestBackend
from clearskies_gitlab.rest.models import gitlab_rest_project_reference


class GitlabRestProjectVariable(
    gitlab_cicd_variable.GitlabCICDVariable,
):
    """
    Model for GitLab project CI/CD variables.

    This model provides access to the GitLab Project Variables API for managing
    CI/CD variables at the project level. It extends the base GitlabCICDVariable
    class with project-specific functionality.

    See https://docs.gitlab.com/api/project_level_variables/ for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestProjectVariable


    def my_function(variables: GitlabRestProjectVariable):
        # List all variables for a project
        for var in variables.where("project_id=123"):
            print(f"Variable: {var.key}")
            print(f"Protected: {var.protected}")
            print(f"Masked: {var.masked}")

        # Get a specific variable
        api_key = variables.find("project_id=123&key=API_KEY")
        if api_key:
            print(f"Value: {api_key.value}")

        # Create a new variable
        variables.create(
            {
                "project_id": 123,
                "key": "NEW_VAR",
                "value": "secret_value",
                "protected": True,
                "masked": True,
            }
        )
    ```
    """

    backend = GitlabRestBackend()
    id_column_name = "key"

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "projects/:project_id/variables"

    """
    The ID of the project this variable belongs to.
    """
    project_id = BelongsToId(gitlab_rest_project_reference.GitlabRestProjectReference)

    """
    The project model this variable belongs to.
    """
    project = BelongsToModel("project_id")
