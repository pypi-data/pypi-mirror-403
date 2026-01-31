from yta_math_easings.enums import EasingFunctionName
from yta_math_easings.utils import clamp_value_normalized
from yta_validation.parameter import ParameterValidator
from yta_programming.decorators.requires_dependency import requires_dependency
from abc import ABC, abstractmethod

import numpy as np


class EasingFunction(ABC):
    """
    *Abstract class*

    Abstract class to be inherited by the specific
    easing implementations.

    An easing function that is able to calculate the
    normalized value associated to the `t_normalized`
    provided.

    If you need to use real values or duration, check
    the `EasingAnimatedFunction` class instead.
    """
    _registry: dict[str, type['EasingFunction']] = {}
    """
    *For internal use only*
    
    A register to simplify the way we instantiate
    new classes from strings.
    """
    _name: str
    """
    *For internal use only*

    The string name of the specific easing implementation
    class.
    """
    may_overshoot: bool
    """
    Boolean flag to indicate if the easing function can
    generate values out of the bounds or not.
    """

    def __init_subclass__(
        cls,
        **kwargs
    ):
        """
        Init the subclass and register it.
        """
        super().__init_subclass__(**kwargs)

        if hasattr(cls, '_name'):
            EasingFunction._registry[cls.get_name()] = cls

    @classmethod
    def get(
        cls,
        name: EasingFunctionName
    ) -> type['EasingFunction']:
        """
        Get the specific class associated to the given
        easing animated function `name`.
        """
        name = EasingFunctionName.to_enum(name)

        return cls._registry[name.value]

    @classmethod
    def get_name(
        cls
    ) -> str:
        """
        Get the string name of the specific easing
        implementation class.
        """
        return cls._name

    @abstractmethod
    def _ease(
        self,
        t_normalized: float,
        **kwargs
    ) -> float:
        """
        *For internal use only*

        The proper calculation of the easing, that must be
        implemented for each specific class.

        The ease calculation will provide the normalized
        value (in `[0.0, 1.0]` range) for the given 
        `t_normalized` time (in `[0.0, 1.0]` range also),
        that is the value (but normalized) associated to
        that time moment.
        """
        pass

    def ease(
        self,
        t_normalized: float,
        do_clamp: bool = True,
        **kwargs
    ) -> float:
        """
        Apply the easing to the `t_normalized` value provided,
        that must be a value in the `[0.0, 1.0]` range, to
        obtain the normalized value associated to it.

        The value will be clamp if the `do_clamp` parameter is
        `True` and it's needed.

        Some easing functions could return values that are out
        of the limits (`value < 0.0` or `value > 1.0`), which
        is called 'overshoot'. The clamp will transform those
        values out of bounds into the limits, turning `1.1`
        into `1.0` or `-0.1` into `0.0`.
        """
        ParameterValidator.validate_mandatory_number_between(
            name = 't_normalized',
            value = t_normalized,
            lower_limit = 0.0,
            upper_limit = 1.0,
            do_include_lower_limit = True,
            do_include_upper_limit = True
        )
        # Value is already clamp if no exception raise

        value_eased = self._ease(
            t_normalized = t_normalized,
            **kwargs
        )

        return (
            clamp_value_normalized(value_eased)
            if do_clamp else
            value_eased
        )

    def __call__(
        self,
        t_normalized: float,
        do_clamp: bool = True,
        **kwargs
    ) -> float:
        """
        Special method to allow us doing `ease_function(alpha)`
        instead of `ease_function.ease(alpha)`.

        Apply the easing to the `t_normalized` value provided,
        that must be a value in the `[0.0, 1.0]` range, to
        obtain the normalized value associated to it.

        The value will be clamp if the `do_clamp` parameter is
        `True` and it's needed.

        Some easing functions could return values that are out
        of the limits (`value < 0.0` or `value > 1.0`), which
        is called 'overshoot'. The clamp will transform those
        values out of bounds into the limits, turning `1.1`
        into `1.0` or `-0.1` into `0.0`.
        """
        return self.ease(
            t_normalized = t_normalized,
            do_clamp = do_clamp,
            **kwargs
        )

    @requires_dependency('matplotlib', 'yta_math_easings', 'matplotlib')
    def plot(
        self,
        number_of_samples: int = 100
    ):
        """
        Plot a graphic representing `number_of_samples`
        values, from `0.0` to `1.0`, to see how the easing
        function works.
        """
        import matplotlib.pyplot as plt
        
        # Limit and draw axis
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.axhline(0, color = 'black', linewidth = 1)
        plt.axvline(0, color = 'black', linewidth = 1)

        plt.grid(True)

        # We will draw 'n'' values between 0.0 and 1.1
        x_vals = np.linspace(0.0, 1.0, number_of_samples).tolist()
        y_vals = [
            self.get_n_value(x)
            for x in x_vals
        ]
        plt.scatter(x_vals, y_vals, color = 'white', edgecolors = 'black', s = 100)

        # TODO: I think we don't need to draw anything
        # else. Remove this below if it is ok.
        # # Draw points between nodes
        # for pair_of_node in self.pairs_of_nodes:
        #     positions = pair_of_node.get_n_xy_values_to_plot(100)
        #     t_xs, t_ys = zip(*positions)
        #     xs += t_xs
        #     ys += t_ys
       
        # plt.scatter(xs, ys, color = 'black', s = 1)
        
        plt.title('')
        plt.xlabel('X axis')
        plt.ylabel('Y axis')
        
        plt.show()
