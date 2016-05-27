import venusian

from collections import defaultdict

from pygql.validation import Schema
from pygql.node import Node
from pygql.authorization import Authorization


__all__ = ['Graph']


def Graph():
    """
    This is a path registry/decorator factory. This is a factory so that
    multiple "graphs" can be used simultaneously rather than a single global
    one.
    """
    class graph(object):
        """
        Graph traversal/path registration decorator.
        """
        # `root` is a global registry of GraphQL target callables stored in
        # a tree. It is the entry point to every defined path in the graph.
        root = Context()

        def __init__(self, paths, schema=None, authorize=None):
            """
            Args:
                - paths: list of dotted paths
                - schema: a pygql.validation.Schema subclass for validating
                    queried field names.
                - authorize: a pygql.authorization.Authorization subclass,
                    which may raises AuthorizationError if a query requested
                    at any of these paths is not authorized.
            """
            # initialize each path in global tree. `self.root['a', 'b']`yields
            # a nesting of Context objects, where the `b` ctx is an element of
            # `a.children`.
            self._ctxs = []
            for path in paths:
                ctx = self.root[path.split('.')]
                ctx.path = path
                self._ctxs.append(ctx)

            self._schema = None
            if schema is not None:
                assert issubclass(schema, Schema)
                self._schema = schema()

            self._authorize = None
            if authorize is not None:
                assert issubclass(authorize, Authorization)
                self._authorize = authorize()

        def __call__(self, func):
            """ Registers the wrapped func as a ctx function that executes
                at the terminal ctx in each path in `self.paths`.
            """
            # callback runs synchronously when venusian.Scanner.scan is called
            # in graph.scan.
            def callback(scanner, name, obj):
                """ Register authorization, validation, and query execution
                    objects with the ctx.
                """
                _func = func  # encloses the func reference
                for ctx in self._ctxs:
                    ctx.schema = self._schema
                    ctx.authorize = self._authorize
                    ctx.execute = _func
            venusian.attach(func, callback)
            return func

        @classmethod
        def execute(cls, request, query):
            return Node.execute(request, query, cls)

        @staticmethod
        def scan(*args, **kwargs):
            """
            Run the callbacks registered in `self.__call__`.
            """
            scanner = venusian.Scanner()
            scanner.scan(*args, **kwargs)

    return graph


class Context(object):
    """
    `Context` stores context for a given vertex in a graph.

    Each Context has a dict of child Contexts registered through the `@graph`
    decorator. For instance, a registered path of `user.company` would yield a
    "user" Context with a "company" Context in its `children` dict. The keys in
    this dict are the names or aliases of the corresponding child Contexts.
    """
    def __init__(self, path=None):
        """
            - `self.execute`: callback function registered with the path
            - `self.authorize`: instance of authorization.Authorization
            - `self.schema`: instance of validation.Schema
            - `self.children`: child ctxs do not include queried fields
            - `self.path`: dotted path to this ctx
        """
        self.execute = None
        self.authorize = None
        self.schema = None
        self.children = defaultdict(Context)
        self.path = path or ''

    def __getitem__(self, key):
        """
        You can use a dotted path to implicitly create and fetch nested child
        ctxs. E.G. Suppose you have a new ctx called root. Then root['a.b.c']
        would instantiate a nesting of ctxs called 'a', 'b', and 'c'. This is
        the same as doing root['a']['b']['c'].
        """
        if not isinstance(key, (list, tuple)):
            return self.children[key]
        if not key:
            return self
        ctx = self
        for k in key:
            ctx = ctx.children[k]
        return ctx

    def __repr__(self):
        return 'Context<{}>'.format(self.path)
