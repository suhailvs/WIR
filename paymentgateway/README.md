# Minimal payment gateway — wiring instructions

This adds a Stripe-style "Payment Intent" flow on top of your existing
WIR app. Nothing in your existing `models.py` / `views.py` is
changed — these are additions.

## 1. Files to merge

| File | Action |
|---|---|
| `01_models_additions.py` | Append contents to `models.py` |
| `02_webhooks.py` | Save as `webhooks.py` (new file, same app dir) |
| `03_views_additions.py` | Append to `views.py`; add the extra imports noted at the top of the file |
| `04_urls_additions.py` | Merge into `urls.py` |
| `05_admin_additions.py` | Merge into (or create) `admin.py` |
| `templates/checkout.html` | Save into your templates dir |
| `management/commands/create_merchant.py` | Save into `<yourapp>/management/commands/create_merchant.py` (create the `management/` and `management/commands/` dirs with empty `__init__.py` files if they don't exist), and replace `yourapp` in the import with your real app label |

Add `requests` to `requirements.txt` if it isn't already a dependency (used for webhook delivery).

## 2. Migrate

```bash
python manage.py makemigrations
python manage.py migrate
```

## 3. Onboard a merchant

The merchant needs an existing user account first (sign them up like any user), then:

```bash
python manage.py create_merchant --username 8547622462 --name "Acme Store" --webhook-url https://acme.example/webhooks/staccoin/
```

This prints the secret key once — that's what the merchant's server uses to call the API.

## 4. Merchant creates a payment intent

```bash
curl -X POST http://localhost:8000/pg/api/v1/payment_intents/ \
  -H "Authorization: Bearer sk_b53ac2e2e3ee01b8d33795e7d8cc013490900451791cad9c" \
  -H "Idempotency-Key: order-8842-attempt-1" \
  -H "Content-Type: application/json" \
  -d '{"amount": 250, "order_reference": "ORD-8842", "redirect_url": "https://acme.example/thanks"}'
```

Response includes `checkout_url` — redirect the customer there. They log into their WIR account and approve; on success the merchant gets a webhook, and (if `redirect_url` was set) the customer is redirected back with `?intent_id=...&status=succeeded`.

**Always trust the webhook over the redirect** — the redirect can be skipped if the customer closes the tab.

## 5. Verifying webhooks (merchant side, for their reference)

```python
import hmac, hashlib

def verify(body: bytes, signature_header: str, webhook_secret: str) -> bool:
    expected = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```
## 6. if somehow webhook not arraived we can check payment by 
```bash
curl http://localhost:8000/pg/api/v1/payment_intents/1/ \
  -H "Authorization: Bearer sk_b53ac2e2e3ee01b8d33795e7d8cc013490900451791cad9c"
```
## What's deliberately left out of this "minimal" version

- **Webhook retries.** Delivery is fire-and-forget with a 5s timeout. Move `send_webhook` onto Celery/RQ with backoff before handling real volume — a merchant's server being briefly down shouldn't mean they never learn a payment succeeded.
- **Refunds / cancellations.** Only the happy path (create → pay → succeed) and expiry are handled.
- **Merchant self-service dashboard / key rotation.** Onboarding is a management command; add an admin UI or `rotate_secret` command when you need it.
- **Partial captures / multi-currency.** Amounts are plain integers, same unit as your existing `balance` field.

## Note on the existing `home()` transfer view

The `checkout()` view above uses `select_for_update()` to lock both accounts before checking `can_spend()` — this closes a race condition that also exists in your current peer-to-peer `home()` view (two concurrent transfers can both read a stale balance and together exceed the sender's credit limit). Worth applying the same locking pattern there, independent of the gateway work.