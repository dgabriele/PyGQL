import venusian
from pygql.schema import Schema
from pygql.context import Context
from pygql.node import Node
from pygql.path import Path

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
                     path:object=None,
                     context:Context=None,
                     yields:bool=False):
            """
            Args:
                - `path`: a dotted path string or list of strings
                - `context`: subclass of pygql.Context
                - `yields`: indicates that the wrapped function is a generator
                            which yields state to its child functions.
            """
            dotted_paths = set()
            if isinstance(path, str):
                dotted_paths.add(path)
            elif isinstance(path, (list, tuple, set)):
                for dotted_path in path:
                    dotted_paths.add(dotted_path)

            assert dotted_paths
            assert (context is None) or issubclass(context, Context)
            assert not [x for x in dotted_paths if not isinstance(x, str)]

            # initialize each path in global tree. `self.root['a', 'b']`yields
            # a nesting of Path objects, where the `b` path is an
            # element of `a.children`.
            self._paths = []
            for dotted_path in dotted_paths:
                path = self.root.traverse(dotted_path.split('.'))
                path.root = self.root
                path.name = dotted_path
                path.context_class = context
                path.yields = yields
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
        def execute(cls, request, query:str):
            return Node.execute(request, query, cls)

        @staticmethod
        def scan(*args, **kwargs):
            """
            Run the callbacks registered in `self.__call__`.
            """
            scanner = venusian.Scanner()
            scanner.scan(*args, **kwargs)

    return graph
