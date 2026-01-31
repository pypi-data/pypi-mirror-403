from __future__ import annotations

from typing import Self

from clearskies import Model
from clearskies.columns import Boolean, Datetime, Email, HasOne, Integer, Json, String

from clearskies_gitlab.rest.backends import GitlabRestBackend
from clearskies_gitlab.rest.models import gitlab_rest_project_repository_commit_diff


class GitlabRestProjectRepositoryCommit(
    Model,
):
    """
    Model for GitLab project repository commits.

    This model provides access to the GitLab Commits API for retrieving
    commit information from a project's repository. Commits represent
    individual changes to the repository.

    See https://docs.gitlab.com/api/commits/ for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestProjectRepositoryCommit


    def my_function(commits: GitlabRestProjectRepositoryCommit):
        # List commits for a project
        for commit in commits.where("project_id=123"):
            print(f"Commit: {commit.short_id}")
            print(f"Author: {commit.author_name}")
            print(f"Title: {commit.title}")

        # Get commits for a specific branch
        for commit in commits.where("project_id=123&ref_name=main"):
            print(f"{commit.short_id}: {commit.title}")

        # Get commits with stats
        for commit in commits.where("project_id=123&with_stats=true"):
            print(f"Commit: {commit.short_id}")
            # Access the diff
            if commit.diff:
                print(f"Diff: {commit.diff.diff}")
    ```
    """

    backend = GitlabRestBackend()
    id_column_name = "id"

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "projects/:project_id/repository/commits"

    """
    The diff associated with this commit.

    Provides access to the file changes in this commit.
    """
    diff = HasOne(
        gitlab_rest_project_repository_commit_diff.GitlabRestProjectRepositoryCommitDiff,
        foreign_column_name="commit_id",
        where=lambda model, parent: model.where(f"gitlab_project_id={parent.id}"),
    )

    """
    The full commit SHA hash.

    This is the unique identifier for the commit.
    """
    id = String()

    """
    The shortened commit SHA hash.

    Typically the first 8 characters of the full SHA.
    """
    short_id = String()

    """
    The commit title (first line of the commit message).
    """
    title = String()

    """
    The name of the commit author.
    """
    author_name = String()

    """
    The email address of the commit author.
    """
    author_email = Email()

    """
    The date and time when the commit was authored.
    """
    authored_date = Datetime()

    """
    The name of the committer.

    May differ from author if the commit was applied by someone else.
    """
    committer_name = String()

    """
    The email address of the committer.
    """
    committer_email = Email()

    """
    The date and time when the commit was committed.
    """
    committed_date = Datetime()

    """
    The date and time when the commit was created in GitLab.
    """
    created_at = Datetime()

    """
    The full commit message.
    """
    messsage = String()

    """
    List of parent commit SHA hashes.

    Most commits have one parent. Merge commits have two.
    """
    parent_ids = Json()

    """
    URL to view the commit in GitLab.
    """
    web_url = String()

    """
    Extended trailer information from the commit message.

    Git trailers are key-value pairs at the end of commit messages.
    """
    extended_trailers = Json()

    ### Search params

    """
    The ID of the project to query commits for.
    """
    project_id = Integer()

    """
    The branch, tag, or commit SHA to list commits from.
    """
    ref_name = String()

    """
    Filter commits after this date.
    """
    since = Datetime()

    """
    Filter commits before this date.
    """
    until = Datetime()

    """
    Filter commits affecting this file path.
    """
    path = String()

    """
    Whether to retrieve commits from all branches.
    """
    all = Boolean()

    """
    Whether to include commit statistics (additions, deletions).
    """
    with_stats = Boolean()

    """
    Whether to follow only the first parent on merge commits.

    Useful for getting a linear history.
    """
    first_parent = Boolean()

    """
    Whether to include Git trailers in the response.
    """
    trailers = Boolean()
