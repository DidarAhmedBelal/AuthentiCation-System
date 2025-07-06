# plans/models.py
from django.db import models
from django.conf import settings
from chat.models import Chat

class Plan(models.Model):
    PLAN_TYPE_CHOICES = [
        ('chat', 'Chat'),
        ('text', 'Text'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='plans'
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    plan_type = models.CharField(max_length=10, choices=PLAN_TYPE_CHOICES, default='chat')
    date = models.DateField(blank=True, null=True)
    time = models.TimeField(blank=True, null=True)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    chat = models.OneToOneField(Chat, null=True, blank=True, on_delete=models.SET_NULL, related_name='plan')

    def __str__(self):
        return f"{self.title} ({self.get_plan_type_display()}) on {self.date} at {self.time}"

    def can_user_create_more_plans(self):
        subscription = getattr(self.user, 'subscription', None)
        if subscription and subscription.is_active:
            return self.user.plans.count() < subscription.max_plans
        return self.user.plans.count() < 10
