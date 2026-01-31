from __future__ import annotations

from typing import Self

from clearskies import Model
from clearskies.columns import Boolean, Datetime, Integer, Json, String

from clearskies_gitlab.rest.backends import GitlabRestBackend


class GitlabRestGroupAccessToken(
    Model,
):
    """
    Model for GitLab group access tokens.

    This model provides access to the GitLab Group Access Tokens API for managing
    access tokens at the group level. Group access tokens can be used for API
    authentication with permissions scoped to a specific group.

    See https://docs.gitlab.com/api/group_access_tokens/ for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestGroupAccessToken


    def my_function(access_tokens: GitlabRestGroupAccessToken):
        # List all access tokens for a group
        for token in access_tokens.where("group_id=123"):
            print(f"Token: {token.name}, Active: {token.active}")
            print(f"Expires: {token.expires_at}")

        # Create a new access token
        new_token = access_tokens.create(
            {
                "group_id": "123",
                "name": "CI Token",
                "scopes": ["read_api", "read_repository"],
                "expires_at": "2025-12-31",
                "access_level": 30,
            }
        )
        print(f"New token: {new_token.token}")
    ```
    """

    id_column_name = "id"
    backend = GitlabRestBackend()

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "groups/:group_id/access_tokens"

    """
    The ID of the group this token belongs to.

    Used to scope API requests to a specific group.
    """
    group_id = String()

    """
    The unique identifier for the access token.
    """
    id = Integer()

    """
    The user ID associated with this token.

    Each access token is associated with a bot user account.
    """
    user_id = Integer()

    """
    The name/description of the access token.

    A human-readable identifier for the token's purpose.
    """
    name = String()

    """
    The date and time when the token was created.
    """
    created_at = Datetime()

    """
    The expiration date of the token.

    After this date, the token will no longer be valid for authentication.
    Format: YYYY-MM-DD
    """
    expires_at = Datetime(date_format="%Y-%m-%d")

    """
    Whether the token is currently active.

    Inactive tokens cannot be used for authentication.
    """
    active = Boolean()

    """
    Whether the token has been revoked.

    Revoked tokens are permanently disabled.
    """
    revoked = Boolean()

    """
    The access level granted by this token.

    Common values:
    - 10: Guest
    - 20: Reporter
    - 30: Developer
    - 40: Maintainer
    - 50: Owner
    """
    access_level = Integer()

    """
    The actual token value.

    This is only returned when creating a new token and should be stored securely.
    It cannot be retrieved again after creation.
    """
    token = String()

    """
    The scopes/permissions granted to this token.

    Array of scope strings like "api", "read_api", "read_repository", etc.
    """
    scopes = Json()
