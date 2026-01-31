import numpy as np
from numpy.typing import NDArray

from star_pso.population.particle import Particle
from star_pso.benchmarks.test_function import TestFunction
from star_pso.utils.auxiliary import identify_global_optima


class UnevenDecreasingMaxima(TestFunction):
    """
    This function was originally proposed in:

    - K. Deb, “Genetic algorithms in multimodal function optimization
      (master thesis and tcga report no. 89002)”,  Ph.D. dissertation,
      Tuscaloosa: University of Alabama, The Clearinghouse for Genetic
      Algorithms, 1989.
    """

    def __init__(self, x_min: float = 0.0, x_max: float = 1.0) -> None:
        """
        Default initializer of the UnevenDecreasingMaxima class.

        :param x_min: (float) the lower bound values of the search space.

        :param x_max: (float) the upper bound values of the search space.

        :return: None.
        """
        # Call the super initializer.
        super().__init__(name="Uneven_Decreasing_Maxima",
                         n_dim=1, x_min=x_min, x_max=x_max)
    # _end_def_

    def func(self, x_pos: NDArray) -> NDArray:
        """
        This is 1D function. There is 1 global and 4 local optima.

        :param x_pos: the current position(s) of the function.

        :return: the function value(s).
        """
        # Initialize function values to NaN.
        f_value = np.full_like(x_pos, np.nan, dtype=float)

        # Condition for the valid range.
        if np.all((self.x_min <= x_pos) & (x_pos <= self.x_max)):
            f_value = (np.exp(-2.0 * np.log(2.0) * ((x_pos - 0.08)/0.854)**2) *
                       np.sin(5.0 * np.pi * (x_pos**(3/4) - 0.05))**6)

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
                                              radius=0.01, f_opt=1.0)
        # Find the number of optima.
        num_optima = len(found_optima)

        # Return the tuple (number of found, total number)
        return num_optima, 1
    # _end_def_

# _end_class_
