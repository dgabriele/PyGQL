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

@graph(path='user', context=UserContext, yield_state=True)
def user(request, node):
    yield {
        'country': 'Afghanistan'
    }

    city = 'Orlando'
    if 'location' in node:
        city = node['location'].result.get('city', city)

    return projection({
        'public_id': 'ABC123',
        'first_name': 'Daniel von {}'.format(city),
        'last_name': 'Gabriele',
        'email': 'foo@bar.baz'
    }, node.fields)


@graph(paths=['company'])
def company(request, node):
    return projection({
        'type': 'LLC',
        'name': 'Generic Company'
    }, node.fields)


@graph(paths=['user.location'])
def user_location(request, node):
    return projection({
        'city': 'New York',
        'state': 'NY',
        'country': node.parent.state.get('country', 'USA'),
    }, node.fields)


def projection(row, cols):
    return {k: row[k] for k in cols if k in row}
