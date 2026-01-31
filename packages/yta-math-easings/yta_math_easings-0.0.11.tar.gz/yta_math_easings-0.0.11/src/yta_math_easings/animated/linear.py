from yta_math_easings.animated.abstract import EasingAnimatedFunction
from yta_math_easings.linear import LinearEasing


class LinearAnimatedEasing(EasingAnimatedFunction):
    """
    A linear function but animated, including a
    range of values and a duration.

    The formula:
    ```
    `t_normalized`
    ```
    """
    may_overshoot: bool = False
    _easing_cls: type['EasingFunction'] = LinearEasing

    def ease(
        self,
        t_normalized: float,
        do_clamp: bool = True,
    ) -> float:
        return super().ease(
            t_normalized = t_normalized,
            do_clamp = do_clamp
        )