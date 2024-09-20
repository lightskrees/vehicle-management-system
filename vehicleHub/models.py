from django.db import models
from django.utils.translation import gettext_lazy as _

from management.models import TimeStampModel


class Document(TimeStampModel):
    class DocumentChoices(models.TextChoices):
        INSURANCE_CERTIFICATE = "INSURANCE_CERTIFICATE", _("Insurance Certificate")
        ROAD_TAX = "ROAD_TAX", _("Road Tax")
        VEHICLE_INSPECTION_REPORT = "VEHICLE_INSPECTION_REPORT", _("Vehicle Inspection Report")
        VEHICLE_REGISTRATION_DOCUMENT = "VEHICLE_REGISTRATION_DOCUMENT", _("Vehicle Registration Document")
        OTHER = "OTHER", _("Other")

    class DocumentTypeChoices(models.TextChoices):
        CORE = "CORE", _("Core Document")
        TRAFFIC_VIOLATION = "TRAFFIC_VIOLATION", _("Traffic Violation")

    class OwnerChoices(models.TextChoices):
        VEHICLE = "VEHICLE", _("Vehicle")
        DRIVER = "DRIVER", _("Driver")

    name = models.CharField(max_length=255, verbose_name=_("Document Name"))
    document_type = models.CharField(max_length=50, choices=DocumentChoices.choices)
    document_category = models.CharField(max_length=50, choices=DocumentTypeChoices.choices)
    issued_to = models.CharField(max_length=50, choices=OwnerChoices.choices)
    issued_vehicle = models.ForeignKey(
        "management.Vehicle",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="documents",
        related_query_name="document",
    )
    issued_driver = models.ForeignKey(
        "authentication.Driver",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="documents",
        related_query_name="document",
    )
    is_renewable = models.BooleanField(default=True)
    validity_period = models.IntegerField(null=True, blank=True)
    renewal_frequency = models.IntegerField(null=True, blank=True)
    issuing_authority = models.CharField(max_length=100)
    exp_begin_date = models.DateField(null=True, blank=True)
    exp_end_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=250, null=True, blank=True)
    document_image = models.ImageField(upload_to="media/document_types/", null=True, blank=True)

    def __str__(self):
        if self.name:
            return f"{self.name} - {self.get_document_type_display()}"
        return f"{self.document_type} - {self.issued_to}"
