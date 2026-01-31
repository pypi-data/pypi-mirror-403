from yta_math_easings.abstract import EasingFunction
from yta_math_easings.enums import EasingFunctionName


class SmoothererStepEasing(EasingFunction):
    """
    A smootherer step easing function.

    Implementation of the 3rd order SmoothStep sigmoid function.
    The 1st, 2nd and 3rd derivatives (speed, acceleration and jerk)
    are zero at the endpoints.
    https://en.wikipedia.org/wiki/Smoothstep

    The formula:
    ```
    (
        35 * n**4 - 84 * n**5 + 70 * n**6 - 20 * n**7
        if 0 < n < 1 else
        1
        if n >= 1 else
        0
    )
    ```
    """
    _name: str = EasingFunctionName.SMOOTHERER_STEP.value

    def ease(
        self,
        t_normalized: float,
        do_clamp: bool = True
    ) -> float:
        return super().ease(
            t_normalized = t_normalized,
            do_clamp = do_clamp
        )

    def _ease(
        self,
        t_normalized: float
    ) -> float:
        return (
            35 * t_normalized**4 - 84 * t_normalized**5 + 70 * t_normalized**6 - 20 * t_normalized**7
            if 0 < t_normalized < 1 else
            1
            if t_normalized >= 1 else
            0
        )