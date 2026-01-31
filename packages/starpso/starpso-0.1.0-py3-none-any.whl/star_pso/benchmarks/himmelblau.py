import numpy as np
from numpy.typing import NDArray

from star_pso.population.particle import Particle
from star_pso.benchmarks.test_function import TestFunction
from star_pso.utils.auxiliary import identify_global_optima


class Himmelblau(TestFunction):
    """
    This function was originally proposed in:

    - K. Deb, “Genetic algorithms in multimodal function optimization
      (master thesis and tcga report no. 89002)”,  Ph.D. dissertation,
      Tuscaloosa: University of Alabama, The Clearinghouse for Genetic
      Algorithms, 1989.
    """

    def __init__(self, x_min: float = -6.0, x_max: float = 6.0) -> None:
        """
        Default initializer of the Himmelblau class.

        :param x_min: (float) the lower bound values of the search space.

        :param x_max: (float) the upper bound values of the search space.

        :return: None.
        """
        # Call the super initializer.
        super().__init__(name="Himmelblau",
                         n_dim=2, x_min=x_min, x_max=x_max)
    # _end_def_

    def func(self, x_pos: NDArray) -> NDArray:
        """
        This is 2D function with is 4 global optima.

        :param x_pos: the current position(s) of the function.

        :return: the function value(s).
        """
        # Initialize function values to NaN.
        f_value = np.full_like(x_pos, np.nan, dtype=float)

        # Check the valid function range.
        if np.all((self.x_min <= x_pos) & (x_pos <= self.x_max)):
            # Calculate the function value.
            f_value = (200.0 - (x_pos[0]**2 + x_pos[1] - 11)**2 -
                       (x_pos[0] + x_pos[1]**2 - 7)**2)

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
                                              radius=0.01, f_opt=200.0)
        # Find the number of optima.
        num_optima = len(found_optima)

        # Return the tuple (number of found, total number)
        return num_optima, 4
    # _end_def_

# _end_class_
