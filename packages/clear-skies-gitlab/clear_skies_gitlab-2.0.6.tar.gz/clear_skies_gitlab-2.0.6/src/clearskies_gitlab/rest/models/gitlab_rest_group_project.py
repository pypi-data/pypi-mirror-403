from __future__ import annotations

from typing import Self

from clearskies_gitlab.rest.models import gitlab_rest_project


class GitlabRestGroupProject(
    gitlab_rest_project.GitlabRestProject,
):
    """
    Model for projects within a GitLab group.

    This model extends GitlabRestProject to provide access to projects scoped
    to a specific group. It inherits all project fields and adds group-specific
    filtering capabilities.

    See https://docs.gitlab.com/api/groups/#list-a-groups-projects for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestGroupProject


    def my_function(group_projects: GitlabRestGroupProject):
        # List all projects in a group
        for project in group_projects.where("group_id=123"):
            print(f"Project: {project.name}")
            print(f"Path: {project.path_with_namespace}")

        # Find a specific project in the group
        my_project = group_projects.find("name=my-project")
        if my_project:
            print(f"Found project: {my_project.web_url}")
    ```
    """

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "groups/:group_id/projects"
