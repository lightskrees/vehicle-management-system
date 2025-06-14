from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, AbstractUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _

from authentication.managers import AppUserManager, DeactivatedUserManager


class AppUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    first_name = models.CharField(max_length=100, verbose_name=_("first name"), null=True, blank=True)
    last_name = models.CharField(max_length=100, verbose_name=_("last name"), null=True, blank=True)
    is_active = models.BooleanField(default=True)
    employeeID = models.CharField(unique=True, null=True, blank=True, max_length=50)

    objects = AppUserManager()
    inactive = DeactivatedUserManager()

    USERNAME_FIELD = "email"

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name}"

    @property
    def is_administrator(self):
        return True if self.is_superuser else False

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.full_name}"
        return self.email

    def get_access_list(self):
        return self.access_roles.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now())

    def has_access(self, role_name):
        access_list = self.get_access_list()
        for access in access_list:
            if role_name == access.role.role_name:
                return True
        return False


class Driver(models.Model):
    class LicenseCategories(models.TextChoices):
        CATEGORY_A = "A", _("Category A")
        CATEGORY_B = "B", _("Category B")
        CATEGORY_C = "C", _("Category C")
        CATEGORY_D1 = "D1", _("Category D1")
        # PCV (Passenger-Carrying nVehicles)
        CATEGORY_D2 = "D2", _("Category D2")
        CATEGORY_E = "E", _("Category E")
        CATEGORY_F = "F", _("Category F")

    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, related_name="driver", related_query_name="drivers", null=True
    )
    driving_license_file = models.ImageField(blank=True, null=True)
    driver_license_document = models.OneToOneField(
        "vehicleHub.Document",
        on_delete=models.PROTECT,
        related_name="owner",
        related_query_name="owner",
        null=True,
        blank=True,
    )
    driving_license_number = models.CharField(max_length=20)
    license_category = models.CharField(
        choices=LicenseCategories.choices, max_length=2, default=LicenseCategories.CATEGORY_B
    )
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.DO_NOTHING,
        related_name="created_drivers",
        related_query_name="created_driver",
        limit_choices_to={"is_active": True},
        blank=True,
        null=True,
    )
    delivery_date = models.DateField()
    expiry_date = models.DateField()

    class Meta:
        ordering = ["license_category", "-expiry_date"]
        unique_together = ["user", "driving_license_number"]

    def __str__(self):
        return f"{self.user.full_name} :: {self.driving_license_number} :: {self.license_category}"

    def have_valid_license(self):
        if self.expiry_date > timezone.now().date() >= self.delivery_date:
            return True
        return False

    def clean(self):
        if self.delivery_date > self.expiry_date:
            raise ValidationError(_("Delivery data must be lower than expiry date"))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Role(models.Model):
    class RoleGroup(models.TextChoices):
        ADMIN = "A", _("Administrator")
        DRIVER = "D", _("Driver")
        TECHNICIAN = "T", _("Technician")
        FINANCIAL = "F", _("Financial")

    role_name = models.CharField(max_length=255, unique=True)
    role_group = models.CharField(choices=RoleGroup.choices, default=RoleGroup.ADMIN, max_length=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.role_name


class AccessRole(models.Model):
    user = models.ForeignKey(
        "authentication.AppUser",
        on_delete=models.PROTECT,
        related_name="access_roles",
        related_query_name="access_role",
    )
    role = models.ForeignKey(
        "authentication.Role", on_delete=models.PROTECT, related_name="roles", related_query_name="role"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    previous_end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.full_name} :: {self.role}"
