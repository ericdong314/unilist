from datetime import timedelta

from django.contrib import auth
from django.http import HttpRequest
from django.test import TestCase
from django.utils import timezone

from acc.authentication import PasswordlessAuthenticationBackend
from acc.models import Token, User


class AuthenticateTest(TestCase):
    def setUp(self):
        self.backend = PasswordlessAuthenticationBackend()

    def authenticate(self, uid):
        return self.backend.authenticate(HttpRequest(), uid)

    def test_returns_none_if_no_such_token(self):
        self.assertIsNone(self.authenticate("no-such-token"))

    def test_returns_none_if_uid_missing(self):
        self.assertIsNone(self.authenticate(None))

    def test_returns_new_user_with_correct_email_if_token_exists(self):
        token = Token.objects.create(email="edith@example.com")
        user = self.authenticate(token.uid)
        self.assertEqual(user, User.objects.get(email="edith@example.com"))

    def test_returns_existing_user_with_correct_email_if_token_exists(self):
        existing_user = User.objects.create(email="edith@example.com")
        token = Token.objects.create(email="edith@example.com")
        self.assertEqual(self.authenticate(token.uid), existing_user)
        self.assertEqual(User.objects.count(), 1)

    def test_token_can_only_be_used_once(self):
        token = Token.objects.create(email="edith@example.com")
        self.assertIsNotNone(self.authenticate(token.uid))
        self.assertIsNone(self.authenticate(token.uid))
        self.assertFalse(Token.objects.exists())

    def test_returns_none_for_expired_token(self):
        token = Token.objects.create(
            email="edith@example.com", created_at=timezone.now() - timedelta(days=1)
        )
        self.assertIsNone(self.authenticate(token.uid))
        self.assertFalse(User.objects.exists())

    def test_expired_token_is_deleted(self):
        token = Token.objects.create(
            email="edith@example.com", created_at=timezone.now() - timedelta(days=1)
        )
        self.authenticate(token.uid)
        self.assertFalse(Token.objects.exists())

    def test_is_used_by_django_authenticate(self):
        token = Token.objects.create(email="edith@example.com")
        user = auth.authenticate(HttpRequest(), uid=token.uid)
        self.assertEqual(user.email, "edith@example.com")


class GetUserTest(TestCase):
    def test_gets_user_by_email(self):
        User.objects.create(email="another@example.com")
        desired_user = User.objects.create(email="edith@example.com")
        found_user = PasswordlessAuthenticationBackend().get_user("edith@example.com")
        self.assertEqual(found_user, desired_user)

    def test_returns_none_if_no_user_with_that_email(self):
        self.assertIsNone(PasswordlessAuthenticationBackend().get_user("edith@example.com"))
