from __future__ import annotations

from clearskies import Model
from clearskies.columns import Datetime, Email, Integer, Json, String


class GitlabMember(Model):
    """
    Base model representing a GitLab group or project member.

    Members in GitLab represent users who have been granted access to a group
    or project with a specific access level. This model maps to the GitLab
    REST API response for membership endpoints.

    Access levels in GitLab are represented as integers:
    - 10: Guest
    - 20: Reporter
    - 30: Developer
    - 40: Maintainer
    - 50: Owner

    ```python
    from clearskies_gitlab.rest import GitlabMember
    from clearskies_gitlab.rest.backends import GitlabRestBackend


    class ProjectMember(GitlabMember):
        backend = GitlabRestBackend()
        table_name = "projects/{project_id}/members"


    # Fetch all members of a project
    members = ProjectMember.where(project_id="my-project").all()
    for member in members:
        print(f"User: {member.username}, Access Level: {member.access_level}")
    ```
    """

    id_column_name = "id"

    """
    The unique identifier for the member (user ID).
    """
    id = Integer()

    """
    The username of the member.
    """
    username = String()

    """
    The display name of the member.
    """
    name = String()

    """
    The current state of the user account.

    Common values include `active`, `blocked`, or `deactivated`.
    """
    state = String()

    """
    URL to the member's avatar image.
    """
    avatar_url = String()

    """
    The access level granted to the member.

    Integer values correspond to GitLab access levels:
    10 (Guest), 20 (Reporter), 30 (Developer), 40 (Maintainer), 50 (Owner).
    """
    access_level = Integer()

    """
    The timestamp when the member was added.
    """
    created_at = Datetime()

    """
    JSON object containing information about who added this member.

    Includes details like the user ID and username of the person who
    granted membership.
    """
    created_by = Json()

    """
    The email address of the member.
    """
    email = Email()

    """
    JSON object containing SAML identity information for the member.

    Only populated when SAML SSO is configured for the group.
    Contains the extern_uid and provider information.
    """
    group_saml_identity = Json()
