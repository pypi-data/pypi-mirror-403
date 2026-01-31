import numpy as np
import pandas as pd
from collections import Counter
from pathlib import Path
from scipy.stats import norm
from scipy.stats import nbinom
from methurator.gt_utils.rational_function import (
    ps2cfa,
    cfa2rf,
    rf2rfa,
    rfa_simplify,
    discoveryrate_ps,
)
from methurator.gt_utils.ztnb import preseqR_ztnb_em


def build_frequency_of_frequencies(cov):
    """
    Build frequency-of-frequencies from .COV/.bedGraph file.
    """
    df = pd.read_csv(
        cov,
        sep="\t",
        header=None,
        skiprows=1,
        low_memory=False,
        names=["chr", "start", "end", "methylation", "mcounts", "unmcounts"],
    )
    df["coverage"] = df["mcounts"] + df["unmcounts"]
    coverages = df["coverage"].values

    # Count frequency-of-frequencies
    freq_of_freq = Counter(coverages)  # f_k = number of CpGs with coverage k

    # Optional: convert to dict for GT function
    f = dict(freq_of_freq)

    return f


def preseqR_rSAC(n, r, mt, size, mu):
    """
    Python translation of best practise preseqR.rSAC
    https://github.com/smithlabcode/preseqR/blob/master/R/rSAC.R
    Authors: Chao Deng

    Parameters
    ----------
    n : array-like, shape (k, 2)
        Histogram: [frequency, count]
    r, mt, size, mu : as in R code

    Returns
    -------
    f_rSAC : callable
    """
    para = preseqR_ztnb_em(n, size, mu)
    shape = para["size"]
    mu = para["mu"]

    if shape <= 1:
        # heterogeneous population
        f_rSAC = ds_rSAC(n=n, r=r, mt=mt)
    else:
        # ZTNB approach
        # probability that a species is observed in the initial sample
        n = np.asarray(n, dtype=float)
        S = np.sum(n[:, 1])
        p = 1 - nbinom.pmf(0, size, size / (size + mu))
        L = S / p

        def f_rSAC(t):
            # upper tail: P(X >= r)
            t = np.atleast_1d(t).astype(float)
            return L * nbinom.sf(r - 1, size, size / (size + mu * t))

    return f_rSAC


def ds_rSAC(n, r, mt):
    n = np.asarray(n, dtype=float)
    freq = n[:, 1]

    # coefficients of average discovery rate for the first mt terms
    PS_coeffs = discoveryrate_ps(n, mt=mt)
    if PS_coeffs is None:
        return None

    # use nonzero coefficients
    mt = min(mt, len(PS_coeffs))
    PS_coeffs = PS_coeffs[:mt]

    # check whether sample size is sufficient
    if mt < 2:
        return lambda t: np.sum(freq)

    # construct the continued fraction approximation to the power seies
    cf = ps2cfa(PS_coeffs, mt)
    rf = cfa2rf(cf)

    # the length of cf could be less than mt
    # even if ps do not have zero terms, coefficients of cf may have
    mt = len(cf)
    mt -= mt % 2

    valid = False
    m = mt

    while not valid and m >= 2:
        # rational function approximants [m / 2 - 1,  m / 2]
        rfa = rf2rfa(rf, m)
        rfa = rfa_simplify(rfa)
        if rfa is None:
            m -= 2
            continue

        poles = rfa["poles"]
        # check stability
        if np.any(np.real(poles) >= 0):
            m -= 2
            continue

        coefs = rfa["coefs"]

        # check whether the estimator is non-decreased
        # Note: it only checks for t >= 1 !!!
        def deriv_f(t):
            return np.real([-np.dot(coefs * poles, 1 / (x - poles) ** 2) for x in t])

        if np.any(deriv_f(np.arange(1, 100, 0.05)) < 0):
            m -= 2
            continue

        def f_rSAC(t):
            return np.real([np.dot(coefs, (x / (x - poles)) ** r) for x in t])

        valid = True

    if valid:
        return f_rSAC
    else:
        # the case S1 = S2 where the numbe of species represented exactly once
        # is 0
        return lambda t: np.sum(freq)


def preseqR_rSAC_bootstrap(n, r, mt, size, mu, times, conf):
    """
    Bootstrap version of preseqR.rSAC with confidence intervals.
    """
    # Ensure numeric
    n = n.astype(float)

    # Fit zero-truncated negative binomial
    para = preseqR_ztnb_em(n, size, mu)
    shape = para["size"]
    mu = para["mu"]

    # Define bootstrap function
    def f_bootstrap(n, r, mt, size, mu):
        counts = n[:, 1]
        total_counts = int(counts.sum())
        bootstrap_counts = np.random.multinomial(total_counts, counts / total_counts)
        n_bootstrap = np.column_stack((n[:, 0], bootstrap_counts))
        N_bootstrap = np.dot(n_bootstrap[:, 0], n_bootstrap[:, 1])
        N = np.dot(n[:, 0], n[:, 1])
        t_scale = N / N_bootstrap

        if shape <= 1:
            f = ds_rSAC(n_bootstrap, r=r, mt=mt)
        else:
            f = ztnb_rSAC(n_bootstrap, r=r, size=size, mu=mu)
        return lambda t: f(np.atleast_1d(t) * t_scale)

    # Generate bootstrap functions
    f_rSACs = [f_bootstrap(n, r, mt, size, mu) for _ in range(times)]

    # Estimator function
    def estimator(t):
        result = np.array([f(t) for f in f_rSACs])
        if np.isscalar(t):
            return np.median(result)
        else:
            return np.median(result, axis=0)

    # Variance function
    def variance(t):
        result = np.array([f(t) for f in f_rSACs])
        if np.isscalar(t):
            return np.var(result, ddof=1)
        else:
            return np.var(result, axis=0, ddof=1)

    # Standard error
    def se(x):
        return np.sqrt(variance(x))

    # Confidence interval
    q = (1 + conf) / 2

    def lb(t):
        est = estimator(t)
        var = variance(t)
        C = np.exp(
            norm.ppf(q) * np.sqrt(np.log(1 + var / np.where(est == 0, 1, est) ** 2))
        )
        C[~np.isfinite(C)] = 1
        return est / C

    def ub(t):
        est = estimator(t)
        var = variance(t)
        C = np.exp(
            norm.ppf(q) * np.sqrt(np.log(1 + var / np.where(est == 0, 1, est) ** 2))
        )
        C[~np.isfinite(C)] = 1
        return est * C

    # Initialize to avoid late binding issues
    estimator(1)
    estimator(np.array([1, 2]))
    variance(1)
    variance(np.array([1, 2]))

    return {"f": estimator, "se": se, "lb": lb, "ub": ub}


def ztnb_rSAC(n, r, size, mu):
    """
    Fitting the negative binoimal distribution to the data by EM algorithm
    """
    n = np.asarray(n, dtype=float)
    freq = n[:, 1]

    S = np.sum(freq)

    # estimate parameters
    opt = preseqR_ztnb_em(n, size, mu)
    size = opt["size"]
    mu = opt["mu"]

    p0 = nbinom.pmf(0, size, size / (size + mu))
    # the probability of a species observed in the initial sample
    p = 1 - p0
    # L is the estimated number of species in total
    L = S / p

    def f_rSAC(t):
        t = np.asarray(t)
        return L * nbinom.sf(r - 1, size, size / (size + mu * t))

    return f_rSAC


def run_estimator(configs):
    df = pd.DataFrame()
    # Run estimator for each coverage file
    for cov in configs.covs.keys():

        # Compute frequency-of-frequencies and total CpGs for the given minimum coverage
        f = build_frequency_of_frequencies(cov)
        t_values = np.arange(0, configs.t_max + configs.t_step, configs.t_step)
        lb = ub = np.array([np.nan] * len(t_values))
        name = Path(cov).stem
        num_reads = int(configs.covs[cov])

        # Loop over the minimum coverages
        min_covs = configs.minimum_coverage.split(",")
        for min_cov in min_covs:

            # Run rSAC estimator with or without confidence intervals
            if configs.compute_ci:
                print(f"Running rSAC estimator with confidence intervals for {cov}...")
                function_preseq_boot = preseqR_rSAC_bootstrap(
                    n=np.array([[k, v] for k, v in f.items()]),
                    r=int(min_cov),
                    mt=int(configs.mt),
                    size=float(configs.size),
                    mu=float(configs.mu),
                    times=int(configs.bootstrap_replicates),
                    conf=float(configs.conf),
                )
                # points: predicted unique CpGs
                # lb, ub: confidence intervals
                points = function_preseq_boot["f"](t_values)
                # 1000x more observed seq depth seems a reasonable
                # number to compute the asymptote
                asymptote = function_preseq_boot["f"]([1000])
                lb = function_preseq_boot["lb"](t_values)
                lb = [int(x) for x in lb]
                ub = function_preseq_boot["ub"](t_values)
                ub = [int(x) for x in ub]

            else:
                print(f"Running rSAC estimator for {cov}...")
                function_preseq = preseqR_rSAC(
                    n=np.array([[k, v] for k, v in f.items()]),
                    r=int(min_cov),
                    mt=int(configs.mt),
                    size=float(configs.size),
                    mu=float(configs.mu),
                )
                # 1000x more observed seq depth seems a reasonable
                # number to compute the asymptote
                asymptote = function_preseq([1000])
                points = function_preseq(t_values)

            # Store results in DataFrame
            points = [int(x) for x in points]
            saturation = points / asymptote
            saturation = [round(x, 4) for x in saturation]
            res = pd.DataFrame(
                {
                    "sample": name,
                    "t": t_values,
                    "reads": num_reads,
                    "min_cov": int(min_cov),
                    "total_cpgs": points,
                    "ci_low": lb,
                    "ci_high": ub,
                    "saturation": saturation,
                    "asymptote": [int(asymptote.item()) for _ in saturation],
                }
            )
            df = pd.concat([df, res], ignore_index=True)

    # Generate YAML summary
    return df
