from django.apps import apps
from django.utils import timezone
from django.db import models

from management.models import VehicleDriverAssignment


class ActiveAssignmentManager(models.Manager):
    VehicleDriverAssignment = apps.get_model("management.VehicleDriverAssignment")

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(ends_at__gt=timezone.now(), assignment_status=VehicleDriverAssignment.AssignmentStatus.ACTIVE)
        )


class InactiveActiveAssignmentManager(models.Manager):
    VehicleDriverAssignment = apps.get_model("management.VehicleDriverAssignment")

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(ends_at__lt=timezone.now(), assignment_status=VehicleDriverAssignment.AssignmentStatus.ACTIVE)
        )
