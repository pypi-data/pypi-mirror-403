import time
from typing import Optional

import h5py
import numpy


class DatasetWriterBase:
    def __init__(
        self,
        parent: h5py.Group,
        name: str,
        attrs: Optional[dict] = None,
        flush_period: Optional[float] = None,
    ) -> None:
        self._file = parent.file
        self._parent = parent
        self._name = name
        self._attrs = attrs
        self._dataset_name = f"{parent.name}/{name}"
        self._dataset = None
        self._flush_period = flush_period
        self._last_flush = None

    @property
    def dataset_name(self) -> str:
        return self._dataset_name

    def __enter__(self) -> "DatasetWriterBase":
        return self

    def __exit__(self, *args) -> None:
        self.flush_buffer()

    @property
    def dataset(self) -> Optional[h5py.Dataset]:
        return self._dataset

    def _create_dataset(self, first_data_point: numpy.ndarray) -> h5py.Dataset:
        raise NotImplementedError

    def flush_buffer(self, align: bool = False) -> bool:
        raise NotImplementedError

    def _flush_time_expired(self) -> bool:
        if self._flush_period is None:
            return False
        if self._last_flush is None:
            self._last_flush = time.time()
            return False
        return (time.time() - self._last_flush) >= self._flush_period

    def _flush_hdf5(self) -> None:
        """Explicit HDF5 flush for non-locking readers."""
        self._file.flush()
