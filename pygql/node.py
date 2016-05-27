import venusian

from collections import defaultdict

from pygql.validation import Schema


__all__ = ['Node']


class Node(object):
    """
    `Node` stores context for a given vertex in a graph.

    Each node has a dict of child nodes registered through the `@graph`
    decorator. For instance, a registered path of `user.company` would yield a
    "user" node with a "company" node in its `children` dict. The keys in this
    dict are the names of the corresponding nodes.
    """
    def __init__(self, path=None):
        """
            - `self.execute`: callback function registered with the path
            - `self.authorize`: instance of authorization.Authorization
            - `self.schema`: instance of validation.Schema
            - `self.children`: child nodes do not include queried fields
            - `self.path`: dotted path to this node
        """
        self.execute = None
        self.authorize = None
        self.schema = None
        self.children = defaultdict(Node)
        self.path = path or ''

    def __getitem__(self, key):
        """
        You can use a dotted path to implicitly create and fetch nested child
        nodes. E.G. Suppose you have a new node called root. Then root['a.b.c']
        would instantiate a nesting of nodes called 'a', 'b', and 'c'. This is
        the same as doing root['a']['b']['c'].
        """
        if not isinstance(key, (list, tuple)):
            return self.children[key]
        if not key:
            return self
        node = self
        for k in key:
            node = node.children[k]
        return node

    def __repr__(self):
        return 'Node<{}>'.format(self.path)
