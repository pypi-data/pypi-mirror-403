import numpy as np

from lbpqca.type_aliases import *


def LWR_to_LWE(A: MatrixInt, b: VectorInt, p: int, q: int) -> tuple[MatrixInt, VectorInt]:
    return A, round(q/p)*b

def RLWE_to_LWE(A: MatrixInt, b: VectorInt, q: int) -> tuple[MatrixInt, VectorInt]:
    b_p = b.flatten()
    m, n, k = A.shape
    a_p=[]
    for i in range(m):
        c=[]
        for j in range(n):
            negc=np.zeros([k,k])
            for x in range(k):
                negc[x][0]=A[i][j][x]
            for y in range(1,k):
                negc[0][y]=-negc[k-1][y-1]
                for x in range(1,k):
                    negc[x][y] = negc[x-1][y-1]
            c.append(negc)
        a_p.append(c)
    return np.block(a_p), b_p

