from collections import Counter

from graphql import parse
from graphql.language.source import Source

from pygql.exceptions import (
    InvalidOperation,
    FieldValidationError,
    AmbiguousFieldError,
)

from pygql.schema import Schema
from pygql.context import Context


class Node(object):
    def __init__(self,
                 root:object,
                 parent:object=None,
                 alias:str=None,
                 name:str=None,
                 args:dict=None,
                 fields:list=None,
                 children:list=None,
                 state:dict=None,
                 context:Context=None):

        self.root = root
        self.parent = parent  # The parent node
        self.alias = alias    # GraphQL node alias
        self.name = name      # Unaliased name of the node

        # Child nodes
        self.children = children or {}

        # Scalar properties queried at this node
        self.fields = fields or []

        # Arguments passed to the GraphQL node
        self.args = args or {}

        # Yielded state (see the @graph yield_state param docs)
        self.state = state or {}

        # User-defined object that implements the Context interface
        self.context = None

        # the "return value" of the node's execution function
        self.result = None

    def __getitem__(self, key):
        return self.children.get(key)

    def __contains__(self, child_name):
        return child_name in self.children

    def reroute(self, dotted_path):
        raise Reroute(self, dotted_path)

    # TODO: merge this logic to reduce number of times the field names
    # are iterated through.
    def validate(self, schema):
        assert isinstance(schema, Schema)
        self._validate_fields(schema)
        self._validate_children(schema)

    def _validate_fields(self, schema):
        """ detect unrecognized field names. replace requested fields list with
            fields that are understood by the path execution function
        """
        valid_names, unrec_names = schema.resolve_scalar_field_names(self.fields)
        if unrec_names:
            raise FieldValidationError(self, unrec_names)
        self._raise_for_duplicate_fields(valid_names)
        self.fields = valid_names


    def _validate_children(self, schema):
        """ detect unrecognized child names
        """
        # we use child path `name` attributes instead of the keys in
        # `children` because the keys are a mixture of valid field names
        # as well as field aliases; whereas path.name is always the field name.
        names = set(v.name for v in self.children.values())
        valid_names, unrec_names = schema.resolve_nested_field_names(names)
        if unrec_names:
            raise FieldValidationError(self, unrec_names)
        self._raise_for_duplicate_fields(valid_names)

    def _raise_for_duplicate_fields(self, field_names):
        counter = Counter()
        duplicate_names = []
        for k in field_names:
            counter[k] += 1
            if counter[k] == 2:
                duplicate_names.append(k)
        if duplicate_names:
            raise AmbiguousFieldError(self, duplicate_names)

    @property
    def is_terminal(self):
        return not self.children

    @classmethod
    def execute(cls, request, query, graph):
        """ Execute a GraphQL node.

            Args:
                - request: an HTTP Request object from your web framework
                - query: A GraphQL query string
                - graph: An instance of `pygql.graph.Context`. This is distinct
                  from user-provided context classes set as @graph params. This
                  is context from the POV of GraphQL query execution.
        """
        return cls._execute(request, cls.parse(query), path=graph.root)

    @classmethod
    def _execute(cls, request, node, path):
        """
        Recursively execute a Node.
        """
        results = {}

        # Authorize the request to the node. If success, validate the queried
        # field and child node names against a return Schema object.
        schema = None
        if path.context_class is not None:
            node.context = path.context_class(request, node)
            schema = node.context.authorize(request, node)
            if schema is not None:
                node.validate(schema)

        # yield this state for consumption by its child nodes
        if path.yield_state:
            state_generator = path.execute(request, node)
            node.state = state_generator.send(None)
        else:
            state_generator = None

        # Execute child nodes in depth-first traversal in order to pass the
        # results back up to the parent (i.e. `node`).
        for k, v in node.children.items():
            results[k] = cls._execute(request, v, path.children[v.name])

        # Execute at node-level, passing results in child results.
        if node.fields:
            try:
                if state_generator is not None:
                    try:
                        state_generator.send(None)
                    except StopIteration as exc:
                        node.result = exc.value
                else:
                    node.result = path.execute(request, node)
            except Reroute as route:
                root = path.root[route.location]
                node.result = cls._execute(request, route.node, root)
            if node.result is None:
                node.result = {}  # to avoid doing results.update(None)
            if isinstance(node.result, dict):
                if schema is not None:
                    # calling schema.load translates the keys in the raw dict
                    # returned by node.execute into what the client expects.
                    node.result, errors = schema.load(node.result)
                    # TODO: log errors
                results.update(node.result)
                return results
            elif isinstance(node.result, (list, tuple, set)):
                if schema is not None:
                    node.result = [schema.load(x).data for x in node.result]
                return node.result
            else:
                raise Exception('illegal path result type')

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
    def _build_node(cls, ast_path, root=None, parent=None):
        """
        Process a graphql-core AST path while parsing.
        """
        node = cls(root=root, parent=parent)

        if ast_path.name:
            node.name = ast_path.name.value

        # TODO: Check type of ast_path instead. i.e. is selectionset
        if hasattr(ast_path, 'alias') and ast_path.alias is not None:
            node.alias = ast_path.alias.value

        node.args = {}
        if hasattr(ast_path, 'arguments'):
            node.args = {
                arg.name.value: arg.value.value for arg in ast_path.arguments
            }
        node.children = {}
        if ast_path.selection_set:
            for child in ast_path.selection_set.selections:
                # store children under alias if alias exists,
                # use the otherwise typename.
                if hasattr(child, 'alias') and child.alias is not None:
                    key = child.alias.value
                else:
                    key = child.name.value
                if child.selection_set:
                    child_node = cls._build_node(child, root=root, parent=node)
                    node.children[key] = child_node
                else:
                    node.fields.append(key)

        return node


class Reroute(Exception):
    def __init__(self, node:object, location:str):
        self.node = node
        self.location = location
