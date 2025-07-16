from django.apps import AppConfig


class VehiclehubConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "vehicleHub"

    def ready(self):
        super(VehiclehubConfig, self).ready()
        import vehicleHub.signals
