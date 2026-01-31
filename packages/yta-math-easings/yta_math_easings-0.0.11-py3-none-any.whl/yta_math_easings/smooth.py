from yta_math_easings.abstract import EasingFunction
from yta_math_easings.enums import EasingFunctionName
from yta_math_common import Math


class SmoothEasing(EasingFunction):
    """
    A smooth easing function.

    The formula:
    ```
    sigmoid = lambda value: 1.0 / (1 + np.exp(-value))
    error = sigmoid(-inflection / 2)

    min(
        max((sigmoid(inflection * (t_normalized - 0.5)) - error) / (1 - 2 * error), 0),
        1,
    )
    ```
    """
    _name: str = EasingFunctionName.SMOOTH.value

    def ease(
        self,
        t_normalized: float,
        inflection: float = 10.0,
        do_clamp: bool = True
    ) -> float:
        # TODO: Maybe explain about 'inflection' (?)
        return super().ease(
            t_normalized = t_normalized,
            inflection = inflection,
            do_clamp = do_clamp
        )

    def _ease(
        self,
        t_normalized: float,
        inflection: float = 10.0
    ) -> float:
        error = Math.sigmoid(-inflection / 2)

        return min(
            max((Math.sigmoid(inflection * (t_normalized - 0.5)) - error) / (1 - 2 * error), 0),
            1,
        )