from yta_math_easings.animated.abstract import EasingAnimatedFunction
from yta_math_easings.smooth_step import SmoothStepEasing


class SmoothStepAnimatedEasing(EasingAnimatedFunction):
    """
    A smooth step function but animated, including a
    range of values and a duration.

    The formula:
    ```
    error = Math.sigmoid(-inflection / 2)

    (
        0
        if t_normalized <= 0 else
        (
            3 * t_normalized**2 - 2 * t_normalized**3
            if t_normalized < 1 else
            1
        )
    )
    """
    may_overshoot: bool = False
    _easing_cls: type['EasingFunction'] = SmoothStepEasing

    def ease(
        self,
        t_normalized: float,
        do_clamp: bool = True
    ) -> float:
        return super().ease(
            t_normalized = t_normalized,
            do_clamp = do_clamp
        )