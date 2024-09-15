from django.contrib import admin

from authentication.models import AppUser, Driver

admin.site.register(AppUser)
admin.site.register(Driver)


# Register your models here.
