import logging
import time
from typing import List
from typing import Optional

import h5py
import numpy
from numpy.typing import ArrayLike

from ..config import guess_dataset_config
from ..types import StrictPositiveIntegral
from ._base import DatasetWriterBase

logger = logging.getLogger(__name__)


class IndexedStackDatasetWriter(DatasetWriterBase):
    """Append arrays of the same shape to each item of a new HDF5 dataset
    in a potentially non-sequential manner per item. So each item of the HDF5 dataset is a
    stack to which we can append data in a sequential manner.

    Instead of creating a dataset with the :code:`h5py` API

    .. code-block::python

        stack0 = [[1,2,3], [4,5,6], [7,8,9]]
        stack1 = [[10,11,12], [13,14,15], [16,17,18]]
        h5group["mydataset"] = [stack0, stack1]

    it can be done like this

    .. code-block::python

        with IndexedStackDatasetWriter(h5group, "mydataset") as writer:
            writer.add_point([4,5,6], 0, 1)
            writer.add_point([13,14,15], 1, 1)
            writer.add_points([[10,11,12], [16,17,18]], [1, 1], [0, 2])
            writer.add_points([[1,2,3], [7,8,9]], [0, 0], [0, 2])

    Chunk size determination, compression and flushing is handled.
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
        self._nstack = nstack
        self._buffer: List[tuple[int, int, ArrayLike]] = []

    def _create_dataset(
        self, first_data_point: ArrayLike, stack_index: int
    ) -> h5py.Dataset:
        scan_shape = (self._nstack, self._npoints)
        first_data_point = numpy.asarray(first_data_point)
        detector_shape = first_data_point.shape
        dtype = first_data_point.dtype

        if self._nstack is None or self._npoints is None:
            shape = (1, 1) + detector_shape
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

        dset = self._parent.create_dataset(self._name, **options)
        if self._attrs:
            dset.attrs.update(self._attrs)
        return dset

    def add_point(self, data: ArrayLike, stack_index: int, point_index: int) -> bool:
        """Append one array to one stack of the dataset."""
        if self._dataset is None:
            self._dataset = self._create_dataset(data, stack_index)

        self._buffer.append((stack_index, point_index, data))
        return self.flush_buffer()

    def add_points(
        self,
        data: ArrayLike,
        stack_indices: ArrayLike,
        point_indices: ArrayLike,
    ) -> bool:
        """Append several arrays at once to one stack of the dataset."""
        if not (len(stack_indices) == len(point_indices) == len(data)):
            raise ValueError(
                "stack_indices, point_indices, and data must have same length"
            )

        if self._dataset is None:
            self._dataset = self._create_dataset(data[0], stack_indices[0])

        self._buffer.extend(
            zip(
                map(int, stack_indices),
                map(int, point_indices),
                data,
            )
        )
        return self.flush_buffer()

    def flush_buffer(self, align: bool = False) -> bool:
        if not self._buffer:
            return False

        if align:
            logger.debug(
                "Chunk-aligned flushing is only supported by StackDatasetWriter. "
                "Only flush when `flush_period` has passed since the last flush."
            )
            if self._flush_time_expired():
                return False

        stack_indices, point_indices, values = zip(*self._buffer)
        stack_indices = numpy.asarray(stack_indices)
        point_indices = numpy.asarray(point_indices)
        values = numpy.asarray(values)

        # Enlarge the dataset when needed
        max_stack = int(stack_indices.max())
        max_point = int(point_indices.max())

        shape0, shape1 = self._dataset.shape[:2]

        if max_stack >= shape0:
            self._dataset.resize(max_stack + 1, axis=0)

        if max_point >= shape1:
            self._dataset.resize(max_point + 1, axis=1)

        # Copy data from buffer to HDF5
        for i0, i1, value in zip(stack_indices, point_indices, values):
            self._dataset[i0, i1] = value

        # Remove copied data from buffer
        self._buffer.clear()

        self._flush_hdf5()
        self._last_flush = time.time()
        return True
