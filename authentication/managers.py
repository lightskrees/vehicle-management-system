from django.contrib.auth.models import BaseUserManager
from django.db import models


class AppUserManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('"email" field is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class DeactivatedUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=False)
