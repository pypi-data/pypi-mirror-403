import numpy as np
from galopy.utils import as_point_set, as_polyline

from forgeo.gdmlib.wrappers import ImplicitFunctor


def _signed_distance_to_polyline(points, polyline):
    """Compute the signed distance from each point to a polyline.

    Warning: this implementation uses several hypotheses about the input data,
    prefer using the `SignedDistanceFunctor` class.

    Parameters
    ----------
    points : np.ndarray
        Shape (m, 2), m >= 1. 2D points where to evaluate the signed distance function
    polyline : np.ndarray
        Shape (n, 2), n >= 2. The polyline vertices

    Returns
    -------
    distances: np.ndarray
        Shape (m,). Signed distances to the polyline. Positive on the left side
        (trigonometric rotation), negative on the right side (clockwise rotation).
        Directions relative to the polyline.
    """
    # Polyline information
    sources = polyline[:-1]  # Shape (n-1, 2)
    segments = polyline[1:] - sources  # Shape (n-1, 2)

    # Vectors between sources and points to evaluate
    vectors = points[:, np.newaxis, :] - sources[np.newaxis, :, :]  # Shape (m, n-1, 2)

    # Project points onto each segment, t = first degree Bezier parameter
    t = np.sum(vectors * segments[np.newaxis, :, :], axis=2)  # Shape (m, n-1)
    t /= np.sum(segments * segments, axis=1)[np.newaxis, :]  # t /= square norm
    # Projections outside segments are clipped to segment vertices
    np.clip(t, 0, 1, out=t)

    # Closest point on each segment for each input point
    closest = t[:, :, np.newaxis] * segments[np.newaxis, :, :]  # Shape (m, n-1, 2)
    closest += sources[np.newaxis, :, :]

    # Unsigned distances from each point to each (projection on) segment
    # Note: closest array reused to avoid additional memory allocations
    closest -= points[:, np.newaxis, :]
    closest *= closest
    distances = np.sum(closest, axis=2)  # Shape (m, n-1), square distance
    del closest  # Encourage to free memory as soon as possible

    # Closest segment for each point
    closest_idx = np.argmin(distances, axis=1)  # Shape (m,)
    # Min distance from each point to polyline
    range_m = np.arange(len(points))  # Just to avoid re-allocating multiple times
    distances = distances[range_m, closest_idx]  # Shape (m,)
    np.sqrt(distances, out=distances)
    t_closest = t[range_m, closest_idx]  # Shape (m,)
    del t

    # Use cross product to determine the sign

    # Cross product on closest pairs of (segments, vectors)
    s_closest = segments[closest_idx]  # Shape (m, 2)
    v_closest = vectors[range_m, closest_idx]  # Shape (m, 2)
    del range_m
    cross = s_closest[:, 0] * v_closest[:, 1]
    cross -= s_closest[:, 1] * v_closest[:, 0]
    del s_closest, v_closest

    # Handle special case: closest point is a vertex (t = 0 or t = 1) and cross
    # product is zero (i.e., point is on the line defined by the segment).
    # We need to use the adjacent segment instead to get the correct sign.
    epsilon = 1e-10
    at_vertex_start = (
        (np.abs(t_closest) < epsilon) & (np.abs(cross) < epsilon) & (closest_idx > 0)
    )
    at_vertex_end = (
        (np.abs(t_closest - 1) < epsilon)
        & (np.abs(cross) < epsilon)
        & (closest_idx < len(segments) - 1)
    )

    # For points at vertex start, use the previous segment
    if np.any(at_vertex_start):
        prev_idx = closest_idx[at_vertex_start] - 1
        s_prev = segments[prev_idx]
        v_prev = vectors[at_vertex_start, prev_idx]
        cross_prev = s_prev[:, 0] * v_prev[:, 1] - s_prev[:, 1] * v_prev[:, 0]
        cross[at_vertex_start] = cross_prev

    # For points at vertex end, use the next segment
    if np.any(at_vertex_end):
        next_idx = closest_idx[at_vertex_end] + 1
        s_next = segments[next_idx]
        v_next = vectors[at_vertex_end, next_idx]
        cross_next = s_next[:, 0] * v_next[:, 1] - s_next[:, 1] * v_next[:, 0]
        cross[at_vertex_end] = cross_next

    sign = np.sign(cross)
    sign[sign == 0] = 1  # Points exactly on the line get positive distance

    distances *= sign
    return distances


class SignedDistanceFunctor:
    """A functor that computes the 2D signed distance to a polyline

    Distance is positive when rotating in the trigonometric sense (i.e., on the
    "left" side of the polyline)
    """

    def __init__(self, polyline):
        polyline = as_polyline(polyline, ndim=2)
        self._polyline = np.copy(polyline)

    def __call__(self, points):
        # TODO Process points by batches to avoid risking running out of RAM
        points = as_point_set(points, ndim=2)
        return _signed_distance_to_polyline(points, self._polyline)

    def as_implicit_functor(self):
        """Returns an implicit version of this signed distance operator that
        evaluates: (x,y,z) -> z - self(x,y).
        """
        return ImplicitFunctor(self)


def _unsigned_distance_to_polyline(points, polyline):
    """Compute the (unsigned) distance from each point to a polyline.

    Warning: this implementation uses several hypotheses about the input data,
    prefer using the `SignedDistanceFunctor` class.

    Parameters
    ----------
    points : np.ndarray
        Shape (m, 2), m >= 1. 2D points where to evaluate the distance function
    polyline : np.ndarray
        Shape (n, 2), n >= 2. The polyline vertices

    Returns
    -------
    distances: np.ndarray
        Shape (m,). Distances to the polyline.
    """

    # Polyline information (all: shape (n-1, 2))
    sources = polyline[:-1]
    segments = polyline[1:] - sources

    # Vectors between sources and points to evaluate, shape (m, n-1, 2)
    vectors = points[:, np.newaxis, :] - sources[np.newaxis, :, :]

    # Project points onto each segment, t = first degree Bezier parameter
    t = np.sum(vectors * segments[np.newaxis, :, :], axis=2)  # Shape (m, n-1)
    t /= np.sum(segments * segments, axis=1)[np.newaxis, :]  # t /= square norm
    # Projections outside segments are clipped to segment vertices
    np.clip(t, 0, 1, out=t)

    # Closest point on each segment for each input point
    closest = vectors  # Reuse memory, rename variable for clarity
    del vectors
    np.multiply(t[:, :, np.newaxis], segments[np.newaxis, :, :], out=closest)
    closest += sources[np.newaxis, :, :]

    # Unsigned distances from each point to each (projection on) segment
    closest -= points[:, np.newaxis, :]
    closest *= closest
    distances = t  # Reuse memory, rename variable for clarity
    del t
    np.sum(closest, axis=2, out=distances)  # Shape (m, n-1), square distance
    del closest  # Encourage to free memory as soon as possible

    # Closest segment for each point
    closest_idx = np.argmin(distances, axis=1)  # Shape (m,)

    distances = distances[np.arange(len(points)), closest_idx]  # Shape (m,)
    np.sqrt(distances, out=distances)

    return distances


class UnsignedDistanceFunctor:
    """A functor that computes the 2D signed distance to a polyline"""

    def __init__(self, polyline):
        polyline = as_polyline(polyline, ndim=2)
        self._polyline = np.copy(polyline)

    def __call__(self, points):
        # TODO Process points by batches to avoid risking running out of RAM
        points = as_point_set(points, ndim=2)
        return _unsigned_distance_to_polyline(points, self._polyline)

    def as_implicit_functor(self):
        """Returns an implicit version of this signed distance operator that
        evaluates: (x,y,z) -> z - self(x,y).
        """
        return ImplicitFunctor(self)
