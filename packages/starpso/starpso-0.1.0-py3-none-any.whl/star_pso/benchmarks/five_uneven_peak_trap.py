import numpy as np
from numpy.typing import NDArray

from star_pso.population.particle import Particle
from star_pso.benchmarks.test_function import TestFunction
from star_pso.utils.auxiliary import identify_global_optima


class FiveUnevenPeakTrap(TestFunction):
    """
    This function was originally proposed in:

    - J.-P. Li, M. E. Balazs, G. T. Parks, and P. J. Clarkson,
      “A species conserving genetic algorithm for multimodal function optimization”
      Evolutionary Computation, vol. 10, no. 3, pp. 207–234, 2002.
    """

    def __init__(self, x_min: float = 0.0, x_max: float = 30.0) -> None:
        """
        Default initializer of the FiveUnevenPeakTrap class.

        :param x_min: (float) the lower bound values of the search space.

        :param x_max: (float) the upper bound values of the search space.

        :return: None.
        """
        # Call the super initializer.
        super().__init__(name="Five_Uneven_Peak_Trap",
                         n_dim=1, x_min=x_min, x_max=x_max)
    # _end_def_

    def func(self, x_pos: NDArray) -> NDArray:
        """
        This is 1D function. There are two global and one local optima.

        :param x_pos: the current position(s) of the function.

        :return: the function value(s).
        """
        # Initialize function values to NaN.
        f_value = np.full_like(x_pos, np.nan, dtype=float)

        # Apply the conditions using boolean indexing.
        cond_1 = (0.0 <= x_pos) & (x_pos < 2.5)
        cond_2 = (2.5 <= x_pos) & (x_pos < 5.0)
        cond_3 = (5.0 <= x_pos) & (x_pos < 7.5)
        cond_4 = (7.5 <= x_pos) & (x_pos < 12.5)
        cond_5 = (12.5 <= x_pos) & (x_pos < 17.5)
        cond_6 = (17.5 <= x_pos) & (x_pos < 22.5)
        cond_7 = (22.5 <= x_pos) & (x_pos < 27.5)
        cond_8 = (27.5 <= x_pos) & (x_pos <= 30.0)

        # Calculate the f_value.
        f_value[cond_1] = 80 * (2.50 - x_pos[cond_1])
        f_value[cond_2] = 64 * (x_pos[cond_2] - 2.50)
        f_value[cond_3] = 64 * (7.50 - x_pos[cond_3])
        f_value[cond_4] = 28 * (x_pos[cond_4] - 7.50)
        f_value[cond_5] = 28 * (17.5 - x_pos[cond_5])
        f_value[cond_6] = 32 * (x_pos[cond_6] - 17.5)
        f_value[cond_7] = 32 * (27.5 - x_pos[cond_7])
        f_value[cond_8] = 80 * (x_pos[cond_8] - 27.5)

        # Return the value.
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
                                              radius=0.01, f_opt=200.0)
        # Find the number of optima.
        num_optima = len(found_optima)

        # Return the tuple (number of found, total number)
        return num_optima, 2
    # _end_def_

# _end_class_
