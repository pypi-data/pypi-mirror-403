from __future__ import annotations

from clearskies import Model
from clearskies.columns import Boolean, String


class GitlabCICDVariable(Model):
    """
    Model representing a GitLab CI/CD variable.

    CI/CD variables in GitLab are used to store values that can be used in
    CI/CD pipelines. They can be defined at the project, group, or instance level.
    This model maps to the GitLab REST API response for CI/CD variables.

    Note that the `key` field is used as the unique identifier (`id_column_name`)
    since GitLab identifies variables by their key name.

    ```python
    from clearskies_gitlab.rest import GitlabCICDVariable
    from clearskies_gitlab.rest.backends import GitlabRestBackend


    class ProjectVariable(GitlabCICDVariable):
        backend = GitlabRestBackend()
        table_name = "projects/{project_id}/variables"


    # Fetch all CI/CD variables for a project
    variables = ProjectVariable.where(project_id="my-project").all()
    for var in variables:
        print(f"Key: {var.key}, Protected: {var.protected}")
    ```
    """

    id_column_name = "key"

    """
    The name of the variable, used as the unique identifier.
    """
    key = String()

    """
    The value stored in the variable.

    This may be masked in API responses if the `masked` flag is set.
    """
    value = String()

    """
    A human-readable description of the variable's purpose.
    """
    description = String()

    """
    The environment scope for the variable.

    Determines which environments the variable is available in.
    Use `*` for all environments or specify a specific environment name.
    """
    environment_scope = String()

    """
    The type of variable.

    Can be `env_var` for environment variables or `file` for file-type variables.
    """
    variable_type = String()

    """
    Whether the variable value is masked in job logs.

    When true, the variable value will be hidden in CI/CD job output.
    """
    masked = Boolean()

    """
    Whether the variable is only available in protected branches/tags.

    When true, the variable is only exposed to pipelines running on
    protected branches or tags.
    """
    protected = Boolean()

    """
    Whether the variable is hidden from the UI.

    Hidden variables cannot be viewed or edited through the GitLab interface.
    """
    hidden = Boolean()

    """
    Whether the variable value should be treated as raw (no variable expansion).

    When true, the variable value is used as-is without expanding any
    embedded variable references.
    """
    raw = Boolean()
