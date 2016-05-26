import venusian

from pygql.node import Node
from pygql.validation import Schema
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
        root = Node()

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
            # a nesting of Node objects, where the `b` node is an element of
            # `a.children`.
            self._nodes = []
            for path in paths:
                node = self.root[path.split('.')]
                node.path = path
                self._nodes.append(node)

            self._schema = None
            if schema is not None:
                assert issubclass(schema, Schema)
                self._schema = schema()

            self._authorize = None
            if authorize is not None:
                assert issubclass(authorize, Authorization)
                self._authorize = authorize()

        def __call__(self, func):
            """ Registers the wrapped func as a node function that executes
                at the terminal node in each path in `self.paths`.
            """
            # callback runs synchronously when venusian.Scanner.scan is called
            # in graph.scan.
            def callback(scanner, name, obj):
                """ Register authorization, validation, and query execution
                    objects with the node.
                """
                _func = func  # encloses the func reference
                for node in self._nodes:
                    node.schema = self._schema
                    node.authorize = self._authorize
                    node.execute = _func
            venusian.attach(func, callback)
            return func

        @staticmethod
        def scan(*args, **kwargs):
            """
            Run the callbacks registered in `self.__call__`.
            """
            scanner = venusian.Scanner()
            scanner.scan(*args, **kwargs)

    return graph
