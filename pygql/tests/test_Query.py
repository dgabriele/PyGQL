import pytest

from pygql.query import Query

@pytest.fixture(scope='function')
def query_string():
    return '''{
        kitty:cat(id:"1001010") {color, name},
        fish(id: "3434434") {
            phylum, species, location {lng, lat}
        }
    }'''

@pytest.fixture(scope='function')
def query():
    root = Query(
        name='root',
        fields=None,
        children={
            'kitty': Query(
                name='cat',
                alias='kitty',
                args={'id': '1001010'},
                fields=['color', 'name'],
                children={},
            ),
            'fish': Query(
                name='fish',
                args={'id': '3434434'},
                fields=['phylum', 'species'],
                children={
                    'location': Query(
                        name='location',
                        args=None,
                        fields=['lng', 'lat'],
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
    assert query['fish']['location'].fields == ['lng', 'lat']


def test_parse(query_string, query):
    actual_query = Query.parse(query_string)
    assert 'kitty' in actual_query.children
    assert actual_query['kitty'].alias == 'kitty'
    assert actual_query['kitty'].name == 'cat'
    assert set(actual_query['kitty'].fields) == {'color', 'name'}
