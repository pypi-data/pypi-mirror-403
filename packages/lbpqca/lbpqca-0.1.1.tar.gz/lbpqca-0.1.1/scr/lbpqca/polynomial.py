import numpy as np

from lbpqca.type_aliases import *


def add_poly(a: VectorInt, b: VectorInt, q: int):
    return (a+b)%q

def mull_poly(a: VectorInt, b: VectorInt, q: int):
    k = a.shape[0]
    negc=np.zeros([k,k])
    for x in range(k):
        negc[x][0]=a[x]
    for y in range(1,k):
        negc[0][y]=-negc[k-1][y-1]
        for x in range(1,k):
            negc[x][y] = negc[x-1][y-1]
    return (negc@b)%q
