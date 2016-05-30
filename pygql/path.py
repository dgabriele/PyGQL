import abc


class Context(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def authorize(self, request, node):
        pass

    @abc.abstractmethod
    def execute(self, request, node, child_results):
        pass
