"""Explicit OpenRouter integration for one-response coding experiments.

Construction and --help do not call a provider. API keys remain in memory;
exceptions never copy arbitrary HTTP bodies or provider logs into checkpoints.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .experiments import fingerprint

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MAX_RESPONSE_BYTES = 1_000_000


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Credentials belong only to the fixed endpoint, not a redirect target.
        return None


class OpenRouterRunner:
    kind = "openrouter"

    def __init__(self, *, timeout: float = 60, provider: str | None = None,
                 api_key: str | None = None, opener=None):
        if not 1 <= timeout <= 300 or (provider is not None and not provider.strip()):
            raise ValueError("Set HTTP timeout 1–300 seconds and a nonempty optional provider slug.")
        self._key = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY", "")
        if not self._key.strip():
            raise ValueError("Set OPENROUTER_API_KEY locally before running live trials.")
        self.timeout, self.provider = timeout, provider
        self.settings = {"endpoint": ENDPOINT, "timeout": timeout, "provider": provider,
                         "allow_fallbacks": False, "require_parameters": True,
                         "response_format": "json_object", "adapter_version": 1}
        self.identity = fingerprint(self.settings)
        self._opener = opener or urllib.request.build_opener(_NoRedirect())

    def __call__(self, request: dict) -> dict:
        routing = {"allow_fallbacks": False, "require_parameters": True}
        if self.provider:
            routing["only"] = [self.provider]
        payload = {"model": request["model"], "temperature": request["temperature"],
                   "max_tokens": request["max_output_tokens"], "stream": False,
                   "response_format": {"type": "json_object"}, "provider": routing,
                   "messages": [{"role": "user", "content": request["prompt"]}]}
        envelope = {"schema_version": 1, "model": request["model"],
                    "request_hash": request["request_hash"], "status": "provider_error",
                    "usage": None, "provider_metadata": {"adapter": "openrouter", "settings": self.settings}}
        http = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode("utf-8"),
                                     headers={"Authorization": "Bearer " + self._key,
                                              "Content-Type": "application/json"}, method="POST")
        try:
            with self._opener.open(http, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            envelope["status"] = "rate_limited" if exc.code == 429 else "provider_error"
            envelope["provider_metadata"]["http_status"] = exc.code
            exc.close()
            return envelope
        except (OSError, urllib.error.URLError):
            return envelope
        if len(raw) > MAX_RESPONSE_BYTES:
            envelope["status"] = "invalid_response"
            return envelope
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("Expected response object")
        except (ValueError, UnicodeDecodeError):
            envelope["status"] = "invalid_response"
            return envelope
        usage = data.get("usage")
        if isinstance(usage, dict):
            envelope["usage"] = {"input_tokens": usage.get("prompt_tokens"),
                                 "output_tokens": usage.get("completion_tokens"),
                                 "cost_usd": usage.get("cost")}
        # Retain only typed provenance fields, never provider error bodies. Model
        # mismatch must not produce a scored edit under the requested model label.
        for field in ("id", "model", "provider"):
            if isinstance(data.get(field), str):
                envelope["provider_metadata"][field] = data[field][:200]
        if isinstance(data.get("error"), dict):
            envelope["status"] = "rate_limited" if data["error"].get("code") == 429 else "provider_error"
            return envelope
        if data.get("model") != request["model"]:
            envelope["status"] = "model_mismatch"
            return envelope
        try:
            choices = data["choices"]
            if not isinstance(choices, list) or len(choices) != 1:
                raise ValueError("Expected one choice")
            choice = choices[0]
            finish = choice.get("finish_reason")
            envelope["provider_metadata"]["finish_reason"] = finish[:200] if isinstance(finish, str) else None
            if choice.get("finish_reason") != "stop":
                raise ValueError("Incomplete or refused output")
            if choice["message"].get("refusal"):
                raise ValueError("Refused output")
            content = json.loads(choice["message"]["content"])
            edits = content["edits"]
            if not isinstance(edits, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in edits.items()):
                raise ValueError("Expected source edits mapping")
        except (KeyError, TypeError, ValueError, AttributeError):
            envelope["status"] = "invalid_response"
            return envelope
        envelope.update(status="ok", edits=edits)
        return envelope
