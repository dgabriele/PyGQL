from pygql import Schema
from pygql import Context

from . import graph


@graph(path='user')
def user(request, node):
    user_id = node.args.get('id')
    if user_id == 'ABC123':
        return {'name': 'Kirkegard'}
    return {'name': 'Unknown'}


@graph(path='project.assignee')
def project_assignee(request, node):
    project_id = node.parent.args['id']
    node.args['id'] = query_assignee_id(project_id)
    node.reroute('user')


def query_assignee_id(project_id):
    return 'ABC123'
