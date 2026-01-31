import clearskies


class GitlabDefaultAuth(clearskies.di.AdditionalConfigAutoImport):
    """
    Dependency injection provider for GitLab authentication.

    This class automatically provides GitLab authentication credentials to the
    dependency injection container. It reads the authentication token from the
    `GITLAB_AUTH_KEY` environment variable and configures a Bearer token
    authentication handler.

    The authentication is used by the GitlabRestBackend to authenticate API
    requests to GitLab.

    ```python
    # Set environment variable with your GitLab personal access token
    # export GITLAB_AUTH_KEY=glpat-xxxxxxxxxxxxxxxxxxxx

    from clearskies_gitlab.rest.backends import GitlabRestBackend


    class MyModel(clearskies.Model):
        backend = GitlabRestBackend()
        # Will automatically use the configured authentication
    ```

    The token should be a GitLab Personal Access Token (PAT) or Project/Group
    Access Token with appropriate scopes for the API operations you need to perform.
    """

    def provide_gitlab_auth(self, environment: clearskies.Environment):
        """
        Provide the GitLab authentication handler from environment.

        Reads the `GITLAB_AUTH_KEY` environment variable and returns a
        SecretBearer authentication handler configured with the `Bearer ` prefix
        as required by the GitLab API.
        """
        secret_key = environment.get("GITLAB_AUTH_KEY", True)
        return clearskies.authentication.SecretBearer(secret_key=secret_key, header_prefix="Bearer ")
