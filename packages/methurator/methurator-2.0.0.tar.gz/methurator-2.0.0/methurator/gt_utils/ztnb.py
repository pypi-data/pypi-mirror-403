from scipy.stats import nbinom
from scipy.special import digamma
from scipy.optimize import minimize
import numpy as np


def preseqR_ztnb_em(n, size, mu):
    """
    EM algorithm to fit the histogram with a negative binomial distribution
    n is the histogram for observed species
    the number of unobserved species is the missing data
    """
    # termination conditions for EM algorithm
    TOLERANCE = 1e-10
    ITER_TOLERANCE = 1e5

    x = n[:, 0]
    freq = n[:, 1]
    p0 = nbinom.pmf(0, size, size / (size + mu))

    S = np.sum(freq)
    # estimate the total number of species
    L = S / (1 - p0)
    # expected the number of zero counts
    zero_counts = L * p0

    # estimated mean and variance
    m = np.dot(x, freq) / L
    v = (np.dot((x - m) ** 2, freq) + m**2 * zero_counts) / (L - 1)

    # target function  objective
    def objective(s):
        return -nb_loglikelihood(n, zero_counts, s[0], m) / L

    # derivative of objective
    # zero.counts is an external variable that are updated by the EM algorithm
    def gradient(s):
        s = s[0]
        term1 = (digamma(s) * zero_counts + np.dot(digamma(x + s), freq)) / L
        term2 = digamma(s)
        term3 = np.log(s) - np.log(s + m)
        return np.array([-(term1 - term2 + term3)])

    # estimate size and mu based on first and second moments
    if v > m:
        init = m**2 / (v - m)
    else:
        init = size

    res = minimize(
        objective, x0=[init], jac=gradient, method="L-BFGS-B", bounds=[(1e-4, 1e4)]
    )

    # count the times of iteration
    iter_count = 1
    # initialize the negative loglikelihood
    loglik_prev = np.inf
    # zero-truncated loglikelihood
    loglik = ztnb_minus_loglikelihood(n, res.x[0], m)

    # EM algorithm
    while (loglik_prev - loglik) / S > TOLERANCE and iter_count < ITER_TOLERANCE:

        # update negative loglikelihood
        loglik_prev = loglik
        # update parameters
        size = res.x[0]
        mu = m

        # E-step: estimate the number of unobserved species
        p0 = nbinom.pmf(0, size, size / (size + mu))
        L = S / (1 - p0)
        zero_counts = L * p0

        m = np.dot(x, freq) / L
        v = (np.dot((x - m) ** 2, freq) + m**2 * zero_counts) / (L - 1)

        # M step: estimate the parameters size and mu
        if v > m:
            init = m**2 / (v - m)
        else:
            init = size

        res = minimize(
            objective, x0=[init], jac=gradient, method="L-BFGS-B", bounds=[(1e-4, 1e4)]
        )

        iter_count += 1
        loglik = ztnb_minus_loglikelihood(n, res.x[0], m)

    return {"size": size, "mu": mu, "loglik": -loglik_prev}


def nb_loglikelihood(n, zero_count, size, mu):
    """
    Calculate the negative binomial loglikelihood
    zero.count is the number of unobserved species
    """
    # loglikelihood for nonzero counts
    x = n[:, 0]
    freq = n[:, 1]

    p = size / (size + mu)

    # add loglikelihood for zero count
    loglik = np.dot(nbinom.logpmf(x, size, p), freq)
    loglik += zero_count * nbinom.logpmf(0, size, p)

    return loglik


def ztnb_minus_loglikelihood(n, size, mu):
    """
    Zero-truncated negative loglikelihood
    n : array (k, 2) [count, frequency]
    """
    x = n[:, 0]
    freq = n[:, 1]

    log_prob = dztnb(x, size, mu, log=True)
    return -np.dot(log_prob, freq)


def dztnb(x, size, mu, log=False):
    """
    Density function of a zero-truncated negative binomial distribution
    size and mu are two parameters for the negative binomial.
    """
    x = np.asarray(x)

    # the density of x in negative binomial
    p = size / (size + mu)

    # set zeros in x with zero probability
    if log:
        prob = nbinom.logpmf(x, size, p)
        prob[x == 0] = -np.inf
    else:
        prob = nbinom.pmf(x, size, p)
        prob[x == 0] = 0.0

    # the density of non-zero in negative binomial
    q = 1 - nbinom.pmf(0, size, p)

    # normalize all non-zero values in negrative binomial
    if log:
        return prob - np.log(q)
    else:
        return prob / q
