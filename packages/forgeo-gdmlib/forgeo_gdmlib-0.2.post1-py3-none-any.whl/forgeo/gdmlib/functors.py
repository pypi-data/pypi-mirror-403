from collections.abc import Callable, Iterable

import numpy as np
from galopy import gstlearn as gl
from galopy.model import add_external_drifts, add_polynomial_drift
from galopy.utils import as_point_set

from forgeo.gdmlib.wrappers import (
    FunctorNotWrappableError,
    ImplicitFunctor,
    ScalarFunctor,
)


def _make_db(samples, ndim, external_drifts):
    samples = as_point_set(samples, ndim=ndim)
    names = ["x1", "x2"]
    if ndim == 3:
        names.append("z1")
    if external_drifts is not None:
        names = names + [f"f{i + 1}" for i in range(len(external_drifts))]
        drifts = [f(samples[:, :2])[:, np.newaxis] for f in external_drifts]
        samples = np.concatenate((samples, *drifts), axis=1)
    return gl.Db.createFromSamples(
        nech=len(samples),
        order=gl.ELoadBy.SAMPLE,
        tab=samples.reshape(-1),
        names=names,
        locatorNames=names,
        flagAddSampleRank=False,
    )


class UniversalKrigingFunctor:
    """A functor that encapsulates a 2D universal kriging operator. The kriging
    uses a moving neighborhood when performing the estimation.

    The kriging has the following properties:
    - 2D
    - Universal kriging
    - Moving neighborhood
    - Handles drifts (both external and coodinate-based polynomial)
    - Handles discontinuities (treated as screens: when estimating a point X, a
      sample Ni cannot be used if a screen intersects the segment XNi)

    The following parameters are user-provided:
    - Input data samples (at least one)
    - Covariance functions (at least one)
    - Neighborhood search parameters
    - Polynomial drift function(s) (optional): Constant/Coordinate-dependent drift
      terms
    - External drifts, as functors (optional): Any (other) drift term
    - Discontinuities (optional): Polylines

    Note about the univeral kriging:
    If the "universality condition" (synonym: constant drift, sum of all lambda_i is
    equal to one, `gstlearn.Drift1` in the code) is present in the input model (which
    stores all covariance and drift functions), then the value estimated at a location
    with no neighbors (e.g., far away from input samples, or isolated by screens, etc)
    is the mean of the input random variable distribution. Otherwise (without this
    "universality condition"), the estimated value at a location with no neighbors
    is zero.

    Note about functor classes:
    Functor classes require to be instanciated from a fully defined set of
    parameters. You may prefer to use the related `*Builder` classes, that
    provide an API to build functors step by step.
    """

    def __init__(
        self,
        samples,
        model: gl.Model,
        neighborhood: gl.NeighMoving,
        external_drifts: Iterable[Callable] | None = None,
        compute_estimation: bool = True,
        compute_standard_deviation: bool = False,
    ):
        """
        Parameters
        ----------
        samples: array_like
            Shape (N,3). All know data points, each point being (X, Y, Variable)
        model: gstlearn.Model
            The geostatistical model: provides both the list of covariance functions
            and the polynomial drit term, if any.
        neighborhood: gl.NeighMoving
            The neighborhood search parameters
        external_drifts: (optional) Iterable[Callable]
            The external drift functors. Basically, any callable that satisfy the
            `ScalarFunctor` interface (that can evaluate a function `z = f(x,y)`)
        compute_estimation: (optional) bool
            If True, the functor will compute (and return) the kriging estimation
            when called. Default is True
        compute_standard_deviation: (optional) bool
            If True, the functor will compute (and return) the kriging standard
            deviation when called. Default is False
        """
        self._check_params(
            model,
            neighborhood,
            external_drifts,
            compute_estimation,
            compute_standard_deviation,
        )

        if external_drifts is not None:
            external_drifts = [ScalarFunctor.wrap(f, ndim=2) for f in external_drifts]
            if model.getNExtDrift() == 0:  # In case they were not already declared
                model = model.clone()  # Avoid modifying the input model
                add_external_drifts(model, len(external_drifts))

        self._samples = _make_db(samples, 3, external_drifts)
        self._model = model
        self._neighborhood = neighborhood
        self._external_drifts = external_drifts
        self._compute_estimation = compute_estimation  # Kriging estimation
        self._compute_stdev = compute_standard_deviation  # Kriging standard deviation

    @staticmethod
    def _check_params(
        model,
        neighborhood,
        external_drifts,
        compute_estimation,
        compute_standard_deviation,
    ):
        if not isinstance(model, gl.Model):
            msg = "Invalid model: requires a gstlearn.Model object"
            raise TypeError(msg)
        if not isinstance(neighborhood, gl.NeighMoving):
            msg = "Invalid neighborhood: requires a gstlearn.NeighMoving object"
            raise TypeError(msg)
        if external_drifts is not None:
            nb_external_drifts = model.getNExtDrift()
            nb_functors = len(external_drifts)
            if nb_external_drifts not in {0, nb_functors}:
                msg = f"Inconsistent number of external drifts: {nb_external_drifts} are declared in the model, but {nb_functors} drifts are provided"
                raise ValueError(msg)
        if not (compute_estimation or compute_standard_deviation):
            msg = "Functor should at least compute kriging estimation or standard deviation (both were disabled)"
            raise ValueError(msg)

    def __call__(self, points):
        """Evaluates the kriging operator at a set of 2D (x,y) locations

        Parameters
        ----------
        points: array_like
            Shape (N,2). Coordinates where to evaluate the functor

        Returns
        -------
        z: np.ndarray | 2-tuple[np.ndarray, np.ndarray]
            (Each) Shape (N,). The estimation result(s) for at each input location.
            Will return a single array if only one of the kriging estimation or
            standard deviation was selected, or a pair of arrays if both were selected
        """
        db_out = _make_db(points, 2, self._external_drifts)
        gl.kriging(
            self._samples,
            db_out,
            self._model,
            self._neighborhood,
            flag_est=self._compute_estimation,
            flag_std=self._compute_stdev,
        )
        result = db_out.getColumnByLocator(gl.ELoc.Z)
        if not (self._compute_estimation and self._compute_stdev):
            return result
        return result, db_out.getColumn("Kriging.z1.stdev")

    def as_implicit_functor(self):
        """Returns an implicit version of this kriging operator that evaluates:
        (x,y,z) -> z - self(x,y).

        Note that only estimation can be converted to implicit (it would make no
        sens to have an "implicit" version of stadard deviation)
        """
        if self._compute_stdev:
            msg = (
                "Implicit functor requires this functor to return only estimation "
                "(currently, both estimation and standard deviation are returned)."
            )
            raise FunctorNotWrappableError(msg)
        return ImplicitFunctor(self)


class OrdinaryKrigingFunctor(UniversalKrigingFunctor):
    """A functor that encapsulates a 2D ordinary kriging operator. The kriging
    uses a moving neighborhood when performing the estimation.

    The kriging has the following properties:
    - 2D
    - Ordinary kriging
    - Moving neighborhood
    - Handles discontinuities (treated as screens: when estimating a point X, a
      sample Ni cannot be used if a screen intersects the segment XNi)

    The following parameters are user-provided:
    - Input data samples (at least one)
    - Covariance functions (at least one)
    - Neighborhood search parameters
    - Discontinuities (optional): Polylines

    Note about functor classes:
    Functor classes require to be instanciated from a fully defined set of
    parameters. You may prefer to use the related `*Builder` classes, that
    provide an API to build functors step by step.
    """

    def __init__(
        self,
        samples,
        model: gl.Model,
        neighborhood: gl.NeighMoving,
        compute_estimation: bool = True,
        compute_standard_deviation: bool = False,
    ):
        """
        Parameters
        ----------
        samples: array_like
            Shape (N,3). All know data points, each point being (X, Y, Variable)
        model: gstlearn.Model
            The geostatistical model: provides the list of covariance functions
        neighborhood: gl.NeighMoving
            The neighborhood search parameters
        compute_estimation: (optional) bool
            If True, the functor will compute (and return) the kriging estimation
            when called. Default is True
        compute_standard_deviation: (optional) bool
            If True, the functor will compute (and return) the kriging standard
            deviation when called. Default is False
        """
        model = model.clone()  # Avoid modifying the input model
        model.delAllDrifts()  # Remove any pre-existing polynomial / external drifts
        add_polynomial_drift(model, max_degree=0)
        # The rest is unchanged
        super().__init__(
            samples,
            model,
            neighborhood,
            None,
            compute_estimation,
            compute_standard_deviation,
        )
