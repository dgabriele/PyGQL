from pygql import Schema
from pygql import Context

from . import graph


@graph(path='user')
def user(request, node):
    user_id = node.args.get('id')
    if user_id == 'ABC123':
        return {'name': 'Kirkegard'}
    return {'name': 'Kant'}


@graph(path='user.location')
def user_location(request, node):
    return {
        'lng': 180,
        'lat': -81
    }


@graph(path='project')
def project(request, node):
    return {
        'status': 'draft'
    }


@graph(path='project.assignee', redirect='user')
def project_assignee(request, node):
    # Adapt node args to what the redirect path expects. By redirecting
    # from assignee to user, we can reuse not only the 'user' path but
    # also 'user.location'.
    project_id = node.parent.args['id']
    node.args['id'] = fetch_assignee_id(project_id)


def fetch_assignee_id(project_id):
    return 'ABC123'
