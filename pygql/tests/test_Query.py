import pytest

from pygql.query import Query


@pytest.fixture(scope='function')
def query():
    root = Query(
        name='root',
        props=None,
        children={
            'cat': Query(
                name='cat',
                args={'id': '1001010'},
                props=['color', 'name'],
                children={},
            ),
            'fish': Query(
                name='fish',
                args={'id': '3434434'},
                props=['phylum', 'species'],
                children={
                    'location': Query(
                        name='location',
                        args=None,
                        props=['lng', 'lat'],
                        children={},
                    )
                }
            )
        }
    )

    def set_parent(node):
        for child in node.children.values():
            child.parent = node
            set_parent(child)

    set_parent(root)
    return root


def test_getitem(query):
    assert query['fish']['location'].props == ['lng', 'lat']
