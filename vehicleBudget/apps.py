from django.apps import AppConfig


class VehiclebudgetConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "vehicleBudget"

    def ready(self):
        super(VehiclebudgetConfig, self).ready()
        import vehicleBudget.signals
