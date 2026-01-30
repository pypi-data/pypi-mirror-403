#  Copyright (C) 2022 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""
Contains classes to handle reading
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class FileReader(Generic[T], ABC):
    """
    Abstract file reader
    """

    @abstractmethod
    def read(self) -> T:
        """
        Read the opened file into a pythonic representation specified by target_type.
        Will automatically figure out if target_type is a dict or a regular object
        """

    @abstractmethod
    def close(self):
        """
        Close the underlying file
        """

    def load(self, instance: T):
        """
        Load all the data from the underlying HDF file
        to preserve it in the objects after closing the
        file.
        """

    def __enter__(self):
        return self.read()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()


class DataReader(ABC):
    """
    Abstract data reader
    """

    @abstractmethod
    def read_member(self, obj, name: str, target_type, optional: bool):
        """
        Read given member from underlying file
        """

    @abstractmethod
    def read_attribute(self, name, owner, from_member, optional):
        """
        Read given attribute from underlying file
        """
