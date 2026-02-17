#!/usr/bin/env bash
# CloudPulse API — curl examples
# Usage: source examples/curl_examples.sh  (or run individual commands)

BASE="http://localhost:8000"
V2="$BASE/api/v2"

# ── Authentication ────────────────────────────────────────────────
# Register and log in to get a JWT token
echo "=== Register ==="
curl -s -X POST "$BASE/api/v1/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{"email": "demo@cloudpulse.io", "password": "demo1234"}' | python3 -m json.tool

echo "=== Login ==="
TOKEN=$(curl -s -X POST "$BASE/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email": "demo@cloudpulse.io", "password": "demo1234"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
echo "Token: ${TOKEN:0:20}..."

AUTH="-H 'Authorization: Bearer $TOKEN'"

# ── Integration Catalog ───────────────────────────────────────────
echo "=== Provider Catalog ==="
curl -s "$V2/integrations/catalog" | python3 -m json.tool

# ── Connect a Provider ────────────────────────────────────────────
echo "=== Connect Datadog ==="
curl -s -X POST "$V2/integrations/connect" \
  -H 'Content-Type: application/json' \
  -d '{"provider": "datadog", "credentials": {"api_key": "your-key", "app_key": "your-app-key", "site": "datadoghq.com"}}' \
  | python3 -m json.tool

# ── List Connected Integrations ───────────────────────────────────
echo "=== Active Integrations ==="
curl -s "$V2/integrations" | python3 -m json.tool

# ── Webhooks ──────────────────────────────────────────────────────
echo "=== Register Webhook ==="
curl -s -X POST "$V2/webhooks" \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://your-endpoint.com/cloudpulse", "events": ["sync.completed", "anomaly.detected"], "secret": "your-hmac-secret"}' \
  | python3 -m json.tool

echo "=== List Webhooks ==="
curl -s "$V2/webhooks" | python3 -m json.tool

echo "=== Available Events ==="
curl -s "$V2/webhooks/events" | python3 -m json.tool

# ── Cost Queries ──────────────────────────────────────────────────
echo "=== Query Costs ==="
curl -s -X POST "$V2/query" \
  -H 'Content-Type: application/json' \
  -d '{"granularity": "daily", "limit": 10}' \
  | python3 -m json.tool

# ── API Tokens (for machine-to-machine) ───────────────────────────
echo "=== Create API Token ==="
curl -s -X POST "$V2/api_tokens" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "CI Pipeline", "scopes": "read"}' \
  | python3 -m json.tool
