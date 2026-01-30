#  Copyright (C) 2024 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""
General utils
"""

from typing import Optional, Type, get_args, get_origin, get_type_hints

from numpy import ndarray

from ._monitoring import MonitoredWrapper


def _extract_type(owner: object, name: str) -> Optional[Type]:
    type_hints = get_type_hints(owner)
    return type_hints[name] if name in type_hints else None


def _extract_base_type(target_type: Type):
    args = get_args(target_type)
    if len(args) >= 2:
        return args[1]

    return [
        get_args(b)[1] for b in target_type.__orig_bases__ if get_origin(b) is dict
    ][0]


def _wrap(target_type, value, callback):
    if get_origin(target_type) is list:
        return MonitoredWrapper(callback, value)
    if target_type is ndarray:
        return MonitoredWrapper(callback, value)
    return value
