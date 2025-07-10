from django.contrib import admin

from authentication.models import AccessRole, AppUser, Driver, Role

admin.site.register(AppUser)
admin.site.register(Driver)
admin.site.register(Role)
admin.site.register(AccessRole)


# Register your models here.
