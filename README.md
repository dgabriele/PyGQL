# Overview
In the context of PyGQL, the term _path_ refers to a path in a query graph. For example `user.posts.comments`, would be a path to a collection of comments on a hypothetical user's post.

Suppose you have a project with the following structure:

    my_project/
      |-__init__.py
      |-paths.py
      |-app.py


## Create The Path Registry
In `__init__.py`, you would initialize a registry for your paths

```python
from pygql import Graph

graph = Graph()
```


## Registering Paths
Now in `paths.py`, you would register some paths.

```python
from . import graph

@graph(paths=['user'])
def user(request, node, children):
  """ Return a projection of user data.
  """

@graph(paths=['user.location'])
def user_location(request, node, children):
  """ Return a projection of location data.
  """

@graph(paths=['company', 'user.company'])
def company(request, node, children):
  """ Return a projection of company data.
  """
```

### Arguments

#### `request`
This is an HTTP Request object from your web framework.

#### `node`
This is an instance of `pygql.Node`. It contains the arguments to the node as well as a list of the fields queried, accessed through the `fields` attribute. It also has a recursive mapping to child Query objects in the `children` attribute.

#### `children`
Suppose that you have two distinct paths: `user` and `user.company`. When executing a query for `user.company`, a depth-first traversal is performed. The computed result of each node is passed up to its parent. In the example above, the `children` argument to the `user` node would be a Python dict, mapping `'company'` to the result returned by the callable registered with the `user.company` path.


## Graph Initialization & Query Execution
In `app.py`, you would tell the path registry where your paths can be found, which is either a package or a module. From here, you can execute queries against the graph.

```python
from . import paths, graph

# build a registry of graph traversals or "paths"
# defined in the given module or package.
graph.scan(paths)

# execute a query against the graph
results = graph.execute(request, '''
    {
        company(id: "123") {
            type, name
        },
        jim: user(id: "789") {
            location {city, state}, first_name
        }
        bob: user(id: "145") {
            location {city, state}, first_name
        }
    }''')

print(results)
```

## Exceptions
All PyGQL exceptions use a JSON serialized message. See `exceptions.py`.

## Request Validation
TODO

## Authorization
TODO
