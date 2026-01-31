from lbpqca.lattice.reductions_lattice import BKZ
from lbpqca.matrix import HNF, mod_gauss_elimination
from lbpqca.type_aliases import *
import numpy as np

def BDD_atack(A: MatrixInt, q: int) -> tuple[MatrixInt, VectorInt]:
    m, n = A.shape
    M=np.block([[A.transpose()], [q*np.identity(m)]])
    return HNF(M)[:m,:m]

def BDD_atack_recovery_secret(A: MatrixInt, w: VectorInt, q: int) -> VectorInt:
    return mod_gauss_elimination(A,w,q)

def SVP_atack(A: MatrixInt, b: VectorInt, q: int) -> MatrixInt:
    m, n = A.shape
    Ap=np.block([[A.copy(),b.copy().reshape(-1,1)],[np.zeros(n,int),np.array([1])]])
    M=np.block([[Ap.transpose()], [q*np.identity(m+1, int)]])
    return HNF(M)[:m+1,:m+1]

def SVP_atack_recovery_secret(A: MatrixInt, b: VectorInt, w: VectorInt, q: int) -> VectorInt:
    m, n = A.shape
    if w[-1] == 1:
        As = b - w[:m] 
    else:
        As = b + w[:m]
    return mod_gauss_elimination(A,As,q)

def dual_lattice_atack(A: MatrixInt, q: int) -> MatrixInt:
    m, n = A.shape
    M = np.block([[A.transpose()], [q * np.identity(m)]])
    B_primal = HNF(M)[:m, :m]
    B_inv = np.linalg.inv(B_primal.astype(float))
    B_dual = np.round(q * B_inv.T).astype(int)
    return B_dual













