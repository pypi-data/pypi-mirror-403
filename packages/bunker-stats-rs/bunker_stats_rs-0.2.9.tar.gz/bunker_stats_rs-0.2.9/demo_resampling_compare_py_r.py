#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""demo_resampling_compare_py_r.py

Benchmark + sanity-accuracy demo for bunker-stats resampling module vs:
  - Python libraries (SciPy + arch where available)
  - "Pure Python" (NumPy-based reference implementations)
  - R ecosystem (boot + bayesboot where available), via Rscript

Design goals (matches the spirit of your demo_resampling.py):
  - Scale across multiple N (including 1,000,000)
  - Measure speed with high-resolution timers (perf_counter)
  - Provide interpretable "accuracy" deltas where a direct comparison makes sense
  - Be robust on Windows: optional deps, graceful skips, clear messaging

NOTES / FAIRNESS:
  - Python comparisons use the *same* NumPy arrays for bunker-stats, SciPy, and pure-NumPy.
  - R comparisons are optional and default to generating data in R (to avoid huge cross-process I/O).
    That means R accuracy comparisons are not strictly apples-to-apples unless you enable CSV handoff.
    Speed comparisons for R exclude Rscript startup time by timing inside R and returning elapsed.

Usage:
  python demo_resampling_compare_py_r.py
Optional:
  python demo_resampling_compare_py_r.py --with-r

Dependencies (Python):
  - numpy
  - bunker_stats (your binding)
  - scipy (optional, recommended)
  - arch (optional, for block bootstraps)

Dependencies (R, optional):
  - Rscript on PATH
  - boot, bayesboot, jsonlite (install.packages(c("boot","bayesboot","jsonlite")))

"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np


# ----------------------------
# Import bunker-stats
# ----------------------------
try:
    import bunker_stats as bsr
except Exception as e:
    print("ERROR: Could not import bunker_stats. Are you in your project env? Error:\n", e)
    sys.exit(1)

# ----------------------------
# Optional Python deps
# ----------------------------
try:
    from scipy import stats as scipy_stats  # type: ignore
    HAVE_SCIPY = True
except Exception:
    scipy_stats = None
    HAVE_SCIPY = False

try:
    from arch.bootstrap import (  # type: ignore
        MovingBlockBootstrap,
        CircularBlockBootstrap,
        StationaryBootstrap,
    )
    HAVE_ARCH = True
except Exception:
    MovingBlockBootstrap = CircularBlockBootstrap = StationaryBootstrap = None
    HAVE_ARCH = False


# ----------------------------
# Small utilities
# ----------------------------
def median_time(fn: Callable[[], Any], reps: int = 7, warmup: int = 1) -> float:
    """Return median wall-clock time in seconds (perf_counter)."""
    for _ in range(warmup):
        fn()
    times: List[float] = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return float(np.median(times))


def safe_float(x: Any) -> Optional[float]:
    try:
        v = float(x)
        if math.isfinite(v):
            return v
        return None
    except Exception:
        return None


def fmt_s(x: Optional[float]) -> str:
    if x is None:
        return "—"
    if x < 1e-6:
        return f"{x*1e9:.1f} ns"
    if x < 1e-3:
        return f"{x*1e6:.1f} µs"
    if x < 1.0:
        return f"{x*1e3:.2f} ms"
    return f"{x:.3f} s"


def rel_err(a: float, b: float, eps: float = 1e-12) -> float:
    denom = max(abs(b), eps)
    return abs(a - b) / denom


# ----------------------------
# Pure Python (NumPy) reference implementations
# ----------------------------
def np_bootstrap_mean(x: np.ndarray, n_resamples: int, seed: int) -> float:
    rng = np.random.default_rng(seed)
    n = x.size
    idx = rng.integers(0, n, size=(n_resamples, n), endpoint=False)
    return float(np.mean(np.mean(x[idx], axis=1)))


def np_bootstrap_ci(x: np.ndarray, stat: str, n_resamples: int, alpha: float, seed: int) -> Tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = x.size
    idx = rng.integers(0, n, size=(n_resamples, n), endpoint=False)
    samp = x[idx]
    if stat == "mean":
        thetas = np.mean(samp, axis=1)
    elif stat == "median":
        thetas = np.median(samp, axis=1)
    elif stat == "std":
        thetas = np.std(samp, axis=1, ddof=1)
    else:
        raise ValueError("stat must be mean/median/std")

    lo = float(np.quantile(thetas, alpha / 2))
    hi = float(np.quantile(thetas, 1 - alpha / 2))
    return lo, hi


def np_permutation_corr_test(x: np.ndarray, y: np.ndarray, n_perm: int, seed: int, alternative: str) -> Tuple[float, float]:
    rng = np.random.default_rng(seed)
    obs = float(np.corrcoef(x, y)[0, 1])
    count = 0
    for _ in range(n_perm):
        yp = rng.permutation(y)
        r = float(np.corrcoef(x, yp)[0, 1])
        if not math.isfinite(r):
            continue
        if alternative == "two-sided":
            count += (abs(r) >= abs(obs))
        elif alternative == "greater":
            count += (r >= obs)
        elif alternative == "less":
            count += (r <= obs)
        else:
            raise ValueError("alternative")
    p = (count + 1.0) / (n_perm + 1.0)
    return obs, float(p)


def np_permutation_mean_diff_test(x: np.ndarray, y: np.ndarray, n_perm: int, seed: int, alternative: str) -> Tuple[float, float]:
    rng = np.random.default_rng(seed)
    obs = float(np.mean(x) - np.mean(y))
    pooled = np.concatenate([x, y])
    nx = x.size
    count = 0
    for _ in range(n_perm):
        perm = rng.permutation(pooled)
        diff = float(np.mean(perm[:nx]) - np.mean(perm[nx:]))
        if alternative == "two-sided":
            count += (abs(diff) >= abs(obs))
        elif alternative == "greater":
            count += (diff >= obs)
        elif alternative == "less":
            count += (diff <= obs)
        else:
            raise ValueError("alternative")
    p = (count + 1.0) / (n_perm + 1.0)
    return obs, float(p)


def np_influence_mean(x: np.ndarray) -> np.ndarray:
    mu = np.mean(x)
    return (x - mu).astype(np.float64, copy=False)


# ----------------------------
# Python library (SciPy / arch) wrappers
# ----------------------------
def scipy_bootstrap_ci(x: np.ndarray, stat: str, n_resamples: int, alpha: float, seed: int, method: str) -> Tuple[float, float]:
    if not HAVE_SCIPY:
        raise RuntimeError("SciPy not available")

    def statistic(data, axis):
        if stat == "mean":
            return np.mean(data, axis=axis)
        if stat == "median":
            return np.median(data, axis=axis)
        if stat == "std":
            return np.std(data, axis=axis, ddof=1)
        raise ValueError("stat must be mean/median/std")

    res = scipy_stats.bootstrap(
        (x,),
        statistic,
        n_resamples=n_resamples,
        confidence_level=1 - alpha,
        method=method,  # "percentile" / "basic" / "bca"
        random_state=seed,
        vectorized=True,
        axis=0,
    )
    ci = res.confidence_interval
    return float(ci.low), float(ci.high)


def scipy_permutation_test_corr(x: np.ndarray, y: np.ndarray, n_resamples: int, seed: int, alternative: str) -> Tuple[float, float]:
    if not HAVE_SCIPY:
        raise RuntimeError("SciPy not available")

    obs = float(np.corrcoef(x, y)[0, 1])
    res = scipy_stats.permutation_test(
        (x, y),
        statistic=lambda a, b: float(np.corrcoef(a, b)[0, 1]),
        vectorized=False,
        n_resamples=n_resamples,
        alternative=alternative,
        random_state=seed,
    )
    return obs, float(res.pvalue)


def scipy_permutation_test_mean_diff(x: np.ndarray, y: np.ndarray, n_resamples: int, seed: int, alternative: str) -> Tuple[float, float]:
    if not HAVE_SCIPY:
        raise RuntimeError("SciPy not available")

    obs = float(np.mean(x) - np.mean(y))
    res = scipy_stats.permutation_test(
        (x, y),
        statistic=lambda a, b: float(np.mean(a) - np.mean(b)),
        vectorized=False,
        n_resamples=n_resamples,
        alternative=alternative,
        random_state=seed,
    )
    return obs, float(res.pvalue)


def arch_block_bootstrap_mean_ci(x: np.ndarray, kind: str, n_resamples: int, block_len: int, alpha: float, seed: int) -> Tuple[float, float]:
    if not HAVE_ARCH:
        raise RuntimeError("arch not available")

    rng = np.random.default_rng(seed)

    if kind == "moving":
        bs = MovingBlockBootstrap(block_len, x)
    elif kind == "circular":
        bs = CircularBlockBootstrap(block_len, x)
    elif kind == "stationary":
        bs = StationaryBootstrap(block_len, x)
    else:
        raise ValueError("kind")

    def stat(data):
        (x_,) = data
        return float(np.mean(x_))

    out = bs.conf_int(stat, reps=n_resamples, method="percentile", size=1 - alpha, random_state=rng)
    return float(out[0, 0]), float(out[1, 0])


# ----------------------------
# R harness (optional)
# ----------------------------
R_SCRIPT = r"""
suppressMessages(library(boot))
suppressMessages(library(bayesboot))
suppressMessages(library(jsonlite))

args <- commandArgs(trailingOnly=TRUE)
json_path <- args[1]
payload <- jsonlite::fromJSON(json_path)

time_it <- function(expr) {
  t <- system.time(val <- eval(expr))
  list(value=val, elapsed=as.numeric(t[["elapsed"]]))
}

alpha <- payload$alpha
seed <- payload$seed
n <- payload$n
B <- payload$B
P <- payload$P
block_len <- payload$block_len
alt <- payload$alternative

set.seed(seed)

# Generate data in R (speed comparisons). Python and R won't share identical arrays by default.
x <- rnorm(n)
y <- rnorm(n) + 0.3

boot_stat_mean <- function(data, idx) mean(data[idx])

boot_mean_ci_percentile <- function() {
  b <- boot(x, statistic=boot_stat_mean, R=B, stype="i")
  ci <- boot.ci(b, type="perc", conf=1-alpha)
  c(ci$percent[4], ci$percent[5])
}

boot_mean_ci_bca <- function() {
  b <- boot(x, statistic=boot_stat_mean, R=B, stype="i")
  ci <- boot.ci(b, type="bca", conf=1-alpha)
  c(ci$bca[4], ci$bca[5])
}

boot_mean_ci_studentized <- function() {
  b <- boot(x, statistic=boot_stat_mean, R=B, stype="i")
  ci <- boot.ci(b, type="stud", conf=1-alpha)
  c(ci$stud[4], ci$stud[5])
}

ts_mean <- function(ts) mean(ts)

moving_block_ci <- function(endcorr=FALSE) {
  tb <- tsboot(x, statistic=ts_mean, R=B, l=block_len, sim="fixed", endcorr=endcorr)
  qs <- quantile(tb$t, probs=c(alpha/2, 1-alpha/2), names=FALSE, type=7)
  c(qs[1], qs[2])
}

stationary_block_ci <- function() {
  tb <- tsboot(x, statistic=ts_mean, R=B, l=block_len, sim="geom")
  qs <- quantile(tb$t, probs=c(alpha/2, 1-alpha/2), names=FALSE, type=7)
  c(qs[1], qs[2])
}

perm_corr <- function() {
  obs <- cor(x, y)
  ext <- 0
  for (i in 1:P) {
    yp <- sample(y, replace=FALSE)
    r <- cor(x, yp)
    if (!is.finite(r)) next
    if (alt == "two-sided") {
      if (abs(r) >= abs(obs)) ext <- ext + 1
    } else if (alt == "greater") {
      if (r >= obs) ext <- ext + 1
    } else if (alt == "less") {
      if (r <= obs) ext <- ext + 1
    }
  }
  p <- (ext + 1) / (P + 1)
  c(obs, p)
}

perm_mean_diff <- function() {
  obs <- mean(x) - mean(y)
  pooled <- c(x, y)
  nx <- length(x)
  ext <- 0
  for (i in 1:P) {
    perm <- sample(pooled, replace=FALSE)
    d <- mean(perm[1:nx]) - mean(perm[(nx+1):length(perm)])
    if (alt == "two-sided") {
      if (abs(d) >= abs(obs)) ext <- ext + 1
    } else if (alt == "greater") {
      if (d >= obs) ext <- ext + 1
    } else if (alt == "less") {
      if (d <= obs) ext <- ext + 1
    }
  }
  p <- (ext + 1) / (P + 1)
  c(obs, p)
}

jack_after_boot <- function() {
  b <- boot(x, statistic=boot_stat_mean, R=B, stype="i")
  ja <- jack.after.boot(x, b, boot_stat_mean)
  as.numeric(ja$jack.se)
}

empinf_mean <- function() {
  ei <- empinf(x, theta=mean)
  c(sum(ei$inf), mean(ei$inf), sd(ei$inf))
}

bayesboot_ci_mean <- function() {
  bb <- bayesboot(x, mean, R=B, seed=seed)
  qs <- quantile(bb$t, probs=c(alpha/2, 1-alpha/2), names=FALSE, type=7)
  c(qs[1], qs[2])
}

op <- payload$op

tmp <- NULL
if (op == "boot_perc") tmp <- time_it(quote(boot_mean_ci_percentile()))
else if (op == "boot_bca") tmp <- time_it(quote(boot_mean_ci_bca()))
else if (op == "boot_stud") tmp <- time_it(quote(boot_mean_ci_studentized()))
else if (op == "mbb") tmp <- time_it(quote(moving_block_ci(FALSE)))
else if (op == "cbb") tmp <- time_it(quote(moving_block_ci(TRUE)))
else if (op == "sbb") tmp <- time_it(quote(stationary_block_ci()))
else if (op == "perm_corr") tmp <- time_it(quote(perm_corr()))
else if (op == "perm_mean_diff") tmp <- time_it(quote(perm_mean_diff()))
else if (op == "jack_after_boot") tmp <- time_it(quote(jack_after_boot()))
else if (op == "empinf_mean") tmp <- time_it(quote(empinf_mean()))
else if (op == "bayesboot_ci") tmp <- time_it(quote(bayesboot_ci_mean()))
else stop(paste("Unknown op:", op))

result <- list(op=op, n=n, B=B, P=P, block_len=block_len, alternative=alt,
               value=tmp$value, elapsed=tmp$elapsed)
jsonlite::write_json(result, path=payload$out_path, auto_unbox=TRUE)
"""


def have_rscript() -> bool:
    return shutil.which("Rscript") is not None


def run_r_op(op: str, n: int, B: int, P: int, block_len: int, alpha: float, seed: int, alternative: str) -> Optional[Dict[str, Any]]:
    if not have_rscript():
        return None

    with tempfile.TemporaryDirectory() as td:
        td = os.path.abspath(td)
        r_path = os.path.join(td, "bench_resampling.R")
        in_path = os.path.join(td, "payload.json")
        out_path = os.path.join(td, "out.json")

        with open(r_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(R_SCRIPT)

        payload = {
            "op": op,
            "n": int(n),
            "B": int(B),
            "P": int(P),
            "block_len": int(block_len),
            "alpha": float(alpha),
            "seed": int(seed),
            "alternative": alternative,
            "out_path": out_path,
        }
        with open(in_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        cmd = ["Rscript", r_path, in_path]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            msg = (e.stderr or e.stdout or "").strip()
            print(f"[R] FAILED op={op} n={n}: {msg[:400]}")
            if "there is no package called" in msg or "could not find function" in msg:
                print('[R] Hint: in R, run: install.packages(c("boot","bayesboot","jsonlite"))')
            return None

        with open(out_path, "r", encoding="utf-8") as f:
            return json.load(f)


# ----------------------------
# Benchmark plan
# ----------------------------
@dataclass
class Case:
    name: str
    run_bunker: Callable[[], Any]
    run_py_lib: Optional[Callable[[], Any]]
    run_py_pure: Optional[Callable[[], Any]]
    r_op: Optional[str]
    acc_fn: Optional[Callable[[Any, Any], Optional[float]]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-r", action="store_true", help="Enable R comparisons (requires Rscript + packages).")
    ap.add_argument("--reps", type=int, default=7, help="Repetitions per timing (median).")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    seed = int(args.seed)
    alpha = 0.05
    sizes = [1_000, 10_000, 100_000, 1_000_000]
    block_len = 10

    def choose_B(n: int) -> int:
        if n <= 10_000:
            return 1_000
        if n <= 100_000:
            return 400
        return 200

    def choose_P(n: int) -> int:
        if n <= 10_000:
            return 2_000
        if n <= 100_000:
            return 1_000
        return 500

    def make_data(n: int) -> Tuple[np.ndarray, np.ndarray]:
        rng = np.random.default_rng(seed + n)
        x = rng.normal(0, 1, size=n).astype(np.float64)
        y = (rng.normal(0, 1, size=n) + 0.3).astype(np.float64)
        return x, y

    def acc_scalar(a: Any, b: Any) -> Optional[float]:
        fa = safe_float(a); fb = safe_float(b)
        if fa is None or fb is None:
            return None
        return rel_err(fa, fb)

    def acc_pair_ci(a: Any, b: Any) -> Optional[float]:
        try:
            alo, ahi = a
            blo, bhi = b
            w = max(abs(bhi - blo), 1e-12)
            return float(math.sqrt(((alo - blo) ** 2 + (ahi - bhi) ** 2)) / w)
        except Exception:
            return None

    def acc_perm_out(a: Any, b: Any) -> Optional[float]:
        try:
            a_obs, a_p = a
            b_obs, b_p = b
            o = rel_err(float(a_obs), float(b_obs))
            p = abs(float(a_p) - float(b_p))
            return float(o + p)
        except Exception:
            return None

    def build_cases(x: np.ndarray, y: np.ndarray, n: int) -> List[Case]:
        B = choose_B(n)
        P = choose_P(n)

        cases: List[Case] = []

        # Bootstrap primitives
        cases.append(Case(
            name=f"bootstrap_mean (B={B})",
            run_bunker=lambda: float(bsr.bootstrap_mean(x, n_resamples=B, random_state=seed)),
            run_py_lib=None,
            run_py_pure=lambda: np_bootstrap_mean(x, n_resamples=B, seed=seed),
            r_op=None,
            acc_fn=acc_scalar
        ))

        cases.append(Case(
            name=f"bootstrap_mean_ci perc (B={B})",
            run_bunker=lambda: tuple(map(float, bsr.bootstrap_mean_ci(x, n_resamples=B, random_state=seed))),
            run_py_lib=(lambda: scipy_bootstrap_ci(x, "mean", B, alpha, seed, method="percentile")) if HAVE_SCIPY else None,
            run_py_pure=(lambda: np_bootstrap_ci(x, "mean", B, alpha, seed)),
            r_op="boot_perc",
            acc_fn=acc_pair_ci
        ))

        cases.append(Case(
            name=f"bootstrap_ci median perc (B={B})",
            run_bunker=lambda: tuple(map(float, bsr.bootstrap_ci(x, stat="median", n_resamples=B, random_state=seed))),
            run_py_lib=(lambda: scipy_bootstrap_ci(x, "median", B, alpha, seed, method="percentile")) if HAVE_SCIPY else None,
            run_py_pure=(lambda: np_bootstrap_ci(x, "median", B, alpha, seed)),
            r_op=None,
            acc_fn=acc_pair_ci
        ))

        # BCa is expensive; cap
        if n <= 100_000:
            cases.append(Case(
                name=f"bootstrap_bca_ci mean (B={B})",
                run_bunker=lambda: tuple(map(float, bsr.bootstrap_bca_ci(x, stat="mean", n_resamples=B, random_state=seed))),
                run_py_lib=(lambda: scipy_bootstrap_ci(x, "mean", B, alpha, seed, method="bca")) if HAVE_SCIPY else None,
                run_py_pure=None,
                r_op="boot_bca",
                acc_fn=acc_pair_ci
            ))
            cases.append(Case(
                name=f"bootstrap_t_ci_mean (B={B})",
                run_bunker=lambda: tuple(map(float, bsr.bootstrap_t_ci_mean(x, n_resamples=B, random_state=seed))),
                run_py_lib=None,
                run_py_pure=None,
                r_op="boot_stud",
                acc_fn=None
            ))
        else:
            cases.append(Case("bootstrap_bca_ci mean (SKIP)", lambda: None, None, None, None, None))
            cases.append(Case("bootstrap_t_ci_mean (SKIP)", lambda: None, None, None, None, None))

        cases.append(Case(
            name=f"bayesian_bootstrap_ci mean (B={B})",
            run_bunker=lambda: tuple(map(float, bsr.bayesian_bootstrap_ci(x, stat="mean", n_resamples=B, random_state=seed))),
            run_py_lib=None,
            run_py_pure=None,
            r_op="bayesboot_ci",
            acc_fn=None
        ))

        # Block bootstraps
        cases.append(Case(
            name=f"moving_block_bootstrap_mean_ci (B={B})",
            run_bunker=lambda: tuple(map(float, bsr.moving_block_bootstrap_mean_ci(x, n_resamples=B, block_length=block_len, random_state=seed))),
            run_py_lib=(lambda: arch_block_bootstrap_mean_ci(x, "moving", B, block_len, alpha, seed)) if HAVE_ARCH else None,
            run_py_pure=None,
            r_op="mbb",
            acc_fn=acc_pair_ci if HAVE_ARCH else None
        ))
        cases.append(Case(
            name=f"circular_block_bootstrap_mean_ci (B={B})",
            run_bunker=lambda: tuple(map(float, bsr.circular_block_bootstrap_mean_ci(x, n_resamples=B, block_length=block_len, random_state=seed))),
            run_py_lib=(lambda: arch_block_bootstrap_mean_ci(x, "circular", B, block_len, alpha, seed)) if HAVE_ARCH else None,
            run_py_pure=None,
            r_op="cbb",
            acc_fn=acc_pair_ci if HAVE_ARCH else None
        ))
        cases.append(Case(
            name=f"stationary_bootstrap_mean_ci (B={B})",
            run_bunker=lambda: tuple(map(float, bsr.stationary_bootstrap_mean_ci(x, n_resamples=B, block_length=block_len, random_state=seed))),
            run_py_lib=(lambda: arch_block_bootstrap_mean_ci(x, "stationary", B, block_len, alpha, seed)) if HAVE_ARCH else None,
            run_py_pure=None,
            r_op="sbb",
            acc_fn=acc_pair_ci if HAVE_ARCH else None
        ))

        # Permutation tests
        cases.append(Case(
            name=f"permutation_corr_test (P={P})",
            run_bunker=lambda: tuple(map(float, bsr.permutation_corr_test(x, y, n_permutations=P, random_state=seed))),
            run_py_lib=(lambda: scipy_permutation_test_corr(x, y, P, seed, alternative="two-sided")) if HAVE_SCIPY else None,
            run_py_pure=(lambda: np_permutation_corr_test(x, y, P, seed, alternative="two-sided")),
            r_op="perm_corr",
            acc_fn=acc_perm_out
        ))
        cases.append(Case(
            name=f"permutation_mean_diff_test (P={P})",
            run_bunker=lambda: tuple(map(float, bsr.permutation_mean_diff_test(x, y, n_permutations=P, random_state=seed))),
            run_py_lib=(lambda: scipy_permutation_test_mean_diff(x, y, P, seed, alternative="two-sided")) if HAVE_SCIPY else None,
            run_py_pure=(lambda: np_permutation_mean_diff_test(x, y, P, seed, alternative="two-sided")),
            r_op="perm_mean_diff",
            acc_fn=acc_perm_out
        ))

        # Jackknife + influence
        cases.append(Case(
            name="jackknife_mean",
            run_bunker=lambda: float(bsr.jackknife_mean(x)),
            run_py_lib=None,
            run_py_pure=(lambda: float(np.mean(x))),
            r_op=None,
            acc_fn=acc_scalar
        ))
        cases.append(Case(
            name="jackknife_mean_ci",
            run_bunker=lambda: tuple(map(float, bsr.jackknife_mean_ci(x))),
            run_py_lib=None,
            run_py_pure=None,
            r_op=None,
            acc_fn=None
        ))
        cases.append(Case(
            name="delete_d_jackknife_mean (d=5)",
            run_bunker=lambda: float(bsr.delete_d_jackknife_mean(x, d=5)),
            run_py_lib=None,
            run_py_pure=None,
            r_op=None,
            acc_fn=None
        ))
        cases.append(Case(
            name=f"jackknife_after_bootstrap_se_mean (B={B})",
            run_bunker=lambda: float(bsr.jackknife_after_bootstrap_se_mean(x, n_resamples=B, random_state=seed)),
            run_py_lib=None,
            run_py_pure=None,
            r_op="jack_after_boot",
            acc_fn=None
        ))
        cases.append(Case(
            name="influence_mean (summary)",
            run_bunker=lambda: {
                "sum": float(np.sum(bsr.influence_mean(x))),
                "mean": float(np.mean(bsr.influence_mean(x))),
                "std": float(np.std(bsr.influence_mean(x))),
            },
            run_py_lib=None,
            run_py_pure=(lambda: {
                "sum": float(np.sum(np_influence_mean(x))),
                "mean": float(np.mean(np_influence_mean(x))),
                "std": float(np.std(np_influence_mean(x))),
            }),
            r_op="empinf_mean",
            acc_fn=None
        ))

        # Extra primitives (bunker-only in this demo)
        cases.append(Case(
            name="bootstrap_se (mean)",
            run_bunker=lambda: float(bsr.bootstrap_se(x, stat="mean", n_resamples=B, random_state=seed)),
            run_py_lib=None,
            run_py_pure=None,
            r_op=None,
            acc_fn=None
        ))
        cases.append(Case(
            name="bootstrap_var (mean)",
            run_bunker=lambda: float(bsr.bootstrap_var(x, stat="mean", n_resamples=B, random_state=seed)),
            run_py_lib=None,
            run_py_pure=None,
            r_op=None,
            acc_fn=None
        ))
        cases.append(Case(
            name="bootstrap_corr (CI)",
            run_bunker=lambda: tuple(map(float, bsr.bootstrap_corr(x, y, n_resamples=B, random_state=seed))),
            run_py_lib=None,
            run_py_pure=None,
            r_op=None,
            acc_fn=None
        ))

        return cases

    print("=" * 100)
    print("BUNKER-STATS RESAMPLING BENCH: bunker-stats vs Python libs vs Pure NumPy vs R (optional)")
    print("=" * 100)
    print(f"NumPy: {np.__version__}")
    print(f"bunker_stats: {getattr(bsr, '__version__', 'unknown')}")
    print(f"SciPy available: {HAVE_SCIPY}")
    print(f"arch available:  {HAVE_ARCH}")
    print(f"Rscript available: {have_rscript()}")
    print(f"R enabled: {args.with_r}")
    print()

    rows: List[Dict[str, Any]] = []

    for n in sizes:
        x, y = make_data(n)
        cases = build_cases(x, y, n)
        B = choose_B(n)
        P = choose_P(n)

        print("-" * 100)
        print(f"N={n:,} | B={B} | P={P} | block_len={block_len}")
        print("-" * 100)

        for case in cases:
            if case.name.endswith("(SKIP)") or case.name.endswith("(SKIP)"):
                print(f"{case.name:45s}  SKIP")
                continue

            bunker_out = None
            bunker_t = None
            try:
                bunker_t = median_time(lambda: case.run_bunker(), reps=args.reps, warmup=1)
                bunker_out = case.run_bunker()
            except Exception as e:
                print(f"{case.name:45s}  bunker ERROR: {e}")
                bunker_t = None

            pylib_out = None
            pylib_t = None
            if case.run_py_lib is not None:
                try:
                    pylib_t = median_time(lambda: case.run_py_lib(), reps=args.reps, warmup=1)
                    pylib_out = case.run_py_lib()
                except Exception:
                    pylib_t = None
                    pylib_out = None

            pypure_out = None
            pypure_t = None
            if case.run_py_pure is not None:
                try:
                    pypure_t = median_time(lambda: case.run_py_pure(), reps=args.reps, warmup=1)
                    pypure_out = case.run_py_pure()
                except Exception:
                    pypure_t = None
                    pypure_out = None

            r_out = None
            r_t = None
            if args.with_r and case.r_op is not None:
                rres = run_r_op(case.r_op, n=n, B=B, P=P, block_len=block_len, alpha=alpha, seed=seed, alternative="two-sided")
                if rres is not None:
                    r_t = safe_float(rres.get("elapsed"))
                    r_out = rres.get("value")

            acc = None
            if case.acc_fn is not None and bunker_out is not None:
                ref = pylib_out if pylib_out is not None else pypure_out
                if ref is not None:
                    try:
                        acc = case.acc_fn(bunker_out, ref)
                    except Exception:
                        acc = None

            parts = [f"{case.name:45s}", f"bunker {fmt_s(bunker_t):>10s}"]
            if pylib_t is not None:
                parts.append(f"py-lib {fmt_s(pylib_t):>10s}")
            if pypure_t is not None:
                parts.append(f"py-pure {fmt_s(pypure_t):>10s}")
            if r_t is not None:
                parts.append(f"R {fmt_s(r_t):>10s}")
            if acc is not None:
                parts.append(f"acc {acc:.3e}")
            print(" | ".join(parts))

            rows.append({
                "n": n,
                "case": case.name,
                "bunker_time_s": bunker_t,
                "py_lib_time_s": pylib_t,
                "py_pure_time_s": pypure_t,
                "r_time_s": r_t,
                "acc_metric": acc,
            })

        print()

    out_csv = "resampling_compare_results.csv"
    try:
        import csv
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"Saved results to {out_csv}")
    except Exception:
        pass

    print("\nTips:")
    print("  - For speed regression on Windows, always use perf_counter + loops (like your pytest fix).")
    print("  - For Rust-side perf regression, Criterion baselines in CI are the cleanest.")
    print("  - For R comparisons, ensure packages: boot, bayesboot, jsonlite.")


if __name__ == "__main__":
    main()
