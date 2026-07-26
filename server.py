"""
AgentCore-compatible HTTP server.

AWS AgentCore invokes the container by sending POST requests to /invocations.
A GET to /health is used for the container health check.

The request body (JSON) must contain either a "prompt" or "message" key.
The response body is {"response": "<agent output>"}.
"""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from agent import create_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# Initialise the agent once at startup so it is reused across requests.
_agent = create_agent()

DEFAULT_PROMPT = "What are the five most important AI highlights right now?"


class AgentCoreHandler(BaseHTTPRequestHandler):
    """HTTP request handler for AWS AgentCore."""

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {"status": "healthy"})
        else:
            self._send_json(404, {"error": "Not found"})

    # ------------------------------------------------------------------
    # Agent invocation
    # ------------------------------------------------------------------

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in ("/", "/invocations"):
            self._send_json(404, {"error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length) if content_length else b"{}"
            body = json.loads(raw_body) if raw_body else {}
        except json.JSONDecodeError as exc:
            self._send_json(400, {"error": f"Invalid JSON: {exc}"})
            return

        prompt: str = body.get("prompt", body.get("message", DEFAULT_PROMPT))
        logger.info("Received prompt: %s", prompt[:120])

        try:
            result = _agent(prompt)
            response_text = str(result)
            self._send_json(200, {"response": response_text})
        except Exception as exc:  # noqa: BLE001
            logger.exception("Agent invocation failed")
            self._send_json(500, {"error": str(exc)})

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:  # silence default access log
        logger.info(fmt, *args)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), AgentCoreHandler)
    logger.info("AgentCore server listening on port %d", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped.")
