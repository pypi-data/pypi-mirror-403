import sympy as sp
import numpy as np
import warnings
import math
from decimal import Decimal, ROUND_HALF_UP
from unyt import unyt_quantity, unyt_array, Unit, dimensionless
from copy import error
from .number import Number
from ..debugging import debug_print
from ..validators.input import _is_value, _is_error, _is_unit, _is_unit_str, _is_symbol, _is_value_array, _is_boolean, _is_error_array


class Array(Number):
    def __init__(self, value_array, error_array=None, symbol="x", unit=None, allow_complex=False) -> None:
        super().__init__(value_array, error_array, symbol, unit, allow_complex)

    def round(self) -> None:
        if self._error is None:
            warnings.warn("Error is None, cannot round value and error.")
            return
        
        rounded_values = []
        rounded_errors = []

        for i in range(len(self)):
            #extract float values from unyt quantities for rounding
            value_float = self._value[i].value
            error_float = self._error[i].value

  
            rounded_value, rounded_error = self._round_value_and_error(value_float, error_float)

            rounded_values.append(rounded_value)
            rounded_errors.append(rounded_error)

        rounded_values = unyt_array(rounded_values, self._value.units)
        rounded_errors = unyt_array(rounded_errors, self._error.units)
        obj = self.copy()
        obj._value = rounded_values
        obj._error = rounded_errors
        obj.rounded = True
        return obj

    def get_unit(self):
        return self._value[0].units

    def is_dimensionless(self) -> bool:
        return self._value[0].units.is_dimensionless

    def to_array(self, shape) -> 'Array':
        return self

    def _check_initial_value_input(self, value, allow_complex):
        return _is_value_array(value, allow_complex=allow_complex)
    
    def _check_initial_error_input(self, error, value):
        if error is None:
            return True, None
        is_err, msg_err = _is_error(error)
        is_err_arr, msg_err_arr = _is_error_array(error)
        if is_err:
            return True, None
        elif is_err_arr:
            if np.asarray(error).shape != np.asarray(value).shape:
                return False, "Error array must have the same length as value array."
            return True, None
        return False, msg_err_arr
        
    def _set_initial_value(self, initial_value, unit_string) -> None:
        if unit_string is None:
            unit = dimensionless
        else:
            unit = Unit(unit_string)
        self._value = unyt_array(initial_value, unit)

    def _set_initial_error(self, initial_error, unit_string) -> None:
        if unit_string is None:
            unit = dimensionless
        else:
            unit = Unit(unit_string)

        if np.isscalar(initial_error):
            initial_error  = np.full(self._value.shape, initial_error) * unit
        
        if initial_error is None:
            self._error = None
        else:
            self._error = unyt_array(initial_error, unit)

    def __len__(self) -> int:
        return len(self._value)
    
    def __iter__(self):
        for i in range(len(self)):
            new_Number = Number(0, None)
            new_Number._value = self._value[i]
            new_Number._error = self._error[i] if self._error is not None else None
            new_Number._expr = self._expr
            new_Number._err_expr = self._err_expr
            new_Number._dependencies = self._dependencies
            new_Number._allow_complex = self._allow_complex
            new_Number.rounded = self.rounded
            yield new_Number

    def __getitem__(self, index) -> 'Number':
        new_Number = Number(0, None)
        new_Number._value = self._value[index]
        new_Number._error = self._error[index] if self._error is not None else None
        new_Number._expr = self._expr
        new_Number._err_expr = self._err_expr
        new_Number._dependencies = self._dependencies
        new_Number._allow_complex = self._allow_complex
        new_Number.rounded = self.rounded
        return new_Number