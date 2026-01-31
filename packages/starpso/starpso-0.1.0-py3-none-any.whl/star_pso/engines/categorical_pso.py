from collections import defaultdict
from functools import cached_property

import numpy as np
from numba import njit
from numpy.typing import NDArray
from numpy import subtract as np_subtract

from star_pso.utils import VOptions
from star_pso.engines.generic_pso import GenericPSO
from star_pso.utils.auxiliary import (SpecialMode,
                                      nb_clip_inplace,
                                      nb_median_kl_divergence)
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
__all__ = ["CategoricalPSO", "fast_sum"]


class CategoricalPSO(GenericPSO):
    """
    Description:

    This implements a simplified variant of the original ICPSO algorithm as described in:

    - Strasser, S., Goodman, R., Sheppard, J., et al. "A new discrete particle swarm
      optimization algorithm", Proceedings of 2016 Genetic and Evolutionary Computation
      Conference (GECCO) 16, ACM Press, Denver, Colorado, USA, pp. 53-60.
    """

    def __init__(self, variable_sets: list, permutation_mode: bool = False,
                 **kwargs) -> None:
        """
        Default initializer of the CategoricalPSO class.

        :param variable_sets: this is list with the sets
                              (one for each optimization variable).

        :param permutation_mode: (bool) if True it will sample
                                 permutations of the valid sets.
        """

        # First call the super initializer.
        super().__init__(**kwargs)

        # Local copy of the variable sets.
        self._valid_sets = variable_sets

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

        # Set the special mode to Categorical.
        self._special_mode = SpecialMode.CATEGORICAL
    # _end_def_

    @cached_property
    def size_of_sets(self) -> list[int]:
        """
        Compile a list with the sizes of the valid sets.
        To avoid recomputing the list over and over again
        we decorate it with @cached_property.

        :return: a list with the sizes of the valid sets.
        """
        return [len(k) for k in self._valid_sets]
    # _end_def_

    def generate_uniform_velocities(self) -> None:
        """
        Generates random uniform velocities
        for the categorical variable positions.

        :return: None.
        """
        # Get the length of each set.
        size_k = self.size_of_sets

        # Here we generate the random velocities
        # in a short uniform range, according to
        # the size of the variable set.
        for i in range(self.n_rows):
            for j in range(self.n_cols):
                self._velocities[i, j] = GenericPSO.rng.uniform(-0.1, +0.1,
                                                                size=size_k[j])
    # _end_def_

    def generate_random_positions(self) -> None:
        """
        Generate the population of particles positions setting
        their probabilities to 1/L (for all possible L states).

        :return: None.
        """
        # Get the length of each set.
        size_k = self.size_of_sets

        # Reset the probabilities to uniform values.
        for i in range(self.n_rows):
            for j in range(self.n_cols):
                # Get the length of the j-th set.
                size_j = size_k[j]

                # Set the variables uniformly.
                self.swarm[i][j] = np.ones(size_j) / size_j
    # _end_def_

    def sample_categorical_values(self, positions) -> None:
        """
        Samples an actual categorical position based on
        particle's probabilities and valid set for each
        particle position in the swarm.

        :return: None.
        """
        # Local copy of the valid sets.
        local_sets = self._valid_sets

        # Loop over all positions.
        for x_pos in positions:

            # Each position is sampled according to its
            # particle probabilities and its valid set.
            for j, (set_j, probs_j) in enumerate(zip(local_sets, x_pos)):

                # Sample an item according to its probability.
                # WARNING: shuffle option MUST be set to False!
                x_pos[j] = GenericPSO.rng.choice(set_j,
                                                 p=probs_j,
                                                 shuffle=False)
    # _end_def_

    def sample_permutation_values(self, positions) -> None:
        """
        Samples a permutation from a given set of variables.
        It is used in problems like the 'Traveling Salesman'.

        It is assumed that all particle variables have the
        same valid set of values.

        :return: None.
        """
        # Local copy of the valid sets.
        local_sets = self._valid_sets

        # Create a range of values.
        random_index = np.arange(self.n_cols, dtype=int)

        # Shuffle in place. This is used to avoid introducing
        # biasing by using always the same order of blocks to
        # select first their categorical sample value.
        CategoricalPSO.rng.shuffle(random_index)

        # Loop over all positions.
        for x_pos in positions:

            # Auxiliary set.
            exclude_idx = set()

            # Scan the particle using the random index.
            for j in random_index:
                # Get the j-th element.
                xj = x_pos[j]

                # Reference of the j-th set.
                set_j = local_sets[j]

                # Sort in reverse order from high to low.
                for k in xj.argsort()[::-1]:
                    # Continue until we find the first
                    # unused element of the valid set.
                    if k not in exclude_idx:
                        # Assign the element in
                        # the position[i, j].
                        x_pos[j] = set_j[k]

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
        cogntv = GenericPSO.rng.uniform(0, params.c1, size=arr_shape)

        # Pre-sample the social coefficients.
        social = GenericPSO.rng.uniform(0, params.c2, size=arr_shape)

        # Get the global best.
        if params.mode.lower() == "fipso":

            # In the fully informed case we compute a weighted average
            # from all the positions of the swarm.
            g_best = GenericPSO.fully_informed(self.swarm.population)

            # Finally normalize them to
            # account for probabilities.
            for i in range(self.n_cols):
                g_best[i] /= fast_sum(g_best[i])

        elif params.mode.lower() == "g_best":

            # Get the (global) swarm's best particle position.
            g_best = self.swarm.best_particle().position
        else:
            raise ValueError(f"Unknown operating mode: {params.mode}. "
                             f"Use 'fipso' or 'g_best'")
        # _end_if_

        # Inertia weight parameter.
        w = params.w0

        for i, (particle_i, c1, c2) in enumerate(zip(self.swarm.population,
                                                     cogntv, social)):
            # Get the i-th particle's position.
            x_i = particle_i.position

            # Get the personal best position.
            p_best = particle_i.best_position

            # Update all velocities.
            for j, (xk, vk) in enumerate(zip(x_i, self._velocities[i])):
                # NOTE: Because 'vk' is passed by reference,
                # updating the equations in three steps will
                # not create a new array thus all operations
                # will happen in place.
                vk *= w
                vk += c1[j] * np_subtract(p_best[j], xk)
                vk += c2[j] * np_subtract(g_best[j], xk)

                # Ensure the velocities are within limits.
                nb_clip_inplace(vk, -0.5, +0.5)
    # _end_def_

    def update_positions(self) -> None:
        """
        Updates the positions of the particles in the swarm.

        :return: None.
        """
        # Update all particle positions.
        for particle, v_upd in zip(self.swarm.population,
                                   self._velocities):
            # Process each position separately.
            for x_j, v_j in zip(particle.position, v_upd):
                # NOTE:  All operations happen inplace to avoid
                # reallocating memory and provide some speed up
                # to the update process.
                x_j += v_j

                # Ensure the values stay within limits.
                nb_clip_inplace(x_j, 0.0, 1.0)

                # Ensure there will be at least one
                # element with positive probability.
                if np.all(np.isclose(x_j, 0.0)):
                    x_j[GenericPSO.rng.integers(len(x_j))] = 1.0
                # _end_if_

                # Normalize to account for probabilities.
                x_j /= fast_sum(x_j)
        # _end_for_
    # _end_def_

    def reset_all(self) -> None:
        """
        Resets the particle positions, velocities
        and clear all the statistics dictionary.

        :return: None.
        """
        # Reset particle velocities.
        self.generate_uniform_velocities()

        # Reset particle positions.
        self.generate_random_positions()

        # Clear all the internal bookkeeping.
        self.clear_all()
    # _end_def_

    def calculate_spread(self) -> float:
        """
        Calculates a spread measure for the particle positions
        using the (normalized) median KL divergence.

        A value close to '0' indicates the swarm is converging
        to a single value. On the contrary a value close to '1'
        indicates the swarm is still spread around the search
        space.

        :return: an estimated measure (float) for the spread of
                 the particles.
        """
        # Extract the positions in a 2D numpy array.
        positions = self.swarm.positions_as_array()

        # Feature data holder.
        field = defaultdict(list)

        # Extract the data for each
        # feature block separately.
        for particle in positions:
            for i, data_block in enumerate(particle):
                field[i].append(data_block)
        # _end_for_

        # Preallocate a vector (one for each field).
        per_field = np.empty(len(field))

        # Calculate the spread per field.
        for n, data in field.items():

            # Convert the data to array.
            data_array = np.array(data)

            # Make sure it has two dimensions.
            if data_array.ndim == 1:
                data_array = data_array[:, np.newaxis]

            # Categorical data array is already in 2D.
            per_field[n] = nb_median_kl_divergence(data_array,
                                                   normal=True)
        # _end_for_

        # Return the median value of all fields.
        return np.median(per_field).item()
    # _end_def_

# _end_class_
