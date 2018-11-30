import datetime
from typing import Union, Dict, List
import pydto


def _raise_value_not_valid_type(dto_descriptor, value):
    raise TypeError("Value '{}' is not of type '{}' (field '{}' of DTO class '{}')".format(value,
                                                                                           dto_descriptor._type,
                                                                                           dto_descriptor._field,
                                                                                           dto_descriptor._dto_class_name))


def _check_type_dto_descriptor(dto_descriptor, value):
    try:
        inferred_type = _check_type(dto_descriptor._type, value)
        return inferred_type
    except TypeError:
        _raise_value_not_valid_type(dto_descriptor, value)


def _check_type(type_, value):
    if type(type_) is Union.__class__:
        return _check_type_Union(type_, value)

    elif type_ in [str, float, int, bool, complex, dict, list, datetime.datetime]:
        if not isinstance(value, type_):
            raise TypeError
        return type_

    elif isinstance(type_, pydto.DTO):
        if not isinstance(value, type_):
            raise TypeError
        return type_

    elif issubclass(type_, Dict):
        return _check_type_Dict(type_, value)

    elif issubclass(type_, List):
        return _check_type_List(type_, value)

    elif issubclass(type_, None.__class__):
        return _check_type_None(type_, value)

    else:
        raise NotImplementedError("Type checker for type {} is not implemented".format(type_))


def _check_type_None(type_, value):
    if value is not None:
        raise TypeError
    return type_


def _check_type_Union(type_, value):
    if hasattr(type_, '__args__'):
        # Python 3.6+
        union_args = type_.__args__
    else:
        # Python 3.5
        union_args = type_.__union_params__

    matched_types = []
    for arg in union_args:
        try:
            arg = _check_type(arg, value)
        except TypeError:
            pass
        else:
            matched_types.append(arg)

    if not matched_types:
        raise TypeError

    assert len(
        matched_types) == 1, "Value {} matches multiple subtype of type {}".format(value, type_)

    return _check_type(matched_types[0], value)


def _check_type_Dict(type_, value):
    if not isinstance(value, dict):
        raise TypeError

    key_value_types = getattr(type_, "__args__", type_.__parameters__)

    if key_value_types is not None:
        key_type, value_type = key_value_types

        for k, v in value.items():
            _ = _check_type(key_type, v)
            _ = _check_type(value_type, k)

        return type_

    else:
        return type_


def _check_type_List(type_, value):
    if not isinstance(value, list):
        raise TypeError

    value_type = getattr(type_, "__args__", type_.__parameters__)
    if value_type is not None:
        value_type = value_type[0]

    if value_type is not None:
        # If a list has a subtype but the list is empty should it be treated as type error?!
        # if len(value) == 0:
        #     raise TypeError
        for v in value:
            _ = _check_type(value_type, v)

        return type_

    else:
        return type_
