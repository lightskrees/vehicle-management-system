from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _


class TimeStampModel(models.Model):
    created_by = models.ForeignKey("authentication.AppUser", on_delete=models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        created = self.pk is None
        if not created:
            self.updated_at = timezone.now()

        super().save(*args, **kwargs)


class Vehicle(TimeStampModel):
    class VehicleType(models.TextChoices):
        MOTORCYCLE = "motorcycle", _("Motorcycle")
        CAR = "car", _("Car")
        TRUCK = "truck", _("Truck")
        BUS = "bus", _("Bus")
        OTHER = "other", _("Other")

    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    vehicle_type = models.CharField(max_length=10, choices=VehicleType.choices, default=VehicleType.CAR)
    vin_number = models.CharField(max_length=17, unique=True)
    vehicle_image = models.ImageField(upload_to="media/vehicles/", null=True, blank=True)
    color = models.CharField(max_length=20, null=True, blank=True)
    mileage = models.PositiveIntegerField(null=True, blank=True)
    license_plate_number = models.CharField(max_length=10, unique=True)
    purchase_date = models.DateField(null=True, blank=True)
    last_service_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-year", "make", "model"]
        unique_together = ("make", "model", "year", "vin_number")

    def __str__(self):
        return f"{self.make} - {self.model} ({self.year})"


class VehicleDriverAssignment(TimeStampModel):

    class AssignmentStatus(models.TextChoices):
        ACTIVE = "A", _("active")
        INACTIVE = "I", _("inactive")

    driver = models.ForeignKey(
        "authentication.AppUser", on_delete=models.CASCADE, related_name="assignments", related_query_name="assignment"
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="assignments", related_query_name="assignment"
    )
    assignment_status = models.CharField(
        choices=AssignmentStatus.choices, max_length=1, default=AssignmentStatus.ACTIVE
    )
    begin_at = models.DateField()
    ends_at = models.DateField()

    objects = models.Manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vehicle"],
                condition=Q(assignment_status="A"),
                name="unique_active_vehicle_assignment",
            )
        ]

    def clean(self):
        if self.begin_at > self.ends_at:
            raise ValidationError(_("The begin date must be lower than the end date."))

    def save(self, *args, **kwargs):
        self.clean()
        created = self.pk is None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.driver} assigned to {self.vehicle} - {self.get_assignment_status_display()}"


class VehicleTechnician(TimeStampModel):
    user = models.OneToOneField(
        "authentication.AppUser", on_delete=models.DO_NOTHING, related_name="user", related_query_name="user"
    )
    managed_vehicles = models.ManyToManyField(
        Vehicle, related_name="technician", related_query_name="managing_technician"
    )
    begin_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.user} :: {self.begin_date} - {self.end_date}"
