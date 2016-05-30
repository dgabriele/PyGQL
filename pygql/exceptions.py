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
        'message': 'Invalid GraphQL node operation'
    }

    def __init__(self, op_name):
        super(InvalidOperation, self).__init__({
            'data': {
                'op': op_name
            }
        })

class AuthorizationError(PyGQL_Exception):
    code = 4
    default_payload = {
        'message': 'Not authorized'
    }

    def __init__(self, message=None):
        super(AuthorizationError, self).__init__({
            'message': message if message else 'not authorized',
            'data': {
                # TODO: include node information
            }
        })


class AmbiguousFieldError(PyGQL_Exception):
    code = 2
    default_payload = {
        'message': 'Ambiguous name or alias'
    }

    def __init__(self, node, field_name):
        super(FieldValidationError, self).__init__({
            'data': {
                'field': field_name,
                'name': node.name,
                'alias': node.alias
            }
        })
