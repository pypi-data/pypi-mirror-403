#  Copyright (C) 2022 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""
Contains HDF5 specific classes and methods to define class members as members
of HDF5 files
"""

from typing import Type

from ._readers import DataReader
from ._utils import _extract_type
from ._writers import DataWriter


def member(name: str = None, optional: bool = False, compression: str = None):
    """
    Define a class member as a member of a HDF5 file
    """
    return MemberDef(name, optional, compression)


#  pylint: disable=too-few-public-methods
class MemberDef:
    """
    Decorator to handle the transformation of HDF5 groups
    and datasets to pythonic objects
    """

    def __init__(self, name: str, optional: bool, compression: str):
        self.name = name
        self.property_name: str
        self.optional = optional
        self.compression = compression
        self.type: Type

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name
        self.property_name = name
        self.type = _extract_type(owner, name)

    def __get__(self, instance, obj_type=None):
        if instance is None:
            # attribute is accessed as a class attribute
            return self

        if hasattr(instance, "_data_reader"):
            reader: DataReader = getattr(instance, "_data_reader")
            return reader.read_member(instance, self.name, self.type, self.optional)

        if hasattr(instance, self.attr_name):
            return getattr(instance, self.attr_name)
        return None

    def __set__(self, instance, value):
        if not hasattr(instance, "_data_writer"):
            setattr(instance, self.attr_name, value)
            return

        writer: DataWriter = getattr(instance, "_data_writer")
        writer.write_member(self.name, self.type, value)

        if hasattr(instance, self.attr_name):
            delattr(instance, self.attr_name)

    @property
    def attr_name(self):
        """
        Name used to store the value in the owning object
        """
        return f"_v_{self.name}"
