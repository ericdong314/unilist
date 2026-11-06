from acc.models import Token, User


class PasswordlessAuthenticationBackend:
    """Authenticate a user with a single-use, expiring login token."""

    def authenticate(self, request, uid=None):
        if uid is None:
            return None
        try:
            token = Token.objects.get(uid=uid)
        except Token.DoesNotExist:
            return None
        email = token.email
        expired = token.is_expired
        token.delete()  # tokens are single use, whether or not they're valid
        if expired:
            return None
        user, _ = User.objects.get_or_create(email=email)
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(email=user_id)
        except User.DoesNotExist:
            return None
