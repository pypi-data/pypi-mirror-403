import time
from enum import Enum
from math import fabs
from typing import Callable
from functools import (wraps,
                       partial,
                       lru_cache)
import numpy as np
from numba import njit
from numpy.linalg import norm
from numpy.typing import NDArray

from star_pso.population.particle import Particle


class BlockType(Enum):
    """
    Description:
        BlockType enumeration defines the types that a data block can take.
    """
    FLOAT, INTEGER, BINARY, CATEGORICAL = range(4)
# _end_class_

class SpecialMode(Enum):
    """
    Description:
        SpecialMode enumeration defines specific modes that the GenericPSO
        can accommodate. These are handled internally (i.e. NOT by the end
        user) to call the evaluate_function methods and perform operations
        directly related to the specific versions of PSO method.
    """
    NORMAL, CATEGORICAL, JACK_OF_ALL_TRADES = range(3)
# _end_class_

def check_velocity_parameters(options: dict) -> None:
    """
    Checks that the options dictionary has all the additional
    parameters to estimate the velocities of the optimization
    algorithm:

    - 'w0': inertia weight
    - 'c1': cognitive coefficient
    - 'c2': social coefficient
    - 'mode': mode of operation

    :param options: dictionary to check for missing parameters.

    :return: None.
    """
    # Sanity check.
    for key in ("w0", "c1", "c2", "mode"):
        # Make sure the right keys exist.
        if key not in options:
            raise KeyError(f"Option '{key}' is missing.")
        # _end_if_
# _end_def_

def time_it(func):
    """
    Timing decorator function.

    :param func: the function we want to time.

    :return: the time wrapper method.
    """

    @wraps(func)
    def time_it_wrapper(*args, **kwargs):
        """
        Wrapper function that times the execution of the input function.

        :param args: function positional arguments.

        :param kwargs: function keywords arguments.

        :return: the output of the wrapper function.
        """
        # Initial time instant.
        time_t0 = time.perf_counter()

        # Run the function we want to time.
        result = func(*args, **kwargs)

        # Final time instant.
        time_tf = time.perf_counter()

        # Print final duration in seconds.
        print(f"{func.__name__ }: "
              f"elapsed time = {(time_tf - time_t0):.3f} seconds.")

        return result
    # _end_def_
    return time_it_wrapper
# _end_def_

def pareto_front(points: NDArray) -> NDArray:
    """
    Simple function that calculates the pareto (optimal)
    front points from a given input points numpy array.

    :param points: array of points as [(fx1, fx2, ..., fxn),
                                       (fy1, fy2, ..., fyn),
                                       ....................,
                                       (fk1, fk2, ..., fkn)]

    :return: array of points that lie on the pareto front.
    """
    # Sanity check.
    if points.ndim != 2:
        raise RuntimeError("Points must be a 2-D array.")
    # _end_if_

    # Get the number of points.
    num_points = points.shape[0]

    # Create a boolean array to track Pareto optimal points.
    is_pareto_optimal = np.ones(num_points, dtype=bool)

    for i, point_i in enumerate(points):
        # Compare point i-th with all other points.
        is_dominated = np.any(np.all(points <= point_i, axis=1) &
                              np.any(points < point_i, axis=1))
        # Set the flag appropriately.
        is_pareto_optimal[i] = not is_dominated
    # _end_for_

    # Return only the unique Pareto optimal points.
    return np.unique(points[is_pareto_optimal], axis=0)
# _end_def_

def cost_function(func: Callable = None, minimize: bool = False):
    """
    Decorator for the function we want to optimize. The default
    setting is maximization.

    :param func: the function to be optimized.

    :param minimize: if True it will return the negative function
                     value to allow for the minimization. Default
                     is False.

    :return: the 'function_wrapper' method.
    """

    # This allows the decorator to be called with
    # parenthesis and using the default parameters.
    if func is None:
        return partial(cost_function, minimize=minimize)
    # _end_if_

    @wraps(func)
    def function_wrapper(*args, **kwargs) -> dict:
        """
        Internal function wrapper.

        :param args: function positional arguments.

        :param kwargs: function keywords arguments.

        :return: a dictionary with two key-values.
        """

        # Run the function we want to optimize.
        result = func(*args, **kwargs)

        # Check if the function returns a tuple (with two values)
        # or a single output parameter. In the former, the second
        # value should be boolean to signal that the solution meets
        # the termination requirements.
        if isinstance(result, tuple) and len(result) == 2:

            f_value, solution_is_found = result[0], bool(result[1])
        else:

            f_value, solution_is_found = result, False
        # _end_if_

        return {"f_value": -f_value if minimize else f_value,
                "solution_is_found": solution_is_found}
    # _end_def_

    return function_wrapper
# _end_def_

def identify_global_optima(swarm_population: list[Particle], epsilon: float = 1.0e-5,
                           radius: float = 1.0e-1, f_opt: float | None = None) -> list:
    """
    This auxiliary method will search if the global optimal solution(s)
    are found in the swarm population.

    :param swarm_population: a list[Particle] of potential solutions.

    :param epsilon: accuracy level of the global optimal solution.

    :param radius: niche radius of the distance between two particles.

    :param f_opt: function value for the global optimal solution.

    :return: a list of best-fit individuals identified as solutions.
    """
    # Define a return list that will contain the
    # particles that are on the global solutions.
    optima_list = []

    # Check all the particles.
    for px in swarm_population:

        # Reset the exist flag.
        already_exists = False

        # Check if the fitness is near the global
        # optimal value (within error - epsilon).
        if fabs(f_opt - px.value) <= epsilon:

            # Check if the particle is already
            # in the optimal particles list.
            for k in optima_list:

                # Check if the two particles are close to each other.
                if norm(k.position - px.position) <= radius:
                    already_exists = True
                    break
            # Add the particle only if it doesn't
            # already exist in the list.
            if not already_exists:
                optima_list.append(px)
    # _end_for_

    # Return the list.
    return optima_list
# _end_def_

@lru_cache(maxsize=64)
def linear_rank_probabilities(p_size: int) -> tuple[NDArray, float]:
    """
    Calculate the rank probability distribution over the population size.
    The function is cached so repeated calls with the same input should
    not recompute the same array since the population size of the swarm
    is not expected to change.

    NOTE: Probabilities are returned in ascending order.

    :param p_size: (int) population size.

    :return: (array, float) rank probability distribution in ascending
             order along with their sum. Note: The sum should be one
             but due to small errors it might be less.
    """
    # Sanity check.
    if not isinstance(p_size, int):
        raise TypeError("'p_size' must be an integer number.")
    # _end_if_

    # Sanity check.
    if p_size <= 0:
        raise ValueError("'p_size' must be a positive number.")
    # _end_if_

    # Calculate the sum of all the ranked swarm particles.
    sum_ranked_values = float(0.5 * p_size * (p_size + 1))

    # Calculate the linear ranked probabilities of each
    # particle in the swarm using their ranking position.
    probs = np.arange(1, p_size + 1) / sum_ranked_values

    # Return the probs and their sum.
    return probs, probs.sum()
# _end_def_

@njit
def kl_divergence_item(p: NDArray, q: NDArray) -> float:
    """
    Calculates the Kullback-Leibler divergence between two distributions.
    Note that KL divergence is not symmetric, thus KL(p, q) != KL(q, p).

    NOTE: Both distributions 'p' and 'q' should already be normalized to
    sum to one.

    This method is equivalent to entropy(p, q) from scipy_stats, only it's
    around 10x faster.

    :param p: (NDArray) probability distribution.

    :param q: (NDArray) probability distribution.

    :return: (float) Kullback-Leibler divergence.
    """
    return np.sum(np.where(p != 0.0,
                           np.where(q != 0.0,
                                    p * np.log(p / q), np.nan), 0.0)).item()
# _end_def_

@njit
def kl_divergence_array(p: NDArray, q: NDArray) -> NDArray:
    """
    Calculates the Kullback-Leibler divergence between two distributions.
    Note that KL divergence is not symmetric, thus KL(p, q) != KL(q, p).

    NOTE: Both distributions 'p' and 'q' should already be normalized to
    sum to one.

    This method is equivalent to entropy(p, q, axis=1) from scipy_stats,
    only it's around 10x faster.

    :param p: (NDArray) probability distribution.

    :param q: (NDArray) probability distribution.

    :return: (NDArray) Kullback-Leibler divergence.
    """
    return np.sum(np.where(p != 0.0,
                           np.where(q != 0.0,
                                    p * np.log(p / q), np.nan), 0.0), axis=1)
# _end_def_

@njit
def nb_median_hamming_distance(x_pos: NDArray,
                               normal: bool = False) -> float:
    """
    Compute the median Hamming distance of the input array.
    It is assumed that the input 'x_pos', represents the 2D
    array of particle binary positions {0, 1}.

    :param x_pos: (array) A 2D numpy array (n_particles, n_features)
                  representing the positions of the swarm.

    :param normal: whether to compute the normalized average
                   Hamming distance. This will yield a value
                   between 0 and 1. A value of '0' indicates
                   that all rows are identical. On the contrary
                   a value of '1' indicates that all rows are
                   completely different across all positions.

    The normalization provides a clearer understanding of the
    diversity of the binary strings in relation to their length.

    :return: the (normalized) median Hamming distance value.
    """
    # Get the columns size.
    n_cols = x_pos.shape[1]

    # Initialize the counter.
    total_diff = []

    # Count the non-identical positions.
    for i, p in enumerate(x_pos):
        total_diff.extend(np.count_nonzero(p != x_pos[i + 1:], axis=1))
    # _end_for_

    # Convert the list to an array of floats.
    x_diff = np.array([float(k) for k in total_diff])

    # Check for normalization.
    if normal:
        # In this case the number of columns represents
        # the  maximum  hamming  distance where all the
        # positions between two particles are different.
        x_diff /= n_cols
    # _end_if_

    # Return the median value.
    return np.median(x_diff).item()
# _end_def_

@njit
def nb_median_euclidean_distance(x_pos: NDArray,
                                 normal: bool = False) -> float:
    """
    Calculates a measure of the particles spread, when their position
    is defined by continuous variables in 'R'. First we calculate the
    centroid position of the swarm, and then  we compute its distance
    from all the particles. To get an estimate in [0,1] we can divide
    them with the maximum distance (optional).

    :param x_pos: (array) A 2D numpy array (n_particles, n_features)
                  representing the positions of the swarm.

    :param normal: (bool) if "True", normalize the distances by their
                   maximum distance.

    :return: the median Euclidean distance.
    """

    # Calculate the centroid.
    # NOTE: We use this instead of x_pos.mean(axis=0) because in
    # 'no python mode' numba does not support the 'axis' option.
    x_centroid = np.sum(x_pos, axis=0) / len(x_pos)

    # Get the distances from their centroid.
    x_dist = np.sqrt(np.sum((x_centroid - x_pos) ** 2, axis=1))

    # Find the maximum distance.
    d_max = x_dist.max()

    # Normalize the distances with d_max.
    if normal and d_max != 0.0:
        x_dist /= d_max
    # _end_if_

    # Return the median value.
    return np.median(x_dist).item()
# _end_def_

@njit
def nb_median_taxicab_distance(x_pos: NDArray,
                               normal: bool = False) -> float:
    """
    Calculates a measure of the particles spread, when their position
    is defined by integer variables in 'Z'. First we calculate the
    centroid position of the swarm, and then we compute its distance
    from all the particles. To get an estimate in [0,1] we can divide
    them with the maximum distance (optional).

    :param x_pos: (array) A 2D numpy array (n_particles, n_features)
                  representing the positions of the swarm.

    :param normal: (bool) if "True", normalize the distances by their
                   maximum distance.

    :return: the median TaxiCab (Manhattan) distance.
    """

    # Calculate the centroid.
    # NOTE: We use this instead of x_pos.mean(axis=0) because in
    # 'no python mode' numba does not support the 'axis' option.
    x_centroid = np.sum(x_pos, axis=0) / len(x_pos)

    # Get the distances from their centroid.
    x_dist = np.sum(np.abs(x_centroid - x_pos), axis=1)

    # Find the maximum distance.
    d_max = x_dist.max()

    # Normalize the distances with d_max.
    if normal and d_max != 0.0:
        x_dist /= d_max
    # _end_if_

    # Return the median value.
    return np.median(x_dist).item()
# _end_def_

@njit
def nb_median_kl_divergence(x_pos: NDArray,
                            normal: bool = False) -> float:
    """
    Calculate the 'median KL divergence' value of the input array.
    It is assumed that each row is a distribution (i.e. sum to 1).

    :param x_pos: (array) A 2D numpy array (n_particles, n_features)
                  representing the positions of the swarm.

    :param normal: If enabled the KL values will be normalized using
                   the maximum KL divergence from the data.

    :return: The median KL divergence of the swarm positions.
    """
    # Get the number of rows.
    n_rows = x_pos.shape[0]

    # Compute the "centroid" distribution.
    x_centroid = x_pos.sum(axis=0) / n_rows

    # Normalize to 1.0.
    x_centroid /= x_centroid.sum()

    # Compute the distances from the centroid.
    kl_dist = kl_divergence_array(x_pos, x_centroid)

    # Find the maximum KL.
    kl_max = kl_dist.max()

    # Check for normalization.
    if normal and kl_max != 0.0:
        kl_dist /= kl_max
    # _end_if_

    # Return the median value.
    return np.median(kl_dist).item()
# _end_def_

@njit
def nb_clip_inplace(x: NDArray,
                    x_min: float | NDArray,
                    x_max: float | NDArray) -> None:
    """
    Local auxiliary function that is used to clip the values of
    input array 'x' to [x_min, x_max] range, and put the output
    inplace.

    :param x: the numpy array we want to clip its values.

    :param x_min: the minimum (lower bound).

    :param x_max: the maximum (upper bound).
    """
    np.clip(x, x_min, x_max, out=x)
# _end_def_

@njit
def nb_clip_array(x_new: NDArray,
                  lower_limit: float | NDArray,
                  upper_limit: float | NDArray) -> NDArray:
    """
    Local version of numba clip which limits the values of an array.
    Given an interval values outside the interval are clipped to the
    interval edges.

    :param x_new: array values to be clipped.

    :param lower_limit: lower limit.

    :param upper_limit: upper limit.

    :return: the clipped array values.
    """
    return np.minimum(np.maximum(x_new, lower_limit),
                      upper_limit)
# _end_def_

@njit
def nb_clip_item(x_new: float | NDArray,
                 lower_limit: float | NDArray,
                 upper_limit: float | NDArray) -> int | float:
    """
    Local version of numba clip which limits the values of a scalar.
    Given an interval values outside the interval are clipped to the
    interval edges. The final value is returned with item().

    :param x_new: scalar value to be clipped.

    :param lower_limit: lower limit.

    :param upper_limit: upper limit.

    :return: the clipped item value.
    """
    return np.minimum(np.maximum(x_new, lower_limit),
                      upper_limit).item()
# _end_def_

# Dictionary with block types.
spread_methods: dict = {BlockType.FLOAT: nb_median_euclidean_distance,
                        BlockType.BINARY: nb_median_hamming_distance,
                        BlockType.INTEGER: nb_median_taxicab_distance,
                        BlockType.CATEGORICAL: nb_median_kl_divergence}
"""
Create a dictionary with block types as keys and their corresponding
spread estimation methods as values.
"""

@njit(fastmath=True)
def nb_cdist(x_pos: NDArray, scaled: bool = False) -> NDArray:
    """
    This is equivalent to the scipy.spatial.distance.cdist method
    with Euclidean distance metric. It is a tailored version for
    the purposes of the multimodal operation mode.

    :param x_pos: a numpy array of positions. The dimensions of the
                  input array should [n_rows, n_cols], where n_rows
                  is the number of particles and n_cols are the number
                  of positions.

    :param scaled: boolean flag that allows the input array to be
                   scaled, using the MaxAbsScaler, before computing
                   the distances.

    :return: a square [n_rows, n_rows] numpy array of distances.
    """

    # Get the number of rows/cols.
    n_rows, n_cols = x_pos.shape

    # Check if we want the input data to be scaled.
    if scaled:
        # Get the absolute values first.
        x_abs = np.abs(x_pos)

        # Scale with the max(abs(x_pos)).
        x_pos /= np.array([np.max(x_abs[:, i]) for i in range(n_cols)])
    # _end_if_

    # Create a square matrix with zeros.
    dist_x = np.zeros((n_rows, n_rows), dtype=float)

    # Iterate through all vectors.
    for i in range(n_rows):
        # Compute the Euclidean norm of the 'i-th' element with the rest of them.
        dist_x[i, i + 1:] = np.sqrt(np.sum((x_pos[i] - x_pos[i + 1:, :]) ** 2, axis=1))

        # Since the array is symmetric store the result in the 'i-th' column too.
        dist_x[:, i] = dist_x[i, :]
    # _end_for_
    return dist_x
# _end_def_
