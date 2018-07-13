import json
from typing import Union


class DTODescriptor:
    __slots__ = "_immutable", "_type", "_field", "_validator", "_dto_class_name"

    def __init__(self, dto_class_name: str, field: str, type_: type, immutable: bool = True,
                 validator: callable = None):
        self._dto_class_name = dto_class_name
        self._field = field
        self._type = type_
        self._immutable = immutable
        if validator and not callable(validator):
            raise TypeError("Validator for field '{}' of DTO class '{}' is not callable".format(field,
                                                                                                self._dto_class_name))
        self._validator = validator

    def __get__(self, instance, type):
        if not instance._initialized_dto_descriptors[self._field]:
            raise AttributeError("Not Initialized")
        return instance._dto_descriptors_values.get(self._field)

    def __set__(self, instance, value):

        if self._immutable and instance._initialized_dto_descriptors[self._field]:
            raise AttributeError("Immutable attribute '{}' of DTO class '{}' cannot be changed".format(self._field,
                                                                                                       instance.__class__.__name__))

        if type(self._type) is Union.__class__:
            matched_types = list(filter(lambda t: isinstance(value, t), self._type.__args__))
            if not matched_types:
                raise TypeError("value {} is not of type {}".format(value, self._type))

            else:
                _type = matched_types[0]
                if _type is type(None):
                    instance._dto_descriptors_values[self._field] = None
                else:
                    if self._validator and not self._validator(value):
                        ValueError(
                            "{} is not a valid value for the field '{}' or DTO class {} using its validator".format(
                                value, self._field, self._dto_class_name))
                    instance._dto_descriptors_values[self._field] = _type(value)

        else:
            if not isinstance(value, self._type):
                raise TypeError(
                    "Value {} is not of type '{}' (DTO class '{}', field '{}')".format(value, self._type.__qualname__,
                                                                                       instance.__class__.__name__,
                                                                                       self._field))
            if self._validator and not self._validator(value):
                raise ValueError(
                    "{} is not a valid value field '{}' or DTO class {} using its validator".format(value, self._field,
                                                                                                    self._dto_class_name))
            instance._dto_descriptors_values[self._field] = self._type(value)

        instance._initialized_dto_descriptors[self._field] = True


class DTOMeta(type):

    def __new__(cls, name, bases, class_dict, immutable: bool = True):

        descriptors = {k: v for k, v in class_dict.items() if isinstance(v, tuple)}
        _ = [class_dict.pop(k, None) for k in descriptors]

        class_dict['__slots__'] = set(list(descriptors.keys()) + ['_dto_descriptors',
                                                                  '_initialized_dto_descriptors',
                                                                  '_dto_descriptors_values',
                                                                  '_field_validators'])

        new_type = type.__new__(cls, name, bases, class_dict)
        new_type._dto_descriptors = descriptors
        new_type._field_validators = {}
        for attr in new_type._dto_descriptors:
            attr_type = new_type._dto_descriptors[attr][0]
            descriptor_args = {}
            if len(new_type._dto_descriptors[attr]) > 1:
                descriptor_args = new_type._dto_descriptors[attr][1]
            setattr(new_type, attr, DTODescriptor(dto_class_name=name, field=attr, type_=attr_type, **descriptor_args))
        return new_type

    def __instancecheck__(self, inst):
        if type(inst) == type(self):
            return True
        if isinstance(inst, dict):
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
        assert set(dto_dict.keys()) == set(self._dto_descriptors.keys()), \
            "DTO {} fields {} mismatch the dictionary keys {}".format(self.__class__.__qualname__,
                                                                      list(self._dto_descriptors.keys()),
                                                                      list(dto_dict.keys()))
        for k, v in dto_dict.items():
            setattr(self, k, v)

    def to_dict(self):
        dto_dict = {}
        for k, v in self._dto_descriptors_values.items():
            if issubclass(v.__class__, DTO):
                dto_dict[k] = v.to_dict()
            else:
                dto_dict[k] = v
        return dto_dict

    def __str__(self):
        return str(self._dto_descriptors_values)

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
