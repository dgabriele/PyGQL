import marshmallow

from memoized_property import memoized_property

from pygql.exceptions import FieldValidationError


class Schema(marshmallow.Schema):

    @memoized_property
    def scalar_fields(self):
        return {k: v for k, v in self.fields.items()
        if not isinstance(v, marshmallow.fields.Nested)
    }

    @memoized_property
    def nested_fields(self):
        return {k: v for k, v in self.fields.items()
        if isinstance(v, marshmallow.fields.Nested)
    }

    @memoized_property
    def scalar_field_names(self):
        valid_field_names = set()
        for k, v in self.scalar_fields.items():
            valid_field_names.add(v.load_from or k)
        return valid_field_names

    @memoized_property
    def nested_field_names(self):
        valid_child_names = set()
        for k, v in self.nested_fields.items():
            valid_child_names.add(v.load_from or k)
        return valid_child_names

    def resolve_scalar_field_names(self, field_names):
        computed_field_names = []
        for k in field_names:
            v = self.scalar_fields.get(k)
            if v is not None:
                computed_field_names.append(v.load_from or k)
        return computed_field_names

    def resolve_nested_field_names(self, field_names):
        computed_field_names = []
        for k in field_names:
            v = self.nested_fields.get(k)
            if v is not None:
                computed_field_names.append(v.load_from or k)
        return computed_field_names
