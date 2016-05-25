import venusian

from collections import defaultdict


__all__ = ['Tree']


class Tree(object):
    def __init__(self, path=None):
        self.execute = None
        self.schema = None
        self.children = defaultdict(Tree)
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

    def validate(self, query):
        if self.schema is not None:
            self.schema.validate_query(query)
