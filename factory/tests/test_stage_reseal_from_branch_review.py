"""`forge stage reseal`: refresh a stale stage-local review stamp to HEAD when a
clean three-lens BRANCH review already covers the current committed tree.

A stage seals its `local_review_stamp` against the WHOLE product tree, so any
later product edit — even a one-line branch-review fix already cleared by a
fresh branch review at HEAD — moves `product_tree_digest` and stales the stamp.
Before this command the only way back was another full local autoreview round
(often via a manual degraded window, because `forge delegate`'s sandbox has no
network to run the seal). Reseal re-authorizes the stamp from the branch review
that already covers exactly this tree — and refuses when it does not.
"""
from __future__ import annotations

import hashlib
import json

from test_gates import (  # noqa: I001 — test_gates puts factory/scripts on sys.path
    git, head, intake, record_skeleton_then_frontier, repo, run, save_plan,
    sign_off, skeletal_stage_task,
)
from factory_lib import (  # noqa: E402
    branch_diff_digest, evidence_path, load_json, product_tree_digest,
    protected_decomposition_state_path,
)
from forge_cli.stages import load_stages, task_digest, write_stages  # noqa: E402

__all__ = ["repo"]

STALE_DIGEST = "0" * 64


def _stage(repo, task_id: str = "T1") -> dict:
    return next(s for s in load_stages(repo)["stages"] if s["id"] == task_id)


def _seed_active_stage_with_stale_stamp(repo, tmp_path) -> str:
    """One active T1 stage whose stamp is stale against a fresh product commit.

    Returns the reviewed HEAD sha the branch review should be stamped at.
    """
    sign_off(repo)
    intake(repo)
    save_plan(repo, tmp_path)
    record_skeleton_then_frontier(repo, [skeletal_stage_task("T1")])
    base_sha = head(repo)

    # A product commit the branch review clears but the stage stamp predates.
    # Commit the whole tree (sign-off/intake also touch product files like
    # harness.yaml) so the reviewed HEAD has no dirty product.
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "login.py").write_text("def login():\n    return True\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "T1: login slice")
    reviewed = head(repo)

    contract = next(
        t for t in load_json(protected_decomposition_state_path(repo))["tasks"]
        if t["id"] == "T1")
    write_stages(repo, {
        "issue": "ENG-1",
        "stages": [
            {"id": "T1", "title": "first", "status": "active",
             "task_sha256": task_digest(contract), "base_sha": base_sha,
             "local_review_stamp": {
                 "stage_id": "T1", "task_sha256": task_digest(contract),
                 "brief_sha256": "", "base_sha": base_sha,
                 "product_tree_digest": STALE_DIGEST,
                 "recorded_at": "2026-01-01T00:00:00+00:00",
                 "generated_by": "autoreview"}},
        ],
    })
    return reviewed


def _seed_branch_review(repo, commit: str, *, digest: str | None = None,
                        blocking: bool = False) -> None:
    """Write the three-lens branch review to the story evidence dir."""
    brief_sha256 = hashlib.sha256(b"fixture branch review brief").hexdigest()
    branch_digest = digest if digest is not None else branch_diff_digest(repo)
    review_run_id = hashlib.sha256(
        (brief_sha256 + branch_digest).encode()).hexdigest()
    for aspect in ("quality", "performance", "security"):
        path = evidence_path(repo, "ENG-1", f"reviews/{aspect}.json",
                             for_write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "score": 9,
            "blocking_findings": [{"summary": "x"}] if blocking else [],
            "generated_by": "autoreview", "commit": commit,
            "review_run_id": review_run_id, "brief_sha256": brief_sha256,
            "branch_diff_digest": branch_digest,
        }))


def test_reseal_refreshes_a_stale_stamp_from_a_clean_branch_review(repo, tmp_path):
    reviewed = _seed_active_stage_with_stale_stamp(repo, tmp_path)
    _seed_branch_review(repo, reviewed)

    # The stamp really is stale against the current committed tree.
    assert _stage(repo)["local_review_stamp"]["product_tree_digest"] == STALE_DIGEST
    assert product_tree_digest(repo) != STALE_DIGEST

    code, out = run(repo, "forge.py", "stage", "reseal", "T1", "--repo", str(repo))
    assert code == 0, out
    assert "Resealed" in out, out

    stamp = _stage(repo)["local_review_stamp"]
    assert stamp["product_tree_digest"] == product_tree_digest(repo)
    assert stamp["generated_by"] == "branch-review-reseal"


def test_reseal_refuses_when_the_branch_review_is_stale(repo, tmp_path):
    reviewed = _seed_active_stage_with_stale_stamp(repo, tmp_path)
    # A branch review bound to a DIFFERENT committed diff cannot authorize.
    _seed_branch_review(repo, reviewed, digest="f" * 64)

    code, out = run(repo, "forge.py", "stage", "reseal", "T1", "--repo", str(repo))
    assert code != 0, out
    assert "reseal" in out and "branch review" in out, out
    # The stale stamp is left exactly as it was — no silent refresh.
    assert _stage(repo)["local_review_stamp"]["product_tree_digest"] == STALE_DIGEST


def test_reseal_refuses_on_a_blocking_branch_finding(repo, tmp_path):
    reviewed = _seed_active_stage_with_stale_stamp(repo, tmp_path)
    _seed_branch_review(repo, reviewed, blocking=True)

    code, out = run(repo, "forge.py", "stage", "reseal", "T1", "--repo", str(repo))
    assert code != 0, out
    assert _stage(repo)["local_review_stamp"]["product_tree_digest"] == STALE_DIGEST


def test_reseal_needs_an_existing_stamp_to_refresh(repo, tmp_path):
    reviewed = _seed_active_stage_with_stale_stamp(repo, tmp_path)
    _seed_branch_review(repo, reviewed)
    # A stage that never sealed locally has nothing to re-authorize.
    data = load_stages(repo)
    stage = next(s for s in data["stages"] if s["id"] == "T1")
    stage.pop("local_review_stamp")
    write_stages(repo, data)

    code, out = run(repo, "forge.py", "stage", "reseal", "T1", "--repo", str(repo))
    assert code != 0, out
    assert "no stage-local review stamp" in out, out
