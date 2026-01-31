from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib import parse

from clearskies import configs
from clearskies.backends import ApiBackend
from clearskies.decorators import parameters_to_properties
from clearskies.di import inject
from clearskies.query import Query
from clearskies.query.result import CountQueryResult
from requests.structures import CaseInsensitiveDict

if TYPE_CHECKING:
    from clearskies.authentication import Authentication
    from clearskies.query import Query


class GitlabRestBackend(ApiBackend):
    """
    Backend for interacting with the GitLab REST API.

    This backend extends the clearskies ApiBackend to provide GitLab-specific functionality
    for making REST API calls to GitLab.com or self-hosted GitLab instances. It handles
    authentication, pagination, and response mapping automatically.

    The backend uses dependency injection to obtain the GitLab host URL and authentication
    credentials, making it easy to configure for different environments.

    ```python
    import clearskies
    from clearskies_gitlab.rest.backends import GitlabRestBackend


    class MyGitlabModel(clearskies.Model):
        backend = GitlabRestBackend()
        id_column_name = "id"

        id = clearskies.columns.Integer()
        name = clearskies.columns.String()
    ```

    The backend automatically constructs the base URL using the configured GitLab host
    and appends `/api/v4` for the REST API version.
    """

    """
    Whether this backend supports count operations.

    GitLab REST API supports counting via the `x-total` response header,
    so this is set to True.
    """
    can_count = True

    """
    The GitLab host URL injected from the dependency container.

    This is typically set via the `GITLAB_HOST` environment variable or through
    explicit configuration. Defaults to `https://gitlab.com/` if not specified.
    """
    gitlab_host = inject.ByName("gitlab_host", cache=True)  # type: ignore[assignment]

    """
    The authentication handler injected from the dependency container.

    This is typically configured via the `GITLAB_AUTH_KEY` environment variable
    which provides a bearer token for API authentication.
    """
    authentication = inject.ByName("gitlab_auth", cache=False)  # type: ignore[assignment]

    """
    The requests handler for making HTTP calls.
    """
    requests = inject.Requests()

    _auth_headers: dict[str, str] = {}

    """
    A mapping from API response field names to model field names.

    Use this to handle cases where the GitLab API returns fields with different
    names than your model expects.
    """
    api_to_model_map = configs.AnyDict(default={})

    """
    The name of the query parameter used for pagination.

    GitLab uses `page` for page-based pagination.
    """
    pagination_parameter_name = configs.String(default="page")

    @parameters_to_properties
    def __init__(
        self,
        base_url: str | None = None,
        authentication: Authentication | None = None,
        model_casing: str = "snake_case",
        api_casing: str = "snake_case",
        api_to_model_map: dict[str, str | list[str]] = {},
        pagination_parameter_name: str = "page",
        pagination_parameter_type: str = "str",
        limit_parameter_name: str = "per_page",
    ):
        self.finalize_and_validate_configuration()

    @property
    def base_url(self) -> str:
        """
        Construct the base URL for GitLab API requests.

        Combines the configured GitLab host with the API version path (`/api/v4`).
        The host URL is automatically trimmed of trailing slashes to ensure
        proper URL construction.
        """
        return f"{self.gitlab_host.rstrip('/')}/api/v4"

    def count_method(self, query: Query) -> str:
        """
        Return the HTTP method to use when requesting a record count.

        GitLab supports HEAD requests for efficient counting without
        returning the full response body.
        """
        return "HEAD"

    def count(self, query: Query) -> CountQueryResult:
        """
        Return the count of records matching the query.

        Makes a HEAD request to the GitLab API and extracts the total count
        from the `x-total` response header. Returns a CountQueryResult object
        as required by the clearskies backend interface.
        """
        self.check_query(query)
        (url, method, body, headers) = self.build_records_request(query)
        response = self.execute_request(url, self.count_method(query), json=body, headers=headers)
        count = self._map_count_response(response.headers)
        return CountQueryResult(count=count)

    def _map_count_response(self, headers: CaseInsensitiveDict[str]) -> int:
        """Extract the total record count from GitLab response headers."""
        return int(headers.get("x-total", 0))

    def conditions_to_request_parameters(
        self, query: Query, used_routing_parameters: list[str]
    ) -> tuple[str, dict[str, str], dict[str, Any]]:
        """
        Convert query conditions to GitLab API request parameters.

        Transforms clearskies query conditions into URL parameters suitable for
        the GitLab REST API. Only equality conditions are supported; other operators
        will raise a ValueError.

        If a condition targets the model's ID column, it will be URL-encoded and
        returned as the route_id for path-based lookups.
        """
        route_id = ""

        url_parameters = {}
        for condition in query.conditions:
            if condition.column_name in used_routing_parameters:
                continue
            if condition.operator != "=":
                raise ValueError(
                    f"I'm not very smart and only know how to search with the equals operator, but I received a condition of {condition.parsed}.  If you need to support this, you'll have to extend the ApiBackend and overwrite the build_records_request method."
                )
            if condition.column_name == query.model_class.id_column_name:
                route_id = parse.quote_plus(condition.values[0]).replace("+", "%20")
                continue
            url_parameters[condition.column_name] = condition.values[0]

        return (route_id, url_parameters, {})
