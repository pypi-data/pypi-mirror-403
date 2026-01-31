"""
Module to include the functionality related
to progressions.
"""
from yta_math_easings.abstract import EasingFunction
from yta_math_easings.enums import EasingFunctionName
from yta_validation import PythonValidator
from yta_validation.parameter import ParameterValidator
from typing import Union

import numpy as np


# TODO: Maybe make 'easings' optional (?)
class Progression:
    """
    Class to represent a progression of `n` values from
    `start_value` to `end_value` (including both in that
    `n` number of values), with an associated rate
    function to calculate the values between those
    'start_value' and `end_value` limits.

    The progression can be ascending or descending.

    This class is useful to obtain each individual value
    that must be applied in different use cases.

    The values of the specific progression can be accessed
    by the `.values` property. These values will be cached
    and re-calculated only if some parameter has changed
    since the last time they were accessed.

    You can use this progression directly as a list doing
    `list(progression)`.
    """

    def __iter__(
        self
    ):
        return iter(self.values)
    
    def __getitem__(
        self,
        index
    ):
        return self.values[index]
    
    def __len__(
        self
    ):
        return len(self.values)

    def __repr__(
        self
    ):
        return f"Progression({self.values})"

    # This is to be able to use as a numpy (np.array(p))
    def __array__(
        self,
        dtype = None
    ):
        return np.asarray(self.values, dtype = dtype)

    """
    These properties above are to make the Progression be
    usable as an array of values.
    """

    @property
    def start_value(
        self
    ):
        """
        The first value of the progression, that acts as a
        limit.
        """
        return self._start_value
    
    @start_value.setter
    def start_value(
        self,
        value: float
    ):
        """
        Set the `start_value` parameter and flag the 
        progression to be recalculated if needed due to the
        change.
        """
        ParameterValidator.validate_mandatory_number('value', value)

        if (
            not hasattr(self, '_start_value') or
            self._start_value != value
        ):
            self._values = None
            self._start_value = value

    @property
    def end_value(
        self
    ):
        """
        The last value of the progression, that acts as a
        limit.
        """
        return self._end_value
    
    @end_value.setter
    def end_value(
        self,
        value: float
    ):
        """
        Set the `end_value` parameter and flag the 
        progression to be recalculated if needed due to the
        change.
        """
        ParameterValidator.validate_mandatory_number('value', value)

        if (
            not hasattr(self, '_end_value') or
            self._end_value != value
        ):
            self._values = None
            self._end_value = value

    @property
    def number_of_values(
        self
    ):
        """
        The amount of values that will be calculated for
        the progression, including the limits (`start_value`
        and `end_value`).
        """
        return self._number_of_values
    
    @number_of_values.setter
    def number_of_values(
        self,
        value: float
    ):
        """
        Set the `number_of_values` parameter and flag the 
        progression to be recalculated if needed due to the
        change.
        """
        ParameterValidator.validate_mandatory_positive_number('value', value)

        if (
            not hasattr(self, '_number_of_values') or
            self._number_of_values != value
        ):
            self._values = None
            self._number_of_values = value

    @property
    def easing_function(
        self
    ) -> EasingFunction:
        """
        The easing function that will be applied to calculate
        the `n` values between `start` and `end`, including
        both limits.
        """
        return self._easing_function
    
    @easing_function.setter
    def easing_function(
        self,
        value: Union[EasingFunction, EasingFunctionName, str]
    ):
        """
        Set the `easing_function` parameter and flag the 
        progression to be recalculated if needed due to the
        change.
        """
        value = _validate_easing_function(value)

        if self._easing_function != value:
            self._values = None
            self._easing_function = value

    @property
    def values(
        self
    ):
        """
        The list of `n` values (including `start_value` and
        `end_value`) between those limits and according to
        the provided `easing_function`.
        """
        if (
            self._values is None or
            self.number_of_values != self._number_of_values
        ):
            start_value, end_value = (
                (self.end_value, self.start_value)
                if self.start_value > self.end_value else
                (self.start_value, self.end_value)
            )

            from yta_math_normalization.value_normalizable import ValueNormalizable

            values = [
                float(ValueNormalizable.init_from_value_normalized(
                    value_normalized = normalized_value,
                    lower_limit = start_value,
                    upper_limit = end_value
                ))
                for normalized_value in Progression.get_n_eased_values(
                    n = self.number_of_values,
                    easing_function = self._easing_function
                )
            ]

            # If limits are switched, we need to recalculate it
            # TODO: Refactor this if possible
            values = (
                [
                    self.end_value - value + self.start_value
                    for value in values
                ]
                if self.start_value > self.end_value else
                values
            )

            self._values = values

        return self._values

    def __init__(
        self,
        start_value: float,
        end_value: float,
        number_of_values: int,
        easing_function_name: Union[EasingFunctionName, str] = EasingFunctionName.LINEAR
    ):
        easing_function_name = EasingFunctionName.to_enum(easing_function_name)

        self.start_value: float = start_value
        """
        *For internal use only*

        The starting value of the progression, that acts as a
        limit and is the first value in the progression.
        """
        self.end_value: float = end_value
        """
        *For internal use only*

        The ending value of the progression, that acts as a
        limit and is the last value in the progression.
        """
        self.number_of_values: int = number_of_values
        """
        The number of values in the progression, including
        the `start_value` and `end_value`.
        """

        self._easing_function: EasingFunction = EasingFunction.get(easing_function_name)()
        """
        *For internal use only*

        The easing function to apply for the calculations.
        """

    def get_value_from_progress(
        self,
        d: float
    ) -> float:
        """
        Get the value of the progression that is associated
        to the given `d` normalized progress, that is
        representing the progress in the progression, being
        `d=0.0` the begining (first value) and `d=1.0` the
        end of it (last value).
        """
        d = max(0.0, min(1.0, d))

        value_index = int(d * self.number_of_values)
        # We clamp the 1.0 to be included
        value_index = min(value_index, self.number_of_values - 1)
        
        return self.values[value_index]

    # TODO: This is just a shortcut, so... remove it (?)
    @staticmethod
    def get_n_equally_distributed_normalized_values(
        n: int
    ):
        """
        Get a list containing `n` equally distributed (and
        normalized) values between 0.0 and 1.0. The `n`
        value must be equal or greater than 2.

        This is returning a list of `d` values. Normalized
        values representing the progress in the easing
        function.

        If `n=6`:
        - `[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]`
        """
        return Progression.get_n_eased_values(
            n = n,
            easing_function = EasingFunctionName.LINEAR
        )
    
    @staticmethod
    def get_n_eased_values(
        n: int,
        easing_function: Union[EasingFunction, EasingFunctionName] = EasingFunctionName.default()
    ):
        """
        Get a list including the `0.0` and `1.0` limits
        and `n - 2` values in between, according to the
        `easing_function` provided (that can be the name
        or the function itself).

        The values could surpass the limits due to 
        overshoot according to the easing function
        applied.

        This is returning the `n` normalized values.

        If `n = 6` and `rate_function = ease_in_quad`:
        - `[0.0, 0.04, 0.16, 0.36, 0.64, 1.0]`
        """
        ParameterValidator.validate_mandatory_positive_int('n', n, do_include_zero = False)
        easing_function = _validate_easing_function(easing_function)

        if n < 2:
            raise Exception('The provided "n" parameter is not greater or equal than 2.')

        return [
            easing_function.ease(normalized_value)
            for normalized_value in np.linspace(0.0, 1.0, n).tolist()
        ]
    
def _validate_easing_function(
    easing_function: Union[EasingFunction, EasingFunctionName, str]
) -> EasingFunction:
    """
    *For internal use only*

    Validate the `easing_function` provided, raising an
    exception if not valid, and returning it as an
    `EasingFunction` instance if valid.
    """
    return (
        EasingFunction.get(EasingFunctionName.to_enum(easing_function))()
        # 'EasingFunction' is actually an abstract class so...
        if not PythonValidator.is_instance_of(easing_function, EasingFunction) else
        # if not PythonValidator.is_subclass_of(easing_function, EasingFunction) else
        easing_function
    )