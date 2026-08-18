# ── New file: <app>/management/commands/create_merchant.py ────────────
# Usage: python manage.py create_merchant --username 9999999999 --name "Acme Store"
#
# Prints the secret key ONCE. Only the hash is stored -- if it's lost,
# the merchant must be issued a new one (add a `rotate_secret` command
# the same way if you need that later).

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from paymentgateway.models import Merchant  # TODO: replace `yourapp` with your actual app label

User = get_user_model()


class Command(BaseCommand):
    help = "Create a Merchant account and print its API key + secret (shown once)."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True, help="Existing user's username to attach the merchant to")
        parser.add_argument("--name", required=True, help="Merchant display name")
        parser.add_argument("--webhook-url", default="", help="Optional webhook URL")

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist:
            raise CommandError(f"No user with username {options['username']}")

        if hasattr(user, "merchant"):
            raise CommandError("This user already has a merchant account.")

        raw_secret, secret_hash = Merchant.generate_secret()

        with transaction.atomic():
            merchant = Merchant.objects.create(
                user=user,
                name=options["name"],
                secret_key_hash=secret_hash,
                webhook_url=options["webhook_url"],
            )

        self.stdout.write(self.style.SUCCESS(f"Merchant '{merchant.name}' created."))
        self.stdout.write(f"  Publishable key: {merchant.api_key}")
        self.stdout.write(f"  Secret key:      {raw_secret}   (save this now -- it will not be shown again)")
        self.stdout.write(f"  Webhook secret:  {merchant.webhook_secret}")