from numbers import Number
from typing import List
from typing import Mapping
from typing import Optional
from typing import Tuple

import numpy


def is_data(data):
    if isinstance(data, (numpy.ndarray, Number)):
        return True
    if isinstance(data, (str, list)) and data:
        return True
    return False


def data_from_storage(data, remove_numpy=True):
    if isinstance(data, numpy.ndarray):
        if not remove_numpy:
            return data
        elif data.ndim == 0:
            return data.item()
        else:
            return data.tolist()
    elif isinstance(data, Mapping):
        return {
            k: data_from_storage(v, remove_numpy=remove_numpy)
            for k, v in data.items()
            if not k.startswith("@")
        }
    else:
        return data


def _validate_names(names: Optional[List[str]], name_type: str) -> None:
    if names is None:
        return
    for n in names:
        if not isinstance(n, str) or not n.strip():
            raise ValueError(f"Invalid {name_type} name: {n!r}")


def validate_and_init_names(
    lima_names: Optional[List[str]],
    counter_names: Optional[List[str]],
) -> Tuple[List[str], List[str]]:
    _validate_names(lima_names, "LIMA")
    _validate_names(counter_names, "Counter")
    return (
        lima_names if lima_names is not None else [],
        counter_names if counter_names is not None else [],
    )
