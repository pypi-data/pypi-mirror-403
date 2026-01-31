from yta_math_easings.progress_mapping.abstract import ProgressMapping


class LinearProgressMapping(ProgressMapping):
    """
    The linear progress mapping, that will return
    the exact same value that is defined in the
    progress.

    The formula:
    ```
    u
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
        return u