
"""Tests for discover-repos.sh path handling."""

import json
import os
import subprocess
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "discover-repos.sh"


def run_discover(project_root: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Invoke discover-repos.sh for the given project root."""
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), str(project_root)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


def _run_discover_with_env(
    project_root: Path, extra_env: dict[str, str]
) -> subprocess.CompletedProcess:
    """Invoke discover-repos.sh with extra environment variables merged in."""
    env = {**os.environ, **extra_env}
    # Remove Tier 1 env var unless explicitly set by caller, to avoid test interference
    env.pop("CLAUDE_WORKSPACE_REPOS", None)
    env.update(extra_env)
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), str(project_root)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


def test_sibling_scan_uses_closedloop_repo_identity(tmp_path: Path) -> None:
    """Should discover siblings from `.closedloop-ai/.repo-identity.json` only."""
    parent = tmp_path / "workspace"
    current = parent / "current-repo"
    current.mkdir(parents=True)
    (current / ".closedloop-ai").mkdir()
    (current / ".closedloop-ai" / ".repo-identity.json").write_text(
        '{"name":"current","type":"service"}'
    )

    sibling = parent / "peer-repo"
    sibling.mkdir()
    (sibling / ".closedloop-ai").mkdir()
    (sibling / ".closedloop-ai" / ".repo-identity.json").write_text(
        '{"name":"peer","type":"library","discoverable":true}'
    )

    legacy = parent / "legacy-peer"
    (legacy / ".claude").mkdir(parents=True)
    (legacy / ".claude" / ".repo-identity.json").write_text(
        '{"name":"legacy","type":"library","discoverable":true}'
    )

    result = run_discover(current)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["currentRepo"]["name"] == "current"
    assert payload["discoveryMethod"] == "sibling_scan"
    assert payload["peers"] == [
        {"name": "peer", "type": "library", "path": str(sibling)}
    ]


# ---------------------------------------------------------------------------
# Tier 0: CLOSEDLOOP_ADD_DIRS tests
# ---------------------------------------------------------------------------


def _make_repo(parent: Path, name: str, identity: dict | None = None) -> Path:
    """Create a minimal repo directory, optionally with a .repo-identity.json."""
    repo = parent / name
    repo.mkdir(parents=True, exist_ok=True)
    if identity is not None:
        (repo / ".closedloop-ai").mkdir(exist_ok=True)
        (repo / ".closedloop-ai" / ".repo-identity.json").write_text(
            json.dumps(identity)
        )
    return repo


def test_tier0_add_dir_appears_in_peers(tmp_path: Path) -> None:
    """A path in CLOSEDLOOP_ADD_DIRS should appear in peers with discoveryMethod add_dir."""
    current = _make_repo(tmp_path, "current")
    extra = _make_repo(tmp_path, "extra", {"name": "extra-svc", "type": "service"})

    result = _run_discover_with_env(current, {"CLOSEDLOOP_ADD_DIRS": str(extra)})

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    peer_paths = {p["path"] for p in payload["peers"]}
    assert str(extra) in peer_paths

    extra_peer = next(p for p in payload["peers"] if p["path"] == str(extra))
    assert extra_peer["discoveryMethod"] == "add_dir"
    assert extra_peer["name"] == "extra-svc"
    assert extra_peer["type"] == "service"


def test_tier0_add_dir_falls_back_to_basename_without_identity(tmp_path: Path) -> None:
    """Tier 0 peer with no identity file should use the directory basename as name."""
    current = _make_repo(tmp_path, "current")
    anon = _make_repo(tmp_path, "my-anon-repo")

    result = _run_discover_with_env(current, {"CLOSEDLOOP_ADD_DIRS": str(anon)})

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    peer = next((p for p in payload["peers"] if p["path"] == str(anon)), None)
    assert peer is not None, f"Expected peer for {anon}, got {payload['peers']}"
    assert peer["name"] == "my-anon-repo"


def test_tier0_multiple_add_dirs_pipe_separated(tmp_path: Path) -> None:
    """Multiple pipe-separated paths in CLOSEDLOOP_ADD_DIRS should all appear as peers."""
    current = _make_repo(tmp_path, "current")
    repo_a = _make_repo(tmp_path, "repo-a")
    repo_b = _make_repo(tmp_path, "repo-b")

    add_dirs = f"{repo_a}|{repo_b}"
    result = _run_discover_with_env(current, {"CLOSEDLOOP_ADD_DIRS": add_dirs})

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    peer_paths = {p["path"] for p in payload["peers"]}
    assert str(repo_a) in peer_paths
    assert str(repo_b) in peer_paths


def test_tier0_skips_current_repo(tmp_path: Path) -> None:
    """A CLOSEDLOOP_ADD_DIRS entry equal to the current repo path should be skipped."""
    current = _make_repo(tmp_path, "current")

    result = _run_discover_with_env(current, {"CLOSEDLOOP_ADD_DIRS": str(current)})

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    peer_paths = [p["path"] for p in payload["peers"]]
    assert str(current) not in peer_paths, f"Current repo should not appear in peers: {peer_paths}"


def test_tier0_deduplicates_with_tier2_sibling_scan(tmp_path: Path) -> None:
    """A sibling that is also in CLOSEDLOOP_ADD_DIRS should appear only once in peers."""
    workspace = tmp_path / "workspace"
    current = _make_repo(workspace, "current", {"name": "current", "type": "service"})
    sibling = _make_repo(
        workspace, "sibling-svc", {"name": "sibling-svc", "type": "library", "discoverable": True}
    )

    # The sibling is both a Tier 0 add-dir AND a Tier 2 sibling
    result = _run_discover_with_env(current, {"CLOSEDLOOP_ADD_DIRS": str(sibling)})

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    paths = [p["path"] for p in payload["peers"]]
    assert paths.count(str(sibling)) == 1, (
        f"Sibling should appear exactly once; got peers: {payload['peers']}"
    )


def test_tier0_peer_marked_as_add_dir_not_sibling_scan(tmp_path: Path) -> None:
    """When a sibling is in Tier 0, the peer's discoveryMethod must be 'add_dir', not sibling_scan."""
    workspace = tmp_path / "workspace"
    current = _make_repo(workspace, "current", {"name": "current", "type": "service"})
    sibling = _make_repo(
        workspace, "shared-lib", {"name": "shared-lib", "type": "library", "discoverable": True}
    )

    result = _run_discover_with_env(current, {"CLOSEDLOOP_ADD_DIRS": str(sibling)})

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    peer = next((p for p in payload["peers"] if p["path"] == str(sibling)), None)
    assert peer is not None
    assert peer["discoveryMethod"] == "add_dir"
