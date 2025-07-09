# payments/models.py
from django.db import models
from django.conf import settings

class Subscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    stripe_customer_id = models.CharField(max_length=255)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    current_period_end = models.DateTimeField(blank=True, null=True)
    max_plans = models.IntegerField(default=10)

    def __str__(self):
        return f"Subscription for {self.user.email}"
