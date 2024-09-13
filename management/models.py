from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _

class TimeStampModel(models.Model):
    created_by = models.ForeignKey('authentication.AppUser', on_delete=models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        abstract = True

class Vehicle(TimeStampModel):
    class VehicleType(models.TextChoices):
        MOTORCYCLE = 'motorcycle', _('Motorcycle')
        CAR = 'car', _('Car')
        TRUCK = 'truck', _('Truck')
        BUS = 'bus', _('Bus')
        OTHER = 'other', _('Other')

    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    vehicle_type = models.CharField(max_length=10, choices=VehicleType.choices, default=VehicleType.CAR)
    vin_number = models.CharField(max_length=17, unique=True)
    vehicle_image = models.ImageField(upload_to='media/vehicles/')
    color = models.CharField(max_length=20, null=True, blank=True)
    mileage = models.PositiveIntegerField(null=True, blank=True)
    license_plate_number = models.CharField(max_length=10, unique=True)
    purchase_date = models.DateField(null=True, blank=True)
    last_service_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.make} - {self.model} ({self.year})"

    class Meta:
        ordering = ['-year', 'make', 'model']
        unique_together = ('make', 'model', 'year', 'vin_number')

class VehicleDriverAssignment(TimeStampModel):
    driver = models.ForeignKey("authentication.AppUser", on_delete=models.CASCADE, related_name='assignments', related_query_name='assignment')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='assignments', related_query_name='assignment')
    begin_at = models.DateField()
    ends_at = models.DateField()
    objects = models.Manager()
