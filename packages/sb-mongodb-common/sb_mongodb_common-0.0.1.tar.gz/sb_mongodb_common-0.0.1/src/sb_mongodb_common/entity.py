import inspect

from .utils import get_custom_type


class Entity:
    _mapped_fields = {}

    @classmethod
    def get_mapped_fields(cls):
        if len(cls._mapped_fields) == 0:
            entity_class_fields = {}
            for kls in cls.__mro__:
                for name, attr in inspect.getmembers(kls):
                    if "MappedField" in type(attr).__name__ and name not in entity_class_fields:
                        entity_class_fields[name] = attr
                        # verify type
                        if type(attr.field_type) == str:
                            attr.field_type = get_custom_type(attr.field_type)

            cls._mapped_fields = entity_class_fields
        return cls._mapped_fields
