from . import graph


def select(row, cols):
    return {k: row[k] for k in cols if k in row}


@graph(paths=['user'])
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
