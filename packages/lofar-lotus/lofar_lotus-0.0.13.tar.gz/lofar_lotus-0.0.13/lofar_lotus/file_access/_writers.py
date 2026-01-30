#  Copyright (C) 2023 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""
Contains classes to handle file writing
"""

from abc import ABC, abstractmethod
from typing import TypeVar

from ._readers import DataReader, FileReader

T = TypeVar("T")


class FileWriter(FileReader[T], ABC):
    """
    Abstract file writer
    """

    def __init__(self, create):
        self._create = create

    @abstractmethod
    def create(self) -> T:
        """
        Create the object representing the file
        """

    @abstractmethod
    def open(self) -> T:
        """
        Create the object representing the file
        """

    def __enter__(self):
        if self._create:
            return self.create()
        return self.open()


class DataWriter(DataReader, ABC):
    """
    Abstract data writer
    """

    @abstractmethod
    def write_member(self, name: str, target_type, value):
        """
        Write given member to underlying file
        """

    @abstractmethod
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def write_attribute(self, instance, name, owner, from_member, optional, value):
        """
        Write given attribute to underlying file
        """
