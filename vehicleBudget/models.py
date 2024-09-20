from django.db import models
from django.utils.translation import gettext_lazy as _

from management.models import TimeStampModel


class VehicleMaintenance(TimeStampModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("pending")
        APPROVED = "APPROVED", _("approved")
        REJECTED = "REJECTED", _("rejected")
        CANCELED = "CANCELED", _("canceled")

    name = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("name"))
    estimated_cost = models.PositiveIntegerField(null=True, blank=True)
    issue_report = models.ForeignKey(
        "vehicleHub.IssueReport",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="maintenances",
        related_query_name="maintenance",
    )
    status = models.CharField(choices=Status.choices, default=Status.PENDING, max_length=20)
    vehicle = models.ForeignKey(
        "management.Vehicle", on_delete=models.PROTECT, related_name="maintenances", related_query_name="maintenance"
    )
    maintenance_begin_date = models.DateField(null=True, blank=True)
    maintenance_end_date = models.DateField(null=True, blank=True)
    required_issue_report = models.BooleanField(default=True)

    class Meta:
        unique_together = ("issue_report", "vehicle")

    def __str__(self):
        if self.required_issue_report:
            return f"Maintenance Cost for {self.issue_report}"
        return f"Maintenance Cost for {self.name}"
