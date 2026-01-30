#  Copyright (C) 2022 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""
Class wrappers for lists and dictionaries monitoring changes of itself and notifying
the registered event handler about these changes.
"""

from typing import Any


class MonitoredWrapper:
    """
    A wrapper monitoring changes of itself and notifying the registered event handler
    about changes.
    """

    def __init__(self, event, instance):
        self._event = event
        self._instance = instance

    def __setitem__(self, key, value):
        self._instance.__setitem__(key, value)
        self._event(self._instance)

    def __getitem__(self, item):
        return self._instance.__getitem__(item)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ["_instance", "_event"]:
            object.__setattr__(self, name, value)
        else:
            self._instance.__setattr__(name, value)
            self._event(self._instance)

    def __getattribute__(self, name):
        if name in ["_instance", "_event"]:
            return object.__getattribute__(self, name)
        attr = object.__getattribute__(self._instance, name)
        if hasattr(attr, "__call__"):

            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                self._event(self._instance)
                return result

            return wrapper

        return attr
