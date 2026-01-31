"""
Some explanations to let you understand it better:
Entrada (t): tiempo normalizado en [0, 1].
Salida (a): progreso no lineal en [0, 1].

En animación siempre hay dos espacios independientes:

A. Espacio temporal (time domain)
Tiempo real:
    t ∈ [0, duration]
Tiempo normalizado (también llamado normalized time, alpha):
    u ∈ [0, 1]
    u = t / duration

B. Espacio de valores (value domain)
Valor real:
    v ∈ [start_value, end_value]
Valor normalizado:
    p ∈ [0, 1]


When we talk about easing, we receive a normalized
time moment (u ∈ [0, 1]) and we obtain the normalized
value (p ∈ [0, 1]) associated to that normalized time
moment.

There is a term called 'overshoot', that happens when
the value associated to a `t_normalized` is smaller
than 0.0 or greater than 1.0 (out of bounds). Also,
there is a process called 'clamp' to remove those
values that are out of the limits.
"""
from yta_math_easings.abstract import EasingFunction
from yta_math_easings.enums import EasingFunctionName
from yta_math_easings.utils import clamp_value_normalized
from yta_math_easings.progress_mapping import LinearProgressMapping
from yta_validation.parameter import ParameterValidator
from yta_programming.decorators import classproperty
from abc import ABC


class EasingAnimatedFunction(ABC):
    """
    *Abstract class*

    Abstract class to be inherited by the specific
    easing implementations.

    An easing function that is able to calculate a
    value according to the `n` parameter provided,
    but within a range of possible values and
    according to the duration set.

    The `t_normalized` value is representing the
    time elapsed for the easing function, as a
    normalized value in the `[0.0, 1.0]` range,
    which is also known as the progress or `u`.

    The `value_normalized` (also known as alpha)
    value is representing the progress for the
    easing function, as a normalized value in
    the `[0.0, 1.0]` range.

    We strongly recommend you to clamp the values
    (the default parameter is set to `True` to
    clamping) or you could have unexpected 
    behaviours and/or artifacts.s
    """
    _limit = (0.0, 1.0)
    """
    *For internal use only*

    The limit of the alpha value we can use.
    """
    _registry: dict[str, type['EasingFunction']] = {}
    """
    *For internal use only*

    A register to simplify the way we instantiate
    new classes from strings.
    """
    _easing_cls: type[EasingFunction]
    """
    *For internal use only*

    The class associated to the easing function that
    will be used to calculate the values.
    """

    @classmethod
    def get_name(
        cls
    ) -> str:
        return cls._easing_cls.get_name()
    
    @classproperty
    def may_overshoot(
        cls
    ) -> bool:
        """
        Boolean flag to indicate if the easing function can
        generate values out of the bounds or not.
        """
        return cls._easing_cls.may_overshoot
    
    def __init_subclass__(
        cls,
        **kwargs
    ):
        """
        Init the subclass and register it.
        """
        super().__init_subclass__(**kwargs)

        EasingAnimatedFunction._registry[cls.get_name()] = cls

    @classmethod
    def get(
        cls,
        name: EasingFunctionName
    ) -> type['EasingAnimatedFunction']:
        """
        Get the specific class associated to the given
        easing animated function `name`.
        """
        name = EasingFunctionName.to_enum(name)

        return cls._registry[name.value]

    def __init__(
        self,
        start_value: float,
        end_value: float,
        duration: float = 1.0,
        progress_mapping: 'ProgressMapping' = LinearProgressMapping()
    ):
        """
        The `duration` will be set to `1.0` by default
        to be the same as the normalized. Sometimes we
        don't need the `duration` field at all.
        """
        ParameterValidator.validate_mandatory_number('start_value', start_value, do_include_zero = True)
        ParameterValidator.validate_mandatory_number('end_value', end_value, do_include_zero = True)
        ParameterValidator.validate_mandatory_positive_number('duration', duration, do_include_zero = False)
        ParameterValidator.validate_mandatory_subclass_of('progress_mapping', progress_mapping, 'ProgressMapping')

        self.start_value: float = start_value
        """
        The start value of the valid range of the animated
        easing function.
        """
        self.end_value: float = end_value
        """
        The end value of the valid range of the animated
        easing function.
        """
        self.duration: float = duration
        """
        The total duration (in seconds) that the animated
        easing function will take to go from the
        `start_value` to the `end_value`, that can be used
        to calculate the different values at the different
        time moments requested by the user.
        """
        self._progress_mapping: 'ProgressMapping' = progress_mapping
        """
        *For internal use only*

        The progress mapping function that will transform
        the normalized progress when applying it to 
        calculate the corresponding value. The normalized
        progress is the value corresponding to the time
        from 0 to the `self.duration` but normalized.

        A progress (`u`) of `0.5` in an easing animated
        function with `duration=4` means the real time
        moment `0.5*4=2`. This progress mapping function
        will replace the `0.5` normalized progress value
        by other value, that is the one that will be
        applied in the calculations.

        I give you some examples below for `u=0.3`:
        - `linear` progress mapping function will turn
        it into the same value `u'=0.3`.
        - `reverse` progress mapping function will turn
        it into `u'=0.7`.
        """
        self._easing_function: 'EasingFunction' = self._easing_cls()
        """
        *For internal use only*

        An instance of the easing function associated to
        this animated easing function, that will be the
        one used to calculate the values according to the
        definition.
        """

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

        It will transform the `t_normalized` into the real t
        time moment, and use it to calculate the value 
        associated to it, but returning it normalized.

        The final value will be clamp if the `do_clamp`
        parameter is `True` and it's needed.

        Some easing functions could return values that are out
        of the limits (`value < 0.0` or `value > 1.0`), which
        is called 'overshoot'. The clamp will transform those
        values out of bounds into the limits, turning `1.1`
        into `1.0` or `-0.1` into `0.0`.

        This method will apply the `ProgressMapping` function.

        What do you get:
        - The `value` but normalized (in `[0.0, 1.0]` range).
        """
        # Make sure input is valid (clamp)
        t_normalized = clamp_value_normalized(t_normalized)
        # Transform according to our ProgressMapping function
        t_normalized = self._progress_mapping.map(t_normalized)

        return self._easing_function.ease(
            t_normalized = t_normalized,
            do_clamp = do_clamp,
            **kwargs
        )

    def get_value_from_t_normalized(
        self,
        t_normalized: float,
        do_clamp: bool = True,
        **kwargs
    ) -> float:
        """
        Get the real value (in between the `start_value` and
        the `end_value`) according to the normalized
        `t_normalized` time moment provided (must be a value
        in the `[0.0, 1.0]` range).

        The value will be clamp if the `do_clamp` parameter is
        `True` and it's needed.

        Some easing functions could return values that are out
        of the limits (`value < self.start_value` or
        `value > self.end_value`), which is called 'overshoot'.
        The clamp will transform those values out of bounds
        into the limits of this instance.

        This method will apply the `ProgressMapping` function.

        What do you get:
        - The real `value` (in `[start_value, end_value]`
        range).
        """
        ParameterValidator.validate_mandatory_number_between(
            name = 't_normalized',
            value = t_normalized,
            lower_limit = 0.0,
            upper_limit = 1.0,
            do_include_lower_limit = True,
            do_include_upper_limit = True
        )

        value_normalized = self.ease(
            t_normalized = t_normalized,
            do_clamp = do_clamp,
            **kwargs
        )

        return self.get_value_from_value_normalized(value_normalized)
    
    def get_value_from_t(
        self,
        t: float,
        do_clamp: bool = True,
        **kwargs
    ) -> float:
        """
        Get the real value (in between the `start_value` and
        the `end_value`) for the real `t` time moment provided
        (that must be in the range `[0.0, self.duration]`).

        The value will be clamp if the `do_clamp` parameter is
        `True` and it's needed.

        Some easing functions could return values that are out
        of the limits (`value < self.start_value` or
        `value > self.end_value`), which is called 'overshoot'.
        The clamp will transform those values out of bounds
        into the limits of this instance.

        This method will apply the `ProgressMapping` function.

        What do you get:
        - The real `value` (in `[start_value, end_value]`
        range).
        """
        ParameterValidator.validate_mandatory_number_between(
            name = 't',
            value = t,
            lower_limit = 0.0,
            upper_limit = self.duration,
            do_include_lower_limit = True,
            # TODO: Do we include the upper limit (?)
            do_include_upper_limit = True
        )

        return self.get_value_from_t_normalized(
            progress_normalized = self.get_t_normalized_from_t(
                t = t
            ),
            do_clamp = do_clamp,
            **kwargs
        )
    
    # Utils below
    def get_t_from_t_normalized(
        self,
        t_normalized: float
    ) -> float:
        """
        Get the real time moment associated to the 
        `t_normalized` provided (that must be a value
        in the range `[0.0, 1.0]`).

        This method will not apply the `ProgressMapping`
        function.
        """
        ParameterValidator.validate_mandatory_number_between(
            name = 't_normalized',
            value = t_normalized,
            lower_limit = self._limit[0],
            upper_limit = self._limit[1],
            do_include_lower_limit = True,
            do_include_upper_limit = True
        )

        return t_normalized * self.duration
    
    def get_t_normalized_from_t(
        self,
        t: float
    ) -> float:
        """
        Get the normalized t according to the real
        `t` time moment provided.

        This method will not apply the `ProgressMapping`
        function.
        """
        ParameterValidator.validate_mandatory_number_between(
            name = 't',
            value = t,
            lower_limit = 0.0,
            upper_limit = self.duration,
            do_include_lower_limit = True,
            # TODO: Do we include the upper limit (?)
            do_include_upper_limit = True
        )

        return t / self.duration
    
    def get_value_from_value_normalized(
        self,
        value_normalized: float
    ) -> float:
        """
        Get the real valule associated to the `value_normalized`
        given as parameter.

        This method will not apply the `ProgressMapping`
        function.

        This method can accept and return values out of the
        limits (called 'overshoot').
        """
        return self.start_value * (1 - value_normalized) + self.end_value * value_normalized
        # Equivalent
        return self.start_value + value_normalized * (self.end_value - self.start_value)
    
    def get_value_normalized_from_value(
        self,
        value: float
    ) -> float:
        """
        Get the value normalized associated to the `value`
        given as parameter.

        This method will not apply the `ProgressMapping`
        function.

        This method can accept and return values out of the
        limits (called 'overshoot').
        """
        return (value - self.start_value) / (self.end_value - self.start_value)

    def __call__(
        self,
        t_normalized: float,
        do_clamp: bool = True,
        **kwargs
    ) -> float:
        """
        Special method to allow us doing
        `animated_ease_function(alpha)` instead of
        `animated_ease_function.ease(alpha)`.

        Apply the easing to the `t_normalized` value provided,
        that must be a value in the `[0.0, 1.0]` range, to
        obtain the normalized value associated to it.

        It will transform the `t_normalized` into the real t
        time moment, and use it to calculate the value 
        associated to it, but returning it normalized.

        The value will be clamp if the `do_clamp` parameter is
        `True` and it's needed.

        Some easing functions could return values that are out
        of the limits (`value < 0.0` or `value > 1.0`), which
        is called 'overshoot'. The clamp will transform those
        values out of bounds into the limits, turning `1.1`
        into `1.0` or `-0.1` into `0.0`.

        What do you get:
        - The `value` but normalized (in `[0.0, 1.0]` range).
        """

        """
        This `.__call__` allows us to do this:
        ```
        linear_animated_easing = LinearAnimatedEasing(2.0, 6.0, 1.0)
        linear_animated_easing(0.5)
        ```
        """
        return self.ease(
            t_normalized = t_normalized,
            do_clamp = do_clamp,
            **kwargs
        )