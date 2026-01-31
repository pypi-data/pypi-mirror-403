from yta_math_easings.abstract import EasingFunction
from yta_math_easings.enums import EasingFunctionName


class SmoothStepEasing(EasingFunction):
    """
    A smooth step easing function.

    Implementation of the 1st order SmoothStep sigmoid function.
    The 1st derivative (speed) is zero at the endpoints.
    https://en.wikipedia.org/wiki/Smoothstep

    The formula:
    ```
    (
        0
        if t_normalized <= 0 else
        (
            3 * t_normalized**2 - 2 * t_normalized**3
            if t_normalized < 1 else
            1
        )
    )
    ```
    """
    _name: str = EasingFunctionName.SMOOTH_STEP.value

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
            0
            if t_normalized <= 0 else
            (
                3 * t_normalized**2 - 2 * t_normalized**3
                if t_normalized < 1 else
                1
            )
        )