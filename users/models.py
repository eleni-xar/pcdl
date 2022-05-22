from django.db.models import BooleanField, CharField, DateTimeField, EmailField
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.utils import timezone
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.mail import send_mail


class User(AbstractBaseUser, PermissionsMixin):
    username = CharField(
        max_length=150,
        unique=True,
        # help_text="Required field. Max length 150 characters. It can be a combination of letters digits and any of @.+-_",
        validators=[UnicodeUsernameValidator(),],
        error_messages={
            "unique": "A user with this username already exists.",
        },
    )
    email = EmailField(
        "email address",
         max_length=255,
         help_text="Not required, but needed if you have forgotten your password and you wish to reset it.",
         blank=True,
    )
    is_staff = BooleanField(
        "staff status",
         default=False,
         help_text="Designates whether this user has access to the admin site.",
    )
    is_active = BooleanField(
        "active",
        default=True,
        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting acounts.",
    )
    date_joined = DateTimeField("date joined", default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user"""
        send_mail(subject, message, from_email, [self.email], **kwargs)
