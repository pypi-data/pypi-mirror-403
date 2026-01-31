from lbpqca.type_aliases import *
import numpy as np

def GSO(B: Matrix) -> Tuple[MatrixFloat, SquareMatrixFloat]:
    m, n = B.shape
    B_star = B.astype(float)
    U = np.identity(m)

    for j in range(1, m):
        b = B_star[j].copy()
        for i in range(j):
            U[i, j] = np.dot(b, B_star[i]) / np.dot(B_star[i], B_star[i])
            B_star[j] -= U[i][j] * B_star[i]

    return B_star, U


def LLL(lattice_basis: SquareMatrix, delta: float = 0.75) -> SquareMatrixFloat:
    n = lattice_basis.shape[0]
    B = lattice_basis.astype(float)
    while True:
        for i in range(1, n):
            for j in range(i - 1, -1, -1):
                Bstar, _ = GSO(B)
                cij = round(np.dot(B[i], Bstar[j]) / np.dot(Bstar[j], Bstar[j]))
                B[i] = B[i] - cij * B[j]
        exists = False
        Bstar, _ = GSO(B)
        for i in range(n - 1):
            u = np.dot(B[i + 1], Bstar[i]) / np.dot(Bstar[i], Bstar[i])
            r = u * Bstar[i] + Bstar[i + 1]
            if delta * np.dot(Bstar[i], Bstar[i]) > np.dot(r, r):
                B[[i, i + 1]] = B[[i + 1, i]]
                exists = True
                break
        if not exists:
            break
    return B

def babai_nearest_plane(lattice_basis: SquareMatrix, w: VectorFloat):
    n = lattice_basis.shape[0]
    B = lattice_basis.astype(float)
    b = -w.astype(float)
    Bstar, _ = GSO(B)
    for j in range(n - 1, -1, -1):
        cj = round(np.dot(b, Bstar[j]) / np.dot(Bstar[j], Bstar[j]))
        b = b - cj * B[j]
    return b + w

def enumeration(lattice_basis: Matrix):
    B = lattice_basis.astype(float)
    Bstar, U = GSO(B)
    n = lattice_basis.shape[0]
    A = np.dot(Bstar[0], Bstar[0])
    alpha_min = np.zeros(n)
    alpha_min[0] = 1
    alpha = np.zeros(n)
    alpha[0] = 1
    l = np.zeros(n + 1)
    c = np.zeros(n)
    t = 0
    while t < n:
        l[t] = l[t + 1] + pow(alpha[t] + c[t], 2) * np.dot(Bstar[t], Bstar[t])
        if l[t] < A:
            if t > 0:
                t -= 1
                for i in range(t + 1, n):
                    c[t] += alpha[i] * U[t, i]
                alpha[t] = round(c[t])
            else:
                A = l[t]
                alpha_min = alpha.copy()
        else:
            t += 1
    return alpha_min

def BKZ(lattice_basis: SquareMatrix, beta: int, delta: float = 0.99):
    z = 0
    j = -1
    B = lattice_basis.astype(float)
    B = LLL(B, delta)
    n = lattice_basis.shape[0]
    while z < n - 1:
        j = (j + 1) % (n - 1)
        nj = min(j + beta, n)
        h = min(j + beta + 1, n)
        alpha = enumeration(B[j: nj])
        b = 0 * B[0]
        b=b.astype(float)
        for i in range(nj - j):
            tmp=alpha[i] * B[j + i]
            b += tmp.astype(float)
        Bstar, _ = GSO(B[0: j + 1])
        Btmp = B.copy()
        Btmp[j] = b
        Bstartmp, _ = GSO(Btmp[0: j + 1])
        bjstar = Bstar[j]
        bpi = Bstartmp[j]
        if np.dot(bjstar, bjstar) > delta * np.dot(bpi, bpi) and np.dot(b, b) != 0:
            z = 0
            B[j] = b
            B[0: h] = LLL(B[0: h], delta)
        else:
            z += 1
            B[0: h] = LLL(B[0: h], delta)
    return B.astype(int)


























