from yta_math_easings.abstract import EasingFunction
from yta_math_easings.enums import EasingFunctionName

import numpy as np


class SlowIntoEasing(EasingFunction):
    """
    A slow into easing function.

    The formula:
    ```
    `np.sqrt(1 - (1 - t_normalized) * (1 - t_normalized))`
    ```
    """
    _name: str = EasingFunctionName.SLOW_INTO.value


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
        return np.sqrt(1 - (1 - t_normalized) * (1 - t_normalized))