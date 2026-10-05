"""LLM client.

Each category is sent as its own single-turn request (no shared history, no
system prompt), so answers are independent.

Providers:
    openrouter  OpenAI-compatible chat API at openrouter.ai; key from env or .env
                (OPENROUTER_API_KEY). Stdlib only.
"""

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

# Providers with a working implementation in query_llm().
SUPPORTED_PROVIDERS: set[str] = {"openrouter"}

# Fixed test question from the task spec (JIA_LIU_TASK.md, Task 3).
PROMPT_TEMPLATE = "What are the best brands for {category}? List 10 brands."

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
RETRY_STATUS = {408, 429, 500, 502, 503, 504}


def build_prompt(category_name: str) -> str:
    return PROMPT_TEMPLATE.format(category=category_name)


def _api_key(name: str) -> str:
    if os.environ.get(name):
        return os.environ[name]
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            k, sep, v = line.partition("=")
            if sep and k.strip() == name:
                return v.strip().strip('"').strip("'")
    raise RuntimeError(f"{name} not set (env or .env)")


def _openrouter(prompt: str, model: str, temperature: float, retries: int = 4, timeout: int = 180) -> tuple[str, dict]:
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }).encode()
    headers = {"Authorization": f"Bearer {_api_key('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(OPENROUTER_URL, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
            if "error" in data:
                raise RuntimeError(f"API error: {data['error']}")
            text = data["choices"][0]["message"]["content"] or ""
            if not text.strip():
                raise RuntimeError("empty completion")
            meta = {"served_model": data.get("model"), "provider": data.get("provider"),
                    "usage": data.get("usage"), "finish_reason": data["choices"][0].get("finish_reason")}
            return text, meta
        except urllib.error.HTTPError as e:
            last_err = RuntimeError(f"HTTP {e.code}: {e.read()[:300]!r}")
            if e.code not in RETRY_STATUS:
                raise last_err
        except (urllib.error.URLError, TimeoutError, RuntimeError, KeyError, json.JSONDecodeError) as e:
            last_err = e
        time.sleep(2 ** attempt * 2)
    raise last_err


def query_llm(prompt: str, provider: str, model: str, temperature: float) -> tuple[str, dict]:
    """Send one independent single-turn prompt; return (raw text answer, response metadata)."""
    if provider == "openrouter":
        return _openrouter(prompt, model, temperature)
    raise NotImplementedError(f"Provider '{provider}' is not configured.")
