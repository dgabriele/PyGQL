from graphql import parse
from graphql.language.source import Source

from pygql.exceptions import InvalidOperation
from pygql.validation import Schema


class Query(object):
    def __init__(self, parent=None, alias=None, name=None,
                 children=None, args=None, props=None):

        self.parent = parent
        self.name = name
        self.alias = alias
        self.children = children or {}
        self.props = props or []
        self.args = args or {}

        assert isinstance(self.props, list)
        assert isinstance(self.args, dict)
        assert isinstance(self.children, dict)
        if self.alias is not None:
            assert isinstance(self.alias, str)
        if self.parent is not None:
            assert isinstance(self.parent, Query)

    def __getitem__(self, key):
        return self.children.get(key)

    def validate(self, schema):
        assert isinstance(schema, Schema)
        self._validate_props(schema)
        self._validate_children(schema)

    def _validate_props(self, schema):
        """ detect unrecognized field names
        """
        field_names = set(self.props)
        unrecognized_field_names = field_names - schema.scalar_field_names
        if unrecognized_field_names:
            raise FieldValidationError(
                query.alias, query.name, unrecognized_field_names)

    def _validate_children(self, schema):
        """ detect unrecognized child names
        """
        # detect unrecognized children
        child_names = set(self.children.keys())
        unrecognized_child_names = child_names - schema.nested_field_names
        if unrecognized_child_names:
            raise FieldValidationError(
                query.alias, query.name, unrecognized_child_names)

    @property
    def is_terminal(self):
        return not self.children

    @classmethod
    def execute(cls, request, query_str, graph):
        """ Execute a GraphQL query.

            Args:
                - request: an HTTP Request object from your web framework
                - query_str: A GraphQL query statement
                - graph: An instance of `pygql.Graph`
        """
        return cls._execute(request, cls.parse(query_str), node=graph.root)

    @classmethod
    def _execute(cls, request, query, node):
        """ Recursively execute a Query.
        """
        results = {}

        # raise exception if unrecognized fields or children are queried
        if node.schema is not None:
            query.validate(node.schema)

        # authorize request to query this node
        if node.authorize is not None:
            node.authorize(request, query, node)

        # execute children queries first in order to pass them up to parent
        for k, v in query.children.items():
            results[k] = cls._execute(request, v, node.children[v.name])

        # execute query, passing results of child queries
        if query.props:
            results.update(node.execute(request, query, results))

        return results

    @classmethod
    def parse(cls, query):
        """ Recursively repackage graphql-core AST nodes as Query objects,
            Returning the root Query.
        """
        doc_ast = parse(Source(query))

        if doc_ast.definitions:
            op_def = doc_ast.definitions[0]
            if op_def.operation != 'query':
                raise InvalidOperation(op_def.name.value)
            root = cls._build_query(op_def)
            return root

        return None

    @classmethod
    def _build_query(cls, ast_node, parent=None):
        """ Process a graphql-core AST node while parsing.
        """
        query = cls(parent=parent)

        if ast_node.name:
            query.name = ast_node.name.value

        # TODO: Check type of ast_node instead. i.e. is selectionset
        if hasattr(ast_node, 'alias') and ast_node.alias is not None:
            query.alias = ast_node.alias.value

        query.args = {}
        if hasattr(ast_node, 'arguments'):
            query.args = {
                arg.name.value: arg.value.value for arg in ast_node.arguments
            }
        query.children = {}
        if ast_node.selection_set:
            for child in ast_node.selection_set.selections:
                # store children under alias if alias exists,
                # use the otherwise typename.
                if hasattr(child, 'alias') and child.alias is not None:
                    key = child.alias.value
                else:
                    key = child.name.value
                if child.selection_set:
                    query.children[key] = cls._build_query(child, query)
                else:
                    query.props.append(key)

        return query
