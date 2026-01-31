from yta_math_easings.abstract import EasingFunction
from yta_math_easings.enums import EasingFunctionName


class LinearEasing(EasingFunction):
    """
    A linear easing function.

    The formula:
    ```
    `t_normalized`
    ```
    """
    _name: str = EasingFunctionName.LINEAR.value

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
        return t_normalized
    
