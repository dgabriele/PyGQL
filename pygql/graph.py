import venusian

from pygql.tree import Tree
from pygql.validation import Schema


__all__ = ['Graph']


def Graph(paths=None):
    """ This is a path registry/decorator factory.
    """
    class graph(object):

        # `root` is a global registry of GraphQL target callables stored in
        # a tree. It is the entry point to every defined path in the graph.
        root = Tree()

        def __init__(self, paths, schema=None):
            self.nodes = [self.root[path.split('.')] for path in paths]
            self.schema = None
            if schema is not None:
                assert issubclass(schema, Schema)
                self.schema = schema()

        def __call__(self, func):
            def callback(scanner, name, obj):
                _func = func  # encloses the func reference
                if self.schema is not None:
                    print('here')
                    _func = self.schema.decorate(_func)
                for node in self.nodes:
                    node.execute = _func
            venusian.attach(func, callback)
            return func

        @staticmethod
        def scan(*args, **kwargs):
            scanner = venusian.Scanner()
            scanner.scan(*args, **kwargs)

    if paths is not None:
        graph.scan(paths)

    return graph
