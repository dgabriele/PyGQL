import marshmallow as mm

from pygql.validation import Schema
from pygql.authorization import Authorization
from pygql.exceptions import AuthorizationError

from . import graph

# example validation schemas

class LocationSchema(Schema):
    """ Defines the valid fields for a location query.
    """
    city = mm.fields.Str()
    state = mm.fields.Str()
    country = mm.fields.Str()


class UserSchema(Schema):
    """ Defines the valid fields for a user query.
    """
    first_name = mm.fields.Str()
    last_name = mm.fields.Str()
    email = mm.fields.Str()
    location = mm.fields.Nested(LocationSchema)


# example authorization

class UserAuthorization(Authorization):
    def __call__(self, request, query, node):
        if 'email' in query.props:
            raise AuthorizationError()


# path registration

@graph(paths=['user'], schema=UserSchema, authorize=UserAuthorization)
def user(request, query, children):
    row = {'first_name': 'Foo', 'last_name': 'Bar', 'email': 'foo@bar.baz'}
    return select(row, query.props)


@graph(paths=['company'])
def company(request, query, children):
    row = {'type': 'LLC', 'name': 'Generic Company'}
    return select(row, query.props)


@graph(paths=['user.location'])
def user_location(request, query, children):
    row = {'city': 'New York', 'state': 'NY', 'country':'USA'}
    return select(row, query.props)


def select(row, cols):
    return {k: row[k] for k in cols if k in row}
