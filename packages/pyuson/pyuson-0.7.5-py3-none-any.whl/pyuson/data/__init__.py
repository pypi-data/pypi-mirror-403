"""
The data module.

Provides classes to store data as NeXus groups with the `nexusformat` package.

NeXus groups are similar to HDF5 groups : an object that can host datasets and other
groups, supporting attributes giving metadata about the group and datasets. Datasets in
NeXus terminology are referred to as fields.

NeXus groups are used to store data in a dict-like fashion, but with a hierarchical
structure that can pooled together within a `root` group, that can be easily written
to a standard HDF5 file.

`nexusformat` is used instead of `h5py` directly because it automatically creates
attributes so that the output file is NeXus-compliant.

See Also
--------
The NeXus Data Format : https://www.nexusformat.org/
Python Interface to NeXus : https://nexpy.github.io/nexpy/pythonshell.html
The underlying `h5py` library : https://docs.h5py.org/en/stable/index.html
"""

from ._data import DataProcessed, DataRaw

__all__ = ["DataProcessed", "DataRaw"]
