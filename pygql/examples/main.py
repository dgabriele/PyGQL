from pprint import pprint

from mock import MagicMock

from pygql.examples import graph
from pygql.examples import basic


if __name__ == '__main__':

    request = MagicMock()
    request.session.user.public_id = 'ABC123'

    # build a registry of graph traversals or "paths"
    # defined in the given module or package.
    graph.scan(basic)

    # execute a query against the graph
    results = graph.execute(request, '''
        {
            company(id: "123") {
                type, name
            },
            jim: user(id: "ABC123") {
                location {city, state, country},
                first_name, id
            },
            bob: user(id: "LSD123") {
                first_name, last_name
            }
        }''')

    pprint(results, indent=2)
