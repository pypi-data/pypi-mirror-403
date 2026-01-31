from yta_math_easings.abstract import EasingFunction
from yta_math_easings.enums import EasingFunctionName


class RushIntoEasing(EasingFunction):
    """
    A rush into easing function.

    The formula:
    ```
    2 * SmoothEasing(n / 2.0, inflection)
    ```
    """
    _name: str = EasingFunctionName.RUSH_INTO.value

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

    def _ease(
        self,
        t_normalized: float,
        inflection: float = 10.0
    ) -> float:
        from yta_math_easings.utils import smooth

        return 2 * smooth(t_normalized / 2.0, inflection)