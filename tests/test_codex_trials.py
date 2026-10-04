import json
from dataclasses import replace
import tempfile
import unittest
from pathlib import Path

from diffcontext.coding import load_suite
from diffcontext.codex_trials import parse_events, prepare_trials, run_trials

ROOT = Path(__file__).resolve().parents[1]


def stream(items=None, usage=None, text=None):
    events = [{"type": "thread.started", "thread_id": "fixture"}, {"type": "turn.started"}]
    events.extend(items or [])
    events.append({"type": "item.completed", "item": {"type": "agent_message",
                   "text": text or json.dumps({"edits": [{"path": "a.py", "content": "pass\n"}]})}})
    events.append({"type": "turn.completed", "usage": usage})
    return "\n".join(json.dumps(event) for event in events)


class CodexTrialTests(unittest.TestCase):
    def test_observed_counts_preserve_unknowns_and_zero(self):
        result = parse_events(stream(usage={"input_tokens": 100, "cached_input_tokens": 0, "output_tokens": 7}))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["usage"], {"input_tokens": 100, "cached_input_tokens": 0,
                                          "output_tokens": 7, "reasoning_output_tokens": None})
        self.assertIsNone(parse_events(stream())["usage"])
        self.assertEqual(parse_events(stream(usage={"input_tokens": 1, "cached_input_tokens": 2}))["status"], "invalid_usage")

    def test_external_tool_trace_is_unscored_even_with_valid_response(self):
        for kind in ("mcp_tool_call", "command_execution", "web_search", "file_change"):
            with self.subTest(kind=kind):
                result = parse_events(stream(items=[{"type": "item.started", "item": {"type": kind}}]))
                self.assertEqual(result["status"], "tool_contamination")
                self.assertNotIn("edits", result)

    def test_duplicate_edits_and_incomplete_trace_are_rejected(self):
        candidate = {"edits": [{"path": "a.py", "content": "one"}, {"path": "a.py", "content": "two"}]}
        self.assertEqual(parse_events(stream(text=json.dumps(candidate)))["status"], "invalid_candidate")
        self.assertEqual(parse_events(stream().rsplit("\n", 1)[0])["status"], "provider_error")
        self.assertEqual(parse_events(stream() + "\ntruncated")["status"], "invalid_trace")
        self.assertEqual(parse_events(stream() + '\n{"type":"unknown.tool"}')["status"], "invalid_trace")

    def test_changed_acceptance_definition_rejects_checkpoint_reuse(self):
        import shutil
        task = load_suite(ROOT / "evals/coding_tasks/suite.json")[0]
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            shutil.copytree(task.directory, directory / "task")
            task = replace(task, directory=directory / "task")
            output, scratch = directory / "output", directory / "scratch"
            prepare_trials([task], output, scratch, "requested-small-model", 1)
            run_trials([task], output, scratch, lambda request: {"status": "ok", "edits": {}, "usage": None})
            (task.directory / "checks.py").write_text("# altered acceptance\n")
            with self.assertRaisesRegex(ValueError, "Grader changed"):
                run_trials([task], output, scratch, lambda request: self.fail("No new call allowed"))

    def test_frozen_protocol_counterbalances_and_resumes_without_new_calls(self):
        task = load_suite(ROOT / "evals/coding_tasks/suite.json")[0]
        with tempfile.TemporaryDirectory() as directory:
            output, scratch = Path(directory) / "output", Path(directory) / "scratch"
            manifest = prepare_trials([task], output, scratch, "requested-small-model", 2)
            self.assertEqual(manifest["order"], [f"{task.id}-lexical-r1", f"{task.id}-hybrid-r1",
                                               f"{task.id}-hybrid-r2", f"{task.id}-lexical-r2"])
            calls = []
            def runner(request):
                calls.append(request)
                self.assertIsNone(request["temperature"])
                self.assertNotIn("max_output_tokens", request)
                self.assertLessEqual(request["max_input_estimated_tokens"], 3000)
                return {"status": "ok", "edits": {}, "usage": None, "tool_calls": 0}
            summary = run_trials([task], output, scratch, runner)
            self.assertEqual(len(calls), 4)
            self.assertEqual(summary["conditions_summary"]["hybrid"]["passed"], 0)
            self.assertIsNone(summary["conditions_summary"]["hybrid"]["usage_totals"]["input_tokens"])
            run_trials([task], output, scratch, runner)
            self.assertEqual(len(calls), 4)
            packet = output / "requests" / (manifest["order"][0] + ".json")
            data = json.loads(packet.read_text())
            data["request"]["prompt"] += " changed"
            packet.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "request changed"):
                run_trials([task], output, scratch, runner)

    def test_post_generation_output_budget_violation_is_not_quality_failure(self):
        task = load_suite(ROOT / "evals/coding_tasks/suite.json")[0]
        with tempfile.TemporaryDirectory() as directory:
            output, scratch = Path(directory) / "output", Path(directory) / "scratch"
            prepare_trials([task], output, scratch, "requested-small-model", 1, output_budget=128)
            result = run_trials([task], output, scratch, lambda request: {
                "status": "ok", "edits": {}, "usage": {"input_tokens": 100, "output_tokens": 129}})
            for summary in result["conditions_summary"].values():
                self.assertEqual(summary["scored"], 0)
                self.assertEqual(summary["outcomes"], {"output_budget_violation": 1})


if __name__ == "__main__":
    unittest.main()
