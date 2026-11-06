import uuid
from datetime import timedelta

from django.contrib import auth
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.utils import timezone

from acc.models import Token, User


class UserModelTest(TestCase):
    def test_model_is_configured_for_django_auth(self):
        self.assertEqual(auth.get_user_model(), User)

    def test_user_is_valid_with_email_only(self):
        user = User(email="a@b.com")
        user.full_clean()  # should not raise

    def test_email_is_primary_key(self):
        user = User(email="a@b.com")
        self.assertEqual(user.pk, user.email)

    def test_invalid_email_is_rejected(self):
        user = User(email="not-an-email")
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_blank_email_is_rejected(self):
        user = User(email="")
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_email_must_be_unique(self):
        User.objects.create(email="a@b.com")
        with self.assertRaises(ValidationError):
            User(email="a@b.com").full_clean()

    def test_can_be_looked_up_by_email(self):
        User.objects.create(email="a@b.com")
        self.assertEqual(User.objects.get(pk="a@b.com").email, "a@b.com")

    def test_is_authenticated_and_not_anonymous(self):
        user = User(email="a@b.com")
        self.assertTrue(user.is_authenticated)
        self.assertFalse(user.is_anonymous)

    def test_username_field_is_email(self):
        self.assertEqual(User.USERNAME_FIELD, "email")
        self.assertEqual(User.REQUIRED_FIELDS, [])

    def test_string_representation_is_email(self):
        self.assertEqual(str(User(email="a@b.com")), "a@b.com")


class TokenModelTest(TestCase):
    def test_stores_email(self):
        token = Token.objects.create(email="a@b.com")
        self.assertEqual(Token.objects.get(pk=token.pk).email, "a@b.com")

    def test_uid_is_auto_generated(self):
        token = Token.objects.create(email="a@b.com")
        self.assertTrue(token.uid)

    def test_uid_is_a_valid_uuid(self):
        token = Token.objects.create(email="a@b.com")
        token.refresh_from_db()
        uuid.UUID(token.uid)  # should not raise

    def test_each_token_gets_a_different_uid(self):
        token1 = Token.objects.create(email="a@b.com")
        token2 = Token.objects.create(email="a@b.com")
        self.assertNotEqual(token1.uid, token2.uid)

    def test_multiple_tokens_allowed_per_email(self):
        Token.objects.create(email="a@b.com")
        Token.objects.create(email="a@b.com")
        self.assertEqual(Token.objects.filter(email="a@b.com").count(), 2)

    def test_uid_must_be_unique(self):
        Token.objects.create(email="a@b.com", uid="same")
        with self.assertRaises(IntegrityError):
            Token.objects.create(email="c@d.com", uid="same")

    def test_invalid_email_is_rejected(self):
        token = Token(email="not-an-email")
        with self.assertRaises(ValidationError):
            token.full_clean()

    def test_string_representation_mentions_email(self):
        token = Token(email="a@b.com")
        self.assertEqual(str(token), "Token for a@b.com")


class TokenExpiryTest(TestCase):
    def test_created_at_is_set_automatically(self):
        before = timezone.now()
        token = Token.objects.create(email="a@b.com")
        self.assertGreaterEqual(token.created_at, before)
        self.assertLessEqual(token.created_at, timezone.now())

    def test_fresh_token_is_not_expired(self):
        token = Token.objects.create(email="a@b.com")
        self.assertFalse(token.is_expired)

    @override_settings(LOGIN_TOKEN_MAX_AGE=timedelta(minutes=10))
    def test_token_older_than_max_age_is_expired(self):
        token = Token.objects.create(
            email="a@b.com", created_at=timezone.now() - timedelta(minutes=11)
        )
        self.assertTrue(token.is_expired)

    @override_settings(LOGIN_TOKEN_MAX_AGE=timedelta(minutes=10))
    def test_token_within_max_age_is_not_expired(self):
        token = Token.objects.create(
            email="a@b.com", created_at=timezone.now() - timedelta(minutes=9)
        )
        self.assertFalse(token.is_expired)
