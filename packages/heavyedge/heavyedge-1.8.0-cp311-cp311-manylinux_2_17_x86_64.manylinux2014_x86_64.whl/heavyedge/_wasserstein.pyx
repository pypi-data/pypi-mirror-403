"""Helper functions for wasserstein distance."""

cimport cython
cimport numpy as cnp
from libc.stdlib cimport free, malloc

import numpy as np

cnp.import_array()


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef cnp.ndarray[cnp.float64_t, ndim=2] _quantile(double[:] x, double[:, :] Gs, cnp.int32_t[:] Ls, double[:] t):
    cdef Py_ssize_t i, L, N = Gs.shape[0], M2 = t.shape[0]
    cdef cnp.ndarray[cnp.float64_t, ndim=2] ret = np.empty((N, M2), dtype=np.float64)
    for i in range(N):
        L = Ls[i]
        _quantile_interp(t, Gs[i, :L], x[:L], ret[i, :])
    return ret


cdef void _quantile_interp(double[:] t, double[:] G, double[:] x, double[:] out):
    cdef Py_ssize_t i = 0, j = 0  # indices apply as: t[i], out[i], G[j], x[j]
    cdef Py_ssize_t ii  # variable for emergency loop
    cdef Py_ssize_t M2 = t.shape[0], L = G.shape[0]  # i: [0, M2), j: [0, L)
    cdef double tval, G0, G1, x0, x1

    out[i] = x[j]  # i = j = 0 here
    for i in range(1, M2):
        tval = t[i]
        while j < L - 2 and G[j + 1] < tval:
            j += 1

        G0 = G[j]
        G1 = G[j + 1]
        x0 = x[j]
        x1 = x[j + 1]

        if tval < G[j + 1]:
            out[i] = x0 + (x1 - x0) / (G1 - G0) * (tval - G0)
        else:
            # G[-1] < 1 for numerical reason.
            out[i] = x1


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef cnp.ndarray[cnp.float64_t, ndim=1] _optimize_q(double[:] g):
    # M = number of probability-space grid, N = number of distance-space grid
    cdef Py_ssize_t i, j, idx
    cdef double[:] y_vals = np.unique(g)
    cdef Py_ssize_t M = g.shape[0], N = y_vals.shape[0]
    # Should memory error occurs, may need to make ca 1d and overwrite during loop.
    cdef double *ca = <double *> malloc(M * N * sizeof(double))
    if not ca:
        raise MemoryError()
    cdef int *predecessor = <int *> malloc((M - 1) * N * sizeof(int))
    if not predecessor:
        raise MemoryError()

    # Compute costs
    for i in range(M):  # TODO: parallize this i-loop
        for j in range(N):
            ca[i * N + j] = (g[i] - y_vals[j]) ** 2

    # Accumulate costs
    cdef Py_ssize_t prev_min_j
    cdef double prev_min
    for i in range(1, M):
        prev_min_j = 0
        prev_min = ca[(i - 1) * N + prev_min_j]
        for j in range(N):
            if ca[(i - 1) * N + j] < prev_min:
                prev_min_j = j
                prev_min = ca[(i - 1) * N + j]
            ca[i * N + j] += prev_min
            predecessor[(i - 1) * N + j] = prev_min_j

    # Backtrack
    cdef cnp.ndarray[cnp.float64_t, ndim=1] q = np.empty(M, dtype=np.float64)
    idx = 0
    # Last column
    for j in range(1, N):
        if ca[(M - 1) * N + j] < ca[(M - 1) * N + idx]:
            idx = j
    q[M - 1] = y_vals[idx]
    free(ca)
    # Other columns
    for i in range(1, M):
        idx = predecessor[(M - 1 - i) * N + idx]
        q[M - 1 - i] = y_vals[idx]

    free(predecessor)
    return q
