from datetime import timedelta

from django.contrib import auth
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from acc.models import Token, User
from acc.views import (
    INVALID_EMAIL_MESSAGE,
    INVALID_TOKEN_MESSAGE,
    LOGIN_EMAIL_SENT_MESSAGE,
    LOGIN_EMAIL_SUBJECT,
)

TEST_EMAIL = "edith@example.com"


class SendLoginEmailViewTest(TestCase):
    def post(self, email=TEST_EMAIL, **kwargs):
        return self.client.post("/acc/send_login_email", data={"email": email}, **kwargs)

    def test_redirects_to_todo_home_page(self):
        self.assertRedirects(self.post(), "/todo/")

    def test_sends_mail_to_address_from_post(self):
        self.post()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [TEST_EMAIL])
        self.assertEqual(mail.outbox[0].subject, LOGIN_EMAIL_SUBJECT)

    def test_creates_token_associated_with_email(self):
        self.post()
        self.assertEqual(Token.objects.get().email, TEST_EMAIL)

    def test_sends_link_to_login_using_token_uid(self):
        self.post()
        token = Token.objects.get()
        expected_url = f"http://testserver/acc/login?token={token.uid}"
        self.assertIn("Use this link to log in", mail.outbox[0].body)
        self.assertIn(expected_url, mail.outbox[0].body)

    def test_login_link_is_last_thing_in_email_body(self):
        # the functional test extracts the url with r"http://.+/.+$"
        self.post()
        self.assertTrue(mail.outbox[0].body.endswith(Token.objects.get().uid))

    def test_strips_whitespace_from_email(self):
        self.post(email=f"  {TEST_EMAIL}  ")
        self.assertEqual(Token.objects.get().email, TEST_EMAIL)

    def test_adds_success_message(self):
        response = self.post(follow=True)
        [message] = list(response.context["messages"])
        self.assertEqual(message.message, LOGIN_EMAIL_SENT_MESSAGE)
        self.assertEqual(message.tags, "success")

    def test_success_message_is_shown_on_page(self):
        response = self.post(follow=True)
        self.assertContains(response, "Check your email")

    def test_invalid_email_sends_nothing(self):
        self.post(email="not-an-email")
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(Token.objects.exists())

    def test_invalid_email_adds_error_message(self):
        response = self.post(email="not-an-email", follow=True)
        [message] = list(response.context["messages"])
        self.assertEqual(message.message, INVALID_EMAIL_MESSAGE)
        self.assertEqual(message.tags, "error")

    def test_blank_email_is_rejected(self):
        self.post(email="")
        self.assertEqual(len(mail.outbox), 0)

    def test_get_not_allowed(self):
        response = self.client.get("/acc/send_login_email")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(len(mail.outbox), 0)


class LoginViewTest(TestCase):
    def test_redirects_to_todo_home_page(self):
        response = self.client.get("/acc/login?token=abcd123")
        self.assertRedirects(response, "/todo/")

    def test_logs_in_if_given_valid_token(self):
        token = Token.objects.create(email=TEST_EMAIL)
        self.client.get(f"/acc/login?token={token.uid}")
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.email, TEST_EMAIL)

    def test_creates_user_on_first_login(self):
        token = Token.objects.create(email=TEST_EMAIL)
        self.client.get(f"/acc/login?token={token.uid}")
        self.assertTrue(User.objects.filter(email=TEST_EMAIL).exists())

    def test_does_not_log_in_if_given_invalid_token(self):
        self.client.get("/acc/login?token=invalid-token")
        self.assertFalse(auth.get_user(self.client).is_authenticated)

    def test_does_not_log_in_without_token(self):
        response = self.client.get("/acc/login")
        self.assertRedirects(response, "/todo/")
        self.assertFalse(auth.get_user(self.client).is_authenticated)

    def test_does_not_log_in_with_expired_token(self):
        token = Token.objects.create(
            email=TEST_EMAIL, created_at=timezone.now() - timedelta(days=1)
        )
        self.client.get(f"/acc/login?token={token.uid}")
        self.assertFalse(auth.get_user(self.client).is_authenticated)

    def test_token_cannot_be_reused(self):
        token = Token.objects.create(email=TEST_EMAIL)
        self.client.get(f"/acc/login?token={token.uid}")
        self.client.post("/acc/logout")
        self.client.get(f"/acc/login?token={token.uid}")
        self.assertFalse(auth.get_user(self.client).is_authenticated)

    def test_shows_error_message_if_token_invalid(self):
        response = self.client.get("/acc/login?token=invalid-token", follow=True)
        [message] = list(response.context["messages"])
        self.assertEqual(message.message, INVALID_TOKEN_MESSAGE)
        self.assertEqual(message.tags, "error")


class LogoutViewTest(TestCase):
    def test_logs_out_and_redirects_to_todo_home(self):
        self.client.force_login(User.objects.create(email=TEST_EMAIL))
        response = self.client.post("/acc/logout")
        self.assertRedirects(response, "/todo/")
        self.assertFalse(auth.get_user(self.client).is_authenticated)


class NavbarTest(TestCase):
    def test_shows_login_form_when_logged_out(self):
        response = self.client.get("/todo/")
        self.assertContains(response, 'action="/acc/send_login_email"')
        self.assertContains(response, 'name="email"')
        self.assertNotContains(response, 'id="id_logout"')

    def test_shows_email_and_logout_button_when_logged_in(self):
        self.client.force_login(User.objects.create(email=TEST_EMAIL))
        response = self.client.get("/todo/")
        self.assertContains(response, TEST_EMAIL)
        self.assertContains(response, 'id="id_logout"')
        self.assertContains(response, 'action="/acc/logout"')
        self.assertNotContains(response, 'action="/acc/send_login_email"')
