from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    balance = models.IntegerField(default=0)
    credit_limit = models.PositiveIntegerField(default=0)
    
    def can_spend(self, amount):
        return (self.balance - amount) >= -self.credit_limit    
    @property
    def balance_from_txns(self):
        credited = Transaction.objects.filter(receiver=self).aggregate(t=models.Sum('amount'))['t'] or 0
        debited = Transaction.objects.filter(sender=self).aggregate(t=models.Sum('amount'))['t'] or 0
        return credited - debited

class Transaction(models.Model):
    sender = models.ForeignKey(User, on_delete=models.PROTECT, related_name="sent_transactions")
    receiver = models.ForeignKey(User, on_delete=models.PROTECT, related_name="received_transactions")
    amount = models.IntegerField()
    description = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.amount})"
