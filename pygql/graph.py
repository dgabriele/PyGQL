import venusian

from pygql.tree import Tree


__all__ = ['Graph']


def Graph():
    """ This is a path registry/decorator factory.
    """
    class graph(object):

        # `root` is a global registry of GraphQL target callables stored in
        # a tree. It is the entry point to every defined path in the graph.
        root = Tree()

        def __init__(self, paths):
            self.nodes = [self.root[path.split('.')] for path in paths]

        def __call__(self, func):
            def callback(scanner, name, obj):
                for node in self.nodes:
                    node.execute = func
            venusian.attach(func, callback)
            return func

        @staticmethod
        def scan(*args, **kwargs):
            scanner = venusian.Scanner()
            scanner.scan(*args, **kwargs)

    return graph
