"""Minimal BFL API client: submit a task, poll it, download the result.

The key comes from API_KEY in the repo's .env (or BFL_API_KEY in the
environment). It is sent only to api.bfl.ai and never printed.
"""

import base64
import json
import os
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.bfl.ai/v1"


def api_key():
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in open(path):
            name, _, value = line.strip().partition("=")
            if name in ("API_KEY", "BFL_API_KEY") and value:
                return value.strip().strip("'\"")
    key = os.environ.get("BFL_API_KEY")
    if not key:
        raise SystemExit("No API_KEY in .env and no BFL_API_KEY in env")
    return key


def _request(url, body=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"x-key": api_key(), "Content-Type": "application/json",
                 "accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        raise SystemExit(f"{err.code} from {url}: {err.read().decode()[:2000]}")


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def run(endpoint, body, poll_every=3.0):
    """Submit to /v1/<endpoint>, wait until Ready, return the result dict."""
    task = _request(f"{API}/{endpoint}", body)
    print(f"submitted {endpoint} id={task['id']} cost={task.get('cost')}")
    while True:
        time.sleep(poll_every)
        status = _request(task["polling_url"])
        state = status.get("status")
        if state == "Ready":
            return status["result"]
        if state in ("Error", "Failed", "Request Moderated", "Content Moderated"):
            raise SystemExit(f"{endpoint} {state}: {json.dumps(status)[:2000]}")
        print(f"  {state} {status.get('progress') or ''}", flush=True)


def download(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    urllib.request.urlretrieve(url, path)
    print("saved", os.path.relpath(path, ROOT))
    return path
