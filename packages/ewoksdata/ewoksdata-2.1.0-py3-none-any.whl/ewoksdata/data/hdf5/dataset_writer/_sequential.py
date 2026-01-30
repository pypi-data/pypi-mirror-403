import time
from typing import List
from typing import Optional

import h5py
import numpy
from numpy.typing import ArrayLike

from ..config import guess_dataset_config
from ..types import StrictPositiveIntegral
from ._base import DatasetWriterBase


class DatasetWriter(DatasetWriterBase):
    """Append arrays of the same shape to a new HDF5 dataset in a sequential manner.

    Instead of creating a dataset with the :code:`h5py` API

    .. code-block::python

        h5group["mydataset"] = [[1,2,3], [4,5,6], [7,8,9]]

    it can be done like this

    .. code-block::python

        with DatasetWriter(h5group, "mydataset") as writer:
            writer.add_point([1,2,3])
            writer.add_points([[4,5,6], [7,8,9]])

    Chunk size determination, chunk-aligned writing, compression and flushing is handled.
    """

    def __init__(
        self,
        parent: h5py.Group,
        name: str,
        npoints: Optional[StrictPositiveIntegral] = None,
        attrs: Optional[dict] = None,
        flush_period: Optional[float] = None,
        overwrite: bool = False,
    ) -> None:
        super().__init__(parent, name, attrs=attrs, flush_period=flush_period)
        self._npoints = npoints
        self._overwrite = overwrite
        self._chunked: bool = False
        self._npoints_added: int = 0

        self._buffer: List[ArrayLike] = list()
        self._chunk_size: int = 0
        self._flushed_size: int = 0

    def _create_dataset(self, first_data_point: numpy.ndarray) -> h5py.Dataset:
        scan_shape = (self._npoints,)
        detector_shape = first_data_point.shape
        dtype = first_data_point.dtype

        if self._npoints is None:
            shape = (1,) + detector_shape
            max_shape = scan_shape + detector_shape
        else:
            shape = scan_shape + detector_shape
            max_shape = None

        options = guess_dataset_config(
            scan_shape, detector_shape, dtype=dtype, max_shape=max_shape
        )
        options.update(
            shape=shape,
            dtype=dtype,
            fillvalue=numpy.nan,  # converts to 0 for integers
        )

        if max_shape:
            options["maxshape"] = max_shape

        if options["chunks"]:
            self._chunked = True
            self._chunk_size = options["chunks"][0]

        if self._overwrite and self._name in self._parent:
            del self._parent[self._name]

        dset = self._parent.create_dataset(self._name, **options)
        if self._attrs:
            dset.attrs.update(self._attrs)
        return dset

    @property
    def npoints_added(self) -> int:
        return self._npoints_added

    def add_point(self, data: ArrayLike) -> bool:
        """Append one array to the dataset."""
        if self._dataset is None:
            self._dataset = self._create_dataset(data)

        self._buffer.append(data)
        self._npoints_added += 1
        return self.flush_buffer(align=True)

    def add_points(self, data: ArrayLike) -> bool:
        """Append several arrays at once to the dataset."""
        if self._dataset is None:
            self._dataset = self._create_dataset(data[0])

        self._buffer.extend(data)
        self._npoints_added += len(data)
        return self.flush_buffer(align=True)

    def flush_buffer(self, align: bool = False) -> bool:
        # Determine how many points to flush
        chunk_size = len(self._buffer)

        if self._flush_time_expired():
            flush_size = chunk_size
        elif align and self._chunked:
            n = chunk_size + (self._flushed_size % self._chunk_size)
            flush_size = n // self._chunk_size * self._chunk_size
            flush_size = min(flush_size, chunk_size)
        else:
            flush_size = chunk_size

        if flush_size == 0:
            return False

        # Enlarge the dataset when needed
        nalloc = self._dataset.shape[0]
        istart = self._flushed_size
        flushed_size = istart + flush_size
        if self._chunked and flushed_size > nalloc:
            self._dataset.resize(flushed_size, axis=0)

        # Copy data from buffer to HDF5
        self._dataset[istart : istart + flush_size] = self._buffer[:flush_size]

        # Remove copied data from buffer
        self._buffer = self._buffer[flush_size:]
        self._flushed_size = flushed_size

        self._flush_hdf5()
        self._last_flush = time.time()
        return True
