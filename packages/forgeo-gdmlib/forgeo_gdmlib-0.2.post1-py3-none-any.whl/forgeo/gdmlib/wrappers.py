from collections.abc import Callable

import numpy as np
from galopy.utils import InvalidSpaceDimensionsError, as_point_set


class FunctorNotWrappableError(TypeError):
    pass


class ScalarFunctor:
    """An interface and wrapper class for callable objects that perform (scalar)
    spatial predictions (that evaluate ndim-D points and return scalar values).

    The `ScalarFunctor` "interface" defines one single method:
    - `__call__(Iterable[Iterable[float_like]]) -> Iterable[Any]`: evaluates
      a set of points, with `len(Iterable[float_like]) = ndim`.

    In addition, this class provides methods to check if a functor is compliant
    with the interface or can be wrapped to be compliant.
    """

    def __init__(self, functor: Callable, ndim: int):
        if ndim < 1:
            msg = f"{ndim = } (should be > 0)"
            raise InvalidSpaceDimensionsError(msg)
        if not self.is_wrappable(functor, ndim):
            msg = f"Invalid functor: `{functor}`"
            raise FunctorNotWrappableError(msg)
        self._ndim = ndim
        self._functor = self.vectorize(functor)

    @property
    def ndim(self) -> int:
        """Returns the number of space dimensions"""
        return self._ndim

    def __call__(self, points):
        """Evaluates the wrapped functor at a set of `ndim`-dimensional points

        Parameter
        ---------
        points: array_like
            Shape (N,ndim). The points where to evaluate the functor

        Returns
        -------
        np.ndarray[Any]
            Shape (N,). The evalution result at each input point. The exact dtype
            is defined by `self.dtype`
        """
        points = as_point_set(points, ndim=self.ndim)
        return self._functor(points)

    @classmethod
    def vectorize(cls, functor: Callable):
        return np.vectorize(functor, otypes=[np.float64], signature="(n)->()")

    @classmethod
    def is_wrappable(cls, functor: Callable, ndim: int) -> bool:
        """Returns whether the input functor can be wrapped into a `ScalarFunctor`
        object or not

        This requires:
        - `functor` to be callable,
        - `functor` to be able to evaluate independently a set of N-D elements
          (see `is_valid`)

        Parameters
        ----------
        functor: Callable
            The functor to test
        ndim: int > 0
            The number of dimensions. `functor` should accept `ndim`-D points
        dtype: type
            Defaults to None. Data type returned by the functor evaluation. If
            None, it is automatically inferred

        Returns
        -------
        bool:
            True if `functor` succeeds to individually evaluate all input samples,
            False otherwise.
        """
        if ndim < 1:
            return False
        try:
            f = cls.vectorize(functor)
        except Exception:
            return False
        return cls.is_valid(f, ndim)

    @classmethod
    def is_valid(cls, functor: Callable, ndim: int) -> bool:
        """Checks whether the input `functor` satisfies the `ScalarFunctor` interface

        To be valid, `functor` must be able to process a 2D numpy array of shape
        (N,ndim)

        Parameters
        ----------
        functor: Callable
            The functor to test
        ndim: int > 0
            The number of dimensions. `functor` should accept `ndim`-D points

        Returns
        -------
        bool:
            True if `functor` implements: `__call__(Points) -> Scalars`,
            where `Points` is a numpy array of shape (N,ndim), otherwise False.
        """
        if ndim < 1:
            return False
        test_samples = [ndim * [0], np.ones(ndim)]
        for i in range(5):
            test_samples.append(1.5 * np.arange(ndim) - i)
        test_samples = np.array(test_samples, dtype=np.float64)
        try:
            result = functor(test_samples)
            result = np.asarray(result, dtype=np.float64)
            return len(result) == len(test_samples)
        except Exception:
            return False

    @classmethod
    def wrap(cls, functor: Callable, ndim: int):
        """Returns a functor compatible with the `ScalarFunctor` interface

        If the input `functor` already satistifies it, it is returned direcly.
        Otherwise, it is wrapped in a `ScalarFunctor` object.

        Parameters
        ----------
        functor: Callable
            The functor to test
        ndim: int > 0
            The number of dimensions. `functor` should accept `ndim`-D points

        Returns
        -------
        func: Callable
            A functor that satisfies the `ScalarFunctor` interface

        Raises
        ------
        ValueError:
            If `ndim < 1`
        FunctorNotWrappableError:
            If the functor cannot be wrapped in a ScalarFunctor object
        """
        if cls.is_valid(functor, ndim):
            return functor
        return cls(functor, ndim)


class ImplicitFunctor:
    """Wraps a 2D functor that evaluates `z = f(x,y)` into 3D functor that evaluates
    `v = z - f(x,y)`, where the 0 level set corresponds to the surface described by
    the 2D functor.

    Details: Let `f` be the encapsulated 2D functor. For any 3D point
    `P(x,y,z)`, the wrapper returns `v = z - f(x,y)`, so:
    * `v > 0`, if `P` is located above (i.e., is younger than) the surface
    * `v = 0`, if `P` is located on the surface
    * `v < 0`, if `P` is located below (i.e., is older than) the surface

    The wrapped functor should at least be wrappable in a `functory.ScalarFunctor`.
    """

    def __init__(self, functor: Callable):
        self._functor = ScalarFunctor.wrap(functor, ndim=2)

    def __call__(self, points, result=None):
        """Evaluates the functor at a set of 3D locations `Pi(xi,yi,zi)`

        Parameters
        ----------
        points: array_like
            Shape (N,3). The `(xi,yi,zi)` locations where to evaluate the functor

        Returns
        -------
        val: array_like
            Shape (N,). The evalution result at each input location `Pi`, with
            * `val[i] > 0`, if `Pi` is located above (younger than) the surface
            * `val[i] = 0`, if `Pi` is located on the surface
            * `val[i] < 0`, if `Pi` is located below (older than) the surface
        """
        points = as_point_set(points, ndim=3)
        if result is None:
            result = points[:, 2].copy()
        else:
            result[:] = points[:, 2]
        result -= self._functor(points[:, :2])
        return result
