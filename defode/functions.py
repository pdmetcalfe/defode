from defode.variable import function_factory

"""
Reflect some common C functions back into defode.
"""

__all__ = ['sin', 'cos', 'exp', 'log',
           'expm1', 'log1p', 'pow']

sin = function_factory('sin', 1)
cos = function_factory('cos', 1)
exp = function_factory('exp', 1)
log = function_factory('log', 1)
expm1 = function_factory('expm1', 1)
log1p = function_factory('log1p', 1)
pow = function_factory('pow', 2)
