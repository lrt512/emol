from rest_framework import serializers


class WritableSerializerMethodField(serializers.SerializerMethodField):
    """
    Turn a SerializerMethodField into a read-write field.
    From https://stackoverflow.com/a/64274128
    """

    def __init__(self, **kwargs):
        self.setter_method_name = kwargs.pop("setter_method_name", None)
        self.deserializer_field = kwargs.pop("deserializer_field")

        super().__init__(**kwargs)

        self.read_only = False

    def bind(self, field_name, parent):
        super().bind(field_name, parent)
        if not self.setter_method_name:
            self.setter_method_name = f"set_{field_name}"

    def get_default(self):
        default = super().get_default()

        return {self.field_name: default}

    def to_internal_value(self, data):
        value = self.deserializer_field.to_internal_value(data)
        method = getattr(self.parent, self.setter_method_name)
        method(value)

        return {self.field_name: getattr(self.parent.instance, self.field_name)}
