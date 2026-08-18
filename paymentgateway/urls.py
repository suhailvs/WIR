# ── Add to urls.py (inside urlpatterns) ────────────────────────────────
from django.urls import path
from . import views

urlpatterns = [
    path("checkout/<int:intent_id>/", views.checkout, name="checkout"),
    path("api/v1/payment_intents/", views.create_payment_intent, name="create_payment_intent"),
    path("api/v1/payment_intents/<int:intent_id>/", views.retrieve_payment_intent, name="retrieve_payment_intent"),
]