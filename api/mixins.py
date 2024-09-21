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
