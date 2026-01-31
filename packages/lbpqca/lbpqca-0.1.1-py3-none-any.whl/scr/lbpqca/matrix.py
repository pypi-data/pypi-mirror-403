from lbpqca.type_aliases import *
import numpy as np

def mod_gauss_elimination(A1: MatrixInt, b1: MatrixInt , q: int):
    A=A1.copy()
    b=b1.copy()
    n, m = A.shape
    for i in range(m):
        pivot = -1
        for j in range(i,n):
            if A[j, i] != 0:
                pivot = j
                break
        A[[i,pivot]]=A[[pivot,i]]
        b[[i, pivot]] = b[[pivot, i]]
        inv=pow(int(A[i,i]),-1,q)
        A[i]=inv*A[i]%q
        b[i] = inv * b[i] % q
        for j in range(n):
            if i!=j:
                c=A[j,i]
                A[j]=(A[j]-A[i]*c)%q
                b[j] = (b[j] - b[i] * c) % q
    return b[:m]

def HNF(A: MatrixInt) -> MatrixInt:
    H = A.copy()
    m, n = H.shape
    p = min(m, n)
    k = 0
    while k < p:
        col = H[k:, k]
        col_non0 =col[col!=0]
        if len(col_non0) == 0:
            k +=1
        else:
            min_value = np.min(np.abs(col_non0))
            pivot = np.where(np.abs(col) == min_value)[0][0] + k
            H[[k, pivot]]=H[[pivot, k]]
            if H[k, k] < 0:
                H[k] = -H[k]
            for i in range(k+1, m):
                H[i] -= round(H[i, k] / H[k, k]) * H[k]
            if np.all(H[k+1:, k] == 0):
                for i in range(k):
                    H[i] -= (H[i, k] // H[k, k]) * H[k]
                k+=1
    return H



























