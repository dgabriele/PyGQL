import json


class PyGQL_Exception(Exception):
    """
    Base exception
    """
    code = 1
    default_payload = {
        'message': '',
        'data': {},
    }

    def __init__(self, custom_payload=None):
        payload = self.default_payload.copy()
        payload['code'] = self.code
        if payload is not None:
            payload.update(custom_payload)
        super(PyGQL_Exception, self).__init__(json.dumps(payload))


class FieldValidationError(PyGQL_Exception):
    code = 2
    default_payload = {
        'message': 'Unauthorized or unknown fields'
    }

    def __init__(self, node, field_names):
        super(FieldValidationError, self).__init__({
            'data': {
                'fields': list(field_names),
                'name': node.name,
                'alias': node.alias
            }
        })


class InvalidOperation(PyGQL_Exception):
    code = 3
    default_payload = {
        'message': 'invalid GraphQL node operation'
    }

    def __init__(self, op_name):
        super(InvalidOperation, self).__init__({
            'data': {
                'op': op_name
            }
        })


class FieldAmbiguityError(PyGQL_Exception):
    code = 3
    default_payload = {
        'message': 'ambiguous name or alias'
    }

    def __init__(self, node, field_name):
        super(FieldValidationError, self).__init__({
            'data': {
                'field': field_name,
                'name': node.name,
                'alias': node.alias
            }
        })


class InvalidResult(PyGQL_Exception):
    code = 4
    default_payload = {
        'message': 'unsupported return value data type; '
                   'expecting dict or iterable'
    }

    def __init__(self, path:str, result):
        super(InvalidResult, self).__init__({
            'data': {
                'path': path,
                'type': type(result).__name__
            }
        })


class NotFound(PyGQL_Exception):
    code = 4
    default_payload = {
        'message': 'path function not registered'
    }

    def __init__(self, path:str):
        super(NotFound, self).__init__({
            'data': {
                'path': path,
            }
        })
