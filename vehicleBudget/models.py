from django.db import models
from django.utils.translation import gettext_lazy as _

from management.models import TimeStampModel


class PaymentMixin(models.Model):
    class PaymentMethods(models.TextChoices):
        CASH = "CASH", _("Cash")
        BANK = "BANK", _("Bank")
        MOBILE = "MOBILE", _("Mobile")

    payment_date = models.DateField(null=True, blank=True, verbose_name=_("Payment date"))
    payment_amount = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Payment amount"))
    payment_method = models.CharField(choices=PaymentMethods.choices, default=PaymentMethods.CASH)

    class Meta:
        abstract = True


class VehicleMaintenance(TimeStampModel, PaymentMixin):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("pending")
        APPROVED = "APPROVED", _("approved")
        REJECTED = "REJECTED", _("rejected")
        CANCELED = "CANCELED", _("canceled")

    name = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("name"))
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
    partner = models.ForeignKey(
        "vehicleHub.Partner",
        models.PROTECT,
        null=True,
        blank=True,
        related_name="completed_maintenances",
        related_query_name="completed_maintenance",
        verbose_name=_("Maintenance partnership"),
    )

    class Meta:
        unique_together = ("issue_report", "vehicle")

    def __str__(self):
        if self.required_issue_report:
            return f"Maintenance Cost for {self.issue_report} by {self.maintenance_partnership}"
        return f"Maintenance Cost for {self.name} by {self.maintenance_partnership}"


class DocumentCost(TimeStampModel, PaymentMixin):
    document = models.ForeignKey(
        "vehicleHub.Document", on_delete=models.PROTECT, related_name="costs", related_query_name="costs"
    )
    notes = models.CharField(max_length=250, null=True, blank=True, verbose_name=_("notes"))

    def __str__(self):
        return f"{self.document} - {self.payment_amount}"


class FuelConsumption(TimeStampModel, PaymentMixin):

    class QuantityType(models.TextChoices):
        LITER = "LITER", _("liter")
        KWH = "KWH", _("kWh")

    vehicle = models.ForeignKey(
        "management.Vehicle",
        on_delete=models.PROTECT,
        related_name="fuel_consumptions",
        related_query_name="fuel_consumption",
    )
    fuel_type = models.ForeignKey(
        "vehicleHub.FuelType",
        on_delete=models.PROTECT,
        related_name="fuel_consumptions",
        related_query_name="fuel_consumption",
    )
    quantity_type = models.CharField(choices=QuantityType.choices, max_length=20, default=QuantityType.LITER)
    quantity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fuel_cost = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("fuel cost"))
    date = models.DateField(null=True, blank=True, verbose_name=_("Fuel Consumption date"))
    partner = models.ForeignKey(
        "management.Partner",
        on_delete=models.PROTECT,
        related_name="fuel_consumptions",
        related_query_name="fuel_consumption",
    )

    def __str__(self):
        return f"{self.date} - {self.vehicle} - {self.quantity} - {self.quantity_type}"


class FinancialRecord(TimeStampModel):
    document_cost = models.ForeignKey(
        "vehicleBudget.DocumentCost", on_delete=models.PROTECT, related_name="financial_records"
    )
    vehicle_maintenance = models.ForeignKey(
        "vehicleBudget.VehicleMaintenance", on_delete=models.PROTECT, related_name="financial_records"
    )
    fuel_consumption = models.ForeignKey(
        "vehicleBudget.FuelConsumption", on_delete=models.PROTECT, related_name="financial_records"
    )
    cost = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    payment_method = models.CharField(
        choices=PaymentMixin.PaymentMethods.choices, default=PaymentMixin.PaymentMethods.CASH
    )
    record_date = models.DateField(null=True, blank=True)

    def __str__(self):
        if self.document_cost:
            return f"RECORD :: {self.cost}  - {self.document_cost.document} - {self.payment_method}"
        elif self.fuel_consumption:
            return f"RECORD :: {self.cost} - {self.fuel_consumption} - {self.payment_method}"
        elif self.vehicle_maintenance:
            if self.vehicle_maintenance.issue_report:
                return f"RECORD :: {self.cost} - {self.vehicle_maintenance.issue_report} - {self.payment_method}"
            return f"RECORD :: {self.cost} - {self.vehicle_maintenance.name} - {self.payment_method}"
