import datetime
from typing import Union, Dict, List, Tuple, Set, Sequence, Optional
import pydto


def _raise_value_not_valid_type(dto_descriptor, value):
    raise TypeError("Value {} is not of type {} (field '{}' of DTO class '{}')".format(value,
                                                                                       dto_descriptor._field,
                                                                                       dto_descriptor._dto_class_name,
                                                                                       dto_descriptor._type))


def _check_type_dto_descriptor(dto_descriptor, value):
    try:
        inferred_type = _check_type(dto_descriptor._type, value)
        return inferred_type
    except TypeError:
        _raise_value_not_valid_type(dto_descriptor, value)


def _check_type(type_, value):
    if type(type_) is Union.__class__:
        _check_type_Union(type_, value)

    elif type_ in [str, float, int, bool, complex, dict, datetime.datetime]:
        if not isinstance(value, type_):
            raise TypeError
        return type_

    elif isinstance(type_, pydto.DTO):
        if not isinstance(value, type_):
            raise TypeError
        return type_

    elif type(type_) is Dict.__class__:
        _check_type_Dict(type_, value)

    else:
        raise NotImplementedError("Type checker for type {} is not implemented".format(type_))


def _check_type_Union(type_, value):
    if hasattr(type_, '__args__'):
        # Python 3.6+
        union_args = type_.__args__
    else:
        # Python 3.5
        union_args = type_.__union_params__

    matched_types = list(filter(lambda t: isinstance(value, t), union_args))
    if not matched_types:
        raise TypeError

    assert len(
        matched_types) == 1, "Value {} matches multiple subtype of type {}".format(value, type_)

    return matched_types[0]


def _check_type_Dict(dto_descriptor, value):

    if not isinstance(value, dict):
        _raise_value_not_valid_type(dto_descriptor, value)

    key_type, value_type = getattr(dto_descriptor._type, "__args__", dto_descriptor._type.__parameters__)

    for k, v in value.items():
        _check_type(key_type, v)
        _check_type(value_type, k)