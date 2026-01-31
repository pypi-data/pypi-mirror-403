from copy import error
import warnings
import math
import sympy as sp
import numpy as np
import copy
from typing import Self
from unyt import unyt_quantity, unyt_array, Unit, dimensionless
from ..validators.input import _is_value, _is_error, _is_unit, _is_unit_str, _is_symbol, _is_value_array, _is_boolean, _is_error_array
from ..debugging import debug_print, dump_object


class Number():

    def __init__(self, value, error=None, symbol="x", unit=None, allow_complex=False) -> None:
        is_val, msg_val = self._check_initial_value_input(value, allow_complex)
        is_err, msg_err = self._check_initial_error_input(error, value)
        is_unit_str, msg_unit_str = self._check_initial_unit_str_input(unit)
        is_sym, msg_sym = self._check_initial_symbol_input(symbol)
        is_bool, msg_bool = self._check_initial_allow_complex_input(allow_complex)

        # check if one of the checks failed
        if not (is_val and is_err and is_unit_str and is_sym and is_bool):
            error_msgs = []
            if not is_val:
                error_msgs.append(msg_val)
            if not is_err:
                error_msgs.append(msg_err)
            if not is_unit_str:
                error_msgs.append(msg_unit_str)
            if not is_sym:
                error_msgs.append(msg_sym)
            if not is_bool:
                error_msgs.append(msg_bool)
            raise ValueError(" ".join(error_msgs))
        
        self._set_initial_value(value, unit)
        self._set_initial_error(error, unit)

        self._allow_complex = allow_complex
        self._dependencies = [self]
        self._set_symbol(symbol)
        self.rounded = False

    def print_info(self) -> None:
        print(f"Value: {self._value}, Error: {self._error}, Unit: '{self._unit}', Symbol: {self._expr}, Error Symbol: {self._err_expr}") 
    
    def convert_unit_to(self, unit) -> None:
        try:
            new_value = self._value.to(unit)
            new_error = self._error.to(unit) if self._error is not None else None
            obj = self.copy()
            obj._value = new_value
            obj._error = new_error
            return obj
        except Exception as e:
            raise ValueError(f"Could not convert to unit '{unit}': {e}")
    
    def round(self) -> None:
        if self._error is None:
            warnings.warn("Error is None, cannot round value and error.")
            return
        
        #extract float values from unyt quantities for rounding
        if isinstance(self._value, unyt_quantity):
            value_float = self._value.value
        else:
            value_float = self._value
        if isinstance(self._error, unyt_quantity):
            error_float = self._error.value
        else:
            error_float = self._error
            
        rounded_value, rounded_error = self._round_value_and_error(value_float, error_float)

        #reapply units if necessary
        if isinstance(self._value, unyt_quantity):
            rounded_value = rounded_value * self._value.units
        else:
            rounded_value = rounded_value
        if isinstance(self._error, unyt_quantity):
            rounded_error = rounded_error * self._error.units
        else:
            rounded_error = rounded_error

        obj = self.copy()
        obj._value = rounded_value
        obj._error = rounded_error
        obj.rounded = True
        return obj

    def get_expr(self) -> sp.Symbol:
        return self._expr
    
    def get_err_expr(self) -> sp.Symbol:
        return self._err_expr

    def is_dimensionless(self) -> bool:
        return self._value.units.is_dimensionless

    def get_unit(self):
        return self._value.units
    
    def set_symbol(self, symbol : str) -> Self:
        is_sym, msg_sym = self._check_initial_symbol_input(symbol)
        if not is_sym:
            raise ValueError(msg_sym)
        obj = self.copy()
        obj._set_symbol(symbol)
        obj._dependencies = [obj]
        return obj
        
    def copy(self) -> Self:
        cls = self.__class__
        obj = cls.__new__(cls)   # create uninitialized instance

        # SAFE COPIES:

        # _value and _error may be unyt_quantity or unyt_array → both are mutable
        obj._value = copy.deepcopy(self._value)
        obj._error = copy.deepcopy(self._error)

        # SymPy expressions are immutable → shallow assignment is safe
        obj._expr = self._expr
        obj._err_expr = self._err_expr

        # dependencies list must be copied (shallow ok because it contains Number objects)
        obj._dependencies = list(self._dependencies)

        obj._allow_complex = self._allow_complex
        obj.rounded = self.rounded

        return obj

    def _set_symbol(self, symbol : str) -> None:
        self._expr = sp.Symbol(symbol, real=not self._allow_complex)
        self._err_expr = sp.Symbol("\\Delta{" + symbol + "}", real=True, positive=True)

    def _build(self, expr, vars) -> 'Number':
        from .array import Array
        # create a list of all dependencies 
        dependencies = []
        for var in vars:
            dependencies.extend(var._dependencies)
        # remove duplicates
        dependencies = list(set(dependencies))
        # create dictionary mapping symbols to values and errors
        value_dict = {var._expr: var._value for var in dependencies}
        error_dict = {var._err_expr: var._error for var in dependencies}

        debug_print(f"value_dict: {value_dict}", level="trace")
        debug_print(f"error_dict: {error_dict}", level="trace")
        # get the symbolic expression for the propagated error
        error_expr = self._get_symbolic_expression_for_gaussian_error_propagation(expr, dependencies)

        # create numeric functions for value and error
        value_func = self._simpy_expr_to_unyt_func(expr, list(value_dict.keys()))
        error_func = self._simpy_expr_to_unyt_func(error_expr, list(value_dict.keys()) + list(error_dict.keys()))

        # compute numeric value and error
        value = value_func(*value_dict.values())
        error = error_func(*value_dict.values(), *error_dict.values())
        # check if any of the errors <= 0, if so set error to None
        if error is not None and np.any(error <= 0):
            warnings.warn(f"Computed error is non-positive (error={error}), setting error to None.")
            error = None

        # allow complex if one of the dependencies allows complex
        allow_complex = any([var._allow_complex for var in dependencies])

        # convert the result back into a unyt object if unit has been lost due to sympy calculations
        if not isinstance(value, (unyt_quantity, unyt_array)):
            debug_print(f"The value type is {type(value)}. Need to convert back to unyt object.", level="warning")
            value = value * dimensionless

        # convert error back into unyt object if unit has been lost due to sympy calculations and reshape if necessary
        if error is not None:
            if not isinstance(error, (unyt_quantity, unyt_array)):
                error = error * dimensionless
            # Make sure the error has the same shape as the value
            if self._is_unyt_array(value) and self._is_unyt_quantity(error):
                # convert quantity to array with same shape as value
                error = unyt_array(np.full(value.shape, error.value), error.units)
            elif self._is_unyt_array(value) and self._is_unyt_array(error) and error.shape != value.shape and error.shape == (1,):
                # broadcast error to value shape
                error = unyt_array(np.full(value.shape, error.value[0]), error.units)
            if error.units != value.units:
                # convert error to value's unit
                error = error.to(value.units)

        # check result for validity
        if error is None:
            if not (self._is_unyt_array(value) or self._is_unyt_quantity(value)):
                raise TypeError("Resulting value is neither unyt_quantity nor unyt_array. This should not happen. Please consult the developer.")
        else:
            if not ((self._is_unyt_quantity(error) and self._is_unyt_quantity(value)) or (self._is_unyt_array(error) and self._is_unyt_array(value))):
                raise TypeError(f"After Calculation the value and error types do not match. Type of value is {type(value)} and type of error is {type(error)}. This should not happen. Please consult the developer.")
            if self._is_unyt_array(value) and self._is_unyt_array(error):
                if value.shape != error.shape:
                    raise ValueError(f"After Calculation the value's shape is {value.shape} and the error's shape is {error.shape}. They should be the same. Please consult the developer. value: {value}, error: {error}")
            if error.units != value.units:
                raise ValueError(f"After Calculation the value's unit is {value.units} and the error's unit is {error.units}. They should be the same. Please consult the developer. value: {value}, error: {error}")

        if self._is_unyt_quantity(value):
            new_obj = Number(0, None)
        elif self._is_unyt_array(value):
            new_obj = Array([0], None)
        else:
            raise TypeError("Resulting value is neither unyt_quantity nor unyt_array. Please Ask Jonas for help.")
        
        new_obj._value = value
        new_obj._error = error
        new_obj._expr = expr
        new_obj._err_expr = error_expr
        new_obj._dependencies = dependencies
        new_obj._allow_complex = allow_complex

        debug_print(f"Build a new object from expression {expr}: \n {dump_object(new_obj)}", level="trace")
        return new_obj
  
    def _get_symbolic_expression_for_gaussian_error_propagation(self, expr, dependencies) -> sp.Expr:   
        # compute the symbolic propagated error expression using Gaussian error propagation. Only compute derivatives for dependencies that have a non-None error
        error_expr = 0
        for var in dependencies:
            if var._error is not None:
                deriv = sp.diff(expr, var._expr)
                error_expr += (deriv * var._err_expr)**2
        error_expr = sp.sqrt(error_expr)
        return error_expr
    
    def _simpy_expr_to_unyt_func(self, expr, symbols) -> callable:
        return sp.lambdify(symbols, expr, modules="numpy")

    def _round_value_and_error(self, value, error) -> tuple:
        if error == 0 or error is None:
            warnings.warn("Error is zero or None, cannot round value and error.")
            return value, error
        
        first_digit, decimals = self._get_first_significant_digit_and_rounding_decimals(error)
        rounded_error = self._round_up(error, decimals)

        _, decimals_rounded = self._get_first_significant_digit_and_rounding_decimals(rounded_error)

        # Wert auf gleiche Anzahl an Dezimalstellen runden
        rounded_value = self._round_half_up(value, -decimals_rounded)

        return rounded_value, rounded_error

    def _get_first_significant_digit_and_rounding_decimals(self, err) -> tuple:
        # Fehler signifikante Stellen bestimmen
        exp = int(np.floor(np.log10(abs(err))))
        first_digit = int(err / 10**exp)

         # 1 signif. Stelle wenn 1 oder 2, sonst 2 signif. Stellen
        sig = 2 if first_digit in (1, 2) else 1
        decimals = exp - sig + 1
        return first_digit, decimals

    def _round_up(self, value, digits) -> float:
        return math.ceil(value * 10**(-digits)) * 10**digits

    def _round_half_up(self, value, digits) -> float:
        factor = 10 ** digits
        return math.floor(value * factor + 0.5) / factor

    def _check_initial_value_input(self, value, allow_complex) -> tuple:
        return _is_value(value, allow_complex=allow_complex)
    
    def _check_initial_error_input(self, error, value) -> tuple:
        return _is_error(error)

    def _check_initial_unit_str_input(self, unit_str) -> tuple:
        return _is_unit_str(unit_str)
    
    def _check_initial_symbol_input(self, symbol_str) -> tuple:
        return _is_symbol(symbol_str)

    def _check_initial_allow_complex_input(self, allow_complex) -> tuple:
        return _is_boolean(allow_complex)

    def _set_initial_value(self, initial_value, unit_string) -> None:
        if unit_string is None:
            unit = dimensionless
        else:
            unit = Unit(unit_string)
        self._value = initial_value * unit

    def _set_initial_error(self, initial_error, unit_string) -> None:
        if unit_string is None:
            unit = dimensionless
        else:
            unit = Unit(unit_string)
        if initial_error is None:
            self._error = None
        else:
            self._error = initial_error * unit

    def _is_unyt_quantity(self, x) -> bool:
        return isinstance(x, unyt_quantity)
    
    def _is_unyt_array(self, x) -> bool:
        return (isinstance(x, unyt_array) and not isinstance(x, unyt_quantity))

    def _repr_latex_(self):
        if self._error is not None:
            return (
                r"$\displaystyle "
                r"\begin{aligned}"
                rf"\text{{Value:}} &\quad {sp.latex(self._expr)} \\"
                rf"\text{{Error:}} &\quad {sp.latex(self._err_expr)}"
                r"\end{aligned}"
                r"$"
            )
        else:
            return (
                r"$\displaystyle "
                r"\begin{aligned}"
                rf"\text{{Value:}} &\quad {sp.latex(self._expr)}"
                r"\end{aligned}"
                r"$"
            )

    def __str__(self) -> str:
        unit = "" if self.is_dimensionless() else self.get_unit()
        if self._error is not None:
            error_str = f" ± {self._error.value} "
        else:
            error_str = ""
        return f"{self._value.value}{error_str} {unit}"


    def __add__(self, other) -> 'Number':
        if isinstance(other, Number):
            return self._build(self._expr + other._expr, [self, other])
        else:
            return self._build(self._expr + other, [self])

    def __radd__(self, other) -> 'Number':
        return self.__add__(other)
    
    def __sub__(self, other) -> 'Number':
        if isinstance(other, Number):
            return self._build(self._expr - other._expr, [self, other])
        else:
            return self._build(self._expr - other, [self])
    
    def __rsub__(self, other) -> 'Number':
        if isinstance(other, Number):
            return self._build(other._expr - self._expr, [self, other])
        else:
            return self._build(other - self._expr, [self])
    
    def __mul__(self, other) -> 'Number':
        if isinstance(other, Number):
            return self._build(self._expr * other._expr, [self, other])
        else:
            return self._build(self._expr * other, [self])
        
    def __rmul__(self, other) -> 'Number':
        return self.__mul__(other)
    
    def __truediv__(self, other) -> 'Number':
        if isinstance(other, Number):
            return self._build(self._expr / other._expr, [self, other])
        else:
            return self._build(self._expr / other, [self])
        
    def __rtruediv__(self, other) -> 'Number':
        if isinstance(other, Number):
            return self._build(other._expr / self._expr, [self, other])
        else:
            return self._build(other / self._expr, [self])
        
    def __pow__(self, other) -> 'Number':
        debug_print(f"Computing power: {self} ** {other}", level="trace")
        if isinstance(other, Number):
            return self._build(self._expr**other._expr, [self, other])
        else:
            return self._build(self._expr**other, [self])

    def __rpow__(self, other) -> 'Number':
        debug_print(f"Computing power: {other} ** {self}", level="trace")
        if isinstance(other, Number):
            return self._build(other._expr**self._expr, [self, other])
        else:
            return self._build(other**self._expr, [self])
