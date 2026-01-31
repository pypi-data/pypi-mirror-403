from yta_math_easings.animated.abstract import EasingAnimatedFunction
from yta_math_easings.smootherer_step import SmoothererStepEasing


class SmoothererStepAnimatedEasing(EasingAnimatedFunction):
    """
    A smootherer step function but animated, including a
    range of values and a duration.

    The formula:
    ```
    (
        35 * n**4 - 84 * n**5 + 70 * n**6 - 20 * n**7
        if 0 < n < 1 else
        1
        if n >= 1 else
        0
    )
    """
    may_overshoot: bool = False
    _easing_cls: type['EasingFunction'] = SmoothererStepEasing

    def ease(
        self,
        t_normalized: float,
        do_clamp: bool = True
    ) -> float:
        return super().ease(
            t_normalized = t_normalized,
            do_clamp = do_clamp
        )