import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

DEFAULT_TOKEN_MAX_AGE = timedelta(hours=1)


class Token(models.Model):
    email = models.EmailField()
    uid = models.CharField(default=uuid.uuid4, max_length=40, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Token for {self.email}"

    @property
    def is_expired(self):
        max_age = getattr(settings, 'LOGIN_TOKEN_MAX_AGE', DEFAULT_TOKEN_MAX_AGE)
        return timezone.now() > self.created_at + max_age


class User(models.Model):
    email = models.EmailField(primary_key=True)

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'
    is_anonymous = False
    is_authenticated = True

    def __str__(self):
        return self.email
