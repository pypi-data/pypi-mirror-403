#  Copyright (C) 2025 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""
Utils to handle transformation of HDF5 specific classes to pythonic objects
"""

from collections.abc import MutableMapping
from inspect import get_annotations, getattr_static
from typing import Type, TypeVar, get_origin

from numpy import ndarray

T = TypeVar("T")


def _assert_is_dataset(value):
    if issubclass(type(value), MutableMapping):
        raise TypeError(
            f"Only <Dataset> can be mappet do primitive type while "
            f"value is of type <{type(value).__name__}>"
        )


def _assert_is_group(value):
    if not issubclass(type(value), MutableMapping):
        raise TypeError(
            "Only Group can be mapped to <object> while value"
            f" is of type <{type(value).__name__}>"
        )


def _is_attachable(target_type: Type[T]):
    origin_type = get_origin(target_type)
    if origin_type is dict:
        return False
    if get_origin(target_type) is list:
        return False
    if target_type is ndarray:
        return False
    return True


def _attach_object(target_type: Type[T], instance):
    for cls in target_type.mro():
        annotations = get_annotations(cls)

        for annotation in annotations:
            attr = getattr_static(target_type, annotation)
            if hasattr(instance, attr.attr_name):
                setattr(instance, attr.property_name, getattr(instance, attr.attr_name))
