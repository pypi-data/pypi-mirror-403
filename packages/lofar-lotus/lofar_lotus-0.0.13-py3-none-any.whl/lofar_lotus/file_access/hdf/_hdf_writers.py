#  Copyright (C) 2024 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""
Contains classes to handle file writing
"""

from inspect import getattr_static
from typing import Dict, Type, TypeVar, get_origin

import h5py
from numpy import ndarray

from .._lazy_dict import LazyDict
from .._utils import _extract_base_type, _wrap
from .._writers import DataWriter, FileWriter
from ._hdf5_utils import (
    _assert_is_dataset,
    _assert_is_group,
    _attach_object,
    _is_attachable,
)
from ._hdf_readers import HdfDataReader, HdfFileReader

T = TypeVar("T")


class HdfFileWriter(HdfFileReader[T], FileWriter[T]):
    """
    HDF5 specific file writer
    """

    def __init__(self, name, target_type, create):
        self._create = create
        self.writers: list[HdfDataWriter] = []
        super().__init__(name, target_type)

    def _open_file(self, name):
        self._hdf5_file = h5py.File(name, "w" if self._create else "a")
        self._is_closed = False

    def flush(self):
        """
        Flush all registered writers
        """
        for writer in self.writers:
            writer.flush()
        self.writers = []

        if not self._is_closed:
            self._hdf5_file.flush()

    def close(self):
        self.flush()
        super().close()

    def open(self) -> T:
        return self.create()

    def create(self) -> T:
        """
        Create the object representing the HDF file
        """
        data_writer = HdfDataWriter(self, self._hdf5_file)
        reader = HdfDataWriter.detect_reader(self._target_type, data_writer)
        obj = reader(self._hdf5_file)
        if isinstance(obj, dict):
            obj = _wrap(
                self._target_type,
                obj,
                lambda value: HdfDataWriter.write_dict(
                    self._target_type,
                    self._hdf5_file,
                    value,
                    data_writer,
                ),
            )
        try:
            setattr(obj, "_data_writer", data_writer)
        except AttributeError:
            pass
        return obj


class HdfDataWriter(HdfDataReader, DataWriter):
    """
    HDF data writer
    """

    def read_member(self, obj, name, target_type, optional):
        instance = super().read_member(obj, name, target_type, optional)

        return _wrap(
            target_type,
            instance,
            lambda a: setattr(obj, name, a),
        )

    @classmethod
    def _read_dict(
        cls, target_type: Type[T], value, dict_type, data_reader: "HdfDataWriter"
    ) -> Dict[str, T]:
        obj = super()._read_dict(target_type, value, dict_type, data_reader)
        data_writer = cls(data_reader.file_writer, value)
        if dict_type is not dict:
            setattr(obj, "_data_writer", data_writer)
        if isinstance(obj, LazyDict):
            obj.setup_write(
                lambda k, v: cls.write_dict_member(
                    target_type, value, k, v, data_writer
                )
            )
        return obj

    @classmethod
    def _read_object(
        cls, target_type: Type[T], value, file_reader: "HdfDataWriter"
    ) -> T:
        obj = super()._read_object(target_type, value, file_reader)
        setattr(obj, "_data_writer", cls(file_reader.file_writer, value))
        return obj

    def __init__(self, file_writer: HdfFileWriter, data):
        self.file_writer = file_writer
        self.file_writer.writers.append(self)
        self.data = data
        self.write_actions = []
        super().__init__(file_writer, data)
        super(HdfDataReader, self).__init__()

    def write_member(self, name: str, target_type: Type[T], value):
        data = self.data
        writer = self.detect_writer(target_type, self)
        writer(data, name, value)

        if _is_attachable(target_type):
            _attach_object(target_type, value)

    def flush(self):
        """
        Executed all pending write actions
        """
        for action in self.write_actions:
            action()

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def write_attribute(self, instance, name, owner, from_member, optional, value):
        self.write_actions.append(
            lambda: self._write_attribute(name, owner, from_member, value)
        )

    def _write_attribute(self, name, owner, from_member, value):
        attrs = self._resolve_attrs(owner, from_member)

        try:
            attrs[name] = value
        except (RuntimeError, TypeError) as exc:
            raise ValueError(
                f"Failed to write to attribute {self.data.name}.{name}"
            ) from exc

    def _resolve_attrs(self, owner, from_member):
        """
        Finds the right attribute to write into
        """
        if from_member is None:
            return self.data.attrs

        member = getattr_static(owner, from_member)
        return self.data[member.name].attrs

    @classmethod
    def detect_writer(cls, target_type, data_writer: "HdfDataWriter"):
        """
        Detect required writer based on expected type
        """
        origin_type = get_origin(target_type)
        if origin_type is dict:
            return lambda data, key, value: cls._write_dict_group(
                target_type, data, key, value, data_writer
            )
        if get_origin(target_type) is list:
            return lambda data, key, value: cls._write_ndarray(
                list, data, key, value, data_writer
            )
        if target_type is ndarray or issubclass(target_type, ndarray):
            return lambda data, key, value: cls._write_ndarray(
                target_type, data, key, value, data_writer
            )
        if issubclass(target_type, dict):
            return lambda data, key, value: cls._write_dict_group(
                target_type, data, key, value, data_writer
            )
        return lambda data, key, value: cls._write_object(
            target_type, data, key, value, data_writer
        )

    @classmethod
    def _write_ndarray(
        cls, target_type: Type[T], data, key, value, data_writer: "HdfDataWriter"
    ):
        _assert_is_group(data)
        if key in data:
            _assert_is_dataset(data[key])
            del data[key]

        # GZIP filter ("gzip"). Available with every installation of HDF5.
        # compression_opts sets the compression level and may be an integer from 0 to 9,
        # default is 4.
        # https://docs.h5py.org/en/stable/high/dataset.html#lossless-compression-filters
        data.create_dataset(key, data=value, compression="gzip", compression_opts=9)
        if target_type is not ndarray and issubclass(target_type, ndarray):
            data_writer = cls(data_writer.file_writer, data[key])
            setattr(value, "_data_writer", data_writer)
            setattr(value, "_data_reader", data_writer)
            _attach_object(target_type, value)

    @classmethod
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def _write_dict_group(
        cls, target_type: Type[T], data, key, value, data_writer: "HdfDataWriter"
    ):
        _assert_is_group(data)
        if key not in data:
            data.create_group(key)

        try:
            data_writer = cls(data_writer.file_writer, data[key])
            setattr(value, "_data_writer", data_writer)
            setattr(value, "_data_reader", data_writer)
            _attach_object(target_type, value)
        except AttributeError:
            pass

        cls.write_dict(
            target_type, data[key], value, cls(data_writer.file_writer, data[key])
        )

    @classmethod
    def write_dict(
        cls, target_type: Type[T], data, value, data_writer: "HdfDataWriter"
    ):
        """
        Write given dictionary to given data group
        """
        _assert_is_group(data)
        for k in data.keys():
            if k not in value:
                del data[k]
        writer = HdfDataWriter.detect_writer(
            _extract_base_type(target_type), data_writer
        )

        for k in value.keys():
            writer(data, k, value[k])

    @classmethod
    def write_dict_member(
        cls, target_type: Type[T], data, key, value, data_writer: "HdfDataWriter"
    ):
        """
        Write single given dictionary member to given data group
        """
        _assert_is_group(data)
        writer = HdfDataWriter.detect_writer(target_type, data_writer)
        writer(data, key, value)

    @classmethod
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def _write_object(
        cls, target_type: Type[T], data, key, value: T, data_writer: "HdfDataWriter"
    ):
        _assert_is_group(data)
        if key in data:
            _assert_is_group(data[key])
        else:
            data.create_group(key)
            data_writer = cls(data_writer.file_writer, data[key])
            setattr(value, "_data_writer", data_writer)
            setattr(value, "_data_reader", data_writer)
            _attach_object(target_type, value)


def open_hdf5(name, target_type: Type[T]) -> FileWriter[T]:
    """
    Open a HDF5 file by name/path
    """
    return HdfFileWriter[T](name, target_type, False)


def create_hdf5(name, target_type: Type[T]) -> FileWriter[T]:
    """
    Create a HDF5 file by name/path
    """
    return HdfFileWriter[T](name, target_type, True)
