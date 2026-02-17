#!/usr/bin/env python3
"""
Example: Webhook receiver for CloudPulse events.

This is a minimal Flask/FastAPI-compatible server that receives
CloudPulse webhook events. You can use this as a starting point
to integrate CloudPulse events into Slack, PagerDuty, Jira, etc.

Usage:
    pip install flask
    python examples/webhook_receiver.py

    # Then register the webhook in CloudPulse:
    curl -X POST http://localhost:8000/api/v2/webhooks \\
      -H 'Content-Type: application/json' \\
      -d '{"url": "http://your-server:5050/webhook", "events": ["sync.completed", "anomaly.detected"], "secret": "my-secret"}'
"""

import hashlib
import hmac
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

WEBHOOK_SECRET = "my-secret"  # Must match the secret you registered


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # Verify HMAC signature (if secret is set)
        sig_header = self.headers.get("X-CloudPulse-Signature", "")
        if WEBHOOK_SECRET and sig_header:
            expected = "sha256=" + hmac.new(
                WEBHOOK_SECRET.encode(), body, hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(sig_header, expected):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Invalid signature")
                return

        event = json.loads(body)
        print(f"\n{'='*60}")
        print(f"Event:     {event['event']}")
        print(f"Timestamp: {event['timestamp']}")
        print(f"Data:      {json.dumps(event['data'], indent=2)}")
        print(f"{'='*60}")

        # TODO: Forward to Slack, PagerDuty, Jira, etc.

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass  # Suppress default logging


if __name__ == "__main__":
    port = 5050
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    print(f"Webhook receiver listening on http://0.0.0.0:{port}/webhook")
    print("Register this URL in CloudPulse:")
    print(f'  curl -X POST http://localhost:8000/api/v2/webhooks -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"url": "http://host.docker.internal:{port}", "events": ["sync.completed", "anomaly.detected"], "secret": "{WEBHOOK_SECRET}"}}\'')
    server.serve_forever()
