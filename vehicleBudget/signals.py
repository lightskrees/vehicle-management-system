from django.db.models.signals import post_save

from vehicleBudget.models import DocumentCost, FinancialRecord, FuelConsumption, VehicleMaintenance


def create_clone_in_financial_records(sender, instance: VehicleMaintenance, created, **kwargs):
    # if not created and not sender.__name__ == "VehicleMaintenance":
    #     return

    payment_details = {
        "cost": instance.payment_amount,
        "payment_method": instance.payment_method,
        "record_date": instance.payment_date,
    }

    if sender.__name__ == "DocumentCost":
        if created:
            FinancialRecord.objects.create(document_cost=instance, **payment_details)
        else:
            FinancialRecord.objects.filter(id=instance.id).update(document_cost=instance, **payment_details)

    elif sender.__name__ == "FuelConsumption":
        if created:
            FinancialRecord.objects.create(fuel_consumption=instance, **payment_details)
        else:
            FinancialRecord.objects.filter(id=instance.id).update(fuel_consumption=instance, **payment_details)
    elif (
        sender.__name__ == "VehicleMaintenance"
        and instance.status == sender.Status.APPROVED
        and instance.maintenance_end_date
    ):
        if created:
            FinancialRecord.objects.create(vehicle_maintenance=instance, **payment_details)
        else:
            FinancialRecord.objects.filter(id=instance.id).update(vehicle_maintenance=instance, **payment_details)


post_save.connect(create_clone_in_financial_records, sender=DocumentCost)
post_save.connect(create_clone_in_financial_records, sender=FuelConsumption)
post_save.connect(create_clone_in_financial_records, sender=VehicleMaintenance)
