import numpy as np
from numba import njit
from numpy.typing import NDArray

from star_pso.utils import VOptions
from star_pso.engines.generic_pso import GenericPSO
from star_pso.utils.auxiliary import (nb_clip_inplace,
                                      nb_median_hamming_distance)

@njit(fastmath=True)
def fast_logistic(x: NDArray) -> NDArray:
    """
    Local auxiliary function that is used to compute
    the logistic values of input array 'x'.

    :param x: a numpy array with the input values.

    :return: the numpy array with the logistic values.
    """
    return 1.0 / (1.0 + np.exp(-x))
# _end_def_


# Public interface.
__all__ = ["BinaryPSO", "fast_logistic"]


class BinaryPSO(GenericPSO):
    """
    Description:

    This class implements the (discrete) binary particle swarm optimization variant
    as described in:

    - Kennedy, J., and R. C. Eberhart 1997. “A Discrete Binary Version of the Particle
      Swarm Algorithm.” IEEE International conference on systems, man, and cybernetics,
      1997. Computational cybernetics and simulation, Vol. 5, Orlando, FL, October 12–15,
      pp: 4104–4108.
    """

    def __init__(self, v_min: float = -10.0, v_max: float = 10.0, **kwargs) -> None:
        """
        Default initializer of the BinaryPSO class.

        :param v_min: (float) minimum value for the velocity parameter.

        :param v_max: (float) maximum value for the velocity parameter.

        :return: None.
        """
        # Call the super initializer with default parameters.
        super().__init__(lower_bound=v_min, upper_bound=v_max, **kwargs)

        # Generate initial particle velocities.
        self._velocities = GenericPSO.rng.uniform(self.lower_bound,
                                                  self.upper_bound,
                                                  size=(self.n_rows,
                                                        self.n_cols))
    # _end_def_

    def update_velocities(self, params: VOptions) -> None:
        """
        Performs the update on the velocity equations.

        :param params: VOptions tuple with the PSO options.

        :return: None.
        """
        # Call the method of the parent class.
        super().update_velocities(params)

        # Clip velocities in [v_min, v_max].
        nb_clip_inplace(self._velocities,
                        self.lower_bound,
                        self.upper_bound)
    # _end_def_

    def update_positions(self) -> None:
        """
        Updates the positions of the particles in the swarm.

        :return: None.
        """
        # Generate random vectors in U(0, 1).
        uniform_values = GenericPSO.rng.random(size=(self.n_rows, self.n_cols),
                                               dtype=float)
        # Create a matrix with zeros.
        new_positions = np.zeros_like(uniform_values, dtype=int)

        # Compute the logistic values.
        logistic_values = fast_logistic(self._velocities)

        # Where the logistic function values are higher
        # than the random values set to one.
        new_positions[logistic_values > uniform_values] = 1

        # Update all particle positions.
        self.swarm.set_positions(new_positions)
    # _end_def_

    def generate_random_positions(self) -> None:
        """
        Generate the population of particles positions by
        sampling discrete binary random numbers within the
        {0, 1} set.

        :return: None.
        """
        # Generate random BINARY positions Bin(0, 1).
        binary_positions = GenericPSO.rng.integers(0, 1,
                                                   endpoint=True,
                                                   size=(self.n_rows,
                                                         self.n_cols))
        # Assign the new positions in the swarm.
        self.swarm.set_positions(binary_positions)
    # _end_def_

    def reset_all(self) -> None:
        """
        Resets the particle positions, velocities
        and clear all the statistics dictionary.

        :return: None.
        """
        # Reset particle velocities.
        self._velocities = GenericPSO.rng.uniform(self.lower_bound,
                                                  self.upper_bound,
                                                  size=(self.n_rows,
                                                        self.n_cols))
        # Generate random binary positions.
        self.generate_random_positions()

        # Clear all the internal bookkeeping.
        self.clear_all()
    # _end_def_

    def calculate_spread(self) -> float:
        """
        Calculates a spread measure for the particle positions
        using the normalized median Hamming distance.

        A value close to '0' indicates the swarm is converging
        to a single value. On the contrary a value close to '1'
        indicates the swarm is still spread around the search
        space.

        :return: an estimated measure (float) for the spread of
                 the particles.
        """
        # Extract the positions in a 2D numpy array.
        positions = self.swarm.positions_as_array()

        # Normalized median Hamming distance.
        return nb_median_hamming_distance(positions, normal=True)
    # _end_def_

# _end_class_
