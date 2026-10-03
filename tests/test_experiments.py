import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import test_core
from diffcontext.coding import load_suite, trial_workspace
from diffcontext.experiments import CONDITIONS, CommandRunner, ReplayRunner, RunnerError, export_requests, make_request, run_experiment, validate_response, write_json

SUITE = Path(__file__).resolve().parents[1] / "evals" / "coding_tasks" / "suite.json"


class ScriptedRunner:
    kind = "scripted_test"

    def __init__(self, tasks, fixed=True):
        self.tasks = {task.id: task for task in tasks}
        self.fixed = fixed
        self.calls = 0

    def __call__(self, request):
        self.calls += 1
        task = self.tasks[request["trial_id"].split(":")[0]]
        edits = json.loads((task.directory / "reference.json").read_text()) if self.fixed else {}
        return {"schema_version": 1, "model": request["model"], "request_hash": request["request_hash"], "status": "ok", "edits": edits}


class ExperimentTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    def test_packets_budget_leakage_memory_and_reproducibility(self):
        tasks = load_suite(SUITE)
        for task in tasks:
            for condition in CONDITIONS:
                with trial_workspace(task, self.root / "scratch") as root:
                    request, diagnostics = make_request(task, root, condition, "test-model")
                with trial_workspace(task, self.root / "scratch") as root:
                    repeat, _ = make_request(task, root, condition, "test-model")
                self.assertEqual(request["request_hash"], repeat["request_hash"])
                self.assertLessEqual(diagnostics["prompt_estimated_tokens"], 4000)
                self.assertNotIn("checks.py", request["prompt"])
                self.assertNotIn("reference.json", request["prompt"])
                self.assertNotIn("test_exhaustion_preserves_exception_and_count", request["prompt"])
                self.assertNotIn("test_page_boundaries", request["prompt"])
                if condition == "memory":
                    self.assertTrue(diagnostics["included_lessons"])
                    self.assertIn(task.lesson, request["prompt"])
                elif condition == "stale_memory":
                    self.assertFalse(diagnostics["included_lessons"])
                    self.assertNotIn(task.lesson, request["prompt"])
                    self.assertTrue(diagnostics["excluded_lessons"][0]["stale"])

    def test_reference_trials_resume_and_changed_config_rejected(self):
        tasks = load_suite(SUITE)[:1]
        runner = ScriptedRunner(tasks)
        output = self.root / "experiment"
        report = run_experiment(tasks, output, self.root / "scratch", runner, "test-model")
        self.assertEqual(runner.calls, 4)
        self.assertTrue(all(row["outcome"] == "passed" for row in report["trials"]))
        self.assertIsNone(report["reported_cost_usd"])
        resumed = run_experiment(tasks, output, self.root / "scratch", runner, "test-model")
        self.assertEqual(runner.calls, 4)
        self.assertEqual(resumed["runner_invocations_this_execution"], 0)
        with self.assertRaisesRegex(ValueError, "configuration"):
            run_experiment(tasks, output, self.root / "scratch", runner, "different-model")
        runner.identity = "different runner"
        with self.assertRaisesRegex(ValueError, "identity"):
            run_experiment(tasks, output, self.root / "scratch", runner, "test-model")

    def test_quota_stops_dispatch_and_resume_retries_unscored(self):
        tasks = load_suite(SUITE)[:1]
        runner = ScriptedRunner(tasks)
        output = self.root / "experiment"
        def limited(request):
            runner.calls += 1
            return {"schema_version": 1, "model": request["model"], "request_hash": request["request_hash"], "status": "rate_limited"}
        with patch.object(ScriptedRunner, "__call__", side_effect=limited):
            report = run_experiment(tasks, output, self.root / "scratch", runner, "test-model")
        self.assertEqual(runner.calls, 1)
        self.assertEqual(report["completed"], 1)
        self.assertEqual(report["summary"]["lexical"]["scored"], 0)
        self.assertIsNone(report["summary"]["lexical"]["success_rate"])
        original_call = ScriptedRunner.__call__
        def known_cost(request):
            response = original_call(runner, request)
            response["usage"] = {"cost_usd": 0.01}
            return response
        with patch.object(ScriptedRunner, "__call__", side_effect=known_cost):
            resumed = run_experiment(tasks, output, self.root / "scratch", runner, "test-model")
        self.assertEqual(resumed["completed"], 4)
        self.assertEqual(runner.calls, 5)
        self.assertEqual(len(resumed["trials"][0]["attempts"]), 2)
        self.assertEqual(resumed["checkpointed_attempts"], 5)
        self.assertIsNone(resumed["reported_cost_usd"])

    def test_failed_candidates_record_persisting_acceptance_checks(self):
        tasks = load_suite(SUITE)[:1]
        report = run_experiment(tasks, self.root / "experiment", self.root / "scratch", ScriptedRunner(tasks, False), "test-model")
        self.assertTrue(all(row["outcome"] == "test_failed" for row in report["trials"]))
        self.assertTrue(all(row["persisting_acceptance_failures"] for row in report["trials"]))
        self.assertEqual(report["pairs"][0]["matched_tasks"], 1)

    def test_response_provenance_usage_and_budget_validation(self):
        request = {"model": "test", "request_hash": "hash", "max_output_tokens": 128}
        base = {"schema_version": 1, "model": "test", "request_hash": "hash", "status": "ok", "edits": {}}
        self.assertEqual(validate_response(request, base)["cost_usd"], None)
        for update in [{"model": "wrong"}, {"request_hash": "wrong"}, {"status": "provider_error"},
                       {"usage": {"cost_usd": -1}}, {"usage": {"output_tokens": 129}}, {"usage": "bad"}]:
            with self.assertRaises(RunnerError):
                validate_response(request, {**base, **update})

    def test_provider_errors_are_not_task_failures_and_invalid_edits_are(self):
        tasks = load_suite(SUITE)[:1]
        runner = ScriptedRunner(tasks)
        original_call = ScriptedRunner.__call__
        def invalid_edit(request):
            response = original_call(runner, request)
            response["edits"] = {"test_public.py": ""}
            return response
        with patch.object(ScriptedRunner, "__call__", side_effect=invalid_edit):
            report = run_experiment(tasks, self.root / "invalid", self.root / "scratch", runner, "test-model")
        self.assertTrue(all(row["outcome"] == "invalid_candidate" for row in report["trials"]))
        self.assertEqual(report["summary"]["lexical"]["success_rate"], 0)
        def unavailable(request):
            return {"schema_version": 1, "model": request["model"], "request_hash": request["request_hash"], "status": "provider_error"}
        with patch.object(ScriptedRunner, "__call__", side_effect=unavailable):
            report = run_experiment(tasks, self.root / "unavailable", self.root / "scratch", runner, "test-model")
        self.assertEqual(report["pairs"][0]["matched_tasks"], 0)
        self.assertEqual(report["summary"]["graph"]["scored"], 0)

    def test_command_runner_json_errors_and_timeout(self):
        code = "import json,sys; r=json.load(sys.stdin); print(json.dumps({'schema_version':1,'model':r['model'],'request_hash':r['request_hash'],'status':'ok','edits':{}}))"
        request = {"model": "test", "request_hash": "hash", "max_output_tokens": 128}
        runner = CommandRunner([sys.executable, "-c", code])
        self.assertEqual(validate_response(request, runner(request))["input_tokens"], None)
        # Response classification needs enough time to start Python on loaded
        # Windows machines; only the sleeping candidate tests a short deadline.
        for code, expected, timeout in [("print('not json')", "invalid_response", 5),
                                        ("raise SystemExit(1)", "provider_error", 5),
                                        ("import time; time.sleep(2)", "runner_timeout", 0.2)]:
            with self.assertRaises(RunnerError) as caught:
                CommandRunner([sys.executable, "-c", code], timeout=timeout)(request)
            self.assertEqual(caught.exception.outcome, expected)
        with self.assertRaises(ValueError):
            CommandRunner("python adapter.py")

    def test_prepare_replay_and_packet_mismatch(self):
        tasks = load_suite(SUITE)[:1]
        output = self.root / "experiment"
        export_requests(tasks, output, self.root / "scratch", "test-model")
        responses = {}
        for path in (output / "requests").glob("*.json"):
            packet = json.loads(path.read_text())
            responses[packet["trial_id"]] = ScriptedRunner(tasks)(packet)
        replay = self.root / "responses.json"
        write_json(replay, {"schema_version": 1, "responses": responses})
        report = run_experiment(tasks, output, self.root / "scratch", ReplayRunner(replay), "test-model")
        self.assertEqual(report["summary"]["graph"]["success_rate"], 1)
        packet["request_hash"] = "changed"
        with self.assertRaises(RunnerError):
            validate_response(packet, ReplayRunner(replay)(packet))

    def test_bench_cli_calibration(self):
        script = SUITE.parents[1] / "coding_bench.py"
        result = subprocess.run([sys.executable, str(script), "calibrate"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["passed"])
        adapter = self.root / "adapter with spaces.py"
        adapter.write_text("import json,sys\nr=json.load(sys.stdin)\nprint(json.dumps({'schema_version':1,'model':r['model'],'request_hash':r['request_hash'],'status':'ok','edits':{}}))\n", encoding="utf-8")
        command_file = self.root / "runner.json"
        command_file.write_text(json.dumps([sys.executable, str(adapter)]), encoding="utf-8-sig")
        run = subprocess.run([sys.executable, str(script), "run", "--model", "test-model", "--output", str(self.root / "cli-run"),
                              "--command-file", str(command_file)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report["completed"], 12)
        self.assertTrue(all(row["outcome"] == "test_failed" for row in report["trials"]))
