"""
Versioned migrations for PullRequestResults data.

When the schema changes, add a new migration function and append it to ResultsMigrator.migrations.
Old stored data will be migrated on-the-fly when loaded via from_dict().
"""

from __future__ import annotations

from typing import Any


def migrate_resview_results_scopes(data: dict[str, Any]) -> dict[str, Any]:
    """
    Migrate v1 -> v2:
    - ReviewResult.scopes -> reviewed_for
    - ReviewResult.state computed from review.state
    """
    if "review_results" in data:
        for review_result in data["review_results"].values():
            # Rename scopes -> reviewed_for
            if "scopes" in review_result:
                review_result["matched_scopes"] = review_result.pop("scopes")

    return data


class ResultsMigrator:
    """
    Handles versioned migrations for PullRequestResults data.
    """

    # Ordered list of migration functions.
    # Index 0 = v1->v2, index 1 = v2->v3, etc.
    migrations = [
        migrate_resview_results_scopes,
    ]

    @classmethod
    def current_version(cls) -> int:
        """Current version is always 1 more than the number of migrations."""
        return len(cls.migrations) + 1

    @classmethod
    def migrate(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Apply all necessary migrations to bring data to current version.

        Data without a version field is assumed to be v1.
        """
        version = data.get("version", 1)

        # Apply migrations from current version to latest
        for migration in cls.migrations[version - 1 :]:
            data = migration(data)

        data["version"] = cls.current_version()
        return data
