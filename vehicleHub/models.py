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
        CORE = "core", _("Core Document")
        TRAFFIC_VIOLATION = "traffic_violation", _("Traffic Violation")

    class RenewalFrequencyPeriod(models.TextChoices):
        MONTH = "M", _("Months")
        YEAR = "Y", _("Years")

    class OwnerChoices(models.TextChoices):
        VEHICLE = "V", _("Vehicle")
        DRIVER = "D", _("Driver")

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
    validity_period = models.IntegerField(null=True, blank=True, default=1)
    renewal_frequency = models.CharField(
        max_length=50, choices=RenewalFrequencyPeriod.choices, default=RenewalFrequencyPeriod.YEAR
    )
    issuing_authority = models.ForeignKey(
        "vehicleHub.Partner",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="issued_documents",
        related_query_name="issued_document",
        verbose_name=_("Issuing Authority"),
    )
    exp_begin_date = models.DateField(null=True, blank=True, default=timezone.now().date)
    exp_end_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=250, null=True, blank=True)
    document_file = models.FileField(upload_to="media/document/", null=True, blank=True)

    def __str__(self):
        if self.name:
            return f"{self.name} - {self.get_document_type_display()}"
        return f"{self.document_type} - {self.issued_to}"

    def clean(self):
        if self.is_renewable and not self.exp_begin_date or not self.exp_end_date:
            raise ValidationError(_("the expiration begin and end date are required for a renewable document."))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Partnership(TimeStampModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        INACTIVE = "INACTIVE", _("Inactive")
        TERMINATED = "TERMINATED", _("Terminated")

    name = models.CharField(max_length=255, verbose_name=_("Partnership Name"), unique=True)
    start_date = models.DateField(null=True, blank=True, verbose_name=_("Start Date"))
    end_date = models.DateField(null=True, blank=True, verbose_name=_("End Date"))
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.ACTIVE)
    is_permanent_partner = models.BooleanField(default=False)
    description = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.start_date} - {self.end_date} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.is_permanent_partner = True
        else:
            self.is_permanent_partner = False
        super().save(*args, **kwargs)


class Partner(TimeStampModel):
    partnership = models.OneToOneField("vehicleHub.Partnership", on_delete=models.PROTECT, null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name=_("Partner Address"), null=True, blank=True)
    email = models.EmailField(unique=True, verbose_name=_("Partner Email"))
    website = models.URLField(unique=True, null=True, blank=True, verbose_name=_("Partner Website"))
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    companyNIF = models.CharField(unique=True, max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.partnership.name} - {self.companyNIF}"


class Fuel(TimeStampModel):
    class FuelType(models.TextChoices):
        GASOLINE = "GASOLINE", _("Gasoline")
        DIESEL = "DIESEL", _("Diesel")
        ELECTRIC = "ELECTRIC", _("Electric")
        OTHER = "OTHER", _("Other")

    vehicle = models.ForeignKey("management.Vehicle", on_delete=models.PROTECT, null=True, blank=True)
    fuel_type = models.CharField(max_length=50, choices=FuelType.choices, default=FuelType.GASOLINE)

    def __str__(self):
        return f"{self.vehicle} - {self.fuel_type}"


class IssueReport(TimeStampModel):
    class Priority(models.TextChoices):
        LOW = "LOW", _("Low")
        MEDIUM = "MEDIUM", _("Medium")
        HIGH = "HIGH", _("High")

    name = models.CharField(max_length=255, verbose_name=_("Issue Report Name"))
    vehicle = models.ForeignKey(
        "management.Vehicle",
        on_delete=models.PROTECT,
        related_name="issue_reports",
        related_query_name="issue_report",
        null=True,
        blank=True,
    )
    priority = models.CharField(max_length=50, choices=Priority.choices, default=Priority.HIGH)
    report_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return f"{self.name} for {self.vehicle} - {self.get_priority_display()}"
