from yta_math_easings.animated.abstract import EasingAnimatedFunction
from yta_math_easings.rush_into import RushIntoEasing


class RushIntoAnimatedEasing(EasingAnimatedFunction):
    """
    A rush into function but animated, including a
    range of values and a duration.

    The formula:
    ```
    2 * SmoothEasing(n / 2.0, inflection)
    """
    may_overshoot: bool = False
    _easing_cls: type['EasingFunction'] = RushIntoEasing

    def ease(
        self,
        t_normalized: float,
        do_clamp: bool = True,
        inflection: float = 10.0
    ) -> float:
        return super().ease(
            t_normalized = t_normalized,
            do_clamp = do_clamp,
            inflection = inflection
        )