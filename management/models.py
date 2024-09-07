from django.db import models
from django.utils.translation import gettext as _


class Vehicle(models.Model):
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




