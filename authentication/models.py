from django.db import models
from django.contrib.auth.models import AbstractUser, AbstractBaseUser, PermissionsMixin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from authentication.managers import CustomUserManager


class AppUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    employeeID = models.IntegerField(unique=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'

    def _str_(self):
        return self.email
