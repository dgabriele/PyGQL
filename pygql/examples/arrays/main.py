from pprint import pprint

from mock import MagicMock

from . import graph, paths


# register the functions annotated with @graph decorator
graph.scan(paths)

# mock the HTTP request
request = MagicMock()

pprint(graph.execute(request, '''
    {
        user(id: "ABC123") {
            id, name,
            photos {
                id, url, caption,
                location {lng, lat}
            }
        }
    }'''))
