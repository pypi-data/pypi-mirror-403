from yta_math_easings.progress_mapping.abstract import ProgressMapping


class PingPongProgressMapping(ProgressMapping):
    """
    The ping pong progress mapping.

    The formula:
    ```
    1.0 - abs(2.0 * u - 1.0)
    ```
    """

    def map(
        self,
        u: float
    ) -> float:
        return super().map(
            u = u
        )

    def _map(
        self,
        u: float
    ) -> float:
        return 1.0 - abs(2.0 * u - 1.0)