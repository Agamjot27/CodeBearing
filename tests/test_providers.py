import io
import json
import urllib.error
import unittest
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import test_core
from test_experiments import SUITE
from codebearing.coding import load_suite
from codebearing.experiments import RunnerError, run_experiment, validate_response
from codebearing.providers import ENDPOINT, MAX_RESPONSE_BYTES, OpenRouterRunner


class Transport:
    def __init__(self, data=None, error=None, raw=None):
        self.data, self.error, self.raw = data, error, raw
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if self.error:
            raise self.error
        return io.BytesIO(self.raw if self.raw is not None else json.dumps(self.data).encode())


def answer(**changes):
    return {"id": "generation-test", "model": "test/model", "provider": "test-provider",
            "choices": [{"finish_reason": "stop", "message": {"content": '{"edits":{}}'}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 10, "cost": 0.02}, **changes}


def packet():
    return {"model": "test/model", "request_hash": "test-hash", "temperature": 0,
            "prompt": "Return JSON edits using this evidence.", "max_output_tokens": 128}


class ProviderTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    def test_payload_settings_usage_and_identity_exclude_key(self):
        transport = Transport(answer())
        runner = OpenRouterRunner(api_key="secret-sentinel", provider="test-provider", opener=transport)
        response = runner(packet())
        self.assertEqual(response["status"], "ok")
        self.assertEqual(validate_response(packet(), response)["cost_usd"], 0.02)
        request, timeout = transport.calls[0]
        self.assertEqual(request.full_url, ENDPOINT)
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "test/model")
        self.assertEqual(payload["temperature"], 0)
        self.assertEqual(payload["max_tokens"], 128)
        self.assertEqual(payload["provider"], {"allow_fallbacks": False, "require_parameters": True, "only": ["test-provider"]})
        self.assertEqual(payload["messages"][0]["content"], packet()["prompt"])
        self.assertEqual(timeout, 60)
        self.assertNotIn("secret-sentinel", json.dumps(response) + json.dumps(runner.settings) + runner.identity)

    def test_quota_http_embedded_errors_and_no_retry(self):
        for code, status in [(429, "rate_limited"), (401, "provider_error"), (503, "provider_error")]:
            transport = Transport(error=urllib.error.HTTPError(ENDPOINT, code, "secret-sentinel", {}, io.BytesIO(b"private logs")))
            response = OpenRouterRunner(api_key="key", opener=transport)(packet())
            self.assertEqual(response["status"], status)
            self.assertEqual(len(transport.calls), 1)
            self.assertNotIn("secret-sentinel", json.dumps(response))
            self.assertNotIn("private logs", json.dumps(response))
        response = OpenRouterRunner(api_key="key", opener=Transport({"error": {"code": 429, "message": "private"}}))(packet())
        self.assertEqual(response["status"], "rate_limited")

    def test_mismatch_incomplete_malformed_and_oversize_responses(self):
        for data, status in [(answer(model="different/model"), "model_mismatch"),
                             (answer(choices=[{"finish_reason": "length", "message": {"content": '{"edits":{}}'}}]), "invalid_response"),
                             (answer(choices=[{"finish_reason": "stop", "message": {"content": '```json\n{}\n```'}}]), "invalid_response"),
                             (answer(choices=[]), "invalid_response"), ([], "invalid_response")]:
            response = OpenRouterRunner(api_key="key", opener=Transport(data))(packet())
            self.assertEqual(response["status"], status)
            with self.assertRaises(RunnerError):
                validate_response(packet(), response)
        for raw in [b"not json", b"x" * (MAX_RESPONSE_BYTES + 1)]:
            response = OpenRouterRunner(api_key="key", opener=Transport(raw=raw))(packet())
            self.assertEqual(response["status"], "invalid_response")

    def test_missing_key_is_local_and_transport_failure_is_unscored(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "OPENROUTER_API_KEY"):
                OpenRouterRunner()
        runner = OpenRouterRunner(api_key="key", opener=Transport(error=urllib.error.URLError("private")))
        response = runner(packet())
        self.assertEqual(response["status"], "provider_error")
        self.assertNotIn("private", json.dumps(response))

    def test_paid_unusable_response_keeps_usage_provenance_and_cost(self):
        tasks = load_suite(SUITE)[:1]
        transport = Transport(answer(model="different/model"))
        runner = OpenRouterRunner(api_key="secret-sentinel", opener=transport)
        output = self.root / "paid-failure"
        report = run_experiment(tasks, output, self.root / "scratch", runner, "test/model", conditions=("graph",))
        row = report["trials"][0]
        self.assertEqual(row["outcome"], "model_mismatch")
        self.assertEqual(row["usage"]["cost_usd"], 0.02)
        self.assertEqual(report["reported_cost_usd"], 0.02)
        self.assertEqual(report["summary"]["graph"]["scored"], 0)
        self.assertEqual(row["provider_metadata"]["model"], "different/model")
        self.assertNotIn("secret-sentinel", (output / "runner.json").read_text() + (output / "report.json").read_text())
        transport.data = answer(model="different/model", id="generation-second")
        resumed = run_experiment(tasks, output, self.root / "scratch", runner, "test/model", conditions=("graph",))
        attempts = resumed["trials"][0]["attempts"]
        self.assertEqual(attempts[0]["provider_metadata"]["id"], "generation-test")
        self.assertEqual(attempts[1]["provider_metadata"]["id"], "generation-second")
        self.assertEqual(resumed["reported_cost_usd"], 0.04)

    def test_quota_stops_live_adapter_dispatch(self):
        transport = Transport({"error": {"code": 429}})
        report = run_experiment(load_suite(SUITE)[:1], self.root / "quota", self.root / "scratch",
                                OpenRouterRunner(api_key="key", opener=transport), "test/model")
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(report["completed"], 1)
        self.assertEqual(report["trials"][0]["outcome"], "rate_limited")

    def test_cli_preflight_is_local_and_missing_key_is_actionable(self):
        script = Path(__file__).resolve().parents[1] / "evals" / "coding_bench.py"
        env = {**os.environ, "OPENROUTER_API_KEY": "secret-sentinel"}
        result = subprocess.run([sys.executable, str(script), "check-provider", "--model", "test/model"],
                                capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["network_calls"], 0)
        self.assertEqual(report["status"], "locally_configured")
        self.assertNotIn("secret-sentinel", result.stdout + result.stderr)
        env["OPENROUTER_API_KEY"] = ""
        failed = subprocess.run([sys.executable, str(script), "check-provider", "--model", "test/model"],
                                capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(failed.returncode, 2)
        self.assertIn("OPENROUTER_API_KEY", failed.stderr)
