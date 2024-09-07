from django.db import models
from django.contrib.auth.models import AbstractUser, AbstractBaseUser, PermissionsMixin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from authentication.managers import CustomUserManager


class AppUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    first_name = models.CharField(max_length=100, verbose_name=_('first name'), null=True, blank=True)
    last_name = models.CharField(max_length=100, verbose_name=_('last name'), null=True, blank=True)
    is_active = models.BooleanField(default=True)
    employeeID = models.IntegerField(unique=True, null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'

    def _str_(self):
        return self.email


class Driver(models.Model):
    class LicenseCategories(models.TextChoices):
        CATEGORY_A = "A", _("Category A")
        CATEGORY_B = "B", _("Category B")
        CATEGORY_C = "C", _("Category C")
        CATEGORY_D1 = "D1", _("Category D1")
        # PCV (Passenger-Carrying Vehicles)
        CATEGORY_D2 = "D2", _("Category D2")
        CATEGORY_E = "E", _("Category E")
        CATEGORY_F = "F", _("Category F")

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name="driver",
                                related_query_name="drivers")
    driving_license_file = models.ImageField(blank=True, null=True)
    driving_license_number = models.CharField(max_length=20)
    license_category = models.CharField(choices=LicenseCategories.choices, max_length=2,
                                        default=LicenseCategories.CATEGORY_B)
    delivery_date = models.DateField()
    expiry_date = models.DateField()

    class Meta:
        ordering = ["license_category", "-expiry_date"]
        unique_together = ["user", "driving_license_number"]