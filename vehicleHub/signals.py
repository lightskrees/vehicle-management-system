from django.db.models.signals import post_save

from vehicleHub.models import IssueReport


def update_maintenance_overall(sender, instance, created, **kwargs):
    print("made it here!!!")
    if not created and instance.is_fixed:
        return
    print("first step")
    active_maintenances = instance.maintenances.all()

    if not active_maintenances:
        return
    else:
        for maintenance in active_maintenances:
            maintenance.update_maintenance_cost()


post_save.connect(update_maintenance_overall, sender=IssueReport)
