import marshmallow

from pygql.exceptions import FieldValidationError
from pygql.decorators import reify

class Schema(marshmallow.Schema):

    @reify
    def scalar_fields(self):
        return {k: v for k, v in self.fields.items()
        if not isinstance(v, marshmallow.fields.Nested)
    }

    @reify
    def nested_fields(self):
        return {k: v for k, v in self.fields.items()
        if not isinstance(v, marshmallow.fields.Nested)
    }

    def decorate(self, func):
        """
        Return a function that decorates the target query function, which
        raises an exception if the request query props are not valid according
        to this schema.
        """
        valid_field_names = set(self.scalar_fields.keys())

        def wrapper(request, query, children):
            field_names = set(query.props)
            if (field_names & valid_field_names) != field_names:
                unrecognized_field_names = field_names - valid_field_names
                raise FieldValidationError(query.alias, query.name, unrecognized_field_names)
            return func(request, query, children)

        wrapper.__name__ = func.__name__
        return wrapper
