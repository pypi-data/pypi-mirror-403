from __future__ import annotations

from typing import Self

from clearskies import Model
from clearskies.columns import Boolean, Integer, String

from clearskies_gitlab.rest.backends import GitlabRestBackend


class GitlabRestProjectRepositoryCommitDiff(
    Model,
):
    r"""
    Model for GitLab project repository commit diffs.

    This model provides access to the GitLab Commits API for retrieving
    the diff (file changes) of a specific commit. Each diff entry represents
    changes to a single file.

    See https://docs.gitlab.com/api/commits/#get-the-diff-of-a-commit for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestProjectRepositoryCommitDiff


    def my_function(diffs: GitlabRestProjectRepositoryCommitDiff):
        # Get diff for a specific commit
        for diff in diffs.where("project_id=123&commit_id=abc123"):
            print(f"File: {diff.new_path}")
            if diff.new_file:
                print("  (new file)")
            elif diff.deleted_file:
                print("  (deleted)")
            elif diff.renamed_file:
                print(f"  (renamed from {diff.old_path})")
            print(f"Diff:\n{diff.diff}")

        # Get unified diff format
        for diff in diffs.where("project_id=123&commit_id=abc123&unidiff=true"):
            print(diff.diff)
    ```
    """

    id_column_name = "commit_id"

    backend = GitlabRestBackend()

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "projects/:project_id/repository/commits/:commit_id/diff"

    """
    The diff content showing the changes.

    Contains the unified diff format showing additions and deletions.
    """
    diff = String()

    """
    The new file path after the commit.

    For renamed files, this is the destination path.
    """
    new_path = String()

    """
    The old file path before the commit.

    For renamed files, this is the source path.
    """
    old_path = String()

    """
    The file mode before the change.

    Unix file permission mode (e.g., 100644 for regular file).
    """
    a_mode = Integer()

    """
    The file mode after the change.

    Unix file permission mode (e.g., 100644 for regular file).
    """
    b_mode = Integer()

    """
    Whether this is a newly created file.
    """
    new_file = Boolean()

    """
    Whether this file was renamed.
    """
    renamed_file = Boolean()

    """
    Whether this file was deleted.
    """
    deleted_file = Boolean()

    ### Search params

    """
    The ID of the project containing the commit.
    """
    project_id = Integer()

    """
    The SHA hash of the commit to get the diff for.
    """
    commit_id = String()

    """
    Whether to return the diff in unified diff format.

    When true, returns a more standard unified diff format.
    """
    unidiff = Boolean()
