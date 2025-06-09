from django.db.models.signals import post_save

from vehicleBudget.models import DocumentCost, FinancialRecord, FuelConsumption, VehicleMaintenance


def create_clone_in_financial_records(sender, instance, created, **kwargs):
    if not created:
        return

    payment_details = {
        "cost": instance.payment_amount,
        "payment_method": instance.payment_method,
        "record_date": instance.payment_date,
    }

    if sender.__name__ == "DocumentCost":
        FinancialRecord.objects.create(document_cost=instance, **payment_details)
    elif sender.__name__ == "FuelConsumption":
        FinancialRecord.objects.create(fuel_consumption=instance, **payment_details)
    elif sender.__name__ == "VehicleMaintenance":
        FinancialRecord.objects.create(vehicle_maintenance=instance, **payment_details)


post_save.connect(create_clone_in_financial_records, sender=DocumentCost)
post_save.connect(create_clone_in_financial_records, sender=FuelConsumption)
post_save.connect(create_clone_in_financial_records, sender=VehicleMaintenance)
