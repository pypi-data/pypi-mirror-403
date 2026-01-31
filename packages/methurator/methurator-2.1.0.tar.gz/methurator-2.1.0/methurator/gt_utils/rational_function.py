import numpy as np
from numpy.polynomial import Polynomial
from numpy.linalg import solve


def ps2cfa(coefs, mt):
    """
    continued fraction approximant to a power series based on
    QD algorithm
    coefs, coefficients of the power series;
    mt, the number of terms in the power series used for constructing
    the continued fraction approximation
    ref pp. 131, 147 and 148 in the book Pad\'{e} Approximants 2ed
    """
    coefs = np.asarray(coefs, dtype=float)

    # use nonzero terms which are required by QD algorithm
    zero_idx = np.where(coefs == 0)[0]
    if len(zero_idx) == 0:
        mt = min(mt, len(coefs))
    else:
        mt = min(mt, zero_idx[0])
    if mt == 1:
        return np.array([coefs[0]])

    # QD algorithm
    qd = np.zeros((mt, mt))
    # initialize the table
    # the first column is 0
    qd[: mt - 1, 1] = coefs[1:mt] / coefs[: mt - 1]
    if mt == 2:
        return np.array([coefs[0], -qd[0, 1]])

    # two types of columns e or q
    for i in range(2, mt):
        n = mt - i
        if (i + 1) % 2 == 1:
            qd[:n, i] = qd[1 : n + 1, i - 1] - qd[:n, i - 1] + qd[1 : n + 1, i - 2]
        else:
            qd[:n, i] = qd[1 : n + 1, i - 1] / qd[:n, i - 1] * qd[1 : n + 1, i - 2]

        if not np.isfinite(qd[0, i]) or qd[0, i] == 0:
            return np.concatenate(([coefs[0]], -qd[0, 1:i]))

    return np.concatenate(([coefs[0]], -qd[0, 1:mt]))


def cfa2rf(CF):
    """
    convert truncated continued fraction to a series of rational functions
    numerators are stored in set A and denumerators are stored in set B
    equation (2.14a), (2.14b), (2.15) in the book Pad\'{e} Approximants 2ed
    """
    # A, B are sets of polynomials based on recursive formula
    if len(CF) < 2:
        return Polynomial(CF)
    A = []
    B = []

    A.append(Polynomial([CF[0]]))
    A.append(Polynomial([CF[0]]))
    B.append(Polynomial([1]))
    B.append(Polynomial([1, CF[1]]))

    if len(CF) == 2:
        return {"A": A, "B": B}

    for i in range(2, len(CF)):
        A.append(A[i - 1] + Polynomial([0, CF[i]]) * A[i - 2])
        B.append(B[i - 1] + Polynomial([0, CF[i]]) * B[i - 2])

    return {"A": A, "B": B}


def rf2rfa(RF, m):
    """
    Pad '{e} approximant by picking out the numerator and the denominator
     input: two sets of polynomials for numerators and denominators the degree m
     output: Pad '{e} approximant
    """
    return (RF["A"][m - 1], RF["B"][m - 1])


def rfa_simplify(rfa):
    """
    simplify the rational function, eliminate defects and partial-fraction
    decompoistion
    """
    PRECISION = 1e-3
    numer, denom = rfa

    # solving roots
    numer_roots = numer.roots()
    denom_roots = denom.roots()

    # finite
    if not np.all(np.isfinite(np.concatenate([numer_roots, denom_roots]))):
        return None

    # identify defects
    # the root and the pole is a defect if the difference is less than
    # the predefined precision, which is defined by the variable PRECISION
    tmp = []
    for d in denom_roots:
        if len(numer_roots) > 0:
            dist = np.abs(d - numer_roots)
            idx = np.argmin(dist)
            if dist[idx] < PRECISION:
                numer_roots = np.delete(numer_roots, idx)
                tmp.append(d)

    # eliminate defects
    denom_roots = np.array([x for x in denom_roots if x not in tmp])
    # convert roots from t - 1 to t
    poles = denom_roots + 1

    # treat both numerator and denuminator in the rational function as
    # monic polynomials
    # the difference from the original rational function is up to a factor
    if len(numer_roots) == 0:
        poly_numer = Polynomial([1])
    else:
        # construct polynomials using all the roots
        p = Polynomial([1])
        for r in numer_roots:
            p = Polynomial([0, 1]) * p - Polynomial([r]) * p
        # in theory coefficients p of the polynomial should be real numbers
        # Re(p) == p
        poly_numer = Polynomial(np.real(p.coef))

    # coefficients in the partial fraction
    coefs = np.array(
        [
            poly_numer(d) / np.prod(d - np.delete(denom_roots, i))
            for i, d in enumerate(denom_roots)
        ]
    )

    C = numer.coef[-1] / denom.coef[-1]
    coefs *= C

    return {"coefs": coefs, "poles": poles}


def rfa_sample_cov(n, mt):
    """
    modified Pad\'{e} approximant
    close to the average discovery rate and satisfies
    the sum of estimates of E(S_r(t)) for r >= 1 is equal to Nt
    require mt to be odd
    """

    mt = mt - (mt + 1) % 2
    PS = discoveryrate_ps(n, mt)

    m = (mt + 1) // 2
    N = np.dot(n[:, 0], n[:, 1])

    if mt == 1:
        a = np.sum(n[:, 1])
        b = np.array([1, (N - a) / N])
    else:
        # system equation ax = b
        A = np.vstack([PS[i : i + m] for i in range(m - 1)]).T

        # the last equation is adjust to make sure the sum
        last = [N]
        for i in range(m - 1):
            last.append(PS[i] - last[-1])
        A = np.vstack([A, last])

        b0 = -np.concatenate([PS[m:mt], [PS[m - 1] - last[-1]]])
        b = solve(A, b0)
        b = np.concatenate([[1], b[::-1]])
        a = np.array([np.dot(b[: i + 1], PS[: i + 1][::-1]) for i in range(m)])

    return (Polynomial(a), Polynomial(b))


## discriminant of the quadratic polynomial, which is
## the denominator of the discovery rate at m = 2
## OBSOLATE
def discriminant(n):
    if np.max(n[:, 0]) < 3:
        return None

    n = n.copy()
    n[:, 1] = n[:, 1].astype(float)

    S1 = np.sum(n[:, 1])

    def subtract(count):
        idx = np.where(n[:, 0] == count)[0]
        return n[idx[0], 1] if len(idx) else 0

    S2 = S1 - subtract(1)
    S3 = S2 - subtract(2)
    S4 = S3 - subtract(3)

    a = S2 * S4 - S3**2
    b = S1 * S4 - S2 * S3
    c = S1 * S3 - S2**2

    return (b / a) ** 2 - 4 * (c / a)


def discoveryrate_ps(n, mt):
    """
    coefficients for the power series of E(S_1(t)) / t
    return the first mt terms
    """
    n = np.asarray(n, dtype=int)

    # transform histogram into a vector of frequencies
    max_count = np.max(n[:, 0])
    hist_count = np.zeros(max_count, dtype=float)
    hist_count[n[:, 0] - 1] = n[:, 1]

    PS_coeffs = [np.sum(hist_count)]

    if mt == 1:
        return np.array(PS_coeffs)

    change_sign = 0
    for i in range(min(mt - 1, len(hist_count))):
        value = ((-1) ** change_sign) * hist_count[i] - PS_coeffs[-1]
        PS_coeffs.append(value)
        change_sign += 1

    PS_coeffs = np.array(PS_coeffs)

    # truncate at first zero coefficient
    zero_idx = np.where(PS_coeffs == 0)[0]
    if len(zero_idx) > 0:
        return PS_coeffs[: zero_idx[0]]
    else:
        return PS_coeffs
