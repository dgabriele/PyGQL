import abc

class Authorization(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __call__(self, request, gql_query, gql_node):
        """
        Authorize the query to a given node. Raise `AuthorizationError`
        when not authorized.
        """
