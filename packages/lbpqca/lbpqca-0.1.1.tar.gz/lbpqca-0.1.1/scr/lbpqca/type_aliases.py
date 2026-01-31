#The following code was adapted from
#Source: https://github.com/MikolajLH/pqlattice
#Author: Mikołaj Leonhardt
#License: MIT


import numpy as np
from typing import Any, Tuple, Callable, TypeAliasType
from inspect import signature
from functools import wraps




r'''
Hints for elements of $\\mathbb{Z}_{q}$ for some modulus $q$.
These hints are exclusively used in hints for return types.
'''
type ModInt = int  # represents integers from interval [0, q) for some integer q.
type CenteredModInt = int # represents integers from interval (-q//2, q//2] for some integer q.

r'''
Hints for elements of $\\mathbb{R}^{n}$ vector space.
Components types are not explicitly defined.
'''
type Vector = np.ndarray
type Matrix = np.ndarray
type SquareMatrix = np.ndarray


r'''
Hints for elements of $\\mathbb{R}^{n}$ vector space.
Components types are are explicitly floats.
'''
type VectorFloat = np.ndarray[float]
type MatrixFloat = np.ndarray[float]
type SquareMatrixFloat = np.ndarray[float]


r'''
Hints for elements of $\\mathbb{Z}^{n}$ vector space.
'''
type VectorInt = np.ndarray[int]
type MatrixInt = np.ndarray[int]
type SquareMatrixInt = np.ndarray[int]


r'''
Hints for elements of $\\mathbb{Z}_{p}^{n}$ vector space for some modulus $q$.
Used only in return types hints.
'''
type VectorModInt = np.ndarray[int]
type MatrixModInt = np.ndarray[int]
type SquareMatrixModInt = np.ndarray[int]

type VectorCenteredModInt = np.ndarray[int]
type MatrixCenteredModInt = np.ndarray[int]
type SquareMatrixCenteredModInt = np.ndarray[int]




r'''
Predicates for type checking
'''
def _is_nparray(obj: Any) -> bool:
    return isinstance(obj, np.ndarray)


def _is_Vector(obj: Any) -> bool:
    return _is_nparray(obj) and len(obj.shape) == 1


def _is_Matrix(obj: Any) -> bool:
    return _is_nparray(obj) and len(obj.shape) == 2


def _is_SquareMatrix(obj: Any) -> bool:
    return _is_Matrix(obj) and obj.shape[0] == obj.shape[1]


def _is_VectorInt(obj: Any) -> bool:
    return _is_Vector(obj) and obj.dtype == int


def _is_MatrixInt(obj: Any) -> bool:
    return _is_Matrix(obj) and obj.dtype == int


def _is_SquareMatrixInt(obj: Any) -> bool:
    return _is_SquareMatrix(obj) and obj.dtype == int



def _is_VectorFloat(obj: Any) -> bool:
    return _is_Vector(obj) and obj.dtype == float


def _is_MatrixFloat(obj: Any) -> bool:
    return _is_Matrix(obj) and obj.dtype == float


def _is_SquareMatrixFloat(obj: Any) -> bool:
    return _is_SquareMatrix(obj) and obj.dtype == float



def get_predicate(type_name) -> Callable[[Any], bool] | None:
    if type_name in (ModInt, CenteredModInt):
        return lambda t: isinstance(t, int)
    
    if type_name == Vector:
        return _is_Vector
    if type_name == Matrix:
        return _is_Matrix
    if type_name == SquareMatrix:
        return _is_SquareMatrix

    if type_name in (VectorInt, VectorModInt, VectorCenteredModInt):
        return _is_VectorInt
    if type_name in (MatrixInt, MatrixModInt, MatrixCenteredModInt):
        return _is_MatrixInt
    if type_name in (SquareMatrixInt, SquareMatrixModInt, SquareMatrixCenteredModInt):
        return _is_SquareMatrixInt

    if type_name == VectorFloat:
        return _is_VectorFloat

    if type_name == MatrixFloat:
        return _is_MatrixFloat
    if type_name == SquareMatrixFloat:
        return _is_SquareMatrixFloat

    return None




def enforce_type_check(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        sig = signature(func)
        bounded_args = sig.bind(*args, **kwargs)
        bounded_args.apply_defaults()
        for arg_name, arg_value in bounded_args.arguments.items():
            if expected_type := func.__annotations__.get(arg_name):
                if isinstance(expected_type, TypeAliasType):
                    pred = get_predicate(expected_type)
                    if pred is not None and not pred(arg_value):
                        raise TypeError(f"in function <{func.__name__}> argument <{arg_name}> with value {arg_value} of type <{type(arg_value)}> does not fulfill predicate corresponding to expected type {expected_type}")
                    else:
                        continue
                
                if expected_type in [int, float]:
                    if not isinstance(arg_value, (int, np.integer, float, np.floating)):
                        raise TypeError(f"in function <{func.__name__}> argument <{arg_name}> with value \"{arg_value}\" of type <{type(arg_value)}> is not an instance of the expected type {expected_type}")
                    else:
                        continue
                
                #print(f"unexpected?: functions {func.__name__} arg_name: {arg_name}, arg_value: {arg_value}, expected_type: {expected_type}")
        
        
        return func(*args, **kwargs)
    
    return wrapper
