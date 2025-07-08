from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Plan
from chat.models import Chat

@receiver(post_save, sender=Plan)
def create_chat_for_plan(sender, instance, created, **kwargs):
    if created and instance.chat is None:
        chat = Chat.objects.create()
        instance.chat = chat
        instance.save()
