from collections import defaultdict


class Path(object):
    """
    `Path` stores context for a given vertex in a graph.

    Each Path has a dict of child contexts registered through the
    `@graph` decorator. For instance, a registered path of `user.company` would
    yield a "user" Path with a "company" Path in its
    `children` dict. The keys in this dict are the names or aliases of the
    corresponding child Paths.
    """
    def __init__(self, name:str=None, yield_state:bool=False):
        """
            - `self.execute`: callback function registered with the path
            - `self.authorize`: instance of authorization.Authorization
            - `self.schema`: instance of validation.Schema
            - `self.children`: child paths do not include queried fields
            - `self.name`: dotted path to this path
        """
        self.root = None
        self.execute = None
        self.context_class = None
        self.children = defaultdict(Path)
        self.name = name or ''
        self.yield_state = yield_state

    def __getitem__(self, key:str):
        return self.traverse(key)

    def __repr__(self):
        return 'Path<{}>'.format(self.name)

    def traverse(self, key:str):
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
