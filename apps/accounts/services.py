from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

User = get_user_model()


class InvalidResetLink(Exception):
    pass


def send_password_reset_email(email: str) -> None:
    for user in User.objects.filter(email__iexact=email, is_active=True):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        link = f'{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}'
        send_mail(
            subject='Password reset',
            message=f'To reset your password follow this link:\n{link}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )


def confirm_password_reset(uid: str, token: str, new_password: str) -> None:
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)), is_active=True)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        raise InvalidResetLink
    if not default_token_generator.check_token(user, token):
        raise InvalidResetLink
    validate_password(new_password, user)  # може кинути django ValidationError
    user.set_password(new_password)
    user.save(update_fields=['password'])