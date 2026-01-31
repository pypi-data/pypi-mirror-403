from __future__ import annotations

from typing import Self

from clearskies import Model
from clearskies.columns import Boolean, Datetime, Email, Integer, Json, String

from clearskies_gitlab.rest.backends import GitlabRestBackend


class GitlabRestCurrentUser(
    Model,
):
    """
    Model for the current authenticated GitLab user.

    This model provides access to the GitLab User API for retrieving information about
    the currently authenticated user. It returns detailed profile information including
    identity, settings, and capabilities.

    See https://docs.gitlab.com/api/users/#for-normal-users for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestCurrentUser


    def my_function(current_user: GitlabRestCurrentUser):
        # Get the current user's information
        user = current_user.first()
        if user:
            print(f"Logged in as: {user.username}")
            print(f"Email: {user.email}")
            print(f"Can create projects: {user.can_create_project}")
    ```
    """

    id_column_name = "id"
    backend = GitlabRestBackend()

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "user"

    """
    The unique identifier for the user.
    """
    id = Integer()

    """
    The username of the user.

    This is the unique handle used for login and mentions (e.g., @username).
    """
    username = String()

    """
    The primary email address of the user.
    """
    email = Email()

    """
    The display name of the user.
    """
    name = String()

    """
    The current state of the user account.

    Common values include "active", "blocked", "deactivated".
    """
    state = String()

    """
    Whether the user account is locked.

    A locked account cannot sign in until unlocked by an administrator.
    """
    locked = Boolean()

    """
    URL to the user's avatar image.
    """
    avatar_url = String()

    """
    URL to the user's GitLab profile page.
    """
    web_url = String()

    """
    The date and time when the user account was created.
    """
    created_at = Datetime()

    """
    The user's biography/description.

    A short text that appears on the user's profile page.
    """
    bio = String()

    """
    The user's public email address.

    This email is visible to other users on the profile page.
    """
    public_email = Email()

    """
    The organization the user belongs to.
    """
    organization = String()

    """
    Whether this user is a bot account.

    Bot accounts are typically used for automation and CI/CD.
    """
    bot = Boolean()

    """
    The date and time of the user's last sign in.
    """
    last_sign_in_at = Datetime()

    """
    The date and time when the user's email was confirmed.
    """
    confirmed_at = Datetime()

    """
    The date of the user's last activity.
    """
    last_activity_on = Datetime()

    """
    Array of identity provider information.

    Contains details about external identity providers (LDAP, SAML, etc.)
    linked to this account.
    """
    identities = Json()

    """
    Whether the user can create new groups.
    """
    can_create_group = Boolean()

    """
    Whether the user can create new projects.
    """
    can_create_project = Boolean()

    """
    Whether two-factor authentication is enabled for this user.
    """
    two_factor_enabled = Boolean()

    """
    Whether this is an external user.

    External users have limited access to internal projects.
    """
    external = Boolean()

    """
    Whether the user has a private profile.

    Private profiles hide activity and contribution information.
    """
    private_profile = Boolean()

    """
    The email address used for Git commits.
    """
    commit_email = Email()
