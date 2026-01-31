from yta_math_easings.animated.abstract import EasingAnimatedFunction
from yta_math_easings.smoother_step import SmootherStepEasing


class SmootherStepAnimatedEasing(EasingAnimatedFunction):
    """
    A smoother step function but animated, including a
    range of values and a duration.

    The formula:
    ```
    (
        0
        if t_normalized <= 0 else
        (
            6 * t_normalized**5 - 15 * t_normalized**4 + 10 * t_normalized**3
            if t_normalized < 1 else
            1
        )
    )
    """
    may_overshoot: bool = False
    _easing_cls: type['EasingFunction'] = SmootherStepEasing

    def ease(
        self,
        t_normalized: float,
        do_clamp: bool = True
    ) -> float:
        return super().ease(
            t_normalized = t_normalized,
            do_clamp = do_clamp
        )