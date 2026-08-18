# ── Add to admin.py ─────────────────────────────────────────────────
from django.contrib import admin
from .models import Merchant, PaymentIntent


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "api_key", "is_active", "created_at")
    readonly_fields = ("api_key", "secret_key_hash", "webhook_secret", "created_at")


@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = ("id", "merchant", "amount", "status", "buyer", "created_at", "expires_at")
    list_filter = ("status", "merchant")
    readonly_fields = ("idempotency_key", "created_at", "transaction")