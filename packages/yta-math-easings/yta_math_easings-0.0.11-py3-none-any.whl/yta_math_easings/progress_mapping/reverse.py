from yta_math_easings.progress_mapping.abstract import ProgressMapping


class ReverseProgressMapping(ProgressMapping):
    """
    The reverse progress mapping, that will return
    the opositve value than the one provided.

    The formula:
    ```
    1.0 - u
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
        return 1.0 - u