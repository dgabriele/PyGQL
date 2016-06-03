from pprint import pprint

from mock import MagicMock

from . import graph, paths


# build a registry of graph traversals or "paths"
# defined in the given module or package.
graph.scan(paths)

request = MagicMock()
request.session.user.public_id = 'ABC123'

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
