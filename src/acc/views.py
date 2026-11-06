from django.contrib import auth, messages
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from acc.models import Token

LOGIN_EMAIL_SUBJECT = "Your login link for UniList"
LOGIN_EMAIL_SENT_MESSAGE = "Check your email, we've sent you a link you can use to log in."
INVALID_EMAIL_MESSAGE = "Please enter a valid email address."
INVALID_TOKEN_MESSAGE = "Invalid login link, please request a new one."
LOGGED_IN_REDIRECT = 'todolist:home'


@require_POST
def send_login_email(request):
    email = request.POST.get('email', '').strip()
    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, INVALID_EMAIL_MESSAGE)
        return redirect(LOGGED_IN_REDIRECT)

    token = Token.objects.create(email=email)
    url = request.build_absolute_uri(reverse('acc:login') + '?token=' + str(token.uid))
    send_mail(
        LOGIN_EMAIL_SUBJECT,
        f"Use this link to log in:\n\n{url}",
        None,  # DEFAULT_FROM_EMAIL
        [email],
    )
    messages.success(request, LOGIN_EMAIL_SENT_MESSAGE)
    return redirect(LOGGED_IN_REDIRECT)


def login(request):
    user = auth.authenticate(request, uid=request.GET.get('token'))
    if user is not None:
        auth.login(request, user)
    else:
        messages.error(request, INVALID_TOKEN_MESSAGE)
    return redirect(LOGGED_IN_REDIRECT)
