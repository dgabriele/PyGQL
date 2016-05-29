import pytest

from pygql.node import Node

@pytest.fixture(scope='function')
def node_string():
    return '''{
        kitty:cat(id:"1001010") {color, name},
        fish(id: "3434434") {
            phylum, species, location {lng, lat}
        }
    }'''

@pytest.fixture(scope='function')
def node():
    root = Node(
        name='root',
        fields=None,
        children={
            'kitty': Node(
                name='cat',
                alias='kitty',
                args={'id': '1001010'},
                fields=['color', 'name'],
                children={},
            ),
            'fish': Node(
                name='fish',
                args={'id': '3434434'},
                fields=['phylum', 'species'],
                children={
                    'location': Node(
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


def test_getitem(node):
    assert node['fish']['location'].fields == ['lng', 'lat']


def test_parse(node_string, node):
    actual_node = Node.parse(node_string)
    assert 'kitty' in actual_node.children
    assert actual_node['kitty'].alias == 'kitty'
    assert actual_node['kitty'].name == 'cat'
    assert set(actual_node['kitty'].fields) == {'color', 'name'}
