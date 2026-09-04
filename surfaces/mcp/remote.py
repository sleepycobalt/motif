"""
Remote mode: forward tool calls to a hosted Motif service instead of running
the engine in-process. Selected by MOTIF_REMOTE_URL. The hosted service is
not live yet; this client defines the contract and fails loudly until it is.

Contract (JSON over HTTPS, bearer token in MOTIF_REMOTE_TOKEN):
    POST {url}/v1/synthesize   {"transcripts": [{"name", "text"}], "question", "condition", "max_iterations"}
    POST {url}/v1/critique     {"insights" | "document", "run_id" | "transcripts", "question"}
    POST {url}/v1/receipts     {"turn_ids", "run_id"}
    GET  {url}/v1/runs/{id}
Nothing about the transcripts is logged on this side: no bodies, no names,
only the run id and timings.
"""

import json
import os
import urllib.error
import urllib.request


class RemoteUnavailable(RuntimeError):
    pass


def _call(method: str, path: str, payload: dict | None = None, timeout: float = 1800) -> dict:
    url = os.environ["MOTIF_REMOTE_URL"].rstrip("/") + path
    token = os.environ.get("MOTIF_REMOTE_TOKEN", "")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {token}"} if token else
                                 {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RemoteUnavailable(f"hosted Motif service returned {e.code} for {path}") from None
    except (urllib.error.URLError, OSError) as e:
        raise RemoteUnavailable(f"hosted Motif service unreachable at {url}: {e}") from None
    if not isinstance(body, dict) or body.get("error"):
        raise RemoteUnavailable(f"hosted Motif service error: {body.get('error') if isinstance(body, dict) else body}")
    return body


def synthesize(transcripts: list[dict], **kw) -> dict:
    return _call("POST", "/v1/synthesize", {"transcripts": transcripts, **kw})


def critique(**kw) -> dict:
    return _call("POST", "/v1/critique", kw)


def receipts(**kw) -> dict:
    return _call("POST", "/v1/receipts", kw)


def get_run(run_id: str) -> dict:
    return _call("GET", f"/v1/runs/{run_id}")
