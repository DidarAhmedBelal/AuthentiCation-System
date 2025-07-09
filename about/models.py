from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class About(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="about")
    sport_coach = models.CharField(
        max_length=100,
        help_text="What are you interested in? (e.g. Web Development, Freelancing, etc.)"
    )
    details = models.TextField(
        help_text="Tell us about yourself, your goals, passions, or interests."
    )

    def __str__(self):
        return f"About: {self.user.username}"
