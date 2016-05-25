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
        'message': 'You tried to query unrecognized fields.'
    }

    def __init__(self, alias, type_name, field_names):
        payload = {
            'data': {
                'fields': list(field_names),
                'name': type_name,
                'alias': alias
            }
        }
        super(FieldValidationError, self).__init__(payload)
