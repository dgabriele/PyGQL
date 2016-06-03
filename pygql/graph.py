import venusian

from collections import defaultdict

from pygql.schema import Schema
from pygql.context import Context
from pygql.node import Node


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
        root = Path()

        def __init__(self,
                     path=None,
                     paths=None,
                     context=None,
                     yield_state=False,
                     ):
            """
            Args:
                - `paths`: a dotted path strings
                - `paths`: list of dotted path strings
                - `context`: subclass of pygql.Context
            """
            dotted_paths = set(paths or [])
            if path is not None:
                dotted_paths.add(path)

            assert dotted_paths
            assert (context is None) or issubclass(context, Context)
            assert not [x for x in dotted_paths if not isinstance(x, str)]

            # initialize each path in global tree. `self.root['a', 'b']`yields
            # a nesting of Path objects, where the `b` path is an
            # element of `a.children`.
            self._paths = []
            for dotted_path in dotted_paths:
                path = self.root.traverse(dotted_path.split('.'))
                path.name = dotted_path
                path.context_class = context
                path.yield_state = yield_state
                self._paths.append(path)

        def __call__(self, func):
            """ Registers the wrapped func as a path function that executes
                at the terminal path in each path in `self.paths`.
            """
            # callback runs synchronously when venusian.Scanner.scan is called
            # in graph.scan.
            def callback(scanner, name, obj):
                """ Register path function with contexts
                """
                _func = func  # enclose the reference for use in conditionals
                for path in self._paths:
                    path.execute = _func
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


class Path(object):
    """
    `Path` stores context for a given vertex in a graph.

    Each Path has a dict of child contexts registered through the
    `@graph` decorator. For instance, a registered path of `user.company` would
    yield a "user" Path with a "company" Path in its
    `children` dict. The keys in this dict are the names or aliases of the
    corresponding child Paths.
    """
    def __init__(self, name=None, yield_state=False):
        """
            - `self.execute`: callback function registered with the path
            - `self.authorize`: instance of authorization.Authorization
            - `self.schema`: instance of validation.Schema
            - `self.children`: child paths do not include queried fields
            - `self.name`: dotted path to this path
        """
        self.execute = None
        self.context_class = None
        self.children = defaultdict(Path)
        self.name = name or ''
        self.yield_state = yield_state

    def __getitem__(self, key):
        return self.traverse(key)

    def __repr__(self):
        return 'Path<{}>'.format(self.name)

    def traverse(self, key):
        """
        You can use a dotted path to implicitly create and fetch nested child
        paths. E.G. Suppose you have a new path called root. Then root['a.b.c']
        would instantiate a nesting of paths called 'a', 'b', and 'c'. This is
        the same as doing root['a']['b']['c'].
        """
        if not isinstance(key, (list, tuple)):
            return self.children[key]
        if not key:
            return self
        path = self
        for k in key:
            path = path.children[k]
        return path
