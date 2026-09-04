"""End-to-end: spawn the MCP server over stdio and call the tools that need no API key."""

import asyncio
import json
import sys
from pathlib import Path

import pytest
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"

pytestmark = pytest.mark.skipif(not (PROCESSED / "manifest.json").exists(), reason="sample corpus not processed")


def _params(tmp_path):
    return StdioServerParameters(command=sys.executable, args=["-m", "surfaces.mcp.server"], cwd=str(ROOT),
                                 env={"MOTIF_RUNS_DIR": str(tmp_path / "runs"), "PATH": "/usr/bin:/bin",
                                      "ANTHROPIC_API_KEY": "test-key-not-used"})


def _data(res):
    assert not res.is_error, res.content
    d = res.structured_content or json.loads(res.content[0].text)
    return d.get("result", d)


async def _scenario(tmp_path):
    logs = []

    async def on_log(msg):
        logs.append(msg)

    async with Client(_params(tmp_path), logging_callback=on_log) as client:
        names = sorted(t.name for t in (await client.list_tools()).tools)
        assert names == ["motif_board", "motif_critique", "motif_receipts", "motif_runs_get", "motif_synthesize"]

        # receipts against the sample corpus
        r = _data(await client.call_tool("motif_receipts", {
            "turn_ids": ["michelle:0028", "michelle:0001", "nobody:0001"],
            "transcripts_dir": str(PROCESSED), "transcripts": ["michelle"]}))
        assert [x["found"] for x in r["receipts"]] == [True, True, False]
        assert "metadata" in r["receipts"][0]["text"] and r["missing"] == ["nobody:0001"]
        assert r["receipts"][1]["interviewer"] is True

        # every-id-missing is an error, not an empty success
        res = await client.call_tool("motif_receipts", {"turn_ids": ["nobody:0001"], "transcripts_dir": str(PROCESSED)})
        assert res.is_error and "none of the" in res.content[0].text

        # critique argument validation
        res = await client.call_tool("motif_critique", {"transcripts_dir": str(PROCESSED)})
        assert res.is_error and "exactly one" in res.content[0].text
        res = await client.call_tool("motif_critique", {"insights": [], "transcripts_dir": str(PROCESSED)})
        assert res.is_error and "non-empty" in res.content[0].text

        # runs_get on a missing run
        res = await client.call_tool("motif_runs_get", {"run_id": "does-not-exist"})
        assert res.is_error and "no such run" in res.content[0].text

        res = await client.call_tool("motif_board", {"run_id": "does-not-exist"})
        assert res.is_error and "no such run" in res.content[0].text

        # synthesize argument validation (no API call is made)
        res = await client.call_tool("motif_synthesize", {})
        assert res.is_error and "transcripts_dir" in res.content[0].text
        res = await client.call_tool("motif_synthesize", {"transcripts_dir": str(tmp_path / "nothing")})
        assert res.is_error and "not found" in res.content[0].text


def test_server_roundtrip(tmp_path):
    asyncio.run(_scenario(tmp_path))
