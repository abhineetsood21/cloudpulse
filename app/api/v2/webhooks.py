"""
v2 Webhooks API — External System Integration

Allows users to register webhook endpoints that receive real-time
notifications when events occur in CloudPulse (cost syncs, anomalies,
budget alerts, integration status changes).

Events:
    sync.completed      — A provider sync finished successfully
    sync.failed         — A provider sync failed
    anomaly.detected    — A cost anomaly was detected
    budget.exceeded     — A budget threshold was breached
    integration.connected    — A new provider was connected
    integration.disconnected — A provider was disconnected
"""

import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

VALID_EVENTS = [
    "sync.completed",
    "sync.failed",
    "anomaly.detected",
    "budget.exceeded",
    "integration.connected",
    "integration.disconnected",
]

# In-memory store (production would use DB table)
_webhooks: dict[str, dict] = {}


# ── Schemas ───────────────────────────────────────────────────────

class WebhookCreateRequest(BaseModel):
    url: str = Field(..., description="HTTPS endpoint to receive POST events")
    events: list[str] = Field(..., description="Event types to subscribe to")
    secret: Optional[str] = Field(None, description="Shared secret for HMAC signature verification")
    description: Optional[str] = None


class WebhookResponse(BaseModel):
    id: str
    url: str
    events: list[str]
    description: Optional[str]
    active: bool
    created_at: str


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("", response_model=list[WebhookResponse])
async def list_webhooks():
    """List all registered webhooks."""
    return [
        WebhookResponse(
            id=wid,
            url=w["url"],
            events=w["events"],
            description=w.get("description"),
            active=w.get("active", True),
            created_at=w["created_at"],
        )
        for wid, w in _webhooks.items()
    ]


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(payload: WebhookCreateRequest):
    """Register a new webhook endpoint."""
    # Validate events
    invalid = [e for e in payload.events if e not in VALID_EVENTS]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid events: {invalid}. Valid: {VALID_EVENTS}",
        )

    webhook_id = str(uuid.uuid4())
    _webhooks[webhook_id] = {
        "url": payload.url,
        "events": payload.events,
        "secret": payload.secret,
        "description": payload.description,
        "active": True,
        "created_at": datetime.utcnow().isoformat(),
    }

    return WebhookResponse(
        id=webhook_id,
        url=payload.url,
        events=payload.events,
        description=payload.description,
        active=True,
        created_at=_webhooks[webhook_id]["created_at"],
    )


@router.get("/events")
async def list_available_events():
    """List all available webhook event types."""
    return {"events": VALID_EVENTS}


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: str):
    """Remove a webhook registration."""
    if webhook_id not in _webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")
    del _webhooks[webhook_id]
    return {"message": "Webhook deleted"}


# ── Dispatcher (called by other services) ─────────────────────────

async def dispatch_event(event_type: str, payload: dict):
    """
    Fire an event to all matching webhooks.

    Called internally by other modules, e.g.:
        from app.api.v2.webhooks import dispatch_event
        await dispatch_event("sync.completed", {"integration_id": "...", "rows": 500})
    """
    for wid, webhook in _webhooks.items():
        if not webhook.get("active", True):
            continue
        if event_type not in webhook["events"]:
            continue

        body = json.dumps({
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload,
        })

        headers = {"Content-Type": "application/json"}
        if webhook.get("secret"):
            sig = hmac.new(
                webhook["secret"].encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-CloudPulse-Signature"] = f"sha256={sig}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(webhook["url"], content=body, headers=headers)
                logger.info(f"Webhook {wid} -> {webhook['url']} [{resp.status_code}]")
        except Exception as e:
            logger.warning(f"Webhook {wid} delivery failed: {e}")
