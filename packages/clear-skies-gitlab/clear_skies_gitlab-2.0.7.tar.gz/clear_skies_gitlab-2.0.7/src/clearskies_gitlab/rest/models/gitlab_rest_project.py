from __future__ import annotations

from typing import Self

from clearskies import Model
from clearskies.columns import (
    BelongsToId,
    BelongsToModel,
    Boolean,
    Datetime,
    HasMany,
    HasOne,
    Integer,
    Json,
    Select,
    String,
)

from clearskies_gitlab.rest.backends import GitlabRestBackend
from clearskies_gitlab.rest.models import (
    gitlab_rest_group_reference,
    gitlab_rest_namespace,
    gitlab_rest_project_approval_config_reference,
    gitlab_rest_project_approval_rule_reference,
    gitlab_rest_project_protected_branch_reference,
    gitlab_rest_project_variable_reference,
)


class GitlabRestProject(Model):
    """
    Model for GitLab projects.

    This model provides access to the GitLab Projects API for managing projects
    and their settings. Projects are the core organizational unit in GitLab,
    containing repositories, issues, merge requests, and CI/CD pipelines.

    See https://docs.gitlab.com/api/projects/ for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestProject


    def my_function(projects: GitlabRestProject):
        # List all projects
        for project in projects:
            print(f"Project: {project.name}")
            print(f"URL: {project.web_url}")

        # Find a specific project
        my_project = projects.find("path_with_namespace=my-group/my-project")
        if my_project:
            print(f"Default branch: {my_project.default_branch}")
            print(f"Stars: {my_project.star_count}")

            # Access related resources
            for branch in my_project.protected_branches:
                print(f"Protected branch: {branch.name}")
    ```
    """

    id_column_name: str = "id"

    backend = GitlabRestBackend(
        api_to_model_map={
            "namespace.id": ["namespace_id", "group_id"],
        }
    )

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "projects"

    """
    The unique identifier for the project.
    """
    id = String()

    """
    A description of the project.
    """
    description = String()

    """
    The project description rendered as HTML.
    """
    description_html = String()

    """
    The visibility level of the project.

    Values: "public", "internal", or "private".
    """
    visibility = String()

    """
    The SSH URL for cloning the repository.
    """
    ssh_url_to_repo = String()

    """
    The HTTP URL for cloning the repository.
    """
    http_url_to_repo = String()

    """
    URL to the project's GitLab page.
    """
    web_url = String()

    """
    Topics/tags associated with the project.
    """
    topics = Json()

    """
    The display name of the project.
    """
    name = String()

    """
    The URL-friendly path/slug of the project.
    """
    path = String()

    """
    Whether the issues feature is enabled.
    """
    issues_enabled = Boolean()

    """
    The number of open issues.
    """
    open_issues_count = Integer()

    """
    Whether the merge requests feature is enabled.
    """
    merge_requests_enabled = Boolean()

    """
    Whether CI/CD jobs are enabled.
    """
    jobs_enabled = Boolean()

    """
    Whether the wiki feature is enabled.
    """
    wiki_enabled = Boolean()

    """
    Whether the snippets feature is enabled.
    """
    snippets_enabled = Boolean()

    """
    The date and time when the project was created.
    """
    created_at = Datetime()

    """
    The date and time when the project was last updated.
    """
    updated_at = Datetime()

    """
    The date and time of the last activity on the project.
    """
    last_activity_at = Datetime()

    """
    The import status of the project.
    """
    import_status = String()

    """
    Whether the project is archived.

    Archived projects are read-only.
    """
    archived = Boolean()

    """
    URL to the project's avatar image.
    """
    avatar_url = String()

    """
    Whether shared runners are enabled for this project.
    """
    shared_runners_enabled = Boolean()

    """
    The number of forks of this project.
    """
    forks_count = Integer()

    """
    The number of stars this project has received.
    """
    star_count = Integer()

    """
    The ID of the group this project belongs to.
    """
    group_id = BelongsToId(gitlab_rest_group_reference.GitlabRestGroupReference)

    """
    The group model this project belongs to.
    """
    group = BelongsToModel("group_id")

    """
    The ID of the namespace this project belongs to.
    """
    namespace_id = BelongsToId(gitlab_rest_namespace.GitlabRestNamespace)

    """
    The namespace model this project belongs to.
    """
    namespace = BelongsToModel("namespace_id")

    """
    Whether pipeline trigger can approve deployment.
    """
    allow_pipeline_trigger_approve_deployment = Boolean()

    """
    The default branch for the repository.
    """
    default_branch = String()

    """
    The user ID of the project creator.
    """
    creator_id = Integer()

    """
    URL to the project's README file.
    """
    readme_url = String()

    """
    Information about the project owner.
    """
    owner = Json()

    """
    Whether to resolve outdated diff discussions automatically.
    """
    resolve_outdated_diff_discussions = Boolean()

    """
    The URL used to import the project.
    """
    import_url = String()

    """
    The type of import (e.g., "github", "gitlab").
    """
    import_type = String()

    """
    Any error that occurred during import.
    """
    import_error = String()

    """
    URL to the project's license file.
    """
    license_url = String()

    """
    License information for the project.
    """
    license = Json()

    """
    Whether group runners are enabled.
    """
    group_runners_enabled = Boolean()

    """
    The container registry access level.
    """
    container_registry_access_level = Select(allowed_values=["disabled", "private", "enabled"])

    """
    The container security and compliance access level.
    """
    container_security_and_compliance_access_level = Select(allowed_values=["disabled", "private", "enabled"])

    """
    Container expiration policy settings.
    """
    container_expiration_policy = Json()

    """
    The runners registration token for this project.
    """
    runners_token = String()

    """
    Whether CI forward deployment is enabled.
    """
    ci_forward_deployment_enabled = Boolean()

    """
    Whether CI forward deployment rollback is allowed.
    """
    ci_forward_deployment_rollback_allowed = Boolean()

    """
    Whether CI caches are separated.
    """
    ci_separated_caches = Boolean()

    """
    The role required to cancel pipelines.
    """
    ci_restrict_pipeline_cancellation_role = Select(allowed_values=["maintainer", "developer", "no_one"])

    """
    The minimum role required to override pipeline variables.
    """
    ci_pipeline_variables_minimum_override_role = Select(
        allowed_values=["owner", "developer", "maintainer", "no_one_allowed"]
    )

    """
    Whether push to repository for job token is allowed.
    """
    ci_push_repository_for_job_token_allowed = Boolean()

    """
    Whether job logs are public.
    """
    public_jobs = Boolean()

    """
    Groups that this project is shared with.
    """
    shared_with_groups = Json()

    """
    The repository storage location.
    """
    repository_storage = String()

    """
    Whether merge is only allowed if pipeline succeeds.
    """
    only_allow_merge_if_pipeline_succeeds = Boolean()

    """
    Whether merge is allowed on skipped pipeline.
    """
    allow_merge_on_skipped_pipeline = Boolean()

    """
    Whether user-defined variables are restricted.
    """
    restrict_user_defined_variables = Boolean()

    """
    Whether merge is only allowed if all discussions are resolved.
    """
    only_allow_merge_if_all_discussions_are_resolved = Boolean()

    """
    Whether to remove source branch after merge.
    """
    remove_source_branch_after_merge = Boolean()

    """
    Whether to print merge request link after push.
    """
    printing_merge_requests_link_enabled = Boolean()

    """
    Whether users can request access to the project.
    """
    request_access_enabled = Boolean()

    """
    The merge method for the project.
    """
    merge_method = Select(allowed_values=["merge", "rebase_merge", "ff"])

    """
    The squash option for merge requests.
    """
    squash_option = Select(allowed_values=["never", "always", "default_on", "default_off"])

    """
    Whether this project is a mirror.
    """
    mirror = Boolean()

    """
    The user ID of the mirror owner.
    """
    mirror_user_id = Integer()

    """
    Whether mirror triggers builds.
    """
    mirror_trigger_builds = Boolean()

    """
    Whether only protected branches are mirrored.
    """
    only_mirror_protected_branches = Boolean()

    """
    Whether mirror overwrites diverged branches.
    """
    mirror_overwrites_diverged_branches = Boolean()

    """
    External authorization classification label.
    """
    external_authorization_classification_label = String()

    """
    Whether packages are enabled.
    """
    packages_enabled = Boolean()

    """
    Whether service desk is enabled.
    """
    service_desk_enabled = Boolean()

    """
    The service desk email address.
    """
    service_desk_address = String()

    """
    Whether to auto-close referenced issues.
    """
    autoclose_referenced_issues = Boolean()

    """
    The suggestion commit message template.
    """
    suggestion_commit_message = String()

    """
    Whether to enforce auth checks on uploads.
    """
    enforce_auth_checks_on_uploads = Boolean()

    """
    The merge commit message template.
    """
    merge_commit_template = String()

    """
    The squash commit message template.
    """
    squash_commit_template = String()

    """
    The issue branch template.
    """
    issue_branch_template = String()

    """
    Compliance frameworks applied to this project.
    """
    compliance_frameworks = Json()

    """
    Project statistics (storage, commits, etc.).
    """
    statistics = Json()

    """
    The container registry image prefix.
    """
    container_registry_image_prefix = String()

    """
    Whether the user can create merge requests in this project.
    """
    can_create_merge_request_in = Boolean()

    """
    Whether Auto DevOps is enabled.
    """
    auto_devops_enabled = Boolean()

    """
    The Auto DevOps deployment strategy.
    """
    auto_devops_deploy_strategy = Select(allowed_values=["continuous", "manual", "timed_incremental"])

    """
    Whether fork pipelines can run in parent project.
    """
    ci_allow_fork_pipelines_to_run_in_parent_project = Boolean()

    """
    The default Git depth for CI.
    """
    ci_default_git_depth = Integer()

    """
    The full name including namespace.
    """
    name_with_namespace = String()

    """
    The full path including namespace.
    """
    path_with_namespace = String()

    """
    User permissions for this project.
    """
    permissions = Json()

    """
    CI/CD variables for this project.
    """
    variables = HasMany(
        gitlab_rest_project_variable_reference.GitlabRestProjectVariableReference,
        foreign_column_name="project_id",
    )

    """
    Protected branches for this project.
    """
    protected_branches = HasMany(
        gitlab_rest_project_protected_branch_reference.GitlabRestProjectProtectedBranchReference,
        foreign_column_name="project_id",
    )

    """
    Approval configuration for this project.
    """
    approval_config = HasOne(
        gitlab_rest_project_approval_config_reference.GitlabRestProjectApprovalConfigReference,
        foreign_column_name="project_id",
    )

    """
    Approval rules for this project.
    """
    approval_rules = HasMany(
        gitlab_rest_project_approval_rule_reference.GitlabRestProjectApprovalRuleReference,
        foreign_column_name="project_id",
    )

    ### Search params

    """
    Whether to include hidden projects.
    """
    include_hidden = Boolean()

    """
    Whether to include projects pending deletion.
    """
    include_pending_delete = Boolean()

    """
    Filter by last activity after this date.
    """
    last_activity_after = Datetime()

    """
    Filter by last activity before this date.
    """
    last_activity_before = Datetime()

    """
    Whether to only return projects the user is a member of.
    """
    membership = Boolean()

    """
    Minimum access level required.
    """
    min_access_level = Integer()

    """
    Field to order results by.
    """
    order_by = Select(
        allowed_values=[
            "id",
            "name",
            "path",
            "created_at",
            "updated_at",
            "star_count",
            "last_activity_at",
            "similarity",
        ]
    )

    """
    Whether to only return projects owned by the current user.
    """
    owned = Boolean()

    """
    Whether to filter by repository checksum failure.
    """
    repository_checksum_failed = Boolean()

    """
    Filter by repository storage location.
    """
    repository_storage = String()

    """
    Whether to search in namespaces.
    """
    search_namespaces = Boolean()

    """
    Search query to filter projects.
    """
    search = String()

    """
    Whether to return simplified project information.
    """
    simple = Boolean()

    """
    Sort direction (asc or desc).
    """
    sort = String()

    """
    Whether to only return starred projects.
    """
    starred = Boolean()

    """
    Filter by topic ID.
    """
    topic_id = Integer()

    """
    Filter by topic name.
    """
    topic = String()

    """
    Filter by updated after this date.
    """
    updated_after = Datetime()

    """
    Filter by updated before this date.
    """
    updated_before = Datetime()

    """
    Filter by visibility level.
    """
    visibility = Select(allowed_values=["public", "internal", "private"])

    """
    Whether to filter by wiki checksum failure.
    """
    wiki_checksum_failed = Boolean()

    """
    Whether to include custom attributes in the response.
    """
    with_custom_attributes = Boolean()

    """
    Whether to only return projects with issues enabled.
    """
    with_issues_enabled = Boolean()

    """
    Whether to only return projects with merge requests enabled.
    """
    with_merge_requests_enabled = Boolean()

    """
    Filter by programming language.
    """
    with_programming_language = String()

    """
    Filter by deletion date.
    """
    marked_for_deletion_on = Datetime(date_format="%Y-%m-%d")
