from __future__ import annotations

from typing import Self

from clearskies import Model
from clearskies.columns import BelongsToId, BelongsToModel, Boolean, Integer

from clearskies_gitlab.rest.backends import GitlabRestBackend
from clearskies_gitlab.rest.models import gitlab_rest_project_reference


class GitlabRestProjectApprovalConfig(
    Model,
):
    """
    Model for GitLab project approval configuration.

    This model provides access to the GitLab Merge Request Approvals API for
    configuring project-level approval settings. These settings control how
    merge request approvals work across the entire project.

    See https://docs.gitlab.com/api/merge_request_approvals/#get-configuration for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestProjectApprovalConfig


    def my_function(approval_configs: GitlabRestProjectApprovalConfig):
        # Get approval config for a specific project
        config = approval_configs.find("project_id=123")
        if config:
            print(f"Reset approvals on push: {config.reset_approvals_on_push}")
            print(f"Author can approve: {config.merge_requests_author_approval}")

        # Update approval settings
        config.save({"reset_approvals_on_push": True, "merge_requests_author_approval": False})
    ```
    """

    backend = GitlabRestBackend()

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "projects/:project_id/approvals"

    """
    The ID of the project this configuration belongs to.
    """
    project_id = BelongsToId(gitlab_rest_project_reference.GitlabRestProjectReference)

    """
    The project model this configuration belongs to.
    """
    project = BelongsToModel("project_id")

    id_column_name = "project_id"

    """
    Whether to reset approvals when new commits are pushed.

    When enabled, any existing approvals are removed when new commits
    are pushed to the merge request.
    """
    reset_approvals_on_push = Boolean()

    """
    Whether users must enter their password to approve.

    Adds an extra layer of security by requiring password confirmation.
    """
    require_user_password_for_approval = Boolean()

    """
    Whether to prevent overriding approvers per merge request.

    When enabled, the project-level approval rules cannot be modified
    on individual merge requests.
    """
    disable_overriding_approvers_per_merge_request = Boolean()

    """
    Whether merge request authors can approve their own requests.

    When enabled, the author of a merge request can also approve it.
    """
    merge_requests_author_approval = Boolean()

    """
    Whether committers are prevented from approving.

    When enabled, users who have committed to the merge request
    cannot approve it.
    """
    merge_requests_disable_committers_approval = Boolean()

    """
    Whether reauthentication is required to approve.

    When enabled, users must reauthenticate before they can approve
    a merge request.
    """
    require_reauthentication_to_approve = Boolean()

    """
    Whether to reset approvals from Code Owners if their files change.

    When enabled, approvals from Code Owners are reset when files they
    own are modified. Note: To use this field, reset_approvals_on_push
    must be False.
    """
    selective_code_owner_removals = Boolean()

    """
    The number of required approvals before a merge request can merge.

    Deprecated in GitLab 12.3. Use Approval Rules instead.
    This field is still returned by the API for backwards compatibility.
    """
    approvals_before_merge = Integer()
