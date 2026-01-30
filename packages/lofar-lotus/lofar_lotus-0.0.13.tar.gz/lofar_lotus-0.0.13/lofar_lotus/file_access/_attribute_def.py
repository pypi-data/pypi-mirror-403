#  Copyright (C) 2022 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""
Contains HDF5 specific classes and methods to define class members as an HDF attribute
"""

from typing import Any, Type

from ._readers import DataReader
from ._utils import _extract_type
from ._writers import DataWriter


def attribute(name: str = None, optional: bool = False, from_member: str = None):
    """
    Define a class member as an attribute within a HDF5 file
    """
    return AttributeDef(name, optional, from_member)


#  pylint: disable=too-few-public-methods
class AttributeDef:
    """
    Decorator to extract attributes of HDF5 groups and datasets to pythonic objects
    """

    def __init__(self, name: str, optional: bool, from_member: str = None):
        self.name = name
        self.property_name: str
        self.from_member = from_member
        self.optional = optional
        self.owner: Any
        self.type: Type

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name
        self.property_name = name
        self.owner = owner
        self.type = _extract_type(owner, name)

    def __set__(self, instance, value):
        setattr(instance, self.attr_name, value)

        if hasattr(instance, "_data_writer"):
            writer: DataWriter = getattr(instance, "_data_writer")
            writer.write_attribute(
                instance, self.name, self.owner, self.from_member, self.optional, value
            )

    def __get__(self, instance, obj_type=None):
        if instance is None:
            # attribute is accessed as a class attribute
            return self

        if hasattr(instance, self.attr_name):
            return getattr(instance, self.attr_name)

        if hasattr(instance, "_data_reader"):
            reader: DataReader = getattr(instance, "_data_reader")
            attr = reader.read_attribute(
                self.name, self.owner, self.from_member, self.optional
            )
            setattr(instance, self.attr_name, attr)
            return attr
        return None

    @property
    def attr_name(self):
        """
        Name used to store the value in the owning object
        """
        if self.from_member is None:
            return f"_a_{self.name}"
        return f"_a_{self.from_member}_{self.name}"
