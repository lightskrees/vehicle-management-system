from django.contrib import admin

from management.models import Vehicle, VehicleDriverAssignment, VehicleTechnician

admin.site.register(Vehicle)
admin.site.register(VehicleDriverAssignment)
admin.site.register(VehicleTechnician)
