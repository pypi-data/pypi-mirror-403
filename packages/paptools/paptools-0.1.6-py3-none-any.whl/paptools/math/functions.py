import sympy as sp
from .wrap import wrap_func

# Functions that do not require dimensionless inputs
sqrt   = wrap_func(sp.sqrt, inputs_must_be_dimensionless=False)
abs    = wrap_func(sp.Abs, inputs_must_be_dimensionless=False)
sign   = wrap_func(sp.sign, inputs_must_be_dimensionless=False)
floor  = wrap_func(sp.floor, inputs_must_be_dimensionless=False)
ceil   = wrap_func(sp.ceiling, inputs_must_be_dimensionless=False)

# Functions that require dimensionless inputs
sin    = wrap_func(sp.sin, inputs_must_be_dimensionless=True)
cos    = wrap_func(sp.cos, inputs_must_be_dimensionless=True)
tan    = wrap_func(sp.tan, inputs_must_be_dimensionless=True)
cot    = wrap_func(sp.cot, inputs_must_be_dimensionless=True)
sec    = wrap_func(sp.sec, inputs_must_be_dimensionless=True)
csc    = wrap_func(sp.csc, inputs_must_be_dimensionless=True)

asin   = wrap_func(sp.asin, inputs_must_be_dimensionless=True)
acos   = wrap_func(sp.acos, inputs_must_be_dimensionless=True)
atan   = wrap_func(sp.atan, inputs_must_be_dimensionless=True)
atan2  = wrap_func(sp.atan2, inputs_must_be_dimensionless=True)

sinh   = wrap_func(sp.sinh, inputs_must_be_dimensionless=True)
cosh   = wrap_func(sp.cosh, inputs_must_be_dimensionless=True)
tanh   = wrap_func(sp.tanh, inputs_must_be_dimensionless=True)
coth   = wrap_func(sp.coth, inputs_must_be_dimensionless=True)
sech   = wrap_func(sp.sech, inputs_must_be_dimensionless=True)
csch   = wrap_func(sp.csch, inputs_must_be_dimensionless=True)

asinh  = wrap_func(sp.asinh, inputs_must_be_dimensionless=True)
acosh  = wrap_func(sp.acosh, inputs_must_be_dimensionless=True)
atanh  = wrap_func(sp.atanh, inputs_must_be_dimensionless=True)

exp    = wrap_func(sp.exp, inputs_must_be_dimensionless=True)
log    = wrap_func(sp.log, inputs_must_be_dimensionless=True)
ln     = wrap_func(sp.log, inputs_must_be_dimensionless=True)
log10  = wrap_func(lambda x: sp.log(x, 10), inputs_must_be_dimensionless=True)
log2   = wrap_func(lambda x: sp.log(x, 2), inputs_must_be_dimensionless=True)

erf    = wrap_func(sp.erf, inputs_must_be_dimensionless=True)
erfc   = wrap_func(sp.erfc, inputs_must_be_dimensionless=True)

gamma  = wrap_func(sp.gamma, inputs_must_be_dimensionless=True)
digamma = wrap_func(sp.digamma, inputs_must_be_dimensionless=True)
