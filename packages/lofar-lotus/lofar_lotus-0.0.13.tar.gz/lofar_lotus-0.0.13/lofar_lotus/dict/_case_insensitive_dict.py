#  Copyright (C) 2025 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""Provides a special dictionary with case-insensitive keys"""

import abc
from collections import UserDict
from typing import List, Tuple, Union

from ._case_insensitive_string import CaseInsensitiveString


def _case_insensitive_comprehend_keys(data: dict) -> List[CaseInsensitiveString]:
    return [CaseInsensitiveString(key) for key in data]


def _case_insensitive_comprehend_items(
    data: dict,
) -> List[Tuple[CaseInsensitiveString, any]]:
    return [(CaseInsensitiveString(key), value) for key, value in data.items()]


class ReversibleIterator:
    """Reversible iterator using instance of self method

    See real-python for yield iterator method:
        https://realpython.com/python-reverse-list/#the-special-method-__reversed__
    """

    def __init__(self, data: List, start: int, stop: int, step: int):
        self.data = data
        self.current = start
        self.stop = stop
        self.step = step

    def __iter__(self):
        return self

    def __next__(self):
        if self.current == self.stop:
            raise StopIteration

        elem = self.data[self.current]
        self.current += self.step
        return elem

    def __reversed__(self):
        return ReversibleIterator(self.data, self.stop, self.current, -1)


class AbstractReversibleView(abc.ABC):
    """An abstract reversible view"""

    def __init__(self, data: UserDict):
        self.data = data
        self.len = len(data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data})"

    @abc.abstractmethod
    def __iter__(self):
        pass

    @abc.abstractmethod
    def __reversed__(self):
        pass


class ReversibleItemsView(AbstractReversibleView):
    """Reversible view on items"""

    def __iter__(self):
        return ReversibleIterator(
            _case_insensitive_comprehend_items(self.data.data), 0, self.len, 1
        )

    def __reversed__(self):
        return ReversibleIterator(
            _case_insensitive_comprehend_items(self.data.data), self.len - 1, -1, -1
        )


class ReversibleKeysView(AbstractReversibleView):
    """Reversible view on keys"""

    def __iter__(self):
        return ReversibleIterator(
            _case_insensitive_comprehend_keys(self.data.data), 0, self.len, 1
        )

    def __reversed__(self):
        return ReversibleIterator(
            _case_insensitive_comprehend_keys(self.data.data), self.len - 1, -1, -1
        )


class ReversibleValuesView(AbstractReversibleView):
    """Reversible view on values"""

    def __iter__(self):
        return ReversibleIterator(list(self.data.data.values()), 0, self.len, 1)

    def __reversed__(self):
        return ReversibleIterator(list(self.data.data.values()), self.len - 1, -1, -1)


class CaseInsensitiveDict(UserDict):
    """Special dictionary that ignores key casing if string

    While UserDict is the least performant / flexible it ensures __set_item__ and
    __get_item__ are used in all code paths reducing LoC severely.

    Background reference:
        https://realpython.com/inherit-python-dict/#creating-dictionary-like-classes-in-python

    Alternative (should this stop working at some point):
        https://github.com/DeveloperRSquared/case-insensitive-dict/blob/main/case_insensitive_dict/case_insensitive_dict.py
    """

    def __setitem__(self, key, value):
        if isinstance(key, str):
            key = CaseInsensitiveString(key)
        super().__setitem__(key, value)

    def __getitem__(self, key: Union[int, str]):
        if isinstance(key, str):
            key = CaseInsensitiveString(key)
        return super().__getitem__(key)

    def __iter__(self):
        return ReversibleIterator(
            _case_insensitive_comprehend_keys(self.data), 0, len(self.data), 1
        )

    def __contains__(self, key):
        if isinstance(key, str):
            key = CaseInsensitiveString(key)
        return super().__contains__(key)

    def keys(self) -> ReversibleKeysView:
        return ReversibleKeysView(self)

    def values(self) -> ReversibleValuesView:
        return ReversibleValuesView(self)

    def items(self) -> ReversibleItemsView:
        return ReversibleItemsView(self)
