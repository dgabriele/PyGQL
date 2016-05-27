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
    id = mm.fields.Str(load_from='public_id')
    first_name = mm.fields.Str()
    last_name = mm.fields.Str()
    email = mm.fields.Str()
    location = mm.fields.Nested(LocationSchema)


# example authorization

class UserAuthorization(Authorization):
    def __call__(self, request, node):
        if 'email' in node.fields:
            raise AuthorizationError()


# path registration

@graph(paths=['user'], schema=UserSchema, authorize=UserAuthorization)
def user(request, node, children):
    row = {
        'public_id': 'ABC123',
        'first_name': 'Foo',
        'last_name': 'Bar',
        'email': 'foo@bar.baz'
    }
    return select(row, node.fields)


@graph(paths=['company'])
def company(request, node, children):
    row = {'type': 'LLC', 'name': 'Generic Company'}
    return select(row, node.fields)


@graph(paths=['user.location'])
def user_location(request, node, children):
    row = {'city': 'New York', 'state': 'NY', 'country':'USA'}
    return select(row, node.fields)


def select(row, cols):
    return {k: row[k] for k in cols if k in row}
