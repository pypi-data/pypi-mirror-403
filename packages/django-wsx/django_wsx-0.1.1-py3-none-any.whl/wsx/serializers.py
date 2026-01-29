from __future__ import annotations
from typing import Any, Dict

from .exceptions import WSXValidationError


class Field:
    def __init__(self, *, required=True, default=None):
        self.required = required
        self.default = default

    def to_internal_value(self, v):  # noqa
        return v

    def validate(self, v):  # noqa
        return v

    def to_representation(self, v):  # noqa
        return v

    def run_validation(self, data: Dict[str, Any], key: str):
        if key not in data:
            if self.required and self.default is None:
                raise WSXValidationError(fields={key: ["This field is required."]})
            return self.default
        v = data.get(key)
        v = self.to_internal_value(v)
        v = self.validate(v)
        return v


class CharField(Field):
    def __init__(self, *, required=True, default=None, max_length=None, allow_blank=False):
        super().__init__(required=required, default=default)
        self.max_length = max_length
        self.allow_blank = allow_blank

    def to_internal_value(self, v):
        if not isinstance(v, str):
            raise WSXValidationError(fields={"non_field_errors": ["Expected string."]})
        return v

    def validate(self, v):
        if not self.allow_blank and v == "":
            raise WSXValidationError(fields={"non_field_errors": ["Blank not allowed."]})
        if self.max_length is not None and len(v) > self.max_length:
            raise WSXValidationError(fields={"non_field_errors": [f"Max length {self.max_length}."]})
        return v


class IntField(Field):
    def __init__(self, *, required=True, default=None, min_value=None, max_value=None):
        super().__init__(required=required, default=default)
        self.min_value = min_value
        self.max_value = max_value

    def to_internal_value(self, v):
        if isinstance(v, bool) or not isinstance(v, int):
            raise WSXValidationError(fields={"non_field_errors": ["Expected integer."]})
        return v

    def validate(self, v):
        if self.min_value is not None and v < self.min_value:
            raise WSXValidationError(fields={"non_field_errors": [f"Min {self.min_value}."]})
        if self.max_value is not None and v > self.max_value:
            raise WSXValidationError(fields={"non_field_errors": [f"Max {self.max_value}."]})
        return v


class BoolField(Field):
    def to_internal_value(self, v):
        if not isinstance(v, bool):
            raise WSXValidationError(fields={"non_field_errors": ["Expected boolean."]})
        return v


class SerializerMeta(type):
    def __new__(mcls, name, bases, attrs):
        declared = {}
        for k, v in list(attrs.items()):
            if isinstance(v, Field):
                declared[k] = v
                attrs.pop(k)

        cls = super().__new__(mcls, name, bases, attrs)

        fields = {}
        for b in reversed(bases):
            fields.update(getattr(b, "_declared_fields", {}))
        fields.update(declared)

        cls._declared_fields = fields
        return cls


class Serializer(metaclass=SerializerMeta):
    def __init__(self, *, data=None, instance=None, many=False):
        self.initial_data = data
        self.instance = instance
        self.many = many
        self.validated_data = {}
        self.errors = {}

    def is_valid(self, *, raise_exception=False):
        if not isinstance(self.initial_data, dict):
            self.errors = {"non_field_errors": ["Expected object."]}
            if raise_exception:
                raise WSXValidationError(fields=self.errors)
            return False

        out = {}
        errs = {}
        for name, field in self._declared_fields.items():
            try:
                out[name] = field.run_validation(self.initial_data, name)
            except WSXValidationError as e:
                errs[name] = e.fields.get(name) or e.fields.get("non_field_errors") or [e.detail]

        self.errors = errs
        self.validated_data = out if not errs else {}
        if errs and raise_exception:
            raise WSXValidationError(fields=errs)
        return not bool(errs)

    @property
    def data(self):
        if self.many:
            if self.instance is None:
                return []
            if not isinstance(self.instance, (list, tuple)):
                raise WSXValidationError(fields={"non_field_errors": ["Expected list for many=True."]})
            return [self.__class__(instance=item).data for item in self.instance]
        return self.to_representation(self.instance)

    def to_representation(self, obj):
        if obj is None:
            return None
        if isinstance(obj, dict):
            getter = obj.get
        else:
            getter = lambda k: getattr(obj, k, None)  # noqa
        return {name: field.to_representation(getter(name)) for name, field in self._declared_fields.items()}