from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from .managers import CustomUserManager


class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    image = models.ImageField(upload_to='user_profile')
    first_name = models.CharField(_('first_name'), max_length=20)
    last_name = models.CharField(_('last_name'), max_length=20)
    mobile = PhoneNumberField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email
