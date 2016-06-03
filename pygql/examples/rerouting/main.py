from pprint import pprint

from mock import MagicMock

from . import graph, paths


# register the functions annotated with @graph decorator
graph.scan(paths)

# mock the HTTP request
request = MagicMock()

pprint(graph.execute(request, '''
    {
        project(id: "XYZ123") {
            assignee {
                name
            }
        }
    }'''))
