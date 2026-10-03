import json
import unittest

import test_core
from test_experiments import SUITE, ScriptedRunner
from diffcontext.coding import load_suite, trial_workspace
from diffcontext.experiments import HYBRID_CONDITIONS, export_requests, make_request, run_experiment, summarize_results


class HybridExperimentTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    def test_matched_packets_preserve_sources_budgets_and_memory_controls(self):
        for task in load_suite(SUITE):
            packets = {}
            for condition in HYBRID_CONDITIONS:
                with trial_workspace(task, self.root / "scratch") as root:
                    packet, diagnostics = make_request(task, root, condition, "test-model")
                    packets[condition] = packet
                    self.assertLessEqual(diagnostics["prompt_estimated_tokens"], 4000)
                    self.assertNotIn("checks.py", packet["prompt"])
                    if condition.startswith("hybrid"):
                        self.assertEqual(diagnostics["retrieval_policy"], "hybrid")
                    if condition == "hybrid_memory":
                        self.assertTrue(diagnostics["included_lessons"])
                        self.assertIn(task.lesson, packet["prompt"])
                    elif condition == "hybrid_stale_memory":
                        self.assertFalse(diagnostics["included_lessons"])
                        self.assertNotIn(task.lesson, packet["prompt"])
                        self.assertTrue(diagnostics["excluded_lessons"][0]["stale"])
            for left, right in [("graph", "hybrid"), ("memory", "hybrid_memory"), ("stale_memory", "hybrid_stale_memory")]:
                self.assertEqual(packets[left]["source_hashes"], packets[right]["source_hashes"])
                self.assertEqual(packets[left]["max_output_tokens"], packets[right]["max_output_tokens"])
                self.assertEqual(packets[left]["max_input_estimated_tokens"], packets[right]["max_input_estimated_tokens"])

    def test_hybrid_resume_and_condition_change_rejection(self):
        tasks = load_suite(SUITE)[:1]
        output = self.root / "experiment"
        runner = ScriptedRunner(tasks)
        report = run_experiment(tasks, output, self.root / "scratch", runner, "test", conditions=HYBRID_CONDITIONS)
        self.assertEqual(report["planned"], 7)
        self.assertEqual(runner.calls, 7)
        self.assertTrue(all(row["outcome"] == "passed" for row in report["trials"]))
        self.assertEqual(len(report["pairs"]), 8)
        resumed = run_experiment(tasks, output, self.root / "scratch", runner, "test", conditions=HYBRID_CONDITIONS)
        self.assertEqual(resumed["runner_invocations_this_execution"], 0)
        with self.assertRaisesRegex(ValueError, "configuration"):
            run_experiment(tasks, output, self.root / "scratch", runner, "test")
        manifest = json.loads((output / "manifest.json").read_text())
        self.assertEqual(manifest["conditions"], list(HYBRID_CONDITIONS))
        self.assertIn("processes.py", manifest["execution_hashes"])

    def test_pairing_excludes_provider_errors_and_reports_regressions(self):
        rows = [{"task": "a", "condition": "graph", "outcome": "passed"},
                {"task": "a", "condition": "hybrid", "outcome": "test_failed"},
                {"task": "b", "condition": "graph", "outcome": "passed"},
                {"task": "b", "condition": "hybrid", "outcome": "rate_limited"}]
        report = summarize_results(rows, 4, "test", 4, ("graph", "hybrid"))
        self.assertEqual(report["pairs"][0]["matched_tasks"], 1)
        self.assertEqual(report["pairs"][0]["left_only_passed"], 1)
        self.assertEqual(report["summary"]["hybrid"]["unscored_errors"], 1)

    def test_condition_validation_happens_before_output_write(self):
        tasks = load_suite(SUITE)[:1]
        output = self.root / "invalid"
        for values in [(), ("hybrid", "hybrid"), ("unknown",)]:
            with self.assertRaises(ValueError):
                export_requests(tasks, output, self.root / "scratch", "test", conditions=values)
        self.assertFalse(output.exists())
