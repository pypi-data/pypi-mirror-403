import numpy as np
from ..core.number import Number
from ..core.array import Array

def significance_test_simple(x, x_err, y, y_err) -> np.ndarray:
    return np.abs(x - y) / np.sqrt(x_err**2 + y_err**2)


def significance_test(x: Number | Array, y: Number | Array) -> np.ndarray:
    # Make sure x and y are Array or Number instances
    if not isinstance(x, (Number, Array)):
        raise TypeError("x must be an instance of Number or Array")
    if not isinstance(y, (Number, Array)):
        raise TypeError("y must be an instance of Number or Array")
    
    
    