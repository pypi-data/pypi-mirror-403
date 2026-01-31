from copy import deepcopy
from numbers import Number
from functools import cache
from collections import namedtuple
from collections.abc import Iterable

import numpy as np
from numpy import array
from numpy.typing import ArrayLike
from numpy.random import (default_rng, Generator)

from star_pso.utils import ScalarOrArray
from star_pso.utils.auxiliary import (BlockType,
                                      nb_clip_item,
                                      nb_clip_array)

# Create a tuple to pack some inputs.
Params = namedtuple("Params",
                    ["v_new", "x_old", "lower_bound", "upper_bound"])
"""
    Create a tuple to pack some input parameters:
    
    - v_new: new velocity
    - x_old: old position
    - lower_bound: lower bounds for position (or velocity)
    - upper_bound: upper bounds for position (or velocity)
"""

# Public interface.
__all__ = ["DataBlock"]


class DataBlock:
    """
    Description:

       This is the main class that encodes the data of a single particle variable.
       The class encapsulates not only the data (position and best position), but
       also the way that this data can be updated using a specific type dependent
       functions.
    """

    # Make a random number generator (class variable).
    rng: Generator = default_rng()
    """
    Random Number Generator for the whole class.
    """

    # Object variables.
    __slots__ = ("_btype", "_valid_set", "_position", "_best_position",
                 "_lower_bound", "_upper_bound", "_copy_best")

    def __init__(self,
                 position: ScalarOrArray,
                 btype: BlockType,
                 valid_set: list | tuple | None = None,
                 lower_bound: list | Number | None = None,
                 upper_bound: list | Number | None = None) -> None:
        """
        Default initializer for the DataBlock class.

        :param btype: the type of the data block (e.g. FLOAT, INTEGER, etc.).

        :param position: initial position (i.e. initial value in the block).

        :param valid_set: the set of values in the case of CATEGORICAL type.

        :param lower_bound: the lower bound(s) in the search space.

        :param upper_bound: the upper bound(s) in the search space.
        """

        # Sanity check.
        if not isinstance(btype, BlockType):
            raise TypeError(f"{self.__class__.__name__}: Unknown Block Type {btype}.")
        # _end_if_

        # Assign the data block type.
        self._btype = btype

        # Copy the initial position.
        if np.isscalar(position):
            # Make simple copies.
            self._position = position
            self._best_position = position

            # Simple copy to scalar method.
            self._copy_best = self._copy_to_scalar
        else:
            # Make array copies.
            self._position = array(position, copy=True)
            self._best_position = array(position, copy=True)

            # Get a local reference of the copy-to.
            self._copy_best = self._copy_to_array
        # _end_if_

        # Check if the lower and upper bounds are set.
        if (lower_bound is not None) and (upper_bound is not None):
            # Make sure they are numpy arrays.
            self._lower_bound = np.array(lower_bound)
            self._upper_bound = np.array(upper_bound)

            # Check if the boundaries are set correctly.
            if np.any(self._lower_bound > self._upper_bound):
                raise ValueError(f"{self.__class__.__name__}: "
                                 f"Lower and Upper boundaries are set incorrectly.")
        else:
            # Set them to default.
            self._lower_bound = None
            self._upper_bound = None
        # _end_if_

        # Get the valid set (categorical variables).
        self._valid_set = valid_set
    # _end_def_

    def _copy_to_scalar(self, x) -> None:
        """
        Simple copy to scalar method. It is used to provide
        a dynamic interface when copy to the best position.

        :param x: scalar to be copied to best_position.

        :return: None.
        """
        self._best_position = x
    # _end_def_

    def _copy_to_array(self, x) -> None:
        """
        Simple copy to array method. It is used to provide
        a dynamic interface when copy to the best position.

        :param x: array to be copied to best_position.

        :return: None.
        """
        np.copyto(self._best_position, x)
    # _end_def_

    @classmethod
    def set_seed(cls, new_seed=None) -> None:
        """
        Sets a new seed for the random number generator.

        :param new_seed: New seed value (default=None).

        :return: None.
        """
        # Re-initialize the class variable.
        cls.rng = default_rng(seed=new_seed)
    # _end_def_

    @property
    def valid_set(self) -> list | tuple:
        """
        Accessor (getter) method for the valid set.

        :return: The set of valid values of a CATEGORICAL block.
        """
        return self._valid_set
    # _end_def_

    @staticmethod
    def upd_float(params: Params) -> float:
        """
        It is used to update the positions of continuous
        'float' data blocks.

        :param params: tuple which contains the parameters
                       for the update equation.

        :return: a new (float) position.
        """
        # Ensure the new position stays within bounds.
        return nb_clip_item(params.x_old + params.v_new,
                            params.lower_bound,
                            params.upper_bound)
    # _end_def_

    @staticmethod
    def upd_integer(params: Params) -> int:
        """
        It is used to update the positions of discrete 'int'
        data blocks.

        :param params: tuple which contains the parameters
                       for the update equation.

        :return: a new (int) position.
        """
        # Round the new position and convert it to int.
        x_new = np.rint(params.x_old + params.v_new).astype(int)

        # Ensure the new position stays within bounds.
        return nb_clip_item(x_new, params.lower_bound, params.upper_bound)
    # _end_def_

    @classmethod
    def upd_binary(cls, params: Params) -> int:
        """
        It is used to update the positions of discrete
        'binary' data blocks.

        :param params: tuple which contains the parameters
                       for the update equation.

        :return: a new (binary) position.
        """
        # Compute the sigmoid function value.
        threshold = 1.0 / (1.0 + np.exp(-params.v_new))

        # Assign the binary value using U(0,1).
        return 1 if threshold > cls.rng.random() else 0
    # _end_def_

    @classmethod
    def upd_categorical(cls, params: Params) -> ArrayLike:
        """
        It is used to update the positions of discrete
        'categorical' data blocks.

        :param params: tuple which contains the parameters
                       for the update equation.

        :return: a new array like with probabilities.
        """
        # Ensure the velocities are within limits.
        v_new = nb_clip_array(params.v_new, -0.5, +0.5)

        # Ensure the vector stays within limits.
        x_new = nb_clip_array(params.x_old + v_new, 0.0, 1.0)

        # Ensure there will be at least one
        # element with positive probability.
        if all(np.isclose(x_new, 0.0)):
            x_new[cls.rng.integers(len(x_new))] = 1.0
        # _end_if_

        # Normalize (to account for probabilities).
        return x_new / np.sum(x_new, dtype=float)
    # _end_def_

    @staticmethod
    @cache
    def update_methods() -> dict:
        """
        Return a dictionary with keys the method names
        and their corresponding update methods as values.

        :return: a (cached) dictionary with functions
                 that correspond to the correct block types.
        """
        return {BlockType.FLOAT: DataBlock.upd_float,
                BlockType.BINARY: DataBlock.upd_binary,
                BlockType.INTEGER: DataBlock.upd_integer,
                BlockType.CATEGORICAL: DataBlock.upd_categorical}
    # _end_def_

    @classmethod
    def init_float(cls, **kwargs) -> float:
        """
        It is used to initialize randomly the positions
        of a continuous 'float' data blocks.

        :param kwargs: contains the required parameters.

        :return: a new random (float) position.
        """
        # Ensure the random position stays within bounds.
        return cls.rng.uniform(kwargs["lower_bound"],
                               kwargs["upper_bound"])
    # _end_def_

    @classmethod
    def init_integer(cls, **kwargs) -> int:
        """
        It is used to initialize randomly the positions
        of a discrete 'int' data blocks.

        :param kwargs: contains the required parameters.

        :return: a new random (integer) position.
        """
        # Ensure the random position stays within bounds.
        return cls.rng.integers(kwargs["lower_bound"],
                                kwargs["upper_bound"],
                                endpoint=True,
                                dtype=int)
    # _end_def_

    @classmethod
    def init_binary(cls, **kwargs) -> int:
        """
        It is used to initialize randomly the positions
        of a discrete 'binary' data blocks.

        :param kwargs: contains the required parameters.

        :return: a new random (integer) position.
        """
        # Ensure the random position stays within bounds.
        return cls.rng.integers(low=0, high=1,
                                endpoint=True,
                                size=kwargs["n_vars"],
                                dtype=int).item()
    # _end_def_

    @staticmethod
    def init_categorical(**kwargs) -> int:
        """
        It is used to initialize randomly the positions
        of a discrete 'categorical' data blocks.

        :param kwargs: contains the required parameters.

        :return: a new random (integer) position.
        """
        # Get the number of variables.
        n_vars = kwargs["n_vars"]

        # Set the variables uniformly.
        return np.ones(n_vars)/n_vars
    # _end_def_

    @staticmethod
    @cache
    def init_methods() -> dict:
        """
        Create a dictionary with method names as keys and their
        corresponding initialization methods as values.

        :return: a (cached) dictionary with functions that
                 correspond to the correct block types.
        """
        return {BlockType.FLOAT: DataBlock.init_float,
                BlockType.BINARY: DataBlock.init_binary,
                BlockType.INTEGER: DataBlock.init_integer,
                BlockType.CATEGORICAL: DataBlock.init_categorical}
    # _end_def_

    def reset_position(self) -> None:
        """
        This method provides a public interface for the reset
        of the new positions, for all types of data blocks.

        :return: None.
        """
        # Get the dictionary with the methods.
        method_dict = DataBlock.init_methods()

        # Differentiate between scalar and vector data block.
        n_vars = 1 if np.isscalar(self._position) else len(self._position)

        # Assign the function value to the new position.
        self._position = method_dict[self._btype](n_vars=n_vars,
                                                  lower_bound=self._lower_bound,
                                                  upper_bound=self._upper_bound)
    # _end_def_

    @property
    def position(self) -> ScalarOrArray:
        """
        Accessor (getter) of the data block's position.

        :return: the position value of the data block.
        """
        return self._position
    # _end_def_

    @position.setter
    def position(self, v_new: Number) -> None:
        """
        This method provides the public interface for setting
        the new position calculation for all types of data blocks.

        :param v_new: new velocity value.

        :return: None.
        """
        # Get the dictionary with the methods.
        method_dict = DataBlock.update_methods()

        # Pack the parameters in a tuple.
        params = Params(v_new=v_new,
                        x_old=self._position,
                        lower_bound=self._lower_bound,
                        upper_bound=self._upper_bound)

        # Assign the function values to the new position.
        self._position = method_dict[self._btype](params)
    # _end_def_

    @property
    def best_position(self) -> ScalarOrArray:
        """
        Accessor (getter) of the data block's best position.

        :return: the best recorded position value of the data block.
        """
        return self._best_position
    # _end_def_

    @best_position.setter
    def best_position(self, new_value: ScalarOrArray) -> None:
        """
        This method provides the public interface for setting
        the new best position of data block.

        :param new_value: new best position value.

        :return: None.
        """
        self._copy_best(new_value)
    # _end_def_

    @property
    def block_t(self) -> BlockType:
        """
        Accessor (getter) of the data block's type.

        :return: the data block type.
        """
        return self._btype
    # _end_def_

    # Helper function that compares
    # scalars and Iterables (lists).
    @staticmethod
    def _check_equality(a, b) -> bool:
        """
        Compare two objects and return True if equal.
        Handles scalar booleans and general iterables.

        :param a: 1st object to compare.
        :param b: 2nd object to compare.

        :return: the bool outcome of a == b.
        """
        # Do the comparison.
        condition = a == b

        # If the result has an 'all' method
        # (e.g. numpy / pandas) then use it.
        all_method = getattr(condition, "all", None)

        # Quick exit in numpy.
        if callable(all_method):
            return bool(condition.all())

        # Otherwise fall back to standard Python.
        return all(condition) if isinstance(condition,
                                            Iterable) else condition
    # _end_def_

    def __eq__(self, other) -> bool:
        """
        Compares the data block of self with the other and
        returns True if they are identical, otherwise False.

        :param other: data block to compare.

        :return: True if the data blocks are identical else False.
        """
        # Check if they are the same instance.
        if self is other:
            return True
        # _end_if_

        # Make sure both items are of type 'DataBlock'.
        if not isinstance(other, DataBlock):
            return NotImplemented
        # _end_if_

        # Local cache for speed.
        check_it = self._check_equality

        # First check their block type.
        if self._btype == other._btype:

            # Check the positions.
            positions_are_equal = check_it(self._position,
                                           other._position)
            # Check valid sets.
            valid_sets_are_equal = (True if self._valid_set is None
                                    else self._valid_set == other._valid_set)

            # If the bounds are not given (None) we set the conditions to True.
            if (self._lower_bound is not None) and (self._upper_bound is not None):
                # Check lower bounds.
                lower_bounds_are_equal = check_it(self._lower_bound,
                                                  other._lower_bound)
                # Check upper bounds.
                upper_bounds_are_equal = check_it(self._upper_bound,
                                                  other._upper_bound)
            else:
                lower_bounds_are_equal = True
                upper_bounds_are_equal = True
            # _end_if_

            # Return the logical AND from all conditions.
            return (positions_are_equal and valid_sets_are_equal and
                    lower_bounds_are_equal and upper_bounds_are_equal)
        # _end_if_

        # If you get here return False.
        return False
    # _end_def_

    def __deepcopy__(self, memo: dict) -> "DataBlock":
        """
        This custom method overrides the default deepcopy method.

        :param memo: Dictionary of objects already copied during
                     the current copying pass.

        :return: a new identical "clone" of the self object.
        """

        # Create a new instance.
        new_object = DataBlock.__new__(DataBlock)

        # Don't copy self reference.
        memo[id(self)] = new_object

        # Deep copy the position (ScalarOrArray).
        setattr(new_object, "_position", deepcopy(self._position))

        # Deep copy the best position (ScalarOrArray).
        setattr(new_object, "_best_position", deepcopy(self._best_position))

        # Deep copy the valid set (list/tuple).
        setattr(new_object, "_valid_set", deepcopy(self._valid_set))

        # Simple copy the lower/upper bounds (float).
        setattr(new_object, "_lower_bound", self._lower_bound)
        setattr(new_object, "_upper_bound", self._upper_bound)

        # Simple copy the block type value (enum).
        setattr(new_object, "_btype", self._btype)

        # Simple copy of the copy-best method (callable).
        setattr(new_object, "_copy_best", self._copy_best)

        # Return an identical datablock.
        return new_object
    # _end_def_

# _end_class_
