from defode.variable import function_factory

"""
Reflect some common C functions back into defode.
"""

__all__ = ['sin', 'cos', 'exp', 'log',
           'expm1', 'log1p', 'pow']

sin = function_factory('sin')
cos = function_factory('cos')
exp = function_factory('exp')
log = function_factory('log')
expm1 = function_factory('expm1')
log1p = function_factory('log1p')
pow = function_factory('pow')
