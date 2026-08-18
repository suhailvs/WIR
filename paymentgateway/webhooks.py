# ── New file: webhooks.py ────────────────────────────────────────────
# Notifies a merchant's server when a payment intent succeeds.
# Merchants verify authenticity by recomputing the HMAC with their
# webhook_secret and comparing to the X-Signature header (see the
# verification snippet in README.md).

import hmac
import hashlib
import json
import time
import logging

import requests

logger = logging.getLogger(__name__)


def send_webhook(merchant, event_type, data, timeout=5):
    """
    Fire-and-forget HTTP POST to the merchant's webhook_url.

    Minimal version: no retry queue. For production, push this onto
    a task queue (Celery/RQ) with exponential backoff instead of
    calling it inline from the request/response cycle.
    """
    if not merchant.webhook_url:
        return

    payload = {
        "type": event_type,
        "data": data,
        "timestamp": int(time.time()),
    }
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    signature = hmac.new(
        merchant.webhook_secret.encode(), body.encode(), hashlib.sha256
    ).hexdigest()

    try:
        requests.post(
            merchant.webhook_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Signature": signature,
                "X-Timestamp": str(payload["timestamp"]),
            },
            timeout=timeout,
        )
    except requests.RequestException:
        logger.warning("Webhook delivery failed for merchant %s", merchant.id, exc_info=True)