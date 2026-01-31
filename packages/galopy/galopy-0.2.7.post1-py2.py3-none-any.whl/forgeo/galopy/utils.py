import numpy as np


class InvalidSpaceDimensionsError(ValueError):
    pass


def as_point_set(coords, ndim: int, dtype=np.float64) -> np.ndarray:
    """Converts (if needed) the input list of coordinates to a 2D numpy array
    array, and ensures its shape matches (N,ndim)

    Parameters
    ----------
    coords: array_like
        Shape = (N,ndim), an iterable of 'ndim'-D coordinates
    ndim: int
        The number of dimensions of the points in the point set

    Return
    ------
    point_set: np.ndarray
        Shape (N, ndim). The input coordinates stored in a numpy 2D array.

    Raise
    -----
    exception: ValueError | TypeError
        If the input `coords` cannot be converted to a `np.ndarray` with
        `dtype=np.float64`
    exception: InvalidSpaceDimensionsError
        If the input shape is not (N,ndim)
    """
    # copy = None   # FIXME Only compatible with numpy >= 2
    copy = np._CopyMode.IF_NEEDED
    coords = np.array(coords, dtype=dtype, copy=copy, ndmin=2)
    if coords.shape[1] != ndim:
        msg = f"Expected {ndim = },  got ndim = {coords.shape[1]} instead"
        raise InvalidSpaceDimensionsError(msg)
    return coords


def as_polyline(coords, ndim: int, dtype=np.float64) -> np.ndarray:
    """Converts (if needed) the input list of coordinates to a 2D numpy array
    array, and ensures its shape matches (N,ndim)

    Parameters
    ----------
    coords: array_like
        Shape = (N,ndim), an iterable of 'ndim'-D coordinates
    ndim: int
        The number of dimensions of the points in the point set

    Return
    ------
    point_set: np.ndarray
        Shape (N, ndim). The input coordinates stored in a numpy 2D array.

    Raise
    -----
    exception: ValueError | TypeError
        If the input `coords` cannot be converted to a `np.ndarray` with
        `dtype=np.float64`
    exception: InvalidSpaceDimensionsError
        If the input shape is not (N,ndim)
    """
    # copy = None   # FIXME Only compatible with numpy >= 2
    copy = np._CopyMode.IF_NEEDED
    coords = np.array(coords, dtype=dtype, copy=copy, ndmin=2)
    if coords.shape[0] < 2:
        msg = f"Expected at least 2 vertices in polyline, got {coords.shape[0]} instead"
        raise ValueError(msg)
    if coords.shape[1] != ndim:
        msg = f"Expected {ndim = },  got ndim = {coords.shape[1]} instead"
        raise InvalidSpaceDimensionsError(msg)
    if np.any(np.all(np.diff(coords, axis=0) == 0, axis=1)):
        msg = "Polyline contains (consecutive) duplicated vertices"
        raise ValueError(msg)
    return coords
