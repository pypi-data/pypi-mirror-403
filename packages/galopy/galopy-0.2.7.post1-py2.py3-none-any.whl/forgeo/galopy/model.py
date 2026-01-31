from typing import Optional

import gstlearn as gl

from forgeo.galopy.utils import InvalidSpaceDimensionsError


def create_geostatistical_model(
    *,
    ndim: int,
    type: Optional[str] = None,
    range: Optional[float] = None,
    sill: Optional[float] = None,
    max_drift_degree: Optional[int] = None,
    parameters: Optional[dict] = None,
):
    """Returns a geostatistical model as used in gstlearn

    For now, the returned model is isotropic. It consists of one or several
    covariance functions and eventually polynomial drift functions based on
    space coordinates.

    Parameters
    ----------
    ndim: int
        `0 < ndim < 4`: The number of (space) dimensions
    type: str
        For models with a single covariance function: the type of the covariance
        function to use (e.g., "nugget", "spherical", "exponential", "cubic",
        "gaussian"). It should match one of gstlearn available types, and is case
        insensitive. Unused if `parameters` is not `None`
    range: Scalar
        For models with a single covariance function: the range of the covariance
        function. Unused if `parameters` is not `None`
    sill: Scalar
        For models with a single covariance function: the sill of the covariance
        function. Unused if `parameters` is not `None`
    max_drift_degree: int | None
        `max_drift_degree < 4`: If set, adds molynomial drift functions to the model.
        The value controls the maximum monomial degree that will be added. E.g:
        `max_drift_degree=0` adds a constant drift term: `Z*(h) = Z(h) + c` (this is
        the usual `sum(lambda_i)=1` term in the kriging system);
        In 3D, `max_drift_degree=1` adds constant and linear drift terms along X, Y
        and Z axes like: `Z*(h) = Z(h) + a*x + b*y * c*z + d`;
        In 2D, `max_drift_degree=2` adds constant, linear and quadratic terms along X
        and Y axes like: `Z*(h) = Z(h) + a*x^2 + b*y^2 * c**x*y + d*x + e*y + f`
        See `add_polynomial_drift` for more details
    parameters: Iterable[dict_like]
        For models with multiple covariance functions: each element in `parameters`
        describes a single covariance function and is provided as a dict containing
        the following keys: "type", "range", "sill" (see above for documentation)

    Return
    ------
    model: gstlean.Model
        The newly created model
    """
    if not 0 < ndim < 4:
        msg = f"{ndim = } (should be in [[1, 2, 3]])"
        raise InvalidSpaceDimensionsError(msg)
    ctxt = gl.CovContext.create(nvar=1, ndim=ndim)
    model = gl.Model(ctxt)
    if parameters is not None:
        for p in parameters:
            p.setdefault("range", None)  # Missing if type == "nugget"
            add_covariance_structure(model, **p)
    elif type is not None:
        add_covariance_structure(model, type, range=range, sill=sill)
    if max_drift_degree is not None:
        add_polynomial_drift(model, max_drift_degree)
    return model


def add_covariance_structure(model: gl.Model, type: str, *, range: float, sill: float):
    """Adds a new covariance function to an existing geostatistical model

    Note: all gstlearn covariance function types are not supported for the moment.
    This function only handles common types described in terms of range/sill
    parameters (so basically, spherical, exponential, cubic, gaussian).

    Special covariance functions:
    - for nugget, the range parameter is ignored.
    - for linear, the actual `slope = sill / range`

    Parameters
    ----------
    model: gstlean.Model
        The geostatistical model to update
    type: str
        The type of covariance function (e.g., "spherical", "exponential", "cubic", ...)
    range: Scalar > 0
        The range of the covariance function
    sill: Scalar > 0
        The sill of the covariance function. Note: the total sill of the model is
        the sum of the sills of all its covariance functions

    Return
    ------
    model: gstlean.Model
        The input model updated, for convenience (like chained calls)
    """
    type = type.upper()
    if type == "NUGGET":
        add_nugget(model, sill)
    else:
        model.addCovFromParam(gl.ECov.fromKey(type), range, sill)
    return model


def add_nugget(model: gl.Model, sill: float):
    """Adds a nugget contribution to the geostiatical model

    Parameters
    ----------
    model: gstlean.Model
        The geostatistical model to update
    sill: Scalar > 0
        The contribution of the nugget effect to the total model variance
    Return
    ------
    model: gstlean.Model
        The input model updated, for convenience (like chained calls)

    """
    model.addCovFromParam(gl.ECov.NUGGET, 1.0, sill)
    return model


def add_linear_covariance_structure(model: gl.Model, slope: float):
    """Adds a linear "covariance" function to the geostiatical model

    Parameters
    ----------
    model: gstlean.Model
        The geostatistical model to update
    slope: Scalar > 0
        The slope of the linear function

    Return
    ------
    model: gstlean.Model
        The input model updated, for convenience (like chained calls)

    """
    model.addCovFromParam(gl.ECov.LINEAR, 1.0, slope)
    return model


def add_polynomial_drift(
    model: gl.Model, max_degree: int, override_preexisting: bool = False
):
    """Adds a "polynomial drift" to an existing geostatistical `model`

    Polynomial drift: the studied variable is not stationary The trend depends on the
    space coordinates and is defined by any polynomial function of the coordinates.

    In practice, instead of adding one single polynomial drift term to the model, we
    add one drift term for each monomial in the polynomial. This permits to fit
    independently each monomial coefficient. The added polynomial drift contains all
    possible monomials whose degree is lower or equal to `max_degree`

    Parameters
    ----------
    model: gstlean.Model
        The geostatistical model to update
    max_degree: int >= 0
        The maximum degree of the monomials drifts to add to the model
    override_preexisting: bool
        Default is `False`. If `True`, any preexisting monomial drift term is
        removed (particularly: the ones having a degree strictly greater than
        `max_degree`). If False, only the monomial terms with a degree lower or
        equal to `max_degree` that are not present in the model yet are added.
        Note that if `max_degree` is greater or equal to the currently greatest
        monomial degree term present in the model, then the final model will be
        the same whatever the value of `override_preexisting`

    Return
    ------
    model: gstlean.Model
        The input model updated, for convenience (like chained calls)

    Examples
    --------
    In 3D, `max_degree=2` will add the following mononomial drift terms:
    "1", "x", "y", "z", "x2", "xy", "xz", "y2", "yz", "z2", leading to a polynomial
    drift expression looking like:
    `ax^2 + by^2 + cz^2 + dxy + exz + fyz + gx + hy + iz + j`
    """
    if max_degree < 0:
        msg = f"Invalid polynomial drift degree: {max_degree} (should be >= 0)"
        raise ValueError(msg)

    def _remove_trailing_zeros(exponents):
        exponents = list(exponents)  # Avoid having to manually convert before each call
        while exponents and exponents[-1] == 0:
            exponents.pop()
        return exponents

    def _get_all_monomial_combinations(ndim, max_degree):
        """Returns all the possible combinations of `ndim` integers such that they
        sum to `max_degree` or less
        """

        def _get_subcombinations(idim, ndim, max_degree):
            if idim == ndim:
                return [[i] for i in range(max_degree + 1)]
            all_combinations = []
            for degree in range(max_degree + 1):
                sub_combinations = _get_subcombinations(
                    idim + 1, ndim, max_degree - degree
                )
                for c in sub_combinations:
                    c.insert(0, degree)
                all_combinations.extend(sub_combinations)
            return all_combinations

        return _get_subcombinations(0, ndim - 1, max_degree)

    monomials = [
        _remove_trailing_zeros(m)
        for m in _get_all_monomial_combinations(model.getNDim(), max_degree)
    ]
    if override_preexisting:
        # Note: we do not use directly gl.DriftFactory.createDriftListFromIRF while
        # it is restricted to max_order <= 2
        drifts = gl.DriftFactory.createDriftListFromIRF(
            -1, model.getNExtDrift(), model.getContext()
        )  # DriftList containing only the external drift that already exist in the model
        for m in monomials:
            drifts.addDrift(gl.DriftM(m))
        model.setDriftList(drifts)
    else:
        preexisting = []
        for i in range(model.getNDrift()):
            drift = model.getDrift(i)
            if not drift.isDriftExternal():
                preexisting.append(_remove_trailing_zeros(drift.getPowers()))
        for m in monomials:
            if m not in preexisting:
                model.addDrift(gl.DriftM(m))
    return model


def add_external_drifts(
    model: gl.Model, nb_drifts: int, override_preexisting: bool = False
):
    """Declares a given number of external drifts to a gstlearn `Model`

    Parameters
    ----------
    model: gstlearn.Model
    nb_drifts: int
        The number of external drifts to add to the model
    override_preexisting: bool
        Default is False. If False, new external drifts are added to the model in
        addition of the potentially existing ones. If True, removes any preexisting
        external drifts before adding the new ones.

    Return
    ------
    model: gstlean.Model
        The input model updated, for convenience (like chained calls)
    """
    if override_preexisting:
        for i in range(model.getNDrift() - 1, -1, -1):
            if model.getDrift(i).isDriftExternal():
                model.delDrift(i)
        assert model.getNExtDrift() == 0
    nb_ext = model.getNExtDrift()
    for i in range(nb_drifts):
        model.addDrift(gl.DriftF(i + nb_ext))  # (i + nb_ext)-th added external drift
    return model
