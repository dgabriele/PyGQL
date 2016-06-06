import pytest

from pygql.schema import Schema, Field

@pytest.fixture(scope='function')
def roles():
    return ['anonymous', 'user', 'staff']


@pytest.fixture(scope='function')
def schema(roles):
    class TestSchema(Schema):
        id = Field('public_id', roles=roles)
        name = Field('name', roles=roles)
        email = Field('email', roles=['staff'])
        company = Field('company', nested=True, roles=['staff'])
        location = Field('location', nested=True)
        age = Field()

    return TestSchema()


def test_schema_internal_structure(schema, roles):
    for k in ['id', 'name', 'email', 'age']:
        assert k in schema.scalar.keys
        assert k in schema  # testing __getitem__

    for k in roles:
        assert k in schema.scalar.authorized_field_maps

    assert set([_ for _ in schema.scalar.authorized_field_maps['anonymous']]) == {'id', 'name', 'age'}
    assert set([_ for _ in schema.scalar.authorized_field_maps['user']]) == {'id', 'name', 'age'}
    assert set([_ for _ in schema.scalar.authorized_field_maps['staff']]) == {'id', 'name', 'email', 'age'}

    assert set([_ for _ in schema.scalar.authorized_field_maps['anonymous'].values()]) == {'public_id', 'name', 'age'}
    assert set([_ for _ in schema.scalar.authorized_field_maps['user'].values()]) == {'public_id', 'name', 'age'}
    assert set([_ for _ in schema.scalar.authorized_field_maps['staff'].values()]) == {'public_id', 'name', 'email', 'age'}

    assert schema.scalar.keys == {'id', 'name', 'email', 'age'}

    assert schema.inverse == {
        'public_id': 'id',
        'name': 'name',
        'age': 'age',
        'email': 'email',
        'company': 'company',
        'location': 'location',
    }

    assert set(schema.scalar.public_field_map) == {'age'}

    assert set(schema.nested.public_field_map) == {'location'}
    assert dict(schema.nested.authorized_field_maps) == {
        'staff': {'company': 'company', 'location': 'location'}
    }


def test_translate(schema):
    fields, unrecognized = schema.translate([])
    assert fields == []
    assert unrecognized == []

    fields, unrecognized = schema.translate(['id', 'name', 'email', 'age'])
    assert set(fields) == {'age'}
    assert set(unrecognized) == {'id', 'name', 'email'}

    fields, unrecognized = schema.translate(['id', 'name', 'email', 'age'], role='anonymous')
    assert set(fields) == {'public_id', 'name', 'age'}
    assert set(unrecognized) == {'email'}

    fields, unrecognized = schema.translate(['id', 'name', 'email', 'age'], role='staff')
    assert set(fields) == {'public_id', 'name', 'age', 'email'}
    assert not set(unrecognized)


def test_dump(schema):
    assert schema.dump({}) == {}
    assert schema.dump({
        'public_id': '123',
        'name': 'Publius',
        'email': 'virgil@gmail.com',
        'age': 3000
    }) == {
        'id': '123',
        'name': 'Publius',
        'email': 'virgil@gmail.com',
        'age': 3000
    }
