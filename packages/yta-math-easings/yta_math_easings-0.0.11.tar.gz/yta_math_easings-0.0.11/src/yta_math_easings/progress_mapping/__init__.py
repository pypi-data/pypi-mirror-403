"""
Module to include the different progress mapping
functions we have.
"""
from yta_math_easings.progress_mapping.linear import LinearProgressMapping
from yta_math_easings.progress_mapping.reverse import ReverseProgressMapping
from yta_math_easings.progress_mapping.pingpong import PingPongProgressMapping


__all__ = [
    'LinearProgressMapping',
    'ReverseProgressMapping',
    'PingPongProgressMapping'
]