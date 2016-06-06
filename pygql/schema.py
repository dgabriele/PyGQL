from collections import defaultdict


__all__ = ['Field', 'Schema']


class Field(object):
    def __init__(self, name:str=None, nested=False, roles:list=None):
        self.name = name
        self.nested = nested
        self.roles = roles or []


class Schema(object):
    def __init__(self, default_role=None):
        self._default_role = default_role

        # inverse mapping from internal field names to public names
        self.inverse = {}

        # collections of data structures for fields corresponding to
        # scalar properties of the schema
        self.scalar = SchemaFields()

        # same as above but for nested fields, i.e. relationships
        self.nested = SchemaFields()

        # initialize self.scalar and self.nested
        for k, v in self.__class__.__dict__.items():
            if (not k.startswith('__')) and isinstance(v, Field):
                if v.name is None:
                    v.name = k
                self.inverse[v.name] = k
                fields = self.nested if v.nested else self.scalar
                fields.keys.add(k)
                if v.roles:
                    for role in v.roles:
                        fields.authorized_field_maps[role][k] = v.name
                else:
                    fields.public_field_map[k] = v.name

        # add public field maps to all authorized field maps
        if self.scalar.public_field_map:
            for role, field_map in self.scalar.authorized_field_maps.items():
                field_map.update(self.scalar.public_field_map)
        if self.nested.public_field_map:
            for role, field_map in self.nested.authorized_field_maps.items():
                field_map.update(self.nested.public_field_map)

    def __contains__(self, key):
        return (key in self.scalar.keys) or (key in self.nested.keys)

    def set_default_role(self, role):
        self._default_role = role

    def translate(self, keys:list, nested=False, role:str=None):
        valid = []
        unrecognized = []
        role = role if role else self._default_role
        fields = self.nested if nested else self.scalar
        if role is not None:
            field_map = fields.authorized_field_maps[role]
        else:
            field_map = fields.public_field_map
        for k_in in keys:
            k_out = field_map.get(k_in)
            if k_out is not None:
                valid.append(k_out)
            else:
                unrecognized.append(k_in)
        return (valid, unrecognized)

    def dump(self, obj:dict):
        return {
            self.inverse[k]: v for k, v in obj.items()
        }


class SchemaFields(object):
    def __init__(self):
        # map from role to field map
        self.authorized_field_maps = defaultdict(dict)

        # field map for fields with no assigned roles
        self.public_field_map = {}

        # all field names regardless of role
        self.keys = set()
