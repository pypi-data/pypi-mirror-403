import contextlib
import struct
from collections.abc import Mapping
from io import BufferedWriter
import numpy as np
from numpy.lib import format
from numpy.compat import os_fspath
from sortedcontainers import SortedDict


class NpkFile(Mapping):
    def __init__(self, fid: BufferedWriter, keys, sizes, reader, mmap_mode):
        self.fid = fid
        self.reader = reader
        self.mmap_mode = mmap_mode
        self.sizes = SortedDict()
        for i, key in enumerate(keys):
            self.sizes.setdefault(key, sizes[i])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.fid.close()

    def __del__(self):
        self.close()

    # Implement the Mapping ABC
    def __iter__(self):
        return iter(self.sizes)

    def __len__(self):
        return len(self.sizes)
    
    def __get_from_key(self, key):
        self.fid.seek(self.sizes[key])
        return self.reader(self.fid, self.mmap_mode)

    def __getitem__(self, index):
        if isinstance(index, str):
            key = index
            return self.__get_from_key(key)
        else:
            key = index[0]
            return self.__get_from_key(key)[index[1:]]


def save(file, **kwds):
    if hasattr(file, 'write'):
        file_ctx = contextlib.nullcontext(file)
    else:
        file = os_fspath(file)
        if not file.endswith('.npk'):
            file = file + '.npk'
        file_ctx = open(file, "wb")

    keys = np.array([key for key in kwds])
    sizes = np.empty(len(keys) + 1, dtype=int)
    
    with file_ctx as fid:
        for i, (_, arr) in enumerate(kwds.items()):
            sizes[i] = fid.tell()
            arr = np.asanyarray(arr)
            format.write_array(fid, arr, allow_pickle=True,
                            pickle_kwargs=None)
        sizes[-1] = fid.tell()
        format.write_array(fid, keys, allow_pickle=True,
                        pickle_kwargs=None)
        sizes_tell = fid.tell()
        format.write_array(fid, sizes, allow_pickle=True,
                        pickle_kwargs=None)
        fid.write(struct.pack('Q', sizes_tell))


def load(file, mmap_mode=None,
         encoding='ASCII', *, max_header_size=format._MAX_HEADER_SIZE):
    if encoding not in ('ASCII', 'latin1', 'bytes'):
        raise ValueError("encoding must be 'ASCII', 'latin1', or 'bytes'")

    if hasattr(file, 'read'):
        fid = file
    else:
        fid = open(os_fspath(file), "rb")
    
    def read_numpy(fid, mmap_mode):
        N = len(format.MAGIC_PREFIX)
        magic = fid.read(N)
        # If the file size is less than N, we need to make sure not
        # to seek past the beginning of the file
        fid.seek(-min(N, len(magic)), 1)  # back-up
        if magic == format.MAGIC_PREFIX:
            if mmap_mode:
                version = format.read_magic(fid)
                shape, fortran_order, dtype = format._read_array_header(
                        fid, version, max_header_size=max_header_size)
                if dtype.hasobject:
                    msg = "Array can't be memory-mapped: Python objects in dtype."
                    raise ValueError(msg)
                offset = fid.tell()
                if fortran_order:
                    order = 'F'
                else:
                    order = 'C'
                return np.memmap(fid, dtype=dtype, shape=shape, order=order,
                        mode=mmap_mode, offset=offset)
            else:
                return format.read_array(fid, allow_pickle=True,
                                        pickle_kwargs=None,
                                        max_header_size=max_header_size)
    
    int_size = struct.calcsize('Q')
    fid.seek(-int_size, 2)
    sizes_tell = struct.unpack('Q', fid.read(int_size))[0]
    fid.seek(sizes_tell)
    sizes = read_numpy(fid, False)
    fid.seek(sizes[-1])
    keys = read_numpy(fid, False)
    sizes = sizes[:-1]
    
    return NpkFile(fid, keys, sizes, read_numpy, mmap_mode)