"""Incremental delta review (decision 0053): the close gate proves the WHOLE
task diff was reviewed across a chain of contiguous coverage segments, so
`forge review` can re-review only the delta since the last clean round.

These exercise the close-gate logic (`require_coherent_review_run` /
`_review_coverage_problems`) directly against a real git repo — the review run
itself needs the Codex companion, but the coverage guarantee is pure and worth
pinning on its own.
"""
from __future__ import annotations

import hashlib

from test_gates import (  # noqa: I001 — test_gates puts factory/scripts on sys.path
    git, head, repo,
)
from factory_lib import (  # noqa: E402
    branch_diff_digest, require_coherent_review_run,
)

__all__ = ["repo"]


def _commit(repo, path: str, text: str) -> str:
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"edit {path}")
    return head(repo)


def _reviews(repo, coverage, *, digest: str | None = None) -> dict[str, dict]:
    """Three coherent, HEAD-bound lens artifacts carrying a coverage chain."""
    brief = hashlib.sha256(b"fixture brief").hexdigest()
    dig = digest if digest is not None else branch_diff_digest(repo)
    run_id = hashlib.sha256((brief + dig).encode()).hexdigest()
    return {
        aspect: {
            "score": 9, "blocking_findings": [], "generated_by": "autoreview",
            "commit": head(repo), "review_run_id": run_id, "brief_sha256": brief,
            "branch_diff_digest": dig, "coverage": [dict(s) for s in coverage],
        }
        for aspect in ("quality", "performance", "security")
    }


def test_single_full_segment_covers_the_diff(repo):
    base = head(repo)  # == origin/main merge-base
    tip = _commit(repo, "src/a.py", "a = 1\n")
    reviews = _reviews(repo, [{"from": base, "to": tip}])
    assert require_coherent_review_run(repo, reviews) == []


def test_contiguous_delta_segments_cover_the_diff(repo):
    base = head(repo)
    t1 = _commit(repo, "src/a.py", "a = 1\n")
    t2 = _commit(repo, "src/b.py", "b = 2\n")
    reviews = _reviews(repo, [{"from": base, "to": t1}, {"from": t1, "to": t2}])
    assert require_coherent_review_run(repo, reviews) == []


def test_coverage_must_reach_head(repo):
    base = head(repo)
    t1 = _commit(repo, "src/a.py", "a = 1\n")
    _commit(repo, "src/b.py", "b = 2\n")  # HEAD now t2, coverage stops at t1
    reviews = _reviews(repo, [{"from": base, "to": t1}])
    problems = require_coherent_review_run(repo, reviews)
    assert problems and "coverage stops" in problems[0], problems


def test_non_contiguous_segments_are_rejected(repo):
    base = head(repo)
    t1 = _commit(repo, "src/a.py", "a = 1\n")
    t2 = _commit(repo, "src/b.py", "b = 2\n")
    # A gap: [base..t1] then [t2..t2] skips t1..t2.
    reviews = _reviews(repo, [{"from": base, "to": t1}, {"from": t2, "to": t2}])
    problems = require_coherent_review_run(repo, reviews)
    assert problems and "not contiguous" in problems[0], problems


def test_lenses_must_share_one_chain(repo):
    base = head(repo)
    t1 = _commit(repo, "src/a.py", "a = 1\n")
    t2 = _commit(repo, "src/b.py", "b = 2\n")
    reviews = _reviews(repo, [{"from": base, "to": t2}])
    # Security lags a segment behind the other two.
    reviews["security"]["coverage"] = [{"from": base, "to": t1}]
    problems = require_coherent_review_run(repo, reviews)
    assert problems and "identical across" in problems[0], problems


def test_product_change_before_first_segment_is_caught(repo):
    base = head(repo)
    t1 = _commit(repo, "src/early.py", "early = 1\n")  # product change base..t1
    t2 = _commit(repo, "src/late.py", "late = 2\n")
    # Coverage starts at t1, so the product change in base..t1 was never reviewed.
    reviews = _reviews(repo, [{"from": t1, "to": t2}])
    problems = require_coherent_review_run(repo, reviews)
    assert problems and "before the first reviewed commit" in problems[0], problems


def test_legacy_reviews_without_coverage_still_pass(repo):
    base = head(repo)
    tip = _commit(repo, "src/a.py", "a = 1\n")
    reviews = _reviews(repo, [{"from": base, "to": tip}])
    for aspect in reviews:
        del reviews[aspect]["coverage"]
    # No coverage field → legacy full-diff review, coherence-only gate applies.
    assert require_coherent_review_run(repo, reviews) == []


def test_mixed_coverage_presence_fails_closed(repo):
    base = head(repo)
    tip = _commit(repo, "src/a.py", "a = 1\n")
    reviews = _reviews(repo, [{"from": base, "to": tip}])
    # One lens never recorded coverage while the others did — must fail closed,
    # not silently fall back to the legacy (coverage-skipping) path.
    del reviews["security"]["coverage"]
    problems = require_coherent_review_run(repo, reviews)
    assert problems and "some lenses but not security" in problems[0], problems


def test_coverage_is_enforced_at_the_task_shipping_gate(repo):
    import json as _json

    from factory_lib import task_evidence_path, task_proof_problems
    base = head(repo)
    t1 = _commit(repo, "src/a.py", "a = 1\n")
    tip = _commit(repo, "src/b.py", "b = 2\n")  # reviewed tip

    def write(name, payload):
        path = task_evidence_path(repo, "ENG-1", "T1", name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_json.dumps(payload))

    write("verify.json", {"ok": True, "commit": tip, "generated_by": "verify"})
    write("tests.json", {"automated": {"status": "passed",
                                       "generated_by": "implementer"}})
    # Clean scores, but coverage stops at t1 while the reviewed tip is `tip`.
    for lens in ("quality", "performance", "security"):
        write(f"reviews/{lens}.json", {
            "score": 9, "blocking_findings": [], "generated_by": "autoreview",
            "commit": tip, "coverage": [{"from": base, "to": t1}]})

    problems = task_proof_problems(repo, "ENG-1", {"id": "T1"})
    assert any("coverage" in p for p in problems), problems


def _write_lens_coverage(repo, story: str, task_id: str, per_lens: dict) -> None:
    import json as _json

    from factory_lib import task_evidence_path
    for lens, coverage in per_lens.items():
        path = task_evidence_path(repo, story, task_id, f"reviews/{lens}.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"score": 9, "blocking_findings": [], "generated_by": "autoreview"}
        if coverage is not None:
            payload["coverage"] = coverage
        path.write_text(_json.dumps(payload))


def test_prior_coverage_reads_an_agreed_chain(repo):
    from forge_cli.review import _prior_coverage
    chain = [{"from": "a" * 40, "to": "b" * 40}]
    _write_lens_coverage(repo, "ENG-1", "T1", {
        "quality": chain, "performance": chain, "security": chain})
    assert _prior_coverage(repo, "ENG-1", "T1") == chain


def test_prior_coverage_starts_fresh_when_lenses_disagree(repo):
    from forge_cli.review import _prior_coverage
    _write_lens_coverage(repo, "ENG-1", "T1", {
        "quality": [{"from": "a" * 40, "to": "b" * 40}],
        "performance": [{"from": "a" * 40, "to": "c" * 40}],
        "security": [{"from": "a" * 40, "to": "b" * 40}]})
    assert _prior_coverage(repo, "ENG-1", "T1") == []


def test_prior_coverage_starts_fresh_when_a_lens_has_none(repo):
    from forge_cli.review import _prior_coverage
    chain = [{"from": "a" * 40, "to": "b" * 40}]
    _write_lens_coverage(repo, "ENG-1", "T1", {
        "quality": chain, "performance": chain, "security": None})
    assert _prior_coverage(repo, "ENG-1", "T1") == []
