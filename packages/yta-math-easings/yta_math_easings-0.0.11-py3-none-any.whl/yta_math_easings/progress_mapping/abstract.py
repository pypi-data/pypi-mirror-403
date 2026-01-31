from yta_validation.parameter import ParameterValidator
from abc import ABC, abstractmethod


class ProgressMapping(ABC):
    """
    *Abstract class*

    Abstract class to represent a way of mapping the
    progress, being able to transform the received
    value into a new one by applying the specific
    formula we define on each implementation.

    Having a progress from 0 to 1, this function will
    define the way we go through it.
    """
    
    @abstractmethod
    def map(
        self,
        u: float,
        **kwargs
    ) -> float:
        """
        Map the normalized progress value `u` (that
        must be in the range `[0.0, 1.0]`) into another
        normalized progress value (also in the range
        `[0.0, 1.0]`).
        """
        ParameterValidator.validate_mandatory_number_between('u', u, 0.0, 1.0)

        return self._map(
            u = u,
            **kwargs
        )

    @abstractmethod
    def _map(
        self,
        u: float,
        **kwargs
    ) -> float:
        """
        The internal function that will actually map the
        `u` value provided to the one that should be used
        according to the specific implementation.
        """
        pass
