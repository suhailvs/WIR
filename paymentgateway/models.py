from django.db import models

# ── Append to models.py ──────────────────────────────────────────────
# (keeps your existing User / Transaction as-is; imports below are in
#  addition to what's already at the top of models.py)

import secrets
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from myapp.models import Transaction 
User = get_user_model()
class Merchant(models.Model):
    """
    A merchant is a special account that can create Payment Intents.
    api_key  -> safe to expose client-side (like Stripe's pk_...)
    secret_key -> only ever shown once at creation; we store a hash, never the raw value
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="merchant")
    name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=64, unique=True, editable=False)
    secret_key_hash = models.CharField(max_length=128, editable=False)
    webhook_url = models.URLField(blank=True)
    webhook_secret = models.CharField(max_length=64, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = f"pk_{secrets.token_hex(16)}"
        if not self.webhook_secret:
            self.webhook_secret = secrets.token_hex(32)
        super().save(*args, **kwargs)

    @staticmethod
    def generate_secret():
        """Returns (raw_secret_to_show_once, hash_to_store)."""
        raw = f"sk_{secrets.token_hex(24)}"
        return raw, hashlib.sha256(raw.encode()).hexdigest()

    def check_secret(self, raw_secret: str) -> bool:
        return hashlib.sha256(raw_secret.encode()).hexdigest() == self.secret_key_hash

    def __str__(self):
        return self.name


class PaymentIntent(models.Model):
    STATUS_CHOICES = [
        ("requires_payment", "Requires payment"),
        ("succeeded", "Succeeded"),
        ("expired", "Expired"),
        ("canceled", "Canceled"),
    ]

    merchant = models.ForeignKey(Merchant, on_delete=models.PROTECT, related_name="payment_intents")
    amount = models.PositiveIntegerField()
    order_reference = models.CharField(max_length=100, blank=True)
    idempotency_key = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="requires_payment")

    # who actually paid, and the resulting ledger entry -- both null until paid
    buyer = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="payment_intents")
    transaction = models.OneToOneField(Transaction, null=True, blank=True, on_delete=models.SET_NULL)

    redirect_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["merchant", "idempotency_key"], name="uniq_merchant_idempotency"),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)

    def is_expired(self):
        return self.status == "requires_payment" and timezone.now() > self.expires_at

    def __str__(self):
        return f"Intent#{self.id} {self.amount} ({self.status})"
