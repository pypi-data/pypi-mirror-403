import numbers
import numpy as np
import sympy as sp
from unyt.unit_object import Unit
from ..debugging import debug_print


def _is_value(val, allow_complex: bool = False):
    debug_print(f"Checking if variable \"{val}\" of type {type(val)} is a valid value.", level="debug")
    """Check if `val` is a real or (optionally) complex number."""
    if allow_complex:
        if isinstance(val, numbers.Number):
            return True, None
        return False, f"Value must be a real or complex number, but detected {type(val)}."

    if isinstance(val, bool):
        return False, "Value must not be a boolean."

    if isinstance(val, numbers.Real):
        return True, None

    return False, f"Value must be a real number, but detected {type(val)}."

def _is_error(err):
    """Check if error is None or a non-negative real number."""
    if err is None:
        return True, None

    if isinstance(err, bool):
        return False, "Error must not be a boolean."

    if not isinstance(err, numbers.Real):
        return False, f"Error must be a real number, but detected {type(err)}."

    if err <= 0:
        return False, f"Error must be positive, but detected {err}."

    return True, None

def _is_error_array(error_array):
    debug_print(f"Checking if variable \"{error_array}\" of type {type(error_array)} is a valid error array.", level="debug")
    if error_array is None:
        return True, None
    """Check if the input is convertible to a non-negative real numpy array."""
    try:
        arr = np.asarray(error_array)
    except Exception:
        return False, "Error array must be convertible to a numpy array or be None."

    if not np.issubdtype(arr.dtype, np.number):
        return False, f"Error array must contain numeric values or be None, but detected {arr.dtype}."

    if np.iscomplexobj(arr):
        return False, "Error array must not contain complex numbers."

    if arr.ndim != 1:
        return False, "Error array must be a 1-D array of numbers (no nested arrays)."
    
    if arr.size == 0:
        return False, "Error array must contain at least one element."

    if np.any(arr <= 0):
        return False, "Error array must only contain positive values or be None."

    return True, None

def _is_unit(unit):
    debug_print(f"Checking if variable \"{unit}\" of type {type(unit)} is a valid unit.", level="debug")

    # Allow no unit → dimensionless
    if unit is None:
        return True, None

    # Valid unyt unit types:
    if isinstance(unit, (Unit)):
        return True, None

    return False, f"Unit must be a UnytUnit, Dimension, or None, but got {type(unit)}."

def _is_unit_str(unit_str):
    debug_print(f"Checking if variable \"{unit_str}\" of type {type(unit_str)} is a valid unit string.", level="debug")
    if unit_str is None:
        return True, None
    try:
        unit = Unit(unit_str)
        return True, None
    except Exception as e:
        return False, f"'{unit_str}' cannot be converted to a valid unit: {e}"

def _is_symbol(symbol_str):
    debug_print(f"Checking if variable \"{symbol_str}\" of type {type(symbol_str)} is a valid symbol.", level="debug")
    """Validate that symbol can be converted into a SymPy symbol."""
    if not isinstance(symbol_str, str):
        return False, f"Symbol must be a string, but detected {type(symbol_str)}."
    if not symbol_str.strip():
        return False, "Symbol cannot be empty."

    try:
        sp.Symbol(symbol_str)
        return True, None
    except Exception:
        return False, f"'{symbol_str}' cannot be converted to a SymPy symbol."

def _is_value_array(value_array, allow_complex: bool = False):
    debug_print(f"Checking if variable \"{value_array}\" of type {type(value_array)} is a valid value array.", level="debug")
    """Check if the input is convertible to a numeric numpy array."""
    try:
        arr = np.asarray(value_array)
    except Exception:
        return False, "Value array must be convertible to a numpy array."

    if not np.issubdtype(arr.dtype, np.number):
        return False, f"Value array must contain only numeric values, but detected {arr.dtype}."
    
    if arr.ndim != 1:
        return False, "Value array must be a 1-D array of numbers (no nested arrays)."
    
    if arr.size == 0:
        return False, "Value array must contain at least one element."

    if not allow_complex and np.iscomplexobj(arr):
        return False, "Value array must not contain complex numbers."

    return True, None

def _is_boolean(val):
    debug_print(f"Checking if variable \"{val}\" of type {type(val)} is a valid boolean.", level="debug")
    """Check if val is a boolean."""
    if isinstance(val, bool):
        return True, None
    return False, f"Value must be a boolean, but detected {type(val)}."

def _is_valid_sympy_arg(x):
    try:
        sp.sympify(x)
        return True, None
    except Exception as e:
        return False, f"Error when trying to sympify input of type {type(x)}: {e}"