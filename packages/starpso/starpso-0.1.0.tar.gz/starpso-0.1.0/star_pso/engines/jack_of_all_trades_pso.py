from operator import attrgetter
from collections import defaultdict

import numpy as np
from numba import njit
from numpy.typing import NDArray
from numpy import array as np_array
from numpy import isscalar as np_isscalar
from numpy import subtract as np_subtract

from star_pso.utils import VOptions
from star_pso.engines.generic_pso import GenericPSO
from star_pso.utils.auxiliary import (BlockType,
                                      linear_rank_probabilities,
                                      SpecialMode, spread_methods)
# Local fast version of sum method.
@njit(fastmath=True)
def fast_sum(x: NDArray) -> NDArray:
    """
    Local auxiliary function that is used
    to sum the values of input array 'x'.

    :param x: the numpy array we want to sum.

    :return: the sum(x).
    """
    return np.sum(x)
# _end_def_


# Public interface.
__all__ = ["JackOfAllTradesPSO"]


class JackOfAllTradesPSO(GenericPSO):
    """
    Description:

        JackOfAllTradesPSO class is an implementation of the PSO algorithm that
        can deal with mixed types of optimization variables. The supported types
        are:

        - float (continuous)
        - integer (discrete)
        - binary      (0, 1)
        - categorical (sets)

        The fundamental building block of the algorithm is the 'DataBlock' which
        encapsulates the data and the functionality of each variable type.
    """

    def __init__(self, permutation_mode: bool = False, **kwargs) -> None:
        """
        Default initializer of the JackOfAllTradesPSO class.

        :param permutation_mode: (bool) if True it will sample
                                 permutations of the valid sets.
        """

        # Call the super initializer.
        super().__init__(**kwargs)

        # First we declare the velocities to be
        # an [n_rows x n_cols] array of objects.
        self._velocities = np.empty(shape=(self.n_rows, self.n_cols),
                                    dtype=object)

        # Call the random velocity generator.
        self.generate_uniform_velocities()

        # Assign the correct local sample method
        # according to the permutation mode flag.
        if permutation_mode:
            self._items = {"sample_random_values":
                           self.sample_permutation_values}
        else:
            self._items = {"sample_random_values":
                           self.sample_categorical_values}
        # _end_if_

        # Set the special mode to Jack-Of-All-Trades.
        self._special_mode = SpecialMode.JACK_OF_ALL_TRADES
    # _end_def_

    def generate_uniform_velocities(self) -> None:
        """
        Generates random uniform velocities for the data blocks.

        :return: None.
        """

        # Here we generate the random velocities.
        for i, particle in enumerate(self.swarm.population):
            for j, block in enumerate(particle.container):
                # If the block is CATEGORICAL we
                # will use it's valid set length.
                n_vars = len(block.valid_set) if block.valid_set else 1

                # Generate the velocities randomly.
                self._velocities[i, j] = JackOfAllTradesPSO.rng.uniform(-1.0, +1.0,
                                                                        size=n_vars)
    # _end_def_

    def generate_random_positions(self) -> None:
        """
        Generate random positions for the population
        of particles, by calling the btype dependent
        reset methods of each data block.

        :return: None.
        """
        # Go through the whole swarm population.
        for particle in self.swarm.population:
            particle.reset_position()
    # _end_def_

    def sample_categorical_values(self, positions: list[list]) -> None:
        """
        Samples the actual position based on particles probabilities
        and valid sets for each data block.

        :param positions: container with the lists of probabilities
                          (one list for each position).
        :return: None.
        """

        # Check all particles in the swarm.
        for i, particle in enumerate(self.swarm.population):

            # Check all data blocks in the particle.
            for j, block in enumerate(particle.container):

                # If the data block is categorical.
                if block.block_t == BlockType.CATEGORICAL:

                    # Replace the probabilities with an actual sample.
                    # WARNING: 'shuffle' option MUST be set to False!
                    positions[i][j] = JackOfAllTradesPSO.rng.choice(block.valid_set,
                                                                    shuffle=False,
                                                                    p=positions[i][j])
    # _end_def_

    def sample_permutation_values(self, positions: list[list]) -> None:
        """
        Samples a permutation from a given set of variables.
        It is used in problems like the 'Traveling Salesman'.

        It is assumed that all data blocks are CATEGORICAL
        and that they have the same valid set of values.

        :param positions: container with the lists of probabilities
                          (one list for each position).
        :return: None.
        """

        # Create a range of values.
        random_index = np.arange(self.n_cols, dtype=int)

        # Shuffle in place. This is used to avoid introducing
        # biasing by using always the same order of blocks to
        # select first their categorical sample value.
        JackOfAllTradesPSO.rng.shuffle(random_index)

        # Check all particles in the swarm.
        for i, particle in enumerate(self.swarm.population):

            # Auxiliary set.
            exclude_idx = set()

            # Check all data blocks in the particle,
            # using the randomized index.
            for j in random_index:
                # Get the j-th data block.
                block = particle[j]

                # Extract the probability values.
                xj = positions[i][j]

                # Sort in reverse order from high to low.
                for k in xj.argsort()[::-1]:
                    # Continue until we find the first
                    # unused element of the valid set.
                    if k not in exclude_idx:
                        # Assign the element in the right position.
                        positions[i][j] = block.valid_set[k]

                        # Update the set() with
                        # the excluded indexes.
                        exclude_idx.add(k)

                        # Break the internal loop.
                        break
        # _end_for_
    # _end_def_

    def update_velocities(self, params: VOptions) -> None:
        """
        Performs the update on the velocity equations.

        :param params: VOptions tuple with the PSO options.

        :return: None.
        """
        # Get the shape of the velocity array.
        arr_shape = (self.n_rows, self.n_cols)

        # Pre-sample the cognitive coefficients.
        cogntv = JackOfAllTradesPSO.rng.uniform(0, params.c1, size=arr_shape)

        # Pre-sample the social coefficients.
        social = JackOfAllTradesPSO.rng.uniform(0, params.c2, size=arr_shape)

        # Get the global best particle position.
        if params.mode.lower() == "fipso":

            # Extract only their positions and convert to numpy array.
            # Due to the different shapes of the variables we need to
            # set the dtype as object (instead of float).
            all_positions = np.array([item.position
                                      for item in sorted(self.swarm.population,
                                                         key=attrgetter("value"))], dtype=object)
            # Compute the linear rank probability weights.
            rank_weights, _ = linear_rank_probabilities(self.swarm.size)

            # Compute the weighted average according to their ranking.
            g_best = np.average(all_positions, weights=rank_weights, axis=0).tolist()

            # Finally normalize them to
            # account for probabilities.
            for i in range(self.n_cols):
                # Avoid errors with scalar values.
                if not np_isscalar(g_best[i]):
                    g_best[i] /= fast_sum(np_array(g_best[i]))

        elif params.mode.lower() == "g_best":

            # Get the (global) swarm's best particle position.
            g_best = self.swarm.best_particle().position
        else:
            raise ValueError(f"Unknown operating mode: {params.mode}."
                             f" Use 'fipso' or 'g_best'")
        # _end_if_

        # Inertia weight parameter.
        w = params.w0

        for i, (particle_i, c1, c2) in enumerate(zip(self.swarm.population,
                                                     cogntv, social)):
            # Get the old position (as list).
            x_old = particle_i.position

            # Get the personal best position.
            p_best = particle_i.best_position

            # Update all velocity values.
            for j, (xk, vk) in enumerate(zip(x_old, self._velocities[i])):
                # NOTE: Because 'vk' is passed by reference,
                # updating the equations in three steps will
                # not create a new array thus all operations
                # will happen in place.
                vk *= w
                vk += c1[j] * np_subtract(p_best[j], xk)
                vk += c2[j] * np_subtract(g_best[j], xk)
    # _end_def_

    def update_positions(self) -> None:
        """
        Updates the positions of the particles in the swarm.

        :return: None.
        """
        # Update all particle positions.
        self.swarm.set_positions(self._velocities)
    # _end_def_

    def reset_all(self) -> None:
        """
        Resets the particle positions, velocities
        and clear all the statistics dictionary.

        :return: None.
        """
        # Randomize particle velocities.
        self.generate_uniform_velocities()

        # Randomize particle positions.
        self.generate_random_positions()

        # Clear all the internal bookkeeping.
        self.clear_all()
    # _end_def_

    def calculate_spread(self) -> float:
        """
        Calculates a spread measure for the particle positions.

        A value close to '0' indicates the swarm is converging
        to a single value. On the contrary a value close to '1'
        indicates the swarm is still spread around the search
        space.

        :return: an estimated measure (float) for the spread of
                 the particles.
        """
        # Extract the particle positions as a list.
        positions = self.swarm.positions_as_list()

        # Feature data holder.
        field = defaultdict(list)

        # Extract the data for each
        # feature block separately.
        for particle in positions:
            for i, block in enumerate(particle):
                field[i].append(block)
        # _end_for_

        # Preallocate a vector (one for each field).
        per_field = np.empty(len(field))

        # Calculate the spread per data field.
        for n, data in field.items():

            # The Block type will determine which
            # method we will use for the spread.
            b_type = self.swarm[0][n].block_t

            # Convert the data to array.
            data_arr = np.array(data)

            # Make sure it has two dimensions.
            if data_arr.ndim == 1:
                data_arr = data_arr[:, np.newaxis]

            # In categorical data the array is already in 2D.
            per_field[n] = spread_methods[b_type](data_arr,
                                                  normal=True)
        # _end_for_

        # Return the median value of all spreads.
        return np.median(per_field).item()
    # _end_def_

# _end_class_
