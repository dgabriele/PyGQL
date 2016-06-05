from pygql import Schema
from pygql import Context

from . import graph


PHOTOS = [
    {'id': 'id1', 'url': 'http://example.com/1.jpg', 'caption': 'Eating'},
    {'id': 'id2', 'url': 'http://example.com/2.jpg', 'caption': 'Running'},
    {'id': 'id3', 'url': 'http://example.com/3.jpg', 'caption': 'Thinking'},
]

LOCATIONS = {
    'id1': {'lng': 130, 'lat': -27},
    'id2': {'lng': 132, 'lat': -17},
    'id3': {'lng': 138, 'lat': -23},
}


@graph(path='user')
def user(request, node):
    return {'name': 'Einstein', 'id': 'abc124'}


@graph(path='user.photos', yields=True)
def user_photos(request, node):
    # pass ids of photos to child nodes, which will be
    # accessed via node.parent.state
    yield {
        'ids': ['id1', 'id2', 'id3']
    }

    # now that chil nodes have executed, merge location
    # objects back into the photo objects
    photos = PHOTOS.copy()
    for key, child in node.children.items():
        for photo, value in zip(photos, child.result):
            photo[key] = value

    yield photos


@graph(path='user.photos.location')
def photo_locations(request, node):
    # return list of location objects back to parent
    return [LOCATIONS[i].copy() for i in node.parent.state['ids']]
