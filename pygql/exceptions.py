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
        'message': 'You tried to query unrecognized fields'
    }

    def __init__(self, alias, type_name, field_names):
        super(FieldValidationError, self).__init__({
            'data': {
                'fields': list(field_names),
                'name': type_name,
                'alias': alias
            }
        })


class InvalidOperation(PyGQL_Exception):
    code = 3
    default_payload = {
        'message': 'Invalid GraphQL query operation'
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
        'message': 'not authorized'
    }

    def __init__(self, message=None):
        super(AuthorizationError, self).__init__({
            'message': message if message else 'not authorized',
            'data': {
                # TODO: include query information
            }
        })
