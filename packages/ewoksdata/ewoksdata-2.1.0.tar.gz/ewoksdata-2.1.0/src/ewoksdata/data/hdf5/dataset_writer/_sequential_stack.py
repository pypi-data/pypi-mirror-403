import time
from typing import List
from typing import Optional

import h5py
import numpy
from numpy.typing import ArrayLike

from ..config import guess_dataset_config
from ..types import StrictPositiveIntegral
from ._base import DatasetWriterBase


class StackDatasetWriter(DatasetWriterBase):
    """Append arrays of the same shape to each item of a new HDF5 dataset
    in a sequential manner per item. So each item of the HDF5 dataset is a
    stack to which we can append data in a sequential manner.

    Instead of creating a dataset with the :code:`h5py` API

    .. code-block::python

        stack0 = [[1,2,3], [4,5,6], [7,8,9]]
        stack1 = [[10,11,12], [13,14,15], [16,17,18]]
        h5group["mydataset"] = [stack0, stack1]

    it can be done like this

    .. code-block::python

        with StackDatasetWriter(h5group, "mydataset") as writer:
            writer.add_point([1,2,3], 0)
            writer.add_point([10,11,12], 1)
            writer.add_points([[13,14,15], [16,17,18]], 1)
            writer.add_points([[4,5,6], [7,8,9]], 0)

    Chunk size determination, chunk-aligned writing, compression and flushing is handled.
    """

    def __init__(
        self,
        parent: h5py.Group,
        name: str,
        npoints: Optional[StrictPositiveIntegral] = None,
        nstack: Optional[StrictPositiveIntegral] = None,
        attrs: Optional[dict] = None,
        flush_period: Optional[float] = None,
    ) -> None:
        super().__init__(parent, name, attrs=attrs, flush_period=flush_period)
        self._npoints = npoints
        self._chunked: bool = False
        self._nstack = nstack

        self._buffers: List[List[ArrayLike]] = list()
        self._chunk_size: ArrayLike = numpy.zeros(2, dtype=int)
        self._flushed_size_dim1: ArrayLike = numpy.array(list(), dtype=int)

    def _create_dataset(
        self, first_data_point: ArrayLike, stack_index: int
    ) -> h5py.Dataset:
        scan_shape = (self._nstack, self._npoints)
        first_data_point = numpy.asarray(first_data_point)
        detector_shape = first_data_point.shape
        dtype = first_data_point.dtype

        if self._nstack is None or self._npoints is None:
            shape = (stack_index + 1, 1) + detector_shape
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
            self._chunk_size = numpy.array(options["chunks"][:2], dtype=int)

        dset = self._parent.create_dataset(self._name, **options)
        if self._attrs:
            dset.attrs.update(self._attrs)
        return dset

    def add_point(self, data: ArrayLike, stack_index: int) -> bool:
        """Append one array to one stack of the dataset."""
        if self._dataset is None:
            self._dataset = self._create_dataset(data, stack_index)

        buffer = self._get_buffer(stack_index)
        buffer.append(data)
        return self.flush_buffer(align=True)

    def add_points(self, data: ArrayLike, stack_index: int) -> bool:
        """Append several arrays at once to one stack of the dataset."""
        if self._dataset is None:
            self._dataset = self._create_dataset(data[0], stack_index)

        buffer = self._get_buffer(stack_index)
        buffer.extend(data)
        return self.flush_buffer(align=True)

    def flush_buffer(self, align: bool = False) -> bool:
        # Determine how many points to flush for each buffer in the stack
        chunk_sizes = numpy.array([len(buffer) for buffer in self._buffers])
        flushed_size_dim1 = self._flushed_size_dim1
        size_dim0 = len(chunk_sizes)
        assert size_dim0 == len(
            flushed_size_dim1
        ), "Number of buffers and number of flushed dim1 points must be the same"

        chunk_size_dim0, chunk_size_dim1 = self._chunk_size[:2]
        if chunk_size_dim0 == 0:
            chunk_size_dim0 = size_dim0

        if self._flush_time_expired():
            flush_sizes = chunk_sizes
        elif align and self._chunked:
            size_dim0 = size_dim0 // chunk_size_dim0 * chunk_size_dim0
            chunk_sizes = chunk_sizes[:size_dim0]
            flushed_size_dim1 = flushed_size_dim1[:size_dim0]
            if size_dim0:
                n1 = chunk_sizes + (flushed_size_dim1 % chunk_size_dim1)
                flush_sizes = n1 // chunk_size_dim1 * chunk_size_dim1
                flush_sizes = numpy.minimum(flush_sizes, chunk_sizes)
                for i0_chunk0 in range(0, size_dim0, chunk_size_dim0):
                    flush_sizes[i0_chunk0 : i0_chunk0 + chunk_size_dim0] = min(
                        flush_sizes[i0_chunk0 : i0_chunk0 + chunk_size_dim0]
                    )
            else:
                flush_sizes = list()
        else:
            flush_sizes = chunk_sizes

        if not any(flush_sizes):
            return False

        # Enlarge the dataset when needed
        nalloc = self._dataset.shape[:2]
        istart_dim1 = flushed_size_dim1
        flushed_size_dim1 = istart_dim1 + flush_sizes
        nalloc_new = numpy.array([size_dim0, max(flushed_size_dim1)])
        if self._chunked and any(nalloc_new > nalloc):
            for axis, n in enumerate(nalloc_new):
                self._dataset.resize(n, axis=axis)

        # Copy data from buffer to HDF5
        for i0_chunk0 in range(0, size_dim0, chunk_size_dim0):
            idx_dim0 = slice(i0_chunk0, i0_chunk0 + chunk_size_dim0)
            buffers = self._buffers[idx_dim0]

            flush_sizes_dim1 = flush_sizes[idx_dim0]
            non_ragged_buffers = len(set(flush_sizes_dim1)) == 1

            istart0_dim1 = istart_dim1[idx_dim0]
            non_ragged_destination = len(set(istart0_dim1)) == 1

            if non_ragged_destination and non_ragged_buffers:
                data = [buffer[: flush_sizes_dim1[0]] for buffer in buffers]
                idx_dim1 = slice(istart0_dim1[0], istart0_dim1[0] + flush_sizes_dim1[0])
                self._dataset[idx_dim0, idx_dim1] = data
            else:
                for buffer, i_dim0, istart_dim1, i_flush_size_dim1 in zip(
                    buffers,
                    range(i0_chunk0, i0_chunk0 + chunk_size_dim0),
                    istart0_dim1,
                    flush_sizes_dim1,
                ):
                    self._dataset[
                        i_dim0, istart_dim1 : istart_dim1 + i_flush_size_dim1, ...
                    ] = buffer[:i_flush_size_dim1]

        # Remove copied data from buffer
        for i0 in range(size_dim0):
            self._buffers[i0] = self._buffers[i0][flush_sizes[i0] :]
            self._flushed_size_dim1[i0] = flushed_size_dim1[i0]

        self._flush_hdf5()
        self._last_flush = time.time()
        return True

    def _get_buffer(self, stack_index: int) -> List[ArrayLike]:
        # Add stack buffers when needed
        for _ in range(max(stack_index - len(self._buffers) + 1, 0)):
            self._buffers.append(list())
            self._flushed_size_dim1 = numpy.append(self._flushed_size_dim1, 0)
        return self._buffers[stack_index]
