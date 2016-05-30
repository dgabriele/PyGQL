import marshmallow as mm

from pygql import Schema
from pygql import Context

from . import graph

#
# example schemas
#

class LocationSchema(Schema):
    """ Defines the valid fields for a location query.
    """
    city = mm.fields.Str()
    state = mm.fields.Str()
    country = mm.fields.Str()


class UserSchemaFriend(Schema):
    """ Defines the valid fields for a user query.
    """
    id = mm.fields.Str(load_from='public_id')
    first_name = mm.fields.Str()
    last_name = mm.fields.Str()


class UserSchemaOwner(UserSchemaFriend):
    """ Defines the valid fields for a user query.
    """
    location = mm.fields.Nested(LocationSchema)
    email = mm.fields.Str()


#
# path context definitions
#

class UserContext(Context):
    def __init__(self, request, node):
        self.user_public_id = node.args.get('id')

    def authorize(self, request, node):
        if self.user_public_id == request.session.user.public_id:
            return UserSchemaOwner()
        return UserSchemaFriend()

#
# path registration
#

@graph(path='user', context=UserContext)
def user(request, node, children):
    row = {
        'public_id': 'ABC123',
        'first_name': 'Foo',
        'last_name': 'Bar',
        'email': 'foo@bar.baz'
    }
    return projection(row, node.fields)


@graph(paths=['company'])
def company(request, node, children):
    row = {'type': 'LLC', 'name': 'Generic Company'}
    return projection(row, node.fields)


@graph(paths=['user.location'])
def user_location(request, node, children):
    row = {'city': 'New York', 'state': 'NY', 'country':'USA'}
    return projection(row, node.fields)


def projection(row, cols):
    return {k: row[k] for k in cols if k in row}
