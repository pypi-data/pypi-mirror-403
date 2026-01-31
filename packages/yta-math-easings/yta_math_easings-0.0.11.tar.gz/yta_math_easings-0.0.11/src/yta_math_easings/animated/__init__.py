"""
Module to hold the easing functions but using
start and end values and a time duration.
"""
from yta_math_easings.animated.linear import LinearAnimatedEasing
from yta_math_easings.animated.slow_into import SlowIntoAnimatedEasing
from yta_math_easings.animated.smooth import SmoothAnimatedEasing
from yta_math_easings.animated.smooth_step import SmoothStepAnimatedEasing
from yta_math_easings.animated.smoother_step import SmootherStepAnimatedEasing
from yta_math_easings.animated.smootherer_step import SmoothererStepAnimatedEasing
from yta_math_easings.animated.rush_into import RushIntoAnimatedEasing
from yta_math_easings.animated.rush_from import RushFromAnimatedEasing


__all__ = [
    'LinearAnimatedEasing',
    'SlowIntoAnimatedEasing',
    'SmoothAnimatedEasing',
    'SmoothStepAnimatedEasing',
    'SmootherStepAnimatedEasing',
    'SmoothererStepAnimatedEasing',
    'RushIntoAnimatedEasing',
    'RushFromAnimatedEasing'
]