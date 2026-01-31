"""
A module to contain the string names of the
interpolation functions but as Enums to be
able to choose them easy.
"""
from yta_constants.enum import YTAEnum as Enum


class InterpolationFunctionName(Enum):
    """
    Enum to represent the string names of the different
    interpolation functions we have registered in our
    program.
    """

    LINEAR = 'linear'
    BEZIER_QUADRATIC = 'bezier_quadratic'
    BEZIER_CUBIC = 'bezier_cubic'