#!/usr/bin/env python3
"""
Stdio-to-Streamable-HTTP MCP Bridge for LegalZoom (https://www.legalzoom.com/mcp).

Why this bridge is needed:
LegalZoom's MCP endpoint is a stateless Streamable HTTP JSON-RPC service behind CloudFront/Envoy.
However, when an MCP client opens a standalone GET SSE stream (`Accept: text/event-stream`),
instead of returning HTTP 405 Method Not Allowed (as required by the MCP 2025-03-26 spec for
servers that do not emit server-initiated JSON-RPC messages over GET), LegalZoom holds the GET
connection open and only emits bare `event: ping` frames before timing out. This causes the Go
MCP SDK client to fail with:
  `standalone SSE stream: exceeded 5 retries without progress (session ID: )`

By bridging Stdio <-> HTTP POST, all JSON-RPC requests/notifications are forwarded directly to
`https://www.legalzoom.com/mcp` without opening the broken standalone GET SSE stream.
"""

import json
import sys
import threading
import urllib.error
import urllib.request

MCP_ENDPOINT = "https://www.legalzoom.com/mcp"
write_lock = threading.Lock()
session_id = None


def send_stdout(payload_str: str) -> None:
    with write_lock:
        sys.stdout.write(payload_str.strip() + "\n")
        sys.stdout.flush()


def forward_message(raw_line: str) -> None:
    global session_id
    line = raw_line.strip()
    if not line:
        return

    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return

    req_id = msg.get("id") if isinstance(msg, dict) else None

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "Antigravity-LegalZoom-MCP-Bridge/1.0",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id

    req = urllib.request.Request(
        MCP_ENDPOINT,
        data=line.encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            new_sid = resp.headers.get("Mcp-Session-Id")
            if new_sid:
                session_id = new_sid

            status = resp.status
            body = resp.read().decode("utf-8", errors="replace").strip()
            if status == 202 or not body:
                return

            content_type = resp.headers.get("Content-Type", "")
            if "text/event-stream" in content_type:
                for sse_line in body.splitlines():
                    if sse_line.startswith("data:"):
                        data_part = sse_line[5:].strip()
                        if data_part:
                            send_stdout(data_part)
            else:
                # Compact to a single line for MCP stdio framing
                try:
                    parsed = json.loads(body)
                    send_stdout(json.dumps(parsed, separators=(",", ":")))
                except json.JSONDecodeError:
                    send_stdout(body.replace("\n", " "))
    except Exception as exc:
        if req_id is not None:
            err_resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32603,
                    "message": f"LegalZoom MCP HTTP bridge error: {exc}",
                },
            }
            send_stdout(json.dumps(err_resp, separators=(",", ":")))


def main() -> None:
    for raw_line in sys.stdin:
        forward_message(raw_line)


if __name__ == "__main__":
    main()
