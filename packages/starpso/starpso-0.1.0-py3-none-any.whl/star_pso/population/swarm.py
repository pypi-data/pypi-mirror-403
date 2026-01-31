from math import isnan
from typing import Union
from copy import deepcopy
from operator import attrgetter

from numpy import array
from numpy.typing import ArrayLike, NDArray

from star_pso.utils.auxiliary import BlockType
from star_pso.population.particle import Particle
from star_pso.population.jat_particle import JatParticle

# Make a type alias for the particles types.
SwarmParticle = Union[Particle, JatParticle]

# Public interface.
__all__ = ["Swarm", "SwarmParticle"]


class Swarm:
    """
    Description:

        Implements a dataclass for the Swarm entity. This class is responsible
        for holding and organizing the individual solutions (i.e. particles),
        of the optimization problem during the optimization process.
    """

    # Object variables.
    __slots__ = ("_population", "_has_categorical")

    def __init__(self, population: list[SwarmParticle],
                 copy: bool = False) -> None:
        """
        Default initializer for the Swarm class.

        :param population: a list of SwarmParticles.

        :param copy: (bool) if True it will create a deepcopy of the population.

        :return: None.
        """

        # Assign the population list (or a deepcopy of it).
        self._population = deepcopy(population) if copy else population

        # Set the default value for the categorical flag.
        self._has_categorical = False

        # This ensures that in case of JatParticles the
        # flag will be set accurately.
        if isinstance(self._population[0], JatParticle):

            for block in self._population[0]:

                if block.block_t == BlockType.CATEGORICAL:
                    self._has_categorical = True
                    break
        # _end_if_
    # _end_def_

    @property
    def size(self) -> int:
        """
        Returns the size (length) of the population.
        Note that the size of the population is not
        expected to change during the optimization.

        :return: (int) the length of the population.
        """
        return len(self._population)
    # _end_def_

    @property
    def has_categorical(self) -> bool:
        """
        Accessor (getter) of the 'has_categorical' flag.

        :return: true if the data block is CATEGORICAL.
        """
        return self._has_categorical
    # _end_def_

    @property
    def global_best_index(self) -> int:
        """
        Accessor of the global best index.

        :return: the index (int) of the best.
        """
        return self._population.index(self.best_particle())
    # _end_def_

    @property
    def population(self) -> list[SwarmParticle]:
        """
        Accessor of the population list of the swarm.

        :return: the list (of particles) of the swarm.
        """
        return self._population
    # _end_def_

    def best_particle(self) -> SwarmParticle:
        """
        Auxiliary method that returns the particle with the
        highest function value. Safeguard with ignoring NaNs.

        :return: Return the particle with the highest value.
        """
        return max((p for p in self._population if not isnan(p.value)),
                   key=attrgetter("value"), default=None)
    # _end_def_

    def best_n(self, n: int = 1) -> list[SwarmParticle]:
        """
        Auxiliary method that returns the best 'n' particles
        with the highest objective function value.

        :param n: the number of the best chromosomes.

        :return: Return a list with the 'n' top particles.
        """
        # Make sure 'n' is positive integer.
        if not isinstance(n, int) or n <= 0:
            raise TypeError(f"{self.__class__.__name__}: "
                             f"Input must be a positive integer.")
        # _end_if_

        # Ensure the number of return particles do not exceed
        # the size of the swarm.
        if n > len(self._population):
            raise ValueError(f"{self.__class__.__name__}: "
                             f"Best {n} exceeds swarm size.")
        # _end_if_

        # Sort the swarm in descending order.
        sorted_swarm = sorted([p for p in self._population if not isnan(p.value)],
                              key=attrgetter("value"), reverse=True)

        # Return the best 'n' particles.
        return sorted_swarm[0:n]
    # _end_def_

    def function_values(self) -> NDArray:
        """
        Get the objectives function values of all the swarm.

        :return: A numpy array (vector) with all the values.
        """
        return array([p.value for p in self._population])
    # _end_def_

    def value_at(self, index: int) -> float:
        """
        Get the function value of an individual particle of the swarm.

        :param index: Position of the individual in the population.

        :return: The function value (float).
        """
        return self._population[index].value
    # _end_def_

    def position_at(self, index: int) -> ArrayLike:
        """
        Get the position vector of an individual particle of the swarm.

        :param index: Position of the individual in the population.

        :return: The position vector (array).
        """
        return self._population[index].position
    # _end_def_

    def positions_as_array(self) -> NDArray:
        """
        Get the particle positions of all the swarm.

        :return: A numpy array with all the positions.
        """
        return array([p.position for p in self._population])
    # _end_def_

    def best_positions_as_array(self) -> NDArray:
        """
        Get the particle best positions of all the swarm.

        :return: A numpy array with all the best positions.
        """
        return array([p.best_position for p in self._population])
    # _end_def_

    def positions_as_list(self) -> list:
        """
        Get the particle positions of all the swarm.

        :return: A list with all the positions.
        """
        return [p.position for p in self._population]
    # _end_def_

    def update_local_best(self) -> None:
        """
        Update the particles in the swarm to
        their local best values and positions.

        :return: None.
        """
        # Go through all particles.
        for p in self._population:

            # If the current best value is
            # higher than make the updates.
            if p.value > p.best_value:

                # Simple copy of the function value.
                p.best_value = p.value

                # Copy of the current position.
                # NOTE: 'best_position' handles
                #       the copy internally.
                p.best_position = p.position
    # _end_def_

    def set_positions(self, new_positions: NDArray) -> None:
        """
        Sets the positions of the particles in the swarm.

        :param new_positions: (NDArray) the new positions
                              of the particles.
        :return: None.
        """
        # Update all swarm particle to new positions.
        for particle, x_new, in zip(self._population,
                                    new_positions):
            particle.position = x_new
    # _end_def_

    def __len__(self) -> int:
        """
        Accessor of the total size of the population.

        :return: the length (int) of the swarm.
        """
        return len(self._population)
    # _end_def_

    def __getitem__(self, index: int) -> SwarmParticle:
        """
        Get the item at position 'index'.

        :param index: (int) the position that we want to return.

        :return: the reference to a Particle.
        """
        return self._population[index]
    # _end_def_

    def __setitem__(self, index: int, item: SwarmParticle) -> None:
        """
        Set the 'item' at position 'index'.

        :param index: (int) the position that we want to access.

        :param item: (Particle) object we want to assign in the population.

        :return: None.
        """
        self._population[index] = item
    # _end_def_

    def __contains__(self, item: SwarmParticle) -> bool:
        """
        Check for membership.

        :param item: an input particle that we want to check.

        :return: true if the 'item' belongs in the swarm population.
        """
        return item in self._population
    # _end_def_

# _end_class_
