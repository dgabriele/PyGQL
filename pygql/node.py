from collections import Counter, deque

from graphql import parse
from graphql.language.source import Source

from pygql.exceptions import (
    InvalidOperation,
    InvalidResult,
    FieldValidationError,
    FieldAmbiguityError,
    NotFound,
)

from pygql.schema import Schema
from pygql.context import Context
from pygql.path import Path


__all__ = ['Node']


IDX_LABEL = 0
IDX_NODE  = 1
IDX_PATH  = 2
IDX_IGNORE_RESULT = 3


class RerouteException(Exception):
    def __init__(self, node, location:str):
        self.node = node
        self.location = location

class Node(object):
    def __init__(self, root, parent=None):
        self.root = root        # absolute root node
        self.parent = parent    # The parent node

        # Unaliased name of the GraphQL node
        self.name = None

        # GraphQL node alias
        self.alias = None

        # Child nodes, representing nested objects/relationships
        self.children = {}

        # The data elements queried at this node
        self.fields = []

        # Arguments passed to the GraphQL node
        self.args = {}

        # Yielded state (see the @graph yields param docs)
        self.state = {}

        # User-defined object that implements the Context interface,
        # performs authorization.
        self.context = None

        # The "return value" of the node's execution function,
        # merged into the parent node, if exists.
        self.result = {}

        # State generator. state can be passed down to child nodes.
        # this is set by nodes that have a corresponding Path with
        # yields == True.
        self._generator = None

        # Flag that indicates that the generator was instantiated
        self._has_state = False

        # Schema instance returned by Context.authorize method
        self.schema = None

        self._is_validated = False

    def __getitem__(self, key:str):
        return self.children.get(key)

    def __contains__(self, child_name:str):
        return child_name in self.children

    def reroute(self, dotted_path:str):
        raise RerouteException(self, dotted_path)

    @property
    def is_validated(self):
        return self._is_validated

    @classmethod
    def execute(cls, request, query, graph):
        """ Execute a GraphQL node.

            Args:
                - request: HTTP Request object from your web framework
                - query: GraphQL query string
                - graph: `pygql.graph.Graph` class reference
        """
        root_label = None
        root_node = cls.parse(query)
        root_path = graph.root

        # Enqueue the nodes inte query in depth-first order
        # and init their Contexts
        queue = cls._enqueue(request, root_label, root_node, root_path)
        while queue:
            label, node, path, ignore = queue.popleft()

            # Generate node.state for consumption by child nodes
            if path.yields and (not node._has_state):
                node._generate_state(request, path)
                continue

            if node == root_node:
                continue

            # call node.execute
            result = node._execute_node(request, path, ignore)

            # translate the result and store in parent
            if not ignore:
                node._process_result(result, label, path)

        return root_node.result

    @classmethod
    def _enqueue(cls, request, label, node, path, root_path=None, queue=None):

        if queue is None:
            queue = deque()  # base case
            root_path = path

        # ensure that some function has been registered by @graph for the
        # given path.
        if path.name != Path.ROOT_NAME and path.execute is None:
            raise NotFound(path.name)

        # If the node has state (i.e. "yields"), it means that node.execute
        # is a generator function; therefore, we must invoke the generator once
        # before any child nodes execute to ensure that parent state is
        # available to them. We will invoke the generator for a second and
        # final time in the usual depth-first order (i.e. after child nodes).
        if path.yields:
            assert not path.has_redirect
            queue.append((label, node, path, False))

        redirect_path = None
        if path.has_redirect:
            assert not path.yields
            redirect_path = root_path[path.redirect]

        # enqueue children
        for child_label, child_node in node.children.items():
            path_effective = redirect_path if path.has_redirect else path
            child_path = path_effective[child_node.name]
            cls._enqueue(request, child_label, child_node, child_path,
                         root_path, queue=queue)

        # NOTE:
        # since context is instantiated in depth-first order, note that
        # we would not have access to parent context from within any given
        # child context unless with instantiated each context in a first passed
        # preceding the node execution step.
        if path.context_class and (not node.is_validated):
            node.context = path.context_class(request, node)
            node.schema = node.context.authorize(request, node)
            node._validate(request, path)

        if path.has_redirect:
            queue.append((label, node, path, True))
            queue.append((label, node, redirect_path, False))
        else:
            queue.append((label, node, path, False))

        return queue


    def _process_result(self, result, label, path):
        if isinstance(result, dict):
            # We merge the node.result, which at this point already
            # contains items generated by its child nodes.
            if self.schema is not None:
                result = self.schema.dump(result)
            self.result.update(result)
        elif isinstance(result, (list, tuple, set)):
            # Nodes that return lists are responsible for converting
            # the results set by children, which should also be lists,
            # into a single merged array of dicts.
            if self.schema is not None:
                result = [self.schema.dump(x) for x in result]
            self.result = result
        else:
            raise InvalidResult(path.name, result)

        # insert child results into parent node result
        if self.parent is not None:
            self.parent.result[label] = self.result

    def _generate_state(self, request, path):
        self._generator = path.execute(request, self)
        self.state = self._generator.send(None)
        self._has_state = True

    def _execute_node(self, request, path, ignore):
        if not self._has_state:
            result = path.execute(request, self)
        else:
            # this is for paths that "yield"
            result = self._generator.send(None)
            self._has_state = False
        if result is None and not ignore:
            raise InvalidResult('result cannot be null')
        return result

    def _validate(self, request, path):
        # TODO: merge this logic to reduce number of times
        # fields are iterated through.
        self._validate_fields()
        self._validate_children()
        self._is_validated = True

    def _validate_fields(self):
        valid_names, unrec_names = self.schema.translate(self.fields)
        if unrec_names:
            raise FieldValidationError(self, unrec_names)
        self._raise_for_duplicate_fields(valid_names)
        self.fields = valid_names

    def _validate_children(self):
        # we use child path `name` attributes instead of the keys in
        # `children` because the keys are a mixture of valid field names
        # as well as field aliases; whereas path.name is always the field name.
        names = set(v.name for v in self.children.values())
        valid_names, unrec_names = self.schema.translate(names, nested=True)
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
            raise FieldAmbiguityError(self, duplicate_names)

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
