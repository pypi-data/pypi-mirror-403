from yta_math_easings.animated.abstract import EasingAnimatedFunction
from yta_math_easings.slow_into import SlowIntoEasing


class SlowIntoAnimatedEasing(EasingAnimatedFunction):
    """
    A slow into function but animated, including a
    range of values and a duration.

    The formula:
    ```
    `np.sqrt(1 - (1 - t_normalized) * (1 - t_normalized))`
    ```
    """
    may_overshoot: bool = False
    _easing_cls: type['EasingFunction'] = SlowIntoEasing

    def ease(
        self,
        t_normalized: float,
        do_clamp: bool = True,
    ) -> float:
        return super().ease(
            t_normalized = t_normalized,
            do_clamp = do_clamp
        )
