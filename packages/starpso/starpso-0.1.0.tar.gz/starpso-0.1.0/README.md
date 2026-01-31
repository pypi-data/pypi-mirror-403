# StarPSO: An Object-Oriented Library for Advanced Particle Swarm Optimization Algorithms.

![Logo](./logo/main_logo.png)

[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)

**Pylint score: 9.50 / 10**


[![DOI](https://zenodo.org/badge/959816541.svg)](https://doi.org/10.5281/zenodo.18429186)


## Introduction
Particle Swarm Optimization (PSO) is a computational method inspired by the social behavior of birds.
It is utilized for solving optimization problems by simulating a group of individuals or "particles",
that move through a multidimensional search space to find optimal solutions. Each particle adjusts its
position based on its own experience (cognitive component) and that of its neighboring particles (social
component), effectively sharing information about the quality of various solutions. PSO is widely applied
across various fields, including engineering, finance, and artificial intelligence, due to its simplicity
and effectiveness in converging towards optimal solutions in complex problem spaces.

## Overview

The current toolkit offers a comprehensive suite of Particle Swarm Optimization (PSO) implementations
designed to handle a variety of variable types, breaking through the original PSO limitations that
restricted it to continuous (floating-point) variables. The library includes multiple PSO algorithm
variations (with supported options):

| **Algorithm**                                                    | **Var. Type(s)**       | **Adapt parameters** | **G_best** | **FIPSO** | **Multimodal** | **Parallel** |
|:-----------------------------------------------------------------|:-----------------------|:--------------------:|:----------:|:---------:|:--------------:|:------------:|
| [Standard](star_pso/engines/standard_pso.py)                     | continuous     (float) |         Yes          |    Yes     |    Yes    |      Yes       |     Yes      |
| [Binary](star_pso/engines/binary_pso.py)                         | discrete        (0, 1) |         Yes          |    Yes     |    Yes    |       No       |     Yes      |
| [Categorical](star_pso/engines/categorical_pso.py)               | discrete (categorical) |         Yes          |    Yes     |    Yes    |       No       |     Yes      |
| [Integer](star_pso/engines/integer_pso.py)                       | discrete     (integer) |         Yes          |    Yes     |    Yes    |       No       |     Yes      |
| [Jack of all trades](star_pso/engines/jack_of_all_trades_pso.py) | mixed    (data blocks) |         Yes          |    Yes     |    Yes    |       No       |     Yes      |
| [Quantum](star_pso/engines/quantum_pso.py)                       | continuous     (float) |         Yes          |    Yes     |    Yes    |      Yes       |     Yes      |

This versatility makes it a powerful tool for researchers and practitioners in fields such as engineering, finance,
robotics, artificial intelligence, and more. All the above methods inherit from the base class [GenericPSO](star_pso/engines/generic_pso.py),
which provides some common functionality.

Adding new algorithms **MUST** inherit from the base class.

**Note(1):**
Adapting parameters is supported in the Base class (**GenericPSO**), hence is inherited by all algorithms. However,
since the current adapting algorithm version is checking for convergence of the population to a single solution, using
it with the *multimodal* option would not make much sense and in fact it will mess up the results.

**Note(2):**
Moreover, the *Parallel* option is supported only in the evaluation of the objective (or fitness) function. Therefore,
it is beneficial only in cases where the objective function is "heavy" computationally or has many I/Os. In most cases
setting this option to the default (False), will have the best results.

## Features

- **StandardPSO**: The classic implementation that optimizes continuous variables using the basic PSO rules. 
  This version serves as a baseline for comparison with other algorithms in the library.

- **BinaryPSO**: Suitable for optimization problems where decision variables are binary (0 or 1). 
  This implementation adapts the PSO paradigm to effectively handle binary decision-making scenarios.

- **IntegerPSO**: Designed for optimizing discrete integer variables. This implementation enhances the traditional
  PSO methodology to accommodate problems that require integer solutions.

- **QuantumPSO**: Inspired by quantum mechanics, this version introduces quantum behaviors to the particles,
  enabling exploration of the search space more efficiently and potentially avoiding local optima.

- **CategoricalPSO**: Tailored for problems involving categorical variables, allowing optimization when the
  solutions are non-numeric categories. This is particularly useful in fields such as marketing and behavioral
  science.

- **JackOfAllTradesPSO**: Combines various types of variables (continuous, discrete, categorical), within the same
  optimization problem, providing a flexible approach for multi-faceted real-world problems.

## Installation

There are two options to install the software.

The easiest way is to download it from PyPI. Simply run the following command on a terminal:
    
    pip install starpso

Alternatively one can clone the latest version directly from GitHub using git as follows:

    git clone https://github.com/vrettasm/StarPSO.git

After the download of the code (or the git clone), one can use the following commands:

    cd PyStarPSO
    pip install .

This will install the latest StarPSO version in the package management system.

## Objective function

The most important thing the user has to do is to define the "objective function", that is problem dependent.
A template is provided here in addition to the examples that follow. The 'cost_function' decorator is used to
indicate whether the function will be maximized (default), or minimized. The second output parameter ("solution_found")
is optional; only in the cases where we can evaluate if a termination condition is satisfied. The 'cost_function'
will detect if the user has explicitly passed the second argument, and if not it will supplement it with 'False'.

```python
import numpy as np
from numpy.typing import NDArray
from star_pso.utils.auxiliary import cost_function

# Objective function [Template].
@cost_function(minimize=False)
def objective_fun(x_input: NDArray, **kwargs) -> tuple[float, bool]:
    """
    This is how an objective function should look like. The whole
    evaluation should be implemented, or wrapped around this function.
    
    :param x_input: input numpy ndarray, with the positional variables
                    of the particle.
    
    :param kwargs: key-word arguments. They can pass additional
                   parameters, e.g. like the current iteration
                   as kwargs["it"], etc.
    
    :return: the function value evaluated at the particle's position.
             Optionally we return a bool value if a solution has been
             found (True) or not (False).
    """
    
    # Extract the current iteration.
    # IF IT IS NEEDED!
    it = kwargs["it"]
    
    # ... CODE TO IMPLEMENT ...
    
    # Compute the function value.
    # THIS IS ONLY AN EXAMPLE!
    f_value = np.sum(x_input)
    
    # Condition for termination.
    # THIS IS ONLY AN EXAMPLE!
    solution_found = np.isclose(f_value, 0.0)
    
    return f_value, solution_found
# _end_def_
```
Once the objective function has been defined correctly the next steps are straightforward
as described in the _step-by-step_ examples below.

## Examples

Some optimization examples (use cases) on how to use these algorithms are provided below:

| **Problem**                                               | **Variables** | **Objectives** | **Constraints** |
|:----------------------------------------------------------|:-------------:|:--------------:|:---------------:|
| [Sphere](examples/sphere.ipynb)                           |    M (=5)     |       1        |       no        |
| [Rosenbrock](examples/rosenbrock_on_a_disk.ipynb)         |    M (=2)     |       1        |        1        |
| [Binh & Korn](examples/binh_and_korn.ipynb)               |    M (=2)     |       2        |        2        |
| [Traveling Salesman](examples/tsp.ipynb)                  |    M (=10)    |       1        |       yes       |
| [Zakharov](examples/zakharov.ipynb)                       |    M (=8)     |       1        |       no        |
| [Tanaka](examples/tanaka.ipynb)                           |    M (=2)     |       2        |        2        |
| [Shubert](examples/shubert_2D.ipynb)                      |    M (=2)     |       1        |       no        |
| [Gaussian Mixture](examples/gaussian_mixture_2D.ipynb)    |    M (=2)     |       1        |       no        |
| [OneMax](examples/one_max.ipynb)                          |    M (=30)    |       1        |       no        |
| [SumAbs](examples/sum_abs.ipynb)                          |    M (=15)    |       1        |       no        |
| [Mixed-Variable-Types](examples/jack_of_all_trades.ipynb) |    M (=3)     |       1        |       no        |
| [Categorical PSO](examples/categorical_pso.ipynb)         |    M (=4)     |       1        |       no        |
| [Benchmark Functions](examples/benchmark_functions.ipynb) |    M (>1)     |       1        |       no        |

These examples demonstrate the applicability of StarPSO in various problem types such as:

- single/multi objective(s)
- with/without constraints
- single/multi mode(s)

## Multimodal benchmark functions
Special emphasis is given in multimodal problems, where the optimization function involves more than one optimal values.
In these cases standard optimization techniques fail to locate all the optimal values because, by design, they are
focusing on converging to a single optimal solution. Within StarPSO a new powerful option exists that when activated
allows the swarm of particle to focus not only on a single solution but rather to an arbitrary number of them. Since the
multimodal search spaces assume some form of 'distance' notion among the different modes, the multimodal option is
currently available by the "StandardPSO" and "QuantumPSO" that deal only with continuous (float) variables.

Here we have implemented the following benchmarks of **multimodal** functions:

| **Problem Function**                                                        | **Variables** | **Global Optima** |
|:----------------------------------------------------------------------------|:-------------:|:-----------------:|
| [Equal Maxima](star_pso/benchmarks/equal_maxima.py)                         |       1       |         5         |
| [Five Uneven Peak Trap](star_pso/benchmarks/five_uneven_peak_trap.py)       |       1       |         2         |
| [Uneven Decreasing Maxima](star_pso/benchmarks/uneven_decreasing_maxima.py) |       1       |         1         |
| [Himmelbleau](star_pso/benchmarks/himmelblau.py)                            |       2       |         4         |
| [Gaussian Mixture](star_pso/benchmarks/gaussian_mixture.py)                 |       2       |         2         |
| [Six Hump Camel Back](star_pso/benchmarks/six_hump_camel_back.py)           |       2       |         2         |
| [Rastrigin](star_pso/benchmarks/rastrigin.py)                               |       D       |         K         |
| [Shubert](star_pso/benchmarks/shubert.py)                                   |       D       |      $D*3^D$      |
| [Vincent](star_pso/benchmarks/vincent.py)                                   |       D       |       $6^D$       |

All the above benchmarks inherit from the base class [TestFunction](star_pso/benchmarks/test_function.py) which provides some common functionality.
Adding new algorithms **MUST** inherit from the base class.

NOTE: The "Shubert" and "Vincent" functions were tested with D = 2, 3 (for simplicity). The code however
is generalized and can solve any number of dimensions. Also, the "Rastrigin" function was tested for D = 2,
4 and K = 6 and 12 respectively.

## References and Documentation

This work is described in:

- [Michail D. Vrettas and Stefano Silvestri (2026)]

"StarPSO: A Unified Framework for Particle Swarm Optimization Across Multiple Problem Types" (submitted).

You can find the latest documentation [here](https://pystarpso.readthedocs.io/en/latest/).

### Contact

For any questions/comments (**regarding this code**) please contact me at: vrettasm@gmail.com
