import numpy as np
import scipy.sparse as sp


def make_cxf(dls, shape, pmc):
    """Forward colocation in x."""

    Nx, Ny = shape
    if Nx == 1:
        return sp.csr_matrix((Ny, Ny))
    # Create matrix with [1,1,0,...,0], [0,1,1,...,0], etc pattern
    cxf = 0.5 * sp.csr_matrix(sp.diags([1, 1], [0, 1], shape=(Nx, Nx)))

    # Apply boundary conditions before Kronecker product
    if not pmc:
        cxf[0, 0] = 0

    return sp.kron(cxf, sp.eye(Ny))


def make_cxb(dls, shape, pmc):
    """Backward colocation in x."""

    Nx, Ny = shape
    if Nx == 1:
        return sp.csr_matrix((Ny, Ny))

    # Calculate weights for each position
    p1 = dls[:-1]  # First grid spacing
    p2 = dls[1:]  # Second grid spacing

    weights_curr = np.ones(Nx)
    weights_curr[1:] = p1 / (p1 + p2)

    weights_prev = np.zeros(Nx)
    weights_prev[:-1] = p2 / (p1 + p2)

    # Create the matrix using diagonals
    cxb = sp.csr_matrix(sp.diags([weights_curr, weights_prev], [0, -1], shape=(Nx, Nx)))

    # Apply boundary conditions before Kronecker product
    # The matrix is already set up for PEC (cxb[0, 0] = 1)
    if pmc:
        cxb[0, 0] = 0

    return sp.kron(cxb, sp.eye(Ny))


def make_cyf(dls, shape, pmc):
    """Forward colocation in y."""

    Nx, Ny = shape
    if Ny == 1:
        return sp.csr_matrix((Nx, Nx))
    # Create matrix with [1,1,0,...,0], [0,1,1,...,0], etc pattern
    cyf = 0.5 * sp.csr_matrix(sp.diags([1, 1], [0, 1], shape=(Ny, Ny)))

    # Apply boundary conditions before Kronecker product
    if not pmc:
        cyf[0, 0] = 0

    return sp.kron(sp.eye(Nx), cyf)


def make_cyb(dls, shape, pmc):
    """Backward colocation in y."""

    Nx, Ny = shape
    if Ny == 1:
        return sp.csr_matrix((Nx, Nx))

    # Calculate weights for each position
    p1 = dls[:-1]  # First grid spacing
    p2 = dls[1:]  # Second grid spacing

    weights_curr = np.ones(Ny)
    weights_curr[1:] = p1 / (p1 + p2)

    weights_prev = np.zeros(Ny)
    weights_prev[:-1] = p2 / (p1 + p2)

    # Create the matrix using diagonals
    cyb = sp.csr_matrix(sp.diags([weights_curr, weights_prev], [0, -1], shape=(Ny, Ny)))

    # Apply boundary conditions before Kronecker product
    # The matrix is already set up for PEC (cyb[0, 0] = 1)
    if pmc:
        cyb[0, 0] = 0

    return sp.kron(sp.eye(Nx), cyb)


def create_c_matrices(shape, dls, dmin_pmc=(False, False)):
    """Make the colocation matrices. If dmin_pmc is True, the matrices will be modified
    to implement PMC boundary conditions, otherwise they will implement PEC."""

    dlf, _ = dls
    cxf = make_cxf(dlf[0], shape, dmin_pmc[0])
    cxb = make_cxb(dlf[0], shape, dmin_pmc[0])
    cyf = make_cyf(dlf[1], shape, dmin_pmc[1])
    cyb = make_cyb(dlf[1], shape, dmin_pmc[1])

    return (cxf, cxb, cyf, cyb)
