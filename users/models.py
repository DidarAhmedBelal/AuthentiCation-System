from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
from django.utils import timezone

class User(AbstractUser):
    first_name = models.CharField(max_length=10, blank= True, null=True)
    last_name = models.CharField(max_length=10, blank= True, null=True)

    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    is_varified = models.BooleanField(default=False)
    otp_created_at = models.DateTimeField(null=False, blank=True, default=timezone.now)
    otp_request_count = models.IntegerField(default=0)
    otp_request_reset_time = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD ='username'
    REQUIRED_FIELDS =['email']

    def __str__(self):
        return self.username