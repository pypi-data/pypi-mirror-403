import numpy as np
from numpy.typing import NDArray
from scipy.stats import multivariate_normal

from star_pso.population.particle import Particle
from star_pso.benchmarks.test_function import TestFunction
from star_pso.utils.auxiliary import identify_global_optima


class GaussianMixture(TestFunction):
    """
    This function provides a 2D Gaussian mixture model.

    The equations are given by the Multivariate Normal Distribution,
    with four modes (2 global and 2 local):

    .. math::
        f(x) = \sum_{i=1}^{4} \mathcal{N}(\mu_i, \Sigma_i)

    with mean vectors:

    .. math::
        \mu_1 = [-0.0, -1.0]

        \mu_2 = [-4.0, -6.0]

        \mu_3 = [-5.0, +1.0]

        \mu_4 = [5.0, -10.0]

    and covariances:

    .. math::
        \Sigma_1 = [ [ 1.0, 0.1 ], [ 0.1, 1.0 ] ]

        \Sigma_2 = [ [ 1.0, 0.1 ], [ 0.1, 1.0 ] ]

        \Sigma_3 = [ [ 1.2, 0.3 ], [ 0.3, 1.2 ] ]

        \Sigma_4 = [ [ 1.2, 0.3 ], [ 0.3, 1.2 ] ]
    """

    # Auxiliary (class-level) tuple.
    MVN = (multivariate_normal([-0.0, -1.0], [[1.0, 0.1], [0.1, 1.0]]),
           multivariate_normal([-4.0, -6.0], [[1.0, 0.1], [0.1, 1.0]]),
           multivariate_normal([-10.0, 5.0], [[1.2, 0.3], [0.3, 1.2]]),
           multivariate_normal([5.0, -10.0], [[1.2, 0.3], [0.3, 1.2]]))
    """
    Set up four multivariate normal distributions.
    """

    def __init__(self, x_min: float = -15.0, x_max: float = 15.0) -> None:
        """
        Default initializer of the GaussianMixture (2D) class.

        :param x_min: (float) the lower bound values of the search space.

        :param x_max: (float) the upper bound values of the search space.

        :return: None.
        """
        # Call the super initializer.
        super().__init__(name="GaussianMixture",
                         n_dim=2, x_min=x_min, x_max=x_max)
    # _end_def_

    def func(self, x_pos: NDArray) -> NDArray:
        """
        This is 2D function with is 2 global and 2 local optima.

        :param x_pos: the current position(s) of the function.

        :return: the function value(s).
        """
        # Initialize function values to NaN.
        f_value = np.full_like(x_pos, np.nan, dtype=float)

        # Check the valid function range.
        if np.all((self.x_min <= x_pos) & (x_pos <= self.x_max)):
            # Calculate the log of the sum.
            f_value = np.log(np.sum([mvn.pdf(x_pos)
                                     for mvn in GaussianMixture.MVN]))
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
                                              radius=0.5, f_opt=-1.83285)
        # Find the number of optima.
        num_optima = len(found_optima)

        # Return the tuple (number of found, total number)
        return num_optima, 2
    # _end_def_

# _end_class_
