from graphql import parse
from graphql.language.source import Source


class Query(object):
    def __init__(self, parent=None, name=None,
                 children=None, args=None, props=None):
        self.parent = parent
        self.name = name
        self.children = children or {}
        self.props = props or []
        self.args = args or {}

    def __getitem__(self, key):
        return self.children.get(key)

    @classmethod
    def execute(cls, request, query_str, graph):
        """ Execute a GraphQL query.

            Args:
                - query_str: A GraphQL query statement
                - graph: An instance of `pygql.Graph`
        """
        return cls._execute(request, cls.parse(query_str), node=graph.root)

    @classmethod
    def _execute(cls, request, query, node):
        """ Recursively execute a Query tree.
        """
        results = {}
        for k, v in query.children.items():
            results[k] = cls._execute(request, v, node.children[k])
        if query.props:
            results.update(node.execute(request, query, results))
        return results

    @classmethod
    def parse(cls, query):
        """ Recursively repackage graphql-core AST nodes as Query objects,
            Returning the root Query node.
        """
        doc_ast = parse(Source(query))

        if doc_ast.definitions:
            op_def = doc_ast.definitions[0]
            if op_def.operation != 'query':
                raise Exception('unsupported op: {}'.format(op_def.name.value))
            root = cls._from_ast(op_def)
            root.name = None
            return root

        return None

    @classmethod
    def _from_ast(cls, ast_node, parent=None):
        """ Process a graphql-core AST node while parsing.
        """
        query = cls(parent=parent)

        query.name = None
        if ast_node.name:
            query.name = ast_node.name.value

        query.args = {}
        if hasattr(ast_node, 'arguments'):
            query.args = {
                arg.name.value: arg.value.value for arg in ast_node.arguments
            }
        query.children = {}
        if ast_node.selection_set:
            for child in ast_node.selection_set.selections:
                name = child.name.value
                if child.selection_set:
                    query.children[name] = cls._from_ast(child, query)
                else:
                    query.props.append(name)

        return query
