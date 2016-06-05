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
from pygql.path import Path


class Node(object):
    def __init__(self,
                 root,
                 parent=None,
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

        # Yielded state (see the @graph yields param docs)
        self.state = state or {}

        # User-defined object that implements the Context interface
        self.context = None

        # the "return value" of the node's execution function
        self.result = None

    def __getitem__(self, key:str):
        return self.children.get(key)

    def __contains__(self, child_name:str):
        return child_name in self.children

    def reroute(self, location:str):
        raise Reroute(self, location)

    # TODO: merge this logic to reduce number of times the field names
    # are iterated through.
    def validate(self, schema:Schema):
        assert isinstance(schema, Schema)
        self._validate_fields(schema)
        self._validate_children(schema)

    def _validate_fields(self, schema:Schema):
        """ detect unrecognized field names. replace requested fields list with
            fields that are understood by the path execution function
        """
        valid_names, unrec_names = schema.translate(self.fields)
        if unrec_names:
            raise FieldValidationError(self, unrec_names)
        self._raise_for_duplicate_fields(valid_names)
        self.fields = valid_names


    def _validate_children(self, schema:Schema):
        """ detect unrecognized child names
        """
        # we use child path `name` attributes instead of the keys in
        # `children` because the keys are a mixture of valid field names
        # as well as field aliases; whereas path.name is always the field name.
        names = set(v.name for v in self.children.values())
        valid_names, unrec_names = schema.translate(names, nested=True)
        if unrec_names:
            raise FieldValidationError(self, unrec_names)
        self._raise_for_duplicate_fields(valid_names)

    def _raise_for_duplicate_fields(self, field_names:list):
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
    def execute(cls, request, query:str, graph):
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
    def _execute(cls, request, node, path:Path):
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
        if path.yields:
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
                    node.result = state_generator.send(None)
                else:
                    node.result = path.execute(request, node)
            except Reroute as route:
                root = path.root[route.location]
                node.result = cls._execute(request, route.node, root)
            if node.result is None:
                node.result = {}  # to avoid doing results.update(None)
            if isinstance(node.result, dict):
                if schema is not None:
                    node.result = schema.dump(node.result)
                results.update(node.result)
                return results
            elif isinstance(node.result, (list, tuple, set)):
                if schema is not None:
                    node.result = [schema.dump(x) for x in node.result]
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
    def __init__(self, node, location:str):
        self.node = node
        self.location = location
