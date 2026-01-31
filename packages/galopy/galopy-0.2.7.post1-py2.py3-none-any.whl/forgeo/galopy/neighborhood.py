from typing import Optional

import gstlearn as gl
import numpy as np

from .utils import as_point_set


def create_geostatistical_neighborhood(
    *,
    ndim: int,
    unique_neighborhood: bool = False,
    max_search_distance: Optional[float] = None,
    nb_max_samples: int = 24,
    nb_min_samples: int = 1,
    nb_angular_sectors: int = 8,
    nb_max_samples_per_sector: int = 3,
):
    """Returns a new neighborhood

    It can be either a
    - "unique" neighborhood: in this case, all input samples are used to evaluate
      each target location, and the kriging is performed using the dual formulation
      (a large kriging system is solved once at the first estimation, and its solution
      is reused for each further estimation), or a
    - "moving" neighborhood: only a subset of the input samples are used to evaluate
      a given location (a mall kriging system is solved for each target). The criteria
      to select the subset of samples to be used are based on the proximity to the
      target and eventually declustering strategies, presence of discontinuities
      (screens), ...

    Notes:
    - All search parameters detailed below are for moving neighborhoods. Unique
      neighborhood does not require any parameter apart from the space dimensionality

    Parameters
    ----------
    ndim: int
        `0 < ndim < 4`: The number of (space) dimensions
    unique_neighborhood: bool
        True to create a unique neighbohorhood, False to create a moving one
    max_search_distance: float > 0
        Maximum search distance. If the distance between the point to estimate and an
        input sample is greater than this distance, the sample will not be selected
        (even though no closer samples exist). Defaults to None, which means that all
        points will be considered
    nb_max_samples: int > 0
        The maximum number of samples to use when estimating a new location
    nb_min_samples: int > 0
        The minimum number of samples to use when estimating a new location. If this
        requirement is not match...  # TODO Test and update doc!
    nb_angular_sectors: int > 0
        Number of space partitions to use for sample search. If equal to 1, the input
        samples are only selected based on their distance to the point to estimate.
        If greater than 1, at most `nb_max_samples_per_sector` are selected per space
        partition. This means the following: Given X a point to estimate and A and B
        two samples from two different partitions such that `||AX|| < ||BX||`. B can
        be selected instead of A if at least `nb_max_samples_per_sector` Ai exist in
        A partition such that `||AiX|| < ||AX||`.
    nb_max_samples_per_sector: int > 1
        The maximum number of samples to select per angular sector. This parameter is
        only relevant if `nb_angular_sectors > 1`. Otherwise, it defaults to
        `nb_max_samples`.

    Return
    ------
    neighbohorhood: gstlean.NeighUnique | gstlean.NeighMoving
        The newly created neighborhood
    """
    space = gl.SpaceRN.create(ndim)
    if unique_neighborhood:
        return gl.NeighUnique.create(space=space)
    params = {
        "nmaxi": nb_max_samples,
        "nmini": nb_min_samples,
        "nsect": nb_angular_sectors,
        "nsmax": nb_max_samples_per_sector,
        "space": space,
        "radius": max_search_distance,
    }
    # Filter None values that can trigger TypeError when passed to NeighMoving.create
    params = {k: v for k, v in params.items() if v is not None}
    return gl.NeighMoving.create(**params)


def set_moving_neighborhood_search_parameters(
    neighborhood: gl.NeighMoving,
    *,
    max_search_distance: Optional[float] = None,
    nb_max_samples: Optional[int] = None,
    nb_min_samples: Optional[int] = None,
    nb_angular_sectors: Optional[int] = None,
    nb_max_samples_per_sector: Optional[int] = None,
):
    """Sets one or more (moving) neighborhood search parameters

    Only the none `None` parameters are updated

    Parameters
    ----------
    neighborhood: gstlean.NeighMoving
        The geostatistical neighborhood
    max_search_distance: (optional) float > 0
        Maximum search distance. If the distance between the point to estimate
        and an input sample is greater than this distance, the sample will not
        be selected (even though no closer samples exist).
    nb_max_samples: (optional) int > 1
        The maximum number of samples to use when estimating a new location
    nb_min_samples: (optional) int
        The minimum number of samplers to use when estimating a new location.
        If this requirement is not match...  # TODO Test and update doc!
    nb_angular_sectors: (optional) int > 0
        Number of space partitions to use for sample search. If equal to 1, the
        input samples are only selected based on their distance to the point
        to estimate. If greater than 1, at most `nb_max_samples_per_sector` are
        selected per space partition. This means the following:
        Given X a point to estimate and A and B two samples from two different
        partitions such that `||AX|| < ||BX||`. B can be selected instead of A
        if at least `nb_max_samples_per_sector` Ai exist in A partition such
        that `||AiX|| < ||AX||`.
    nb_max_samples_per_sector: (optional) int > 1
        The maximum number of samples to select per angular sector. This
        parameter is only relevant if `nb_angular_sectors > 1`. Otherwise,
        it defaults to `nb_max_samples`.

    Return
    ------
    neighborhood: gstlean.NeighMoving
        The input neighborhood updated, for convenience (like chained calls)
    """
    if max_search_distance is not None:
        # FIXME Should not work? getBiPtDist returns a const BiTargetCheckDistance*
        neighborhood.getBiPtDist().setRadius(max_search_distance)
    if nb_max_samples is not None:
        neighborhood.setNMaxi(nb_max_samples)
    if nb_min_samples is not None:
        neighborhood.setNMini(nb_min_samples)
    if nb_angular_sectors is not None:
        neighborhood.setNSect(nb_angular_sectors)
    if nb_max_samples_per_sector is not None:
        neighborhood.setNSMax(nb_max_samples_per_sector)
    return neighborhood


def add_screen(neighborhood: gl.NeighMoving, polyline):
    """Adds a new discontinuity to a moving neighborhood

    Note: this function uses a (quite dirty) hack to prevent garbage collector
    issues with the SWIG binding (cf. gstlearn issue #46). A reference to each
    temporary object created by the function is stored by the object which uses
    it. So the reference counter of the temporary object is not null and it is
    not garbage collected.


    Parameters
    ----------
    neighborhood: gstlean.NeighMoving
        The geostatistical neighborhood
    polyline: array_like
        Shape (N,2), N > 1. An iterable of 2D vertices

    Return
    ------
    neighborhood: gstlean.NeighMoving
        The input neighborhood updated, for convenience (like chained calls)
    """
    return add_screens(neighborhood, [polyline])


def add_screens(neighborhood: gl.NeighMoving, polylines):
    """Adds a set of discontinuities to a moving neighborhood

    Note: this function uses a (quite dirty) hack to prevent garbage collector
    issues with the SWIG binding (cf. gstlearn issue #46). A reference to each
    temporary object created by the function is stored by the object which uses
    it. So the reference counter of the temporary object is not null and it is
    not garbage collected.


    Parameters
    ----------
    neighborhood: gstlean.NeighMoving
        The geostatistical neighborhood
    polylines: Iterable[array_like]
        The discontinuities (screens) to add. Each array has a shape (Ni,2), Ni > 1,
        which corresponds to an iterable of 2D vertices defining one discontinuity

    Return
    ------
    neighborhood: gstlean.NeighMoving
        The input neighborhood updated, for convenience (like chained calls)
    """
    polylines = [_as_polyline(p, ndim=2) for p in polylines]
    polylines = [gl.PolyLine2D(p[:, 0], p[:, 1]) for p in polylines]

    # FIXME Check if the setattr / getattr hack is still needed, probably not...
    _tmp_name = "_tmp_faults_ref"
    target = getattr(neighborhood, _tmp_name, None)
    if target is None:
        faults = gl.Faults()
        for p in polylines:
            faults.addFault(p)
        setattr(faults, _tmp_name, polylines)
        target = gl.BiTargetCheckFaults(faults)
        setattr(target, _tmp_name, faults)
        neighborhood.addBiTargetCheck(target)
        setattr(neighborhood, _tmp_name, target)
    else:
        faults = getattr(target, _tmp_name)
        for p in polylines:
            faults.addFault(p)
        getattr(faults, _tmp_name).extend(polylines)
    return neighborhood


def _as_polyline(coords, ndim: int) -> np.ndarray:
    """Converts (if needed) the input list of coordinates to a 2D numpy float64
    array, and ensures that 1) its shape matches (N,ndim) with N > 1, 2) it has
    no consecutive duplicated elements

    Parameters
    ----------
    coords: array_like
        Shape = (N,ndim), N > 1, a list of 'ndim'-D coordinates
    ndim: int
        The number of dimensions of the points in the point set

    Return
    ------
    point_set: np.ndarray
        Shape (N, ndim). The input coordinates stored in a numpy 2D array.

    Raise
    -----
    exception: TypeError
        If the input `coords` cannot be converted to a `np.ndarray` with
        `dtype=np.float64`
    exception: ValueError
        If the input shape is not (N,ndim), or if the input contains (consecutive)
        duplicated vertices
    """
    polyline = as_point_set(coords, ndim)
    if len(polyline) < 2:
        msg = f"Polyline should have at least 2 vertices ({polyline = })"
        raise ValueError(msg)
    if np.bitwise_and.reduce(polyline[:-1] == polyline[1:], axis=1).any():
        msg = "Polyline contains consecutive duplicated vertices"
        raise ValueError(msg)
    return polyline
