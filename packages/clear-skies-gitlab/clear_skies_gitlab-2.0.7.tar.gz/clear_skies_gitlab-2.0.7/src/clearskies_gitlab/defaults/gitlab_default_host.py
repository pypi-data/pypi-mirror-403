import clearskies


class GitlabDefaultHost(clearskies.di.AdditionalConfigAutoImport):
    """
    Dependency injection provider for the GitLab host URL.

    This class automatically provides the GitLab host URL to the dependency
    injection container. It reads the host from the `GITLAB_HOST` environment
    variable, falling back to `https://gitlab.com/` if not set.

    This is used by the GitlabRestBackend and other GitLab-related classes
    to determine which GitLab instance to connect to.

    ```python
    # Set environment variable for self-hosted GitLab
    # export GITLAB_HOST=https://gitlab.mycompany.com/

    # Or use the default gitlab.com
    # (no environment variable needed)

    from clearskies_gitlab.rest.backends import GitlabRestBackend


    class MyModel(clearskies.Model):
        backend = GitlabRestBackend()
        # Will automatically use the configured host
    ```
    """

    def provide_gitlab_host(self, environment: clearskies.Environment):
        """
        Provide the GitLab host URL from environment or default.

        Reads the `GITLAB_HOST` environment variable. If not set or empty,
        returns the default GitLab.com URL.
        """
        gitlab_host = environment.get("GITLAB_HOST", True)
        return gitlab_host if gitlab_host else "https://gitlab.com/"
