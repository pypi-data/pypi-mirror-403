from yta_math_easings.animated.abstract import EasingAnimatedFunction
from yta_math_easings.smooth import SmoothEasing


class SmoothAnimatedEasing(EasingAnimatedFunction):
    """
    A smooth function but animated, including a
    range of values and a duration.

    The formula:
    ```
    error = Math.sigmoid(-inflection / 2)

    min(
        max((Math.sigmoid(inflection * (t_normalized - 0.5)) - error) / (1 - 2 * error), 0),
        1,
    )
    """
    may_overshoot: bool = False
    _easing_cls: type['EasingFunction'] = SmoothEasing

    def ease(
        self,
        t_normalized: float,
        inflection: float = 10.0,
        do_clamp: bool = True
    ) -> float:
        # TODO: Maybe define 'inflection' (?)
        return super().ease(
            t_normalized = t_normalized,
            inflection = inflection,
            do_clamp = do_clamp
        )