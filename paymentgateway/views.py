
import json
import hashlib
from functools import wraps
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.db import transaction as db_transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from myapp.models import Transaction
from .models import Merchant, PaymentIntent
from .webhooks import send_webhook
from myapp.views import rate_limit, LIMIT, WINDOW, User
#  are already imported/defined in your existing views.py)


def merchant_auth(view_func):
    """Authenticates a merchant via `Authorization: Bearer sk_...`."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        raw_secret = auth[len("Bearer "):].strip()
        secret_hash = hashlib.sha256(raw_secret.encode()).hexdigest()
        merchant = Merchant.objects.filter(secret_key_hash=secret_hash, is_active=True).first()
        if not merchant:
            return JsonResponse({"error": "Invalid API key"}, status=401)
        request.merchant = merchant
        return view_func(request, *args, **kwargs)
    return _wrapped


def intent_to_dict(request, intent):
    return {
        "id": intent.id,
        "status": intent.status,
        "amount": intent.amount,
        "order_reference": intent.order_reference,
        "checkout_url": request.build_absolute_uri(f"/pg/checkout/{intent.id}/"),
        "created_at": intent.created_at.isoformat(),
        "expires_at": intent.expires_at.isoformat(),
    }


@csrf_exempt
@require_POST
@merchant_auth
@rate_limit(limit=LIMIT, window=WINDOW, prefix="rl:create_intent")
def create_payment_intent(request):
    """
    Merchant-facing: POST /api/v1/payment_intents/
    Headers: Authorization: Bearer sk_..., Idempotency-Key: <unique-per-attempt>
    Body (JSON): {"amount": 500, "order_reference": "ORD-123", "redirect_url": "https://merchant.example/thanks"}
    """
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    idempotency_key = request.headers.get("Idempotency-Key") or body.get("idempotency_key")
    amount = body.get("amount")
    order_reference = str(body.get("order_reference", ""))[:100]
    redirect_url = body.get("redirect_url", "")

    if not idempotency_key:
        return JsonResponse({"error": "Idempotency-Key header is required"}, status=400)
    if not isinstance(amount, int) or amount <= 0:
        return JsonResponse({"error": "amount must be a positive integer"}, status=400)

    # Idempotent replay: same merchant + same key -> return the original intent
    existing = PaymentIntent.objects.filter(
        merchant=request.merchant, idempotency_key=idempotency_key
    ).first()
    if existing:
        return JsonResponse(intent_to_dict(request, existing), status=200)

    intent = PaymentIntent.objects.create(
        merchant=request.merchant,
        amount=amount,
        order_reference=order_reference,
        idempotency_key=idempotency_key,
        redirect_url=redirect_url,
    )
    return JsonResponse(intent_to_dict(request, intent), status=201)


@merchant_auth
def retrieve_payment_intent(request, intent_id):
    """Merchant-facing: GET /api/v1/payment_intents/<id>/"""
    intent = get_object_or_404(PaymentIntent, id=intent_id, merchant=request.merchant)
    if intent.is_expired():
        intent.status = "expired"
        intent.save(update_fields=["status"])
    return JsonResponse(intent_to_dict(request, intent))


@login_required
def checkout(request, intent_id):
    """
    Buyer-facing hosted checkout page. The merchant redirects their
    customer here; the customer logs into *your* platform and approves.
    The receiver is always the merchant's own account -- never something
    the merchant (or anyone else) can override per-request.
    """
    intent = get_object_or_404(PaymentIntent, id=intent_id)

    if intent.is_expired():
        intent.status = "expired"
        intent.save(update_fields=["status"])

    if intent.status != "requires_payment":
        return render(request, "checkout.html", {"intent": intent, "final": True})

    if request.method == "POST":
        merchant_user = intent.merchant.user
        if request.user == merchant_user:
            messages.error(request, "You cannot pay yourself.")
            return render(request, "checkout.html", {"intent": intent})

        with db_transaction.atomic():
            # Re-fetch and lock inside the transaction to guard against
            # double-submission and concurrent payment of the same intent.
            locked_intent = PaymentIntent.objects.select_for_update().get(id=intent.id)
            if locked_intent.status != "requires_payment":
                return redirect("checkout", intent_id=intent.id)

            # Lock both accounts in a consistent order (by pk) to avoid deadlocks.
            first_pk, second_pk = sorted([request.user.pk, merchant_user.pk])
            locked_first = User.objects.select_for_update().get(pk=first_pk)
            locked_second = User.objects.select_for_update().get(pk=second_pk)
            buyer = locked_first if locked_first.pk == request.user.pk else locked_second
            receiver = locked_first if locked_first.pk == merchant_user.pk else locked_second

            if not buyer.can_spend(locked_intent.amount):
                messages.error(request, "Credit limit exceeded")
                return render(request, "checkout.html", {"intent": intent})

            buyer.balance -= locked_intent.amount
            receiver.balance += locked_intent.amount
            buyer.save(update_fields=["balance"])
            receiver.save(update_fields=["balance"])

            txn = Transaction.objects.create(
                sender=buyer,
                receiver=receiver,
                amount=locked_intent.amount,
                description=f"Payment {locked_intent.order_reference or locked_intent.id}"[:50],
            )
            locked_intent.status = "succeeded"
            locked_intent.buyer = request.user
            locked_intent.transaction = txn
            locked_intent.save(update_fields=["status", "buyer", "transaction"])

        send_webhook(intent.merchant, "payment_intent.succeeded", intent_to_dict(request, locked_intent))

        if locked_intent.redirect_url:
            return redirect(f"{locked_intent.redirect_url}?intent_id={locked_intent.id}&status=succeeded")
        return render(request, "checkout.html", {"intent": locked_intent, "final": True})

    return render(request, "checkout.html", {"intent": intent})