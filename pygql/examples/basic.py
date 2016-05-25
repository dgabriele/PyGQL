import marshmallow as mm

from pygql.validation import Schema

from . import graph


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
    location = mm.fields.Nested(LocationSchema)


@graph(paths=['user'], schema=UserSchema)
def user(request, query, children):
    row = {'first_name': 'Daniel', 'last_name': 'Gabriele'}
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
