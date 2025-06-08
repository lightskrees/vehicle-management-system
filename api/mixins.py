from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import ImproperlyConfigured, PermissionDenied


class MultipleSerializerAPIMixin:
    serializer_class = None
    detail_serializer_class = None
    create_serializer_class = None
    update_serializer_class = None
    list_serializer_class = None

    def get_serializer_class(self):
        if not hasattr(self, "action"):
            return super().get_serializer_class()

        if hasattr(self, "details_serializer_class"):
            self.detail_serializer_class = self.details_serializer_class

        if self.action == "retrieve" and self.detail_serializer_class is not None:
            return self.detail_serializer_class
        elif self.action in ["update", "partial_update"] and self.update_serializer_class is not None:
            return self.update_serializer_class
        elif self.action == "create" and self.create_serializer_class is not None:
            return self.create_serializer_class
        elif self.action == "list":
            return self.list_serializer_class or self.serializer_class

        return super().get_serializer_class()


class AccessMixin:
    permission_denied_message = "You do not have access to perform this action."
    raise_exception = True
    access_required = None
    redirect_field_name = REDIRECT_FIELD_NAME

    def get_permission_denied_message(self):
        return self.permission_denied_message

    def get_redirect_field_name(self):
        return self.redirect_field_name

    def handle_no_access(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())

    def get_access_required(self):
        if self.access_required is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing the "
                f"access_required attribute. Define "
                f"{self.__class__.__name__}.access_required, or override "
                f"{self.__class__.__name__}.get_access_required()."
            )
        if isinstance(self.access_required, str):
            perms = (self.access_required,)
        else:
            perms = self.access_required
        return perms

    def check_access(self):
        has_access = False

        if hasattr(self.request, "user"):
            accesses = self.get_access_required()
            for access in accesses:
                role_name = access.split(".")[1]
                if self.request.user.has_access(role_name):
                    has_access = True
                    return has_access

        return has_access

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        if self.access_required:
            if not self.check_access():
                self.handle_no_access()
        else:
            self.get_access_required()
