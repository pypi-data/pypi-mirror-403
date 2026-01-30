#  Copyright (C) 2024 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""
Contains classes to handle file reading
"""

import inspect
import weakref
from inspect import getattr_static
from typing import Dict, List, Type, TypeVar, get_origin

import h5py
from numpy import ndarray, zeros

from .._attribute_def import AttributeDef
from .._lazy_dict import lazy_dict
from .._member_def import MemberDef
from .._readers import DataReader, FileReader
from .._utils import _extract_base_type
from ._hdf5_utils import (
    _assert_is_dataset,
    _assert_is_group,
)

T = TypeVar("T")


class HdfFileReader(FileReader[T]):
    """
    HDF5 specific file reader
    """

    def __init__(self, name, target_type):
        self.file_name = name
        self._is_closed = None
        self._target_type = target_type
        self._open_file(name)
        self._references: List[weakref] = []

    def __del__(self):
        self.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _open_file(self, name):
        self._hdf5_file = h5py.File(name, "r")
        self._is_closed = False

    def read(self) -> T:
        """
        Read the opened file into a pythonic representation specified by target_type.
        Will automatically figure out if target_type is a dict or a regular object
        """
        reader = HdfDataReader.detect_reader(
            self._target_type, HdfDataReader(self, self._hdf5_file)
        )
        return reader(self._hdf5_file)

    def close(self):
        """
        Close the underlying HDF file
        """
        for ref in self._references:
            obj = ref()
            if obj is not None:
                self._detach_object(obj)
        self._references = []

        if not self._is_closed:
            self._is_closed = True
            self._hdf5_file.close()
            del self._hdf5_file

    def load(self, instance: T):
        """
        Load all the data from the underlying HDF file
        to preserve it in the objects after closing the
        file.
        """
        self._references.append(weakref.ref(instance))
        target_type = type(instance)
        for annotation in [
            m[0] for m in inspect.getmembers(instance) if not m[0].startswith("_")
        ]:
            attr = inspect.getattr_static(target_type, annotation)
            if isinstance(attr, (MemberDef, AttributeDef)):
                setattr(instance, attr.attr_name, getattr(instance, attr.property_name))

    def _detach_object(self, instance):
        if not hasattr(instance, "_data_reader"):
            return
        delattr(instance, "_data_reader")
        for attr in [
            m[0]
            for m in inspect.getmembers(instance)
            if not m[0].startswith("_") and m[0] != "T"
        ]:
            item = getattr(instance, attr)
            item_type = type(item)
            if (
                item is not None
                and item is object
                and not (item_type is ndarray or item_type is str)
            ):
                self._detach_object(item)


class HdfDataReader(DataReader):
    """
    HDF data reader
    """

    def __init__(self, file_reader: HdfFileReader, data):
        self.file_reader = file_reader
        self.data = data

    def read_member(self, obj, name, target_type, optional):
        if name not in self.data:
            if optional:
                return None
            raise KeyError(f"Could not find required key {name}")

        reader = self.detect_reader(
            target_type, self.__class__(self.file_reader, self.data[name])
        )
        return reader(self.data[name])

    def read_attribute(self, name, owner, from_member, optional):
        attrs: dict
        if from_member is None:
            attrs = self.data.attrs
        else:
            member = getattr_static(owner, from_member)
            attrs = self.data[member.name].attrs

        if name not in attrs:
            if optional:
                return None
            raise KeyError(f"Could not find required attribute key {name}")

        return attrs[name]

    @classmethod
    def _read_object(
        cls, target_type: Type[T], value, file_reader: "HdfDataReader"
    ) -> T:
        _assert_is_group(value)
        obj = target_type()
        setattr(obj, "_data_reader", cls(file_reader.file_reader, value))
        return obj

    @staticmethod
    def _read_list(value):
        _assert_is_dataset(value)
        return list(value[:])

    @classmethod
    def _read_ndarray(cls, target_type: Type[T], value, file_reader: "HdfDataReader"):
        _assert_is_dataset(value)
        nd_value = zeros(value.shape, value.dtype)
        # convert the data set to a numpy array
        value.read_direct(nd_value)
        if target_type is ndarray:
            return nd_value
        obj = nd_value.view(target_type)
        setattr(obj, "_data_reader", cls(file_reader.file_reader, value))
        return obj

    @classmethod
    def _read_dict(
        cls, target_type: Type[T], value, dict_type, data_reader: "HdfDataReader"
    ) -> Dict[str, T]:
        reader = cls.detect_reader(target_type, data_reader)
        result = lazy_dict(dict_type, lambda k: reader(value[k]))
        for k in value.keys():
            result[k] = lambda n=k: reader(value[n])
        if dict_type is not dict:
            setattr(result, "_data_reader", cls(data_reader.file_reader, value))
        return result

    @classmethod
    def detect_reader(cls, target_type, data_reader: "HdfDataReader"):
        """
        Detect the required reader based on expected type
        """
        origin_type = get_origin(target_type)
        if origin_type is dict:
            return lambda value: cls._read_dict(
                _extract_base_type(target_type), value, dict, data_reader
            )
        if get_origin(target_type) is list:
            return cls._read_list
        if issubclass(target_type, ndarray):
            return lambda value: cls._read_ndarray(target_type, value, data_reader)
        if issubclass(target_type, dict):
            return lambda value: cls._read_dict(
                _extract_base_type(target_type), value, target_type, data_reader
            )
        return lambda value: cls._read_object(target_type, value, data_reader)


def read_hdf5(name, target_type: Type[T]) -> FileReader[T]:
    """
    Open a HDF5 file by name/path
    """
    return HdfFileReader[T](name, target_type)
