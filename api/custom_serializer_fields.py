from django.utils.translation import gettext_lazy as _
from rest_framework.relations import PrimaryKeyRelatedField


class RelatedPartnership(PrimaryKeyRelatedField):
    default_error_messages = {
        "does_not_exist": _("The partnership do not exist."),
        "invalid": _("Invalid partnership."),
        "required": _("This field is required."),
    }
