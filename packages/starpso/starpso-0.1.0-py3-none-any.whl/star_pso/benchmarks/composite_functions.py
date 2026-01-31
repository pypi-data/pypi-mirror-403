import numpy as np
from numba import njit
from numpy.typing import NDArray

from star_pso.population.particle import Particle
from star_pso.benchmarks.test_function import TestFunction
from star_pso.utils.auxiliary import identify_global_optima

# Basic function: 1
@njit(fastmath=True)
def f_sphere(x_pos: NDArray) -> NDArray:
    """
    Computes the sphere function at x_pos.
    """
    return np.sum(x_pos ** 2)
# _end_def_

# Basic function: 2
@njit(fastmath=True)
def f_griewank(x_pos: NDArray) -> NDArray:
    """
    Computes the Griewank function at x_pos.
    """
    # Get the size of the vector.
    n_dim = x_pos.size

    # Compute the sqrt[i], {1, 2, ..., D}.
    sqrt_i = np.sqrt(np.arange(1, n_dim + 1))

    # Get the final value.
    return np.sum(x_pos ** 2) / 4000 - float(np.prod(np.cos(x_pos / sqrt_i))) + 1.0
# _end_def_

# Basic function: 3
@njit(fastmath=True)
def f_rastrigin(x_pos: NDArray,
                kappa: float = 10.0) -> NDArray:
    """
    Computes the Rastrigin function at x_pos,
    with default kappa parameter.
    """
    return np.sum(x_pos ** 2 - kappa * np.cos(2.0 * np.pi * x_pos) + kappa)
# _end_def_

# Basic function: 4
@njit(fastmath=True)
def f_weierstrass(x_pos: NDArray, k_max: int = 9,
                  alpha: float = 0.5, beta: int = 3) -> NDArray:
    """
    Computes the Weierstrass function at x_pos, with default k_max,
    alpha and beta parameters.
    """
    # Get the size of the vector.
    n_dim = x_pos.size

    # Precalculate k-index values.
    k = np.arange(0, k_max + 1)

    # Precalculate: alpha^k
    alpha_k = alpha ** k

    # Precalculate: beta^k
    beta_k = beta ** k

    # Vectorized double summation.
    sum_x = np.sum(alpha_k[:, np.newaxis] * np.cos(2 * np.pi * beta_k[:, np.newaxis] * (x_pos + 0.5)),
                   axis=0).sum()

    # Combine the final result with the last summation.
    return sum_x - n_dim * np.sum(alpha_k * np.cos(np.pi * beta_k))
# _end_def_

# Basic function: 5
@njit(fastmath=True)
def f_ackley(x_pos: NDArray, alpha: float = 20.0,
             beta: float = 0.2) -> NDArray:
    """
    Computes the Ackley function at x_pos,
    with default alpha and beta parameters.
    """
    # Get the size of the vector.
    n_dim = x_pos.size

    # Compute the first part of the equation.
    f_total = -alpha * np.exp(-beta * np.sqrt(np.sum(x_pos ** 2) / n_dim))

    # Update it with the second part.
    f_total -= np.exp(np.sum(np.cos(2.0 * np.pi * x_pos)) / n_dim)

    # Return final result.
    return f_total + alpha + np.e
# _end_def_

# Auxiliary dictionary with the basic functions.
BASIC_FUNCTIONS: dict = {"f_ackley": f_ackley,
                         "f_sphere": f_sphere,
                         "f_griewank": f_griewank,
                         "f_rastrigin": f_rastrigin,
                         "f_weierstrass": f_weierstrass}
"""
Define a dictionary with all the basic functions:

    - Ackley
    - Sphere
    - Griewank
    - Rastrigin
    - Weierstrass
"""


class CompositeFunction(TestFunction):
    """
    Generates a Composite Function using a weighted average of basic
    functions, as defined in the 'BASIC_FUNCTIONS' dictionary.
    """

    def __init__(self, n_dim: int = 2, n_func: int | list = 4,
                 x_min: float = -5.0, x_max: float = 5.0) -> None:
        """
        Default initializer of the CompositeFunction class.

        :param n_dim: (int) number of dimensions of the problem.

        :param n_func: (int | list) is either the number of basic functions
                       that we want to include selected at random, or a list
                       with specific functions that we will include in the
                       given order.

        :param x_min: (float) the lower bound values of the search space.

        :param x_max: (float) the upper bound values of the search space.

        :return: None.
        """
        # Ensure correct type.
        n_dim = int(n_dim)

        # Sanity check.
        if n_dim < 2:
            raise ValueError(f"{self.__class__.__name__}: needs at least 2 dimensions.")
        # _end_if_

        # Call the super initializer.
        super().__init__(name=f"CF_{n_dim}D",
                         n_dim=n_dim, x_min=x_min, x_max=x_max)

        # Ensure correct type.
        if isinstance(n_func, int) and (2 <= n_func <= 20):
            # Create a new list by sampling randomly basic functions.
            self.basic_f = self.rng.choice(list(BASIC_FUNCTIONS.values()),
                                           size=n_func, replace=True).tolist()
        elif isinstance(n_func, list):
            try:
                # Create a new list with the given basic functions.
                self.basic_f = [BASIC_FUNCTIONS[key] for key in n_func]
            except KeyError as ex:
                raise KeyError(f"Unknown basic function. "
                               f"Valid options are: {list(BASIC_FUNCTIONS.keys())}") from ex
        else:
            raise TypeError(f"{self.__class__.__name__}: "
                            f"'n_func' must either be an int in [2, 20], or a list.")
    # _end_def_

    @staticmethod
    @njit
    def compute_weights(x_pos: NDArray, sigma: NDArray) -> NDArray:
        """
        Calculates a set of weights (one for each function).

        :param x_pos: (ndarray) the position that we are evaluating the functions.

        :param sigma: (ndarray) are used to control each function's range.
                      a small value gives a narrow range for the function.

        :return: a (ndarray) of normalized weights.
        """
        # Initialize the weights array.
        weights = np.exp(-0.5 * np.sum(x_pos ** 2) / (x_pos.size * sigma**2))

        # Find the maximum among them.
        w_max = np.max(weights)

        # Raise w_max to the power of 10.
        w_max_power_10 = w_max ** 10

        # Update the weights.
        weights[weights != w_max] *= (1.0 - w_max_power_10)

        # Finally return the normalized values.
        return weights / np.sum(weights)
    # _end_def_

    def func(self, x_pos: NDArray,
             i_bias: float = 0.0, f_bias: float = 0.0) -> float | NDArray:
        """
        Describes the general framework for the construction of
        multimodal composition functions with several global optima.

        :param x_pos: the current position(s) of the function.

        :param i_bias: function value bias for each basic function.

        :param f_bias: function value bias for the composition function.

        :return: the function value(s).
        """
        # Initialize function value to NaN.
        f_value = np.full_like(x_pos, np.nan, dtype=float)

        # Check the valid function range.
        if np.all((self.x_min <= x_pos) & (x_pos <= self.x_max)):
            # Get the number of basic functions.
            num_f = len(self.basic_f)

            # Sigma values for simplicity are set to one.
            sigma = np.ones(num_f, dtype=float)

            # Calculate the weights of the functions.
            weights = CompositeFunction.compute_weights(x_pos, sigma)

            # Get total evaluation of the composite function.
            f_total = np.sum([wi * (fi(x_pos / num_f) + i_bias)
                              for wi, fi in zip(weights, self.basic_f)])
            # Add the bias at the end.
            f_value = f_total + f_bias
        # _end_if_

        # Return the ndarray.
        return f_value
    # _end_def_

    def search_for_optima(self, population: list[Particle],
                          epsilon: float = 1.0e-4) -> tuple[int, int]:
        """
        Searches the input population for the global optimum values
        of the specific test function, using default (problem specific)
        parameters.

        :param population: the population to search the global optimum.

        :param epsilon: accuracy level of the global optimal solution.

        :return: a tuple with the number of global optima found and the
                 total number that exist.
        """
        # Get the global optima particles.
        found_optima = identify_global_optima(population, epsilon=epsilon,
                                              radius=0.1, f_opt=0.0)
        # Find the number of optima.
        num_optima = len(found_optima)

        # Return the tuple (number of found, total number)
        return num_optima, len(self.basic_f)
    # _end_def_

    def __str__(self) -> str:
        """
        Returns a string representation of the CompositeFunction.
        """
        # Initialize the return string.
        cf_str = f"{self.name}(x_min={self.x_min}, x_max={self.x_max})\n"

        # Append all the basis functions.
        for n, func in enumerate(self.basic_f):
            cf_str += f"F{n} -> {func.__name__}\n"

        # Return the new string.
        return cf_str
    # _end_def_

# _end_class_
