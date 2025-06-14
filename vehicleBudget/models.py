from django.db import models
from django.utils.translation import gettext_lazy as _

from management.models import TimeStampModel


class PaymentMixin(models.Model):
    class PaymentMethods(models.TextChoices):
        CASH = "C", _("Cash")
        BANK = "B", _("Bank")
        MOBILE = "M", _("Mobile")

    payment_date = models.DateField(null=True, blank=True, verbose_name=_("Payment date"))
    payment_amount = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Payment amount"))
    payment_method = models.CharField(max_length=1, choices=PaymentMethods.choices, default=PaymentMethods.CASH)

    class Meta:
        abstract = True


class VehicleMaintenance(TimeStampModel, PaymentMixin):
    class Status(models.TextChoices):
        PENDING = "P", _("pending")
        APPROVED = "A", _("approved")
        REJECTED = "R", _("rejected")
        CANCELED = "C", _("canceled")

    name = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("name"))

    issue_reports = models.ManyToManyField(
        "vehicleHub.IssueReport",
        blank=True,
        related_name="maintenances",
        related_query_name="maintenance",
    )
    status = models.CharField(choices=Status.choices, default=Status.PENDING, max_length=1)
    maintenance_begin_date = models.DateField(null=True, blank=True)
    maintenance_end_date = models.DateField(null=True, blank=True)
    required_issue_report = models.BooleanField(default=True)
    partner = models.ForeignKey(
        "vehicleHub.Partner",
        models.PROTECT,
        null=True,
        blank=True,
        related_name="completed_maintenances",
        related_query_name="completed_maintenance",
        verbose_name=_("Maintenance partnership"),
    )

    def __str__(self):
        return f"{self.name} - ({self.get_status_display()})"

    def clean(self):
        if self.maintenance_begin_date and self.maintenance_end_date:
            self.status = self.Status.APPROVED

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def update_maintenance_cost(self, commit=True):
        issue_reports = self.issue_reports.all()
        total = 0
        for report in issue_reports:
            total += report.issue_cost if report.issue_cost else 0  # to avoid value error in the computing process...
        self.payment_amount = total

        if commit:
            self.save()


class DocumentCost(TimeStampModel, PaymentMixin):
    document = models.ForeignKey(
        "vehicleHub.Document", on_delete=models.PROTECT, related_name="costs", related_query_name="costs"
    )
    notes = models.CharField(max_length=250, null=True, blank=True, verbose_name=_("notes"))

    def __str__(self):
        return f"{self.document} - {self.payment_amount}"


class FuelConsumption(TimeStampModel, PaymentMixin):

    class QuantityType(models.TextChoices):
        LITER = "l", _("liter")
        KWH = "kWh", _("kWh")

    vehicle = models.ForeignKey(
        "management.Vehicle",
        on_delete=models.PROTECT,
        related_name="fuel_consumptions",
        related_query_name="fuel_consumption",
    )
    fuel_type = models.ForeignKey(
        "vehicleHub.Fuel",
        on_delete=models.PROTECT,
        related_name="fuel_consumptions",
        related_query_name="fuel_consumption",
    )
    quantity_type = models.CharField(max_length=3, choices=QuantityType.choices, default=QuantityType.LITER)
    quantity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fuel_cost = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("fuel cost"))
    date = models.DateField(null=True, blank=True, verbose_name=_("Fuel Consumption date"))
    partner = models.ForeignKey(
        "vehicleHub.Partner",
        on_delete=models.PROTECT,
        related_name="fuel_consumptions",
        related_query_name="fuel_consumption",
    )

    def __str__(self):
        return f"{self.date} - {self.vehicle} - {self.quantity} - {self.quantity_type}"


class FinancialRecord(TimeStampModel):
    document_cost = models.ForeignKey(
        "vehicleBudget.DocumentCost", on_delete=models.PROTECT, related_name="financial_records", null=True
    )
    vehicle_maintenance = models.ForeignKey(
        "vehicleBudget.VehicleMaintenance", on_delete=models.PROTECT, related_name="financial_records", null=True
    )
    fuel_consumption = models.ForeignKey(
        "vehicleBudget.FuelConsumption", on_delete=models.PROTECT, related_name="financial_records", null=True
    )
    cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    payment_method = models.CharField(
        max_length=1, choices=PaymentMixin.PaymentMethods.choices, default=PaymentMixin.PaymentMethods.CASH
    )
    record_date = models.DateField(null=True, blank=True)

    def __str__(self):
        if self.document_cost:
            return f"RECORD :: {self.cost}  - {self.document_cost.document} - {self.get_payment_method_display()}"
        elif self.fuel_consumption:
            return f"RECORD :: {self.cost} - {self.fuel_consumption} - {self.get_payment_method_display()}"
        elif self.vehicle_maintenance:
            return f"RECORD :: {self.cost} - {self.vehicle_maintenance.name} - {self.get_payment_method_display()}"
