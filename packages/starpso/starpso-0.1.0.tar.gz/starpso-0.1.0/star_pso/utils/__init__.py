from typing import Union
from collections import namedtuple
from numpy.typing import ArrayLike

ScalarOrArray = Union[int, float, ArrayLike]
"""
Make a type alias for the position's type.
"""

VOptions = namedtuple("VOptions",
                      ["w0", "c1", "c2", "mode"], defaults=[False])

# Add documentation to VOptions.
VOptions.__doc__ = """
                   Declare a named tuple with the parameters
                   we want to use in the velocity equations:

                    - "w0": inertia weight
                    - "c1": cognitive coefficient
                    - "c2": social coefficient
                    - "mode": "fipso", "g_best", "multimodal".
                   """
# _end_file_
