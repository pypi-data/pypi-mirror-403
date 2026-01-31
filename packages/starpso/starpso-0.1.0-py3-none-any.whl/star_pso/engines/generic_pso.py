from os import cpu_count
from copy import deepcopy
from operator import attrgetter
from math import inf, fabs, isclose
from collections import deque, defaultdict

from typing import Callable
from joblib import Parallel, delayed

import numpy as np
from numpy.typing import ArrayLike, NDArray
from numpy.random import default_rng, Generator

from star_pso.engines import logger
from star_pso.utils import VOptions
from star_pso.population.swarm import Swarm, SwarmParticle
from star_pso.utils.auxiliary import (time_it, nb_clip_item, SpecialMode,
                                      check_velocity_parameters, nb_cdist,
                                      linear_rank_probabilities)
# Public interface.
__all__ = ["GenericPSO"]


class GenericPSO:
    """
    Description:

        GenericPSO class models the interface of a specific particle swarm
        optimization model or engine. It provides the common variables and
        functionalities that all PSO models should share.

        - J. Kennedy and R. Eberhart (1995). "Particle Swarm Optimization".
          In Proceedings of IEEE International Conference on Neural Networks.
          vol. 4. pp. 1942–1948. doi:10.1109/ICNN.1995.488968.

        - R. Mendes and J. Kennedy and J. Neves (2004). "The fully informed particle
          swarm: simpler, maybe better". In IEEE Transactions on Evolutionary Computation,
          vol. 8, no. 3, pp. 204-210, June 2004, doi: 10.1109/TEVC.2004.826074.

    """

    rng: Generator = default_rng()
    """
    Random Number Generator for the whole class.
    """

    MAX_CPUs: int = 1 if not cpu_count() else cpu_count()
    """
    Set the maximum number of CPUs (at least one).
    """

    # Object variables.
    __slots__ = ("_swarm", "_velocities", "_objective_func", "_upper_bound",
                 "_lower_bound", "_stats", "_items", "_f_evals", "_n_cpus",
                 "_n_rows", "_n_cols", "_special_mode", "_iteration")

    def __init__(self, initial_swarm: Swarm, obj_func: Callable,
                 lower_bound: ArrayLike = None, upper_bound: ArrayLike = None,
                 copy: bool = False, n_cpus: int = None) -> None:
        """
        Default initializer of the GenericPSO class.

        :param initial_swarm: list of the initial population of particles.

        :param obj_func: callable objective function.

        :param lower_bound: lower search space bound.

        :param upper_bound: upper search space bound.

        :param copy: if True it will create a separate (deep) copy of the
                     initial swarm.

        :param n_cpus: number of requested CPUs for the optimization process.
        """

        # Get the swarm population.
        self._swarm = deepcopy(initial_swarm) if copy else initial_swarm

        # Number of particles.
        self._n_rows = len(self._swarm)

        # Size (length) of particle.
        self._n_cols = len(self._swarm[0])

        # Make sure the fitness function is indeed callable.
        if not callable(obj_func):
            raise TypeError(f"{self.__class__.__name__}: "
                            f"Objective function is not callable.")
        # _end_if_

        # Get the objective function.
        self._objective_func = obj_func

        # Check if the lower and upper bounds are set.
        if (lower_bound is not None) and (upper_bound is not None):
            # Make sure they are numpy arrays.
            self._lower_bound = np.asarray(lower_bound)
            self._upper_bound = np.asarray(upper_bound)

            # Check if the boundaries are set correctly.
            if np.any(self._lower_bound > self._upper_bound):
                raise ValueError(f"{self.__class__.__name__}: "
                                 f"Lower and Upper bounds are set incorrectly.")
        else:
            # Set them to default.
            self._lower_bound = None
            self._upper_bound = None
        # _end_if_

        # Get the number of requested CPUs.
        if n_cpus is None:

            # This is the default option.
            self._n_cpus = max(1, GenericPSO.MAX_CPUs-1)
        else:

            # Assign the  requested number, making sure we have
            # enough CPUs and the value entered has the correct
            # type.
            self._n_cpus = max(1, min(GenericPSO.MAX_CPUs-1, int(n_cpus)))
        # _end_if_

        # Log the number of CPUs.
        logger.debug(f"{self.__class__.__name__} uses {self.n_cpus} CPUs.")

        # Dictionary with statistics.
        self._stats = defaultdict(list)

        # Placeholder.
        self._items = None

        # Set velocities to None.
        self._velocities = None

        # Set the function evaluation counter to zero.
        self._f_evals = 0

        # Set the special mode to Normal.
        self._special_mode = SpecialMode.NORMAL

        # Set the iteration counter to zero.
        self._iteration = 0

        # Log the object initialization.
        logger.debug(f"{self.__class__.__name__} initialization complete.")
    # _end_def_

    @property
    def n_cols(self) -> int:
        """
        Accessor (getter) of the number of columns of the swarm matrix
        (i.e. size of particle).

        :return: the n_cols value.
        """
        return self._n_cols
    # _end_def_

    @property
    def n_rows(self) -> int:
        """
        Accessor (getter) of the number of rows of the swarm matrix
        (i.e. number of particles).

        :return: the n_rows value.
        """
        return self._n_rows
    # _end_def_

    @property
    def n_cpus(self) -> int:
        """
        Accessor (getter) of the number of CPUs we will use.

        :return: the n_cpus value.
        """
        return self._n_cpus
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

        # Log the new seed event.
        logger.debug(f"{cls.__name__} random generator has a new seed.")
    # _end_def_

    @staticmethod
    def fully_informed(population: list[SwarmParticle], use_best: bool = False) -> NDArray:
        """
        Uses the input population and computes a weighted average position according to
        the linear ranking of the particles. Those with higher function value also have
        bigger weight in the calculation.

        :param population: list of particles which we want to consider in the calculation
                           of the fully informed best position.

        :param use_best: if True it will use the best_position of each particle to estimate
                         the new weighted best position. Default is False, which means that
                         only the current position is used.

        :return: the weighted best position 'w_best' (as numpy array).
        """

        if use_best:
            # Extract the best positions and convert to numpy array.
            all_positions = np.array([item.best_position for item in sorted(population,
                                                                            key=attrgetter("best_value"))])
        else:
            # Extract the positions and convert to numpy array.
            all_positions = np.array([item.position for item in sorted(population,
                                                                       key=attrgetter("value"))])
        # _end_if_

        # Compute the probabilities.
        p_weights, p_weights_sum = linear_rank_probabilities(len(all_positions))

        # Take a "weighted average" from all the positions of the swarm.
        w_best = np.multiply(all_positions,
                             p_weights[:, np.newaxis]).sum(axis=0) / p_weights_sum

        # Return the weighted best position.
        return w_best
    # _end_def_

    @property
    def iteration(self) -> int:
        """
        Accessor (getter) of the iteration parameter.

        :return: the iteration value.
        """
        return self._iteration
    # _end_def_

    @iteration.setter
    def iteration(self, value: int) -> None:
        """
        Accessor (setter) of the iteration value.

        :param value: (int).
        """
        # Check for correct type and allow only the
        # positive values.
        if not isinstance(value, int) or value < 0:
            raise RuntimeError(f"{self.__class__.__name__}: "
                               f"Iteration value should be positive int: {value}.")
        # Update the iteration value.
        self._iteration = value
    # _end_def_

    @property
    def lower_bound(self) -> NDArray:
        """
        Accessor method that returns the lower bound value(s).

        :return: (numpy array).
        """
        return self._lower_bound
    # _end_def_

    @property
    def upper_bound(self) -> NDArray:
        """
        Accessor method that returns the upper bound value(s).

        :return: (numpy array).
        """
        return self._upper_bound
    # _end_def_

    @property
    def velocities(self) -> NDArray:
        """
        Accessor method that returns the velocity values.

        :return: (numpy array).
        """
        return self._velocities
    # _end_def_

    @property
    def f_evals(self) -> int:
        """
        Accessor method that returns the value of the f_eval.

        :return: (int) the counted number of function evaluations.
        """
        return self._f_evals
    # _end_def_

    @property
    def stats(self) -> dict:
        """
        Accessor method that returns the 'stats' dictionary.

        :return: the dictionary with the statistics from the run.
        """
        return self._stats
    # _end_def_

    @property
    def items(self) -> list | tuple:
        """
        Accessor (getter) of the _items placeholder container.

        :return: _items (if any).
        """
        return self._items
    # _end_def_

    @property
    def swarm(self) -> Swarm:
        """
        Accessor of the swarm.

        :return: the reference the swarm.
        """
        return self._swarm
    # _end_def_

    def _get_typed_positions(self) -> list | NDArray:
        """
        Extracts the positions from the swarm and returns them
        in their correct type according to the setting of the algorithm.

        :return: the particle positions either as list or ndarray.
        """
        # Check which mode is enabled.
        if self._special_mode in (SpecialMode.NORMAL,
                                  SpecialMode.CATEGORICAL):
            # Extract the positions in a 2D numpy array.
            positions = self._swarm.positions_as_array()

            # Only True in CategoricalPSO.
            if self._special_mode == SpecialMode.CATEGORICAL:
                # Sample categorical variable.
                self._items["sample_random_values"](positions)
        else:
            # Extract the positions in a list of lists.
            positions = self._swarm.positions_as_list()

            # Check if the swarm has categorical data blocks.
            if self.swarm.has_categorical:
                # Sample categorical variable.
                self._items["sample_random_values"](positions)
        # _end_if_

        return positions
    # _end_def_

    def evaluate_function(self, parallel_mode: bool = False,
                          backend: str = "threads") -> tuple[float, bool]:
        """
        Evaluate all the particles of the input list with the custom objective
        function. The parallel_mode is optional.

        :param parallel_mode: (bool) enables parallel computation of the objective
                              function. Default is False (serial execution).

        :param backend: backend for the parallel Joblib ('threads' or 'processes').

        :return: the max function value and the found solution flag.
        """
        # Extract the correct type positions.
        positions = self._get_typed_positions()

        # Get a local copy of the objective function.
        func = self._objective_func

        # Local copy of iteration variable.
        current_iter: int = self._iteration

        # Check the 'parallel_mode' flag.
        if parallel_mode:

            # Evaluate the particles in parallel mode.
            f_evaluation = Parallel(n_jobs=self.n_cpus, prefer=backend)(
                delayed(func)(x, it=current_iter) for x in positions
            )
        else:

            # Evaluate all the particles in serial mode.
            f_evaluation = [func(x, it=current_iter) for x in positions]
        # _end_if_

        # Flag to indicate if a solution has been found.
        found_solution = False

        # Initialize f_max.
        f_max = -inf

        # Initialize the optimal position.
        x_opt = None

        # Stores the function values.
        fx_array = np.empty(self.n_rows, dtype=float)

        # Update all particles with their new objective function values.
        for n, (p, result) in enumerate(zip(self._swarm.population, f_evaluation)):
            # Extract the n-th function value.
            f_value = result["f_value"]

            # Attach the function value to each particle.
            p.value = f_value

            # Update the found solution.
            found_solution |= result["solution_is_found"]

            # Update the statistics.
            fx_array[n] = f_value

            # Update f_max value.
            if f_value > f_max:
                f_max = f_value
                x_opt = positions[n]
        # _end_for_

        # Store the function values as ndarray.
        self._stats["f_values"].append(fx_array)

        # Store the optimal sampled position.
        self._stats["x_opt"].append(x_opt)

        # Store the f_max of this iteration.
        self._stats["f_opt"].append(f_max)

        # Update the counter of function evaluations.
        self._f_evals += self._swarm.size

        # Update local best for consistent results.
        self._swarm.update_local_best()

        # Return the tuple.
        return f_max, found_solution
    # _end_def_

    def clear_all(self) -> None:
        """
        Clears the stats dictionary and the f_eval counter.

        :return: None.
        """
        self._stats.clear()
        self._f_evals = 0

        # Log the clearing.
        logger.debug(f"{self.__class__.__name__} "
                     f"'f_eval_counter' and 'stats' dictionary have been cleared.")
    # _end_def_

    def get_optimal_values(self) -> tuple:
        """
        Iterates through the stats to find the best recorded
        position from all the iterations.

        :return: a tuple with the optimal particle position,
                 its function value and the iteration it was
                 found.
        """
        # Get the maximum of the f_opt.
        f_opt = max(self._stats["f_opt"])

        # Get the index of f_opt.
        i_opt = self._stats["f_opt"].index(f_opt)

        # Get the corresponding x_opt.
        x_opt = self._stats["x_opt"][i_opt]

        # Return the optimal particle position,
        # along with its function value and its
        # iteration.
        return i_opt, f_opt, x_opt
    # _end_def_

    def reset_all(self) -> None:
        """
        Resets the particle positions, velocities
        and the  statistics dictionary. Since the
        various implementations vary  this method
        should be implemented separately.

        :return: None.
        """
        raise NotImplementedError(f"{self.__class__.__name__}: "
                                  f"You should implement this method!")
    # _end_def_

    def generate_random_positions(self) -> None:
        """
        Generate a population of particles with random positions.
        Each different class that inherits from here should know
        how to implement it.

        :return: None.
        """
        raise NotImplementedError(f"{self.__class__.__name__}: "
                                  f"You should implement this method!")
    # _end_def_

    def neighborhood_best(self, num_neighbors: int) -> deque[NDArray]:
        """
        For each particle in the swarm, finds the 'n' closest neighbors
        (distance-wise) and computes the local best neighborhood position.

        :param num_neighbors: number of neighbors to consider.

        :return: a container (deque) with the neighborhood best positions.
        """
        # Size of the population.
        swarm_size = self.swarm.size

        # Extract the swarms positions as array.
        x_pos = self.swarm.positions_as_array()

        # Compute the pairwise distances.
        pairwise_dists = nb_cdist(x_pos, scaled=True)

        # Get the indices of the sorted distances.
        # This way we can have the nearest neighbors first.
        x_sorted = np.argsort(pairwise_dists, axis=1)

        # Local best deque with max length.
        l_best = deque(maxlen=swarm_size)

        # Go through each row of the x_sorted matrix and for each
        # particle  compute it's best neighborhood  position as a
        # weighted average of their best positions, weighted with
        # their linear ranked probabilities.
        #
        # NB: Since the first index 0 refers to the same particle
        # we skip it and start counting from 1.
        for row in x_sorted[:, 1:num_neighbors+1]:
            # Collect only the m-local particles.
            near_neighbors = [self.swarm.population[k] for k in row]

            # Use the fully_informed with the 'use_best' option enabled
            # to get a weighted average of the optimal local position.
            optimal_position = GenericPSO.fully_informed(near_neighbors,
                                                         use_best=True)
            # Update the local best deque.
            l_best.append(optimal_position)

        # Return the container.
        return l_best
    # _end_def_

    def get_local_best_positions(self, operating_mode: str = "g_best") -> NDArray:
        """
        This method uses the swarm's population and the current operating mode,
        from the VOptions tuple, to calculate the local best positions.

        :param operating_mode: the operating mode of the algorithm. The default
                               value is set to be the 'g_best' because it works
                               with all the PSO implementations.

        :return: the local best positions (as numpy array).
        """
        # Size of the population.
        swarm_size = self.swarm.size

        # Get the global best.
        if operating_mode == "fipso":
            # Compute a weighted average from all the positions of the swarm,
            # according to their linear ranking (of fitness value).
            l_best = swarm_size * [GenericPSO.fully_informed(self.swarm.population)]

        elif operating_mode == "multimodal":
            # Get the (local) neighborhood's best particles.
            l_best = self.neighborhood_best(num_neighbors=4)

        elif operating_mode == "g_best":
            # Get the (global) swarm's best particle position.
            l_best = swarm_size * [self.swarm.best_particle().position]

        else:
            raise ValueError(f"Unknown operating mode: {operating_mode}."
                             f" Use 'fipso', 'multimodal' or 'g_best'")
        # Return as numpy array.
        return np.array(l_best)
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

        # Get the local best positions (for the social attractor).
        l_best = self.get_local_best_positions(params.mode.lower())

        # Extract the current positions.
        x_current = self.swarm.positions_as_array()

        # Extract the best (historical) positions.
        x_best = self.swarm.best_positions_as_array()

        # Update the new velocity equations (inplace).
        self._velocities *= params.w0
        self._velocities += cogntv * (x_best - x_current)
        self._velocities += social * (l_best - x_current)
    # _end_def_

    def update_positions(self) -> None:
        """
        Updates the positions of the particles in the swarm.

        :return: None.
        """
        raise NotImplementedError(f"{self.__class__.__name__}: "
                                  f"You should implement this method!")
    # _end_def_

    def calculate_spread(self) -> float:
        """
        Calculates a measure of how spread are the particle
        positions, according to the specific type of PSO.

        :return: None.
        """
        raise NotImplementedError(f"{self.__class__.__name__}: "
                                  f"You should implement this method!")
    # _end_def_

    def adapt_velocity_parameters(self, options: dict) -> bool:
        """
        Provides a very basic adapt mechanism for the PSO update
        velocity parameters. It can be used as a placeholder for
        more advanced techniques.

        :param options: (dict) contains the previous estimates of
                        the PSO parameters.

        :return: True if the update happened, False otherwise.
        """
        # Default return parameter.
        have_been_updated = False

        # For the moment hardcode the min/max
        # values of the c1 and c2 parameters.
        c_min, c_max = 0.1, 2.5

        # Get an estimate of the particles' spread
        # ensuring its range is in [0, 1] and use
        # it as the current inertia weight.
        wt = nb_clip_item(self.calculate_spread(),
                          0.0, 1.0)

        # Get the previous values of the parameters.
        w0 = options["w0"]
        c1 = options["c1"]
        c2 = options["c2"]

        # To reduce "noise effects" we allow the update only if the
        # new inertia parameter "wt" differs more than ~5% from the
        # previous one "w0".
        if fabs(wt - w0) > 0.05:

            # Update the cognitive and social parameters.
            if wt > w0:
                # If the inertia weight has increased,
                # then adapt the c1 / c2 coefficients.
                c1 *= 1.1
                c2 *= 0.9
            else:
                # If the inertia weight has decreased,
                # then adapt the c1 / c2 coefficients.
                c1 *= 0.9
                c2 *= 1.1
            # _end_if_

            # Ensure the updated c1 / c2 values
            # stay within their bounds.
            c1 = nb_clip_item(c1, c_min, c_max)
            c2 = nb_clip_item(c2, c_min, c_max)

            # Update the dictionary.
            options["w0"] = wt
            options["c1"] = c1
            options["c2"] = c2

            # Store the updated parameters.
            self._stats["inertia_w"].append(wt)
            self._stats["cogntv_c1"].append(c1)
            self._stats["social_c2"].append(c2)

            # Change the return value.
            have_been_updated = True

            # Log the update.
            logger.debug(f"{self.__class__.__name__} parameters have been updated.")
        # _end_if_

        return have_been_updated
    # _end_def_

    @time_it
    def run(self, max_it: int = 1000, options: dict = None, parallel: bool = False,
            reset_swarm: bool = False, f_tol: float = None, f_max_eval: int = None,
            adapt_params: bool = False, verbose: bool = False) -> None:
        """
        Main method of the GenericPSO class that implements the optimization routine.

        :param max_it: (int) maximum number of iterations in the optimization loop.

        :param f_tol: (float) tolerance in the difference between the optimal function
                       value of two consecutive iterations. It is used to determine the
                       convergence of the swarm. If this value is None (default) the
                       algorithm will terminate using the max_it value.

        :param options: dictionary with update equations options ('w': inertia weight,
                        'c1': cognitive coefficient, 'c2': social coefficient, 'mode':
                        operation mode).

        :param parallel: (bool) flag that enables parallel computation of the objective
                         function.

        :param reset_swarm: (bool) if True it will reset the positions of the swarm to
                            uniformly random respecting the boundaries of each space dimension.

        :param f_max_eval: (int) it sets an upper limit of function evaluations. If the
                            number is exceeded the algorithm stops.

        :param adapt_params: (bool) If set to "True" it will allow the inertia, cognitive
                             and social parameters to adapt according to the convergence
                             of the swarm population to a single solution. Default is set
                             to "False".

        :param verbose: (bool) if True it will display periodically information about the
                        current optimal function values.

        :return: None.
        """
        # Check if resetting the swarm is requested.
        if reset_swarm:
            self.reset_all()

            # Log the reset.
            logger.warning(f"{self.__class__.__name__} has been reset.")
        # _end_if_

        if options is None:
            # Set default values of the simplified version.
            options = {"w0": 0.70, "c1": 1.50, "c2": 1.50,
                       "mode": "g_best"}
        else:
            # Ensure all the parameters are here.
            check_velocity_parameters(options)
        # _end_if_

        # Convert options dict to VOptions.
        params = VOptions(**options)

        # Get the function values before optimization.
        f_opt, _ = self.evaluate_function(parallel)

        # Log the initial f_optimal value.
        logger.info(f"Initial f_optimal = {f_opt:.4f}")

        # Local variable to display information on the screen.
        # To avoid cluttering the screen we print info only 10
        # times regardless of the total number of iterations.
        its_time_to_print = max_it // 10 if max_it > 10 else 2

        # Repeat for 'max_it' times.
        for i in range(max_it):
            # Update the iteration.
            self._iteration = i

            # First update the velocity equations.
            self.update_velocities(params)

            # Then update the positions in the swarm.
            self.update_positions()

            # Calculate the new function values.
            f_new, found_solution = self.evaluate_function(parallel)

            # Check if we want to print output.
            if verbose and (i % its_time_to_print) == 0:
                # Log the f_optimal at the current iteration.
                logger.info(f"Iteration: {i + 1:>5} -> f_optimal = {f_new:.4f}")
            # _end_if_

            # Check for the maximum function evaluations.
            if f_max_eval is not None and self._f_evals >= f_max_eval:
                # Update optimal function.
                f_opt = f_new

                # Log the exit message.
                logger.warning(f"{self.__class__.__name__} reached the maximum "
                               f"number of function evaluations at iteration {i + 1}")
                break
            # _end_if_

            # Check for termination.
            if found_solution:
                # Update optimal function.
                f_opt = f_new

                # Log the warning message.
                logger.warning(f"{self.__class__.__name__} found a solution at iteration {i + 1}")

                break
            # _end_if_

            # Check for convergence.
            if f_tol is not None and isclose(f_new, f_opt, abs_tol=f_tol):
                # Update optimal function.
                f_opt = f_new

                # Log the warning message.
                logger.warning(f"{self.__class__.__name__} converged in {i + 1} iterations")

                break
            # _end_if_

            # Check for adapting the parameters.
            if adapt_params and (i % 10) == 0:
                # Make a copy of the parameters.
                dict_options = params._asdict()

                # Try to perform the update.
                if self.adapt_velocity_parameters(dict_options):
                    # If the update was successful convert the new
                    # parameters to VOptions for the next iteration.
                    params = VOptions(**dict_options)
                # _end_if_
            # _end_if_

            # Update optimal function for next iteration.
            f_opt = f_new
        # _end_for_

        # Display an information message.
        print(f"Final f_optimal = {f_opt:.4f}")
    # _end_def_

    def __call__(self, *args, **kwargs) -> None:
        """
        Wrapper of the run() method.
        """
        return self.run(*args, **kwargs)
    # _end_def_

# _end_class_
