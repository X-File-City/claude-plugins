"""Tests for validate_plan.py."""
import pytest

from validate_plan import validate_schema_fields


def _minimal_plan() -> dict:
    """Return a plan dict with all required fields populated with valid values."""
    return {
        "content": "some content",
        "acceptanceCriteria": [],
        "pendingTasks": [],
        "completedTasks": [],
        "openQuestions": [],
        "answeredQuestions": [],
        "gaps": [],
    }


@pytest.mark.parametrize(
    ("scenario", "repositories"),
    [
        (
            "single_secondary_entry",
            {"secondary": {"path": "/foo", "isPrimary": False}},
        ),
        (
            "primary_and_secondary_entries",
            {
                "primary": {"path": "/abs/primary", "isPrimary": True},
                "frontend": {"path": "/abs/frontend", "isPrimary": False},
            },
        ),
    ],
)
def test_validate_schema_accepts_canonical_repositories(
    scenario: str, repositories: dict
) -> None:
    """validate_schema_fields must accept the canonical multi-repo shape.

    Each 'repositories' entry carries only `path` and `isPrimary` — the two
    fields the schema defines after the `type` field was removed. Both a
    single-entry shape and a multi-entry primary+secondary shape must
    validate without producing any issues.
    """
    plan = _minimal_plan()
    plan["repositories"] = repositories

    issues = validate_schema_fields(plan)

    assert issues == [], f"[{scenario}] expected no issues but got: {issues}"
