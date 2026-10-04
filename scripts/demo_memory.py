"""Disposable, provenance-labeled engineering-memory demonstration.

Default execution proposes advice only. --review-actor explicitly exercises the
existing review transition as an operator demonstration, not human attestation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from diffcontext.index import build_index
from diffcontext.memory import Memory

SOURCE = '''def confirm_booking(commit, cleanup):
    result = commit()
    cleanup()
    return result
'''
FIXED = '''def confirm_booking(commit, cleanup):
    result = commit()
    # A committed booking is durable; optional cleanup cannot revoke it.
    try:
        cleanup()
    except OSError:
        pass
    return result
'''
LESSON = (
    "Exercise the real confirm_booking entrypoint when testing post-commit "
    "cleanup failure. A synthetic rejected cleanup after a transaction wrapper "
    "does not verify whether the service leaks that error. Mock external "
    "dependencies, preserve the real orchestration, and assert durable success."
)


def fresh_request(root: Path, action: str = "lessons") -> dict:
    """A new interpreter observes persisted status/hashes, not a shared object."""
    code = (
        "import json,sys; from pathlib import Path; "
        "from diffcontext.service import RepositoryService; "
        "s=RepositoryService(Path(sys.argv[1])); "
        "r=s.get_lessons(['booking.py:confirm_booking']) if sys.argv[2]=='lessons' "
        "else s.compile_context(symbols=['booking.py:confirm_booking']); "
        "print(json.dumps(r))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(root), action], cwd=PROJECT,
        text=True, capture_output=True, check=True,
    )
    return json.loads(result.stdout)


def check_durable_success(source: str) -> bool:
    namespace = {}
    exec(compile(source, "authored_booking_analogy", "exec"), namespace)
    def cleanup():
        raise OSError("authored cleanup outage")
    try:
        return namespace["confirm_booking"](lambda: {"confirmed": True}, cleanup) == {"confirmed": True}
    except OSError:
        return False


def run_demo(root: Path, review_actor: str | None = None) -> dict:
    root = root.resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError("Choose a new or empty demo directory; existing files are never replaced.")
    if review_actor is not None and not review_actor.strip():
        raise ValueError("Review actor must be nonempty.")
    root.mkdir(parents=True, exist_ok=True)
    report_path = PROJECT / "docs/demos/LUNA_BOOKING_TRIAL.md"
    provenance = {
        "kind": "observed_agent_test_gap_with_authored_analogy",
        "report": "docs/demos/LUNA_BOOKING_TRIAL.md",
        "report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "trial": "WI-020",
        "control_thread": "01a1074f-471b-7f31-b900-05844604b999",
        "claim": "Control's own cleanup check skipped the actual confirmation service; independent checks caught the remaining failure.",
        "source": "Wholly authored Python analogy; no BookMyShow source copied.",
    }
    source_path = root / "booking.py"
    source_path.write_text(SOURCE, encoding="utf-8")
    before = check_durable_success(SOURCE)
    source_path.write_text(FIXED, encoding="utf-8")
    after = check_durable_success(FIXED)
    assert not before and after, "Real-entrypoint regression must distinguish the authored fix."
    index = build_index(root)
    memory = Memory(root)
    try:
        lesson_id = memory.add(index, "booking.py:confirm_booking", LESSON, "booking.py")
    finally:
        memory.close()
    proposed = fresh_request(root)
    assert not proposed["lessons"] and proposed["excluded_lessons"][0]["status"] == "proposed"
    transcript = {
        "provenance": provenance,
        "regression": {"before_fix_passed": before, "after_fix_passed": after},
        "proposal": {"lesson_id": lesson_id, "retrieval": proposed},
        "review": {"performed": False, "human_approval_claimed": False},
    }
    if review_actor is not None:
        memory = Memory(root)
        try:
            memory.set_status(lesson_id, "confirmed")
        finally:
            memory.close()
        reviewed = fresh_request(root)
        compiled = fresh_request(root, "compile")
        assert reviewed["lessons"][0]["lesson"] == LESSON
        assert LESSON in compiled["text"]
        # Even unrelated source edits invalidate whole-file evidence today.
        source_path.write_text(FIXED + "\n# Later session changes the source snapshot.\n", encoding="utf-8")
        stale = fresh_request(root)
        assert not stale["lessons"] and stale["excluded_lessons"][0]["stale"]
        stale_context = fresh_request(root, "compile")
        assert LESSON not in stale_context["text"]
        transcript.update({
            "review": {"performed": True, "actor": review_actor, "kind": "explicit_operator_demo_review", "human_approval_claimed": False, "actor_persisted_in_memory_schema": False},
            "fresh_process_retrieval": reviewed,
            "compiled_lesson_included": True,
            "after_source_change": stale,
            "stale_lesson_compiled": False,
        })
    (root / "MEMORY_DEMO_RESULT.json").write_text(json.dumps(transcript, indent=2) + "\n", encoding="utf-8")
    return transcript


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path, help="New or empty disposable demo directory")
    parser.add_argument("--review-actor", help="Explicitly opt into operator review of this disposable lesson; does not attest human approval")
    args = parser.parse_args()
    print(json.dumps(run_demo(args.repo, args.review_actor), indent=2))


if __name__ == "__main__":
    main()
