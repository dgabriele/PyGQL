import abc


class Context(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, request, node):
        pass

    @abc.abstractmethod
    def authorize(self, request, node):
        pass
