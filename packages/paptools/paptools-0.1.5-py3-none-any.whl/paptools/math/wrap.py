import sympy as sp
import numpy as np
from ..core.number import Number
from ..validators.input import _is_valid_sympy_arg
from ..debugging import debug_print

def wrap_func(sympy_func: callable, inputs_must_be_dimensionless = True) -> callable:

    def wrapped(*args):
        debug_print(f"Wrapping function {sympy_func.__name__} with {len(args)} arguments {args}.", level="debug")
        processed_args = []
        processed_number_args = []
        for i, arg in enumerate(args):
            if isinstance(arg, Number):
                # Validate Number (or Array) argument
                if inputs_must_be_dimensionless and not arg.is_dimensionless():
                    raise ValueError(
                        f"Input to {sympy_func.__name__} must be dimensionless, "
                        f"but got unit {arg.get_unit()}."
                    )
                processed_args.append(arg._expr)
                processed_number_args.append(arg)
            else:
                # Validate raw argument
                ok, err = _is_valid_sympy_arg(arg)
                if not ok:
                    raise ValueError(err)
                processed_args.append(sp.sympify(arg))

        func_result = sympy_func(*processed_args)
        # If there was a Number argument, wrap the result back into a Number
        if len(processed_number_args) > 0:
            first_number_arg = processed_number_args[0]
            return first_number_arg._build(func_result, processed_number_args)
        else:
            return func_result
        
    return wrapped