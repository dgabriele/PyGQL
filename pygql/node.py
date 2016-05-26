import venusian

from collections import defaultdict


__all__ = ['Node']


class Node(object):
    def __init__(self, path=None):
        self.execute = None
        self.authorize = None
        self.schema = None
        self.children = defaultdict(Node)
        self.path = path or ''

    def __getitem__(self, key):
        if not isinstance(key, (list, tuple)):
            return self.children[key]
        if not key:
            return self
        node = self
        for k in key:
            node = node.children[k]
        return node
