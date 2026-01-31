"""
A module to contain the string names of the
easing functions but as Enums to be able to
choose them easy.
"""
from yta_constants.enum import YTAEnum as Enum


class EasingFunctionName(Enum):
    """
    Enum to represent the string names of the different
    easing functions we have registered in our program.
    """

    LINEAR = 'linear'
    SLOW_INTO = 'slow_into'
    SMOOTH = 'smooth'
    SMOOTH_STEP = 'smooth_step'
    SMOOTHER_STEP = 'smoother_step'
    SMOOTHERER_STEP = 'smootherer_step'
    RUSH_INTO = 'rush_into'
    RUSH_FROM = 'rush_from'