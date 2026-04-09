"""Tests for validate_plan.py."""
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


def test_validate_schema_fields_accepts_unknown_repositories_key() -> None:
    """validate_schema_fields must silently accept an unknown top-level key.

    Regression test: a plan dict that contains all required fields PLUS an
    additional 'repositories' key (e.g. added by tooling) should not produce
    any issues, confirming that validate_schema_fields only checks for
    REQUIRED_FIELDS membership and does not reject unknown keys.
    """
    plan = _minimal_plan()
    plan["repositories"] = {"secondary": {"path": "/foo", "isPrimary": False}}

    issues = validate_schema_fields(plan)

    assert issues == [], f"Expected no issues but got: {issues}"
