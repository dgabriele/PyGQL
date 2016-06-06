from pygql import Schema, Field
from pygql import Context

from . import graph

#
# example schemas
#

class UserSchema(Schema):
    id = Field(name='public_id')
    first_name = Field('first_name')
    last_name = Field('last_name')
    email = Field('email')
    location = Field('location', nested=True)

class LocationSchema(Schema):
    city = Field('city')
    state = Field('state')
    country = Field('country')

#
# path context definitions
#

class UserContext(Context):
    def __init__(self, request, node):
        self.user_public_id = node.args.get('id')
        self.schema = UserSchema()

    def authorize(self, request, node):
        return self.schema

class LocationContext(Context):
    def __init__(self, request, node):
        self.schema = LocationSchema()

    def authorize(self, request, node):
        return self.schema

#
# path registration
#

@graph(path='user', context=UserContext, yields=True)
def user(request, node):
    yield {
        'country': 'Afghanistan'
    }

    city = 'Orlando'
    if 'location' in node:
        city = node['location'].result.get('city', city)

    yield projection({
        'public_id': 'ABC123',
        'first_name': 'Daniel von {}'.format(city),
        'last_name': 'Gabriele',
        'email': 'foo@bar.baz'
    }, node.fields)


@graph(path=['company'])
def company(request, node):
    return projection({
        'type': 'LLC',
        'name': 'Generic Company'
    }, node.fields)


@graph(path='user.location', context=LocationContext)
def user_location(request, node):
    return projection({
        'city': 'New York',
        'state': 'NY',
        'country': node.parent.state.get('country', 'USA'),
    }, node.fields)


def projection(row, cols):
    return {k: row[k] for k in cols if k in row}
