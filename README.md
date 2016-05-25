# Overview
In the context of PyGQL, the term _path_ refers to a path in a query graph. For example `user.posts.comments`, would be a path to a collection of comments on a hypothetical user's post.

Suppose you have a project structure with the following structure:

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
Now in `paths.py`, you would register callables with valid paths

```python
from . import graph

@graph(paths=['user'])
def user(request, query, children):
  '''Fetch a projection of user data. Return JSON serializable object.'''

@graph(paths=['user.location'])
def user_location(request, query, children):
  '''Fetch a projection of user_location data.'''

@graph(paths=['company', 'user.company'])
def company(request, query, children):
  '''Fetch a projection of company data.'''
```

### Arguments

#### `request`
This is an HTTP Request object from your web framework.

#### `query`
This is an instance of `pygql.Query`. It contains the arguments to the graph node as well as a list of the queried fields through the `props` attribute. It also has a recusive mapping to child Query objects in the `children` attribute.

#### `children`
Suppose you have two distinct paths called `user` and `user.company`. When the time comes to execute a query, a depth-first traversal is performed, and the intermediate results are passed back up to the parent node. In the example above, `children` would be a dictionary, mapping `'company'` to the data returned by the callable registered with the `user.company` path.


## Initializing The Graph & Executing Queries
In `app.py`, you would tell the path registry where your paths can be found, which is either a package or a module. From here, you can execute queries against the graph.

```python
from pygql import Query
from . import paths, graph

# build a registry of graph traversals or "paths"
# defined in the given module or package.
graph.scan(paths)

# execute a query against the graph
results = Query.execute(request, '''
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
    }''', graph)

print(results)
```

## Exceptions
All PyGQL exceptions use a JSON serialized message. See `exceptions.py`.

## Query validation
One thing you might want to do is ensure that the fields queried come from an allowed set. PyGQL uses the `marshmallow` validation library to do this.

```python
from pygql import Schema
from marshmallow import fields

class UserSchema(Schema):
    first_name = fields.Str()
    last_name = fields.Str()
    location = fields.Nested('LocationSchema')

class LocationSchema(Schema):
    city = fields.Str()
    state = fields.Str()
    country = fields.Str()

@graph(paths=['user'], schema=UserSchema)  # NOTE: the schema param
def user(request, query, children):
    """Do something"""
```

A `FieldValidationError` is raised if a requested field does not match a field set as a schema class attribute.
