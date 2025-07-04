from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Chat(models.Model):
    participants = models.ManyToManyField(User, related_name="chats")
    created_at = models.DateTimeField(auto_now_add=True)

    topic_summary = models.CharField(
        max_length=255, 
        blank=True, 
        default="General Chat",  
        help_text="A brief summary of what this chat is about."
    )

    total_chat_duration = models.DurationField(
        default=timedelta  
    )

    def __str__(self):
        return f"Chat between {', '.join(user.username for user in self.participants.all())}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    content = models.TextField(default="") 
    timestamp = models.DateTimeField(auto_now_add=True)
    is_pinned = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
