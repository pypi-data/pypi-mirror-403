from math import inf
from copy import deepcopy

from star_pso.utils.data_block import DataBlock

# Public interface.
__all__ = ["JatParticle"]


class JatParticle:
    """
    Description:

        Implements a dataclass for the 'Jack of all trades' particle.
        This dataclass maintains a container (list of data blocks) and
        the rest of the information is held in its data blocks.
    """

    # Object variables.
    __slots__ = ("_container", "_value", "_best_value")

    def __init__(self, container: list[DataBlock], value: float = -inf,
                 best_value: float = -inf) -> None:
        """
        Default constructor of the JatParticle class.
        """
        # Define the particle as a list of DataBlocks.
        self._container = container

        # Make sure it's the correct type.
        if not isinstance(value, float):
            raise TypeError(f"{self.__class__.__name__}: Value must be a float")
        # _end_if_

        # Assign the initial value.
        self._value = value

        # Make sure it's the correct type.
        if not isinstance(best_value, float):
            raise TypeError(f"{self.__class__.__name__}: Best value must be a float")
        # _end_if_

        # Assign the initial best value.
        self._best_value = best_value
    # _end_def_

    @property
    def container(self) -> list[DataBlock]:
        """
        Accessor of the container list of the particle.

        :return: the list (of data blocks) of the particle.
        """
        return self._container
    # _end_def_

    @property
    def size(self) -> int:
        """
        Returns the size (or length) of the particle.

        Since the size of the container doesn't change
        dynamically we can cache this value for faster
        retrieval.

        :return: (int) the length of the particle.
        """
        return len(self._container)
    # _end_def_

    @property
    def position(self) -> list:
        """
        Accessor of the particle's position.

        :return: a list with each data block position.
        """
        return [blk.position for blk in self._container]
    # _end_def_

    @position.setter
    def position(self, v_new) -> None:
        """
        Sets a new value to the particle's position
        by updating each data block in the container.

        :param v_new: new velocity values.

        :return: None.
        """
        for block, v in zip(self._container, v_new):
            # This calls internally the 'right'
            # method to update each block type.
            block.position = v
    # _end_def_

    @property
    def best_position(self) -> list:
        """
        Accessor of the particle's best position.

        :return: a list with each data block best position.
        """
        return [block.best_position for block in self._container]
    # _end_def_

    @best_position.setter
    def best_position(self, new_vector: list) -> None:
        """
        Updates the 'best position' in the particle object.

        :param new_vector: (list) new best position vector.

        :return: None.
        """
        for block, new_best in zip(self._container, new_vector):
            block.best_position = new_best
    # _end_def_

    @property
    def value(self) -> float:
        """
        Accessor of the current function value.

        :return: (float) function value.
        """
        return self._value
    # _end_def_

    @value.setter
    def value(self, new_value: float) -> None:
        """
        Updates the best function value in the particle.

        :param new_value: (float) new best function value.

        :return: None.
        """
        self._value = new_value
    # _end_def_

    @property
    def best_value(self) -> float:
        """
        Accessor of the best function value.

        :return: (float) best function value.
        """
        return self._best_value
    # _end_def_

    @best_value.setter
    def best_value(self, new_value: float) -> None:
        """
        Updates the best function value in the particle.

        :param new_value: (float) new best function value.

        :return: None.
        """
        self._best_value = new_value
    # _end_def_

    def reset_position(self) -> None:
        """
        Iterate through all the data blocks in
        the container and reset their positions.

        :return: None.
        """
        for block in self._container:
            block.reset_position()
    # _end_def_

    def __getitem__(self, index: int) -> DataBlock:
        """
        Get the DataBlock item at position 'index'.

        :param index: (int) the position that we want to return.

        :return: the reference to the object in position index.
        """
        return self._container[index]
    # _end_def_

    def __setitem__(self, index: int, item: DataBlock) -> None:
        """
        Set the DataBlock 'item' at position 'index'.

        :param index: (int) the position that we want to access.

        :param item: (DataBlock) object we want to assign in the
                     particle.

        :return: None.
        """
        self._container[index] = item
    # _end_def_

    def __len__(self) -> int:
        """
        Accessor of the total length of the particle.

        :return: the length (int) of the particle.
        """
        return len(self._container)
    # _end_def_

    def __eq__(self, other) -> bool:
        """
        Compares the jat_particle of self with the other and
        returns True if they are identical, otherwise False.

        :param other: jat_particle to compare.

        :return: True if their containers have the same data
                 blocks.
        """
        # Check if they are the same instance.
        if self is other:
            return True
        # _end_if_

        # Make sure both objects are of the same type.
        if not isinstance(other, JatParticle):
            return NotImplemented
        # _end_if_

        # Compare directly their two containers.
        return self._container == other.container
    # _end_def_

    def __deepcopy__(self, memo: dict) -> "JatParticle":
        """
        This custom method overrides the default deepcopy method.

        :param memo: dictionary of objects already copied during
                     the current copying pass.

        :return: a new identical "clone" of the self object.
        """
        # Create a new instance.
        new_object = JatParticle.__new__(JatParticle)

        # Don't copy self reference.
        memo[id(self)] = new_object

        # Deep copy the container list.
        setattr(new_object, "_container", deepcopy(self._container, memo))

        # Simply copy the value (float).
        setattr(new_object, "_value", self._value)

        # Simply copy the best value (float).
        setattr(new_object, "_best_value", self._best_value)

        # Return an identical particle.
        return new_object
    # _end_def_

    def __contains__(self, item: DataBlock) -> bool:
        """
        Check for membership.

        :param item: an input DataBlock that we want to check.

        :return: true if the 'item' belongs in the container.
        """
        return item in self._container
    # _end_def_

    def __str__(self) -> str:
        """
        Override to print a readable string presentation
        of the JatParticle object.

        :return: a string representation of a JatParticle.
        """
        return f"{self.__class__.__name__}: "\
               f"(Position, Value) = ({self.position, self.value})."
    # _end_def_

# _end_class_
