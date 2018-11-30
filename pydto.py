import json
from typing import Union

import type_checker


class DTODescriptor:
    __slots__ = "_immutable", "_type", "_field", "_validator", "_dto_class_name", "_coerce"

    def __init__(self, dto_class_name: str, field: str, type_: type, immutable: bool = True,
                 validator: callable = None, coerce: callable = None):
        self._dto_class_name = dto_class_name
        self._field = field
        self._type = type_
        self._immutable = immutable
        if validator and not callable(validator):
            raise TypeError("Validator for field '{}' of DTO class '{}' is not callable".format(field,
                                                                                                self._dto_class_name))
        self._validator = validator

        if coerce and not callable(coerce):
            raise TypeError("Coerce for field '{}' of DTO class '{}' is not callable".format(field,
                                                                                             self._dto_class_name))
        self._coerce = coerce

    def __get__(self, instance, owner):
        if not instance._initialized_dto_descriptors[self._field]:
            raise AttributeError("Field '{}' of DTO class '{} is not initialized".format(self._field,
                                                                                         self._dto_class_name))
        return instance._dto_descriptors_values.get(self._field)

    def _check_value(self, value):
        if self._validator is not None and not self._validator(value):
            raise ValueError(
                "{} is not a valid value for the field '{}' or DTO class {} using its validator".format(
                    value, self._field, self._dto_class_name))

    def __set__(self, instance: 'DTO', value):
        if self._coerce:
            value = self._coerce(value)

        if self._immutable and instance._initialized_dto_descriptors[self._field]:
            raise AttributeError("Immutable attribute '{}' of DTO class '{}' cannot be changed".
                                 format(self._field, instance.__class__.__name__))

        _type = type_checker._check_type_dto_descriptor(self, value)

        if _type is type(None):
            instance._dto_descriptors_values[self._field] = None

        else:
            self._check_value(value)
            instance._dto_descriptors_values[self._field] = value

        instance._initialized_dto_descriptors[self._field] = True


class DTOMeta(type):

    def __init__(cls, name, bases, namespace, partial: bool = False):
        super().__init__(name, bases, namespace)

    def __new__(cls, name, bases, class_dict, partial: bool = False):

        descriptors = {k: v for k, v in class_dict.items() if isinstance(v, tuple)}
        _ = [class_dict.pop(k, None) for k in descriptors]

        class_dict['__slots__'] = set(list(descriptors.keys()) + ['_dto_descriptors',
                                                                  '_initialized_dto_descriptors',
                                                                  '_dto_descriptors_values',
                                                                  '_field_validators',
                                                                  '_partial'])

        new_type = type.__new__(cls, name, bases, class_dict)
        new_type._dto_descriptors = descriptors
        new_type._field_validators = {}
        new_type._partial = partial
        for attr in new_type._dto_descriptors:
            attr_type = new_type._dto_descriptors[attr][0]
            descriptor_args = {}
            if len(new_type._dto_descriptors[attr]) > 1:
                descriptor_args = new_type._dto_descriptors[attr][1]
            setattr(new_type, attr, DTODescriptor(dto_class_name=name, field=attr, type_=attr_type, **descriptor_args))
        return new_type

    def __instancecheck__(self, inst: Union['DTO', dict]):
        if type(inst) == type(self):
            return True
        if isinstance(inst, dict):
            # Comparing a dictionary and a DTO
            if not self._partial:
                if len(inst.keys()) != len(self._dto_descriptors.keys()):
                    return False
                for k, v in inst.items():
                    try:
                        type_checker._check_type(self._dto_descriptors[k][0], v)
                    except TypeError:
                        return False
            else:
                for k in self._dto_descriptors.keys():
                    try:
                        type_checker._check_type(self._dto_descriptors[k][0], inst[k])
                    except (TypeError, KeyError):
                        return False
            return True
        return False


class DTO(metaclass=DTOMeta):

    def __new__(cls, *args, **kwargs):
        obj = super(DTO, cls).__new__(cls)
        obj._initialized_dto_descriptors = dict()
        obj._dto_descriptors_values = dict()
        for attr in obj._dto_descriptors:
            obj._initialized_dto_descriptors[attr] = False
        return obj

    @classmethod
    def from_dict(cls, dictionary: dict):
        return cls(dictionary)

    @classmethod
    def from_json(cls, json_string: str):
        dict_ = json.loads(json_string)
        return cls.from_dict(dict_)

    def __setattr__(self, attr, val):
        try:
            obj = object.__getattribute__(self, attr)
        except AttributeError:
            object.__setattr__(self, attr, val)
        else:
            if hasattr(obj, '__set__'):
                obj.__set__(self, val)
            else:
                object.__setattr__(self, attr, val)

    def __getattribute__(self, attr):
        obj = object.__getattribute__(self, attr)
        if hasattr(obj, '__get__'):
            return obj.__get__(self, type(self))
        return obj

    def __init__(self, dto_dict: dict):
        if not self._partial:
            assert set(dto_dict.keys()) == set(self._dto_descriptors.keys()), \
                "DTO {} fields {} mismatch the dictionary keys {}".format(self.__class__.__qualname__,
                                                                          list(self._dto_descriptors.keys()),
                                                                          list(dto_dict.keys()))
        else:
            assert set(self._dto_descriptors.keys()) < set(dto_dict.keys()), \
                "Partial DTO {} fields {} are missing in the dictionary keys".format(self.__class__.__qualname__,
                                                                                     set(self._dto_descriptors.keys())
                                                                                     > set(dto_dict.keys()))

        for k in self._dto_descriptors.keys():
            setattr(self, k, dto_dict[k])

    def to_dict(self):
        dto_dict = {}
        for k, v in self._dto_descriptors_values.items():
            if issubclass(v.__class__, DTO):
                dto_dict[k] = v.to_dict()
            else:
                dto_dict[k] = v
        return dto_dict

    def __str__(self):
        return '{}({})'.format(self.__class__.__qualname__, str(self._dto_descriptors_values))

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if type(self) != type(other):
            return False

        if set(self._dto_descriptors.keys()) != set(other._dto_descriptors.keys()):
            return False

        for k in self._dto_descriptors:
            if getattr(self, k) != getattr(other, k):
                return False

        return True
