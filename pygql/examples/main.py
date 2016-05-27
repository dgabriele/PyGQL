from pprint import pprint

from pygql.query import Query
from pygql.examples import graph


if __name__ == '__main__':
    from pygql.examples import basic

    request = None  # this is a mock request

    # build a registry of graph traversals or "paths"
    # defined in the given module or package.
    graph.scan(basic)

    # execute a query against the graph
    results = Query.execute(request, '''
        {
            company(id: "123") {
                type, name
            },
            jim: user(id: "123") {
                location {city, state}, first_name, id
            },
            bob: user(id: "123") {
                loc: location {city, state}, first_name,
            }
        }''', graph)

    pprint(results, indent=2)
