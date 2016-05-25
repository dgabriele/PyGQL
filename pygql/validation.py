import marshmallow

from pygql.exceptions import FieldValidationError
from pygql.decorators import memoized_property

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

    def validate_query(self, query):
        valid_field_names = set(self.scalar_fields.keys())
        valid_child_names = set(self.nested_fields.keys())

        # detect unrecognized props
        field_names = set(query.props)
        unrecognized_field_names = field_names - valid_field_names
        if unrecognized_field_names:
            raise FieldValidationError(
                query.alias, query.name, unrecognized_field_names)

        # detect unrecognized children
        child_names = set(query.children.keys())
        unrecognized_child_names = child_names - valid_child_names
        if unrecognized_child_names:
            raise FieldValidationError(
                query.alias, query.name, unrecognized_child_names)
