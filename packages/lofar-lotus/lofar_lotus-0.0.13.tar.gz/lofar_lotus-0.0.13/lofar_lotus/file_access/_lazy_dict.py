#  Copyright (C) 2023 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""
Provides a dictionary that dynamically resolves its values to reduce memory usage
"""

from abc import abstractmethod
from typing import Dict, Type, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class LazyDict:
    """
    Lazy evaluated dictionary
    """

    @abstractmethod
    def setup_write(self, writer):
        """
        Set up the lazy dict to support write actions
        """

    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "setup_write")
            and callable(subclass.setup_write)
            or NotImplemented
        )


def lazy_dict(base_dict: Type[Dict[K, V]], reader):
    """
    Dynamically derive lazy dict of given type
    """

    class LazyDictImpl(base_dict, LazyDict):
        """
        Implementation of the lazy dict dynamically derived from base dict
        """

        def __init__(self, reader, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._reader = reader
            self._writer = None

        def __setitem__(self, item, value):
            if callable(value):
                super().__setitem__(item, value)
                return

            # write value somewhere
            if self._writer is not None:
                self._writer(item, value)

            super().__setitem__(item, lambda: self._reader(item))

        def __getitem__(self, item):
            return super().__getitem__(item)()

        def items(self):
            """D.items() -> a set-like object providing a view on D's items"""
            for key, value in super().items():
                yield key, value()

        def setup_write(self, writer):
            self._writer = writer

    return LazyDictImpl(reader)
