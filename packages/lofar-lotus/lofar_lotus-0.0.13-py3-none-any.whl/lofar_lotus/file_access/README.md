# HDF file reader

## Define a model

The data structure of the HDF file is defined by python objects using decorators. Currently, there are two decorators
available:

1. `member`: defines a class property to be an HDF group or dataset depending on the type.
2. `attribute`: defines a class property to be an HDF attribute on a group or dataset.

### Dataset definition

A basic data structure to define the HDF file looks like this:

```python
class Data:
    list_of_ints: List[int] = member()
    list_of_floats: List[float] = member()
    numpy_array: ndarray = member()
```

It is important to always use type hints. It not only makes the classes more self-explanatory during development it is
also
important for the file reader to guesstimate the right action to perform.

In this first example we only used arrays and lists. These types always map to a dataset within HDF. By default,
the reader is looking for a dataset with the name of the variable, if the dataset is named differently it can be
overwritten
by specifying the `name` parameter: `member(name='other_name_then_variable')`. Also, all members are required by
default.
If they don't appear in the HDF file an error is thrown. This behavior can be changed by specifying the `optional`
parameter:
`member(optional=True)`.

### Group definition

HDF supports to arrange the data in groups. Groups can be defined as additional classes:

```python
class SubGroup:
    list_of_ints: List[int] = member()

class Data:
    sub_group: SubGroup = member()

```

Additionally, all additional settings apply in the same way as they do for datasets.

### Dictionaries

A special case is the `dict`. It allows to read a set of groups or datasets using the name of the group or dataset as
the key.

```python
class Data:
    data_dict: Dict[str, List[int]] = member()
```

### Attribute definition

Attributes in a HDF file can appear on groups as well as on datasets and can be defined by using `attribute()`:

```python
class Data:
    an_attr: str = attribute()
```

The file reader will look for an attribute with the name `an_attr` on the group that is represented by the class `Data`.
The name of the attribute can be overwritten by specifying the `name` parameter: `attribute(name='other_name')`. All
attributes
are required by default and will cause an exception to be thrown if they are not available. This behavior can be changed
by specifying the `optional` parameter:
`attribute(optional=True)`.

In HDF also datasets can contain attributes. Since they are usually mapped to primitive types it would not be possible
to access
these attributes. Therefor `attribute` allows to specify another member in the class by setting `from_member`.

## Read a HDF file

A file can be read using `read_hdf5`:

```python
with read_hdf5('file_name.h5', Data) as data:
    a = data.an_attr
```

## Create a HDF file

A file can be created using `create_hdf5` - existing files will be overwritten:

```python
with create_hdf5('file_name.h5', Data) as data:
    data.an_attr = "data"
```

NB:

1. Writes are cached until `flush()` is called or the file is closed.
2. Reading back attributes will read them from disk.

## Change a HDF file

A file can be changed using `open_hdf5` - the file must exist:

```python
with open_hdf5('file_name.h5', Data) as data:
    data.an_attr = "new value"
```

## Data write behaviour

### members
All changes to members of the object are immediately written to the underlying HDF file. Therefore, altering the object
should be minimized to have no performance degradation.

### attributes
Attributes are written if `flush()` is invoked on the `FileWriter` or when the `with` scope is exited. This behaviour is
necessary because attributes depend on the underlying members. Therefore, the attributes can only be written after
the members.
