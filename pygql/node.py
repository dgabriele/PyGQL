from graphql import parse
from graphql.language.source import Source

from pygql.exceptions import InvalidOperation, FieldValidationError
from pygql.validation import Schema


class Node(object):
    def __init__(self,
                 parent=None,
                 alias=None,
                 name=None,
                 args=None,
                 fields=None,
                 children=None,
                 state=None):

        self.parent = parent
        self.name = name
        self.alias = alias
        self.children = children or {}
        self.fields = fields or []
        self.args = args or {}
        self.state = state or {}

    def __getitem__(self, key):
        return self.children.get(key)

    def validate(self, schema):
        assert isinstance(schema, Schema)
        self._validate_fields(schema)
        self._validate_children(schema)

    def _validate_fields(self, schema):
        """ detect unrecognized field names. replace requested fields list with
            fields that are understood by the ctx execution function
        """
        # the fields queried by the user may not directly correspond to the
        # names of the fields/columns in the storage backend.
        self.fields = schema.resolve_scalar_field_names(self.fields)

        # detect unrecognized fields
        field_names = set(self.fields)
        unrecognized_field_names = field_names - schema.scalar_field_names
        if unrecognized_field_names:
            raise FieldValidationError(self, unrecognized_field_names)

    def _validate_children(self, schema):
        """ detect unrecognized child names
        """
        # we use child ctx `name` attributes instead of the keys in
        # `children` because the keys are a mixture of valid field names
        # as well as field aliases; whereas ctx.name is always the field name.
        child_names = set(v.name for v in self.children.values())

        # detect unrecognized children
        unrecognized_child_names = child_names - schema.nested_field_names
        if unrecognized_child_names:
            raise FieldValidationError(self, unrecognized_child_names)

    @property
    def is_terminal(self):
        return not self.children

    @classmethod
    def execute(cls, request, query, graph):
        """ Execute a GraphQL node.

            Args:
                - request: an HTTP Request object from your web framework
                - query: A GraphQL query string
                - graph: An instance of `pygql.Graph`
        """
        return cls._execute(request, cls.parse(query), ctx=graph.root)

    @classmethod
    def _execute(cls, request, node, ctx):
        """
        Recursively execute a Node.
        """
        results = {}

        # raise exception if unrecognized fields or children are queried
        if ctx.schema is not None:
            node.validate(ctx.schema)

        # authorize request at this node
        if ctx.authorize is not None:
            ctx.authorize(request, node)

        # execute child nodes first to pass them up to parent next
        for k, v in node.children.items():
            results[k] = cls._execute(request, v, ctx.children[v.name])

        # execute node, passing results of child execution results
        if node.fields:
            result = ctx.execute(request, node, results)
            if result is None:
                result = {}  # to avoid doing results.update(None)
            if ctx.schema is not None:
                result, errors = ctx.schema.load(result)
            if isinstance(result, dict):
                results.update(result)
            else:
                # i.e. result is most likely a list.
                return result

        return results

    @classmethod
    def parse(cls, node):
        """ Parse graphql-code AST into a Context tree.
        """
        doc_ast = parse(Source(node))

        if doc_ast.definitions:
            op_def = doc_ast.definitions[0]
            if op_def.operation != 'query':
                raise InvalidOperation(op_def.name.value)
            root = cls._build_node(op_def)
            return root

        return None

    @classmethod
    def _build_node(cls, ast_ctx, parent=None):
        """
        Process a graphql-core AST ctx while parsing.
        """
        node = cls(parent=parent)

        if ast_ctx.name:
            node.name = ast_ctx.name.value

        # TODO: Check type of ast_ctx instead. i.e. is selectionset
        if hasattr(ast_ctx, 'alias') and ast_ctx.alias is not None:
            node.alias = ast_ctx.alias.value

        node.args = {}
        if hasattr(ast_ctx, 'arguments'):
            node.args = {
                arg.name.value: arg.value.value for arg in ast_ctx.arguments
            }
        node.children = {}
        if ast_ctx.selection_set:
            for child in ast_ctx.selection_set.selections:
                # store children under alias if alias exists,
                # use the otherwise typename.
                if hasattr(child, 'alias') and child.alias is not None:
                    key = child.alias.value
                else:
                    key = child.name.value
                if child.selection_set:
                    node.children[key] = cls._build_node(child, node)
                else:
                    node.fields.append(key)

        return node
