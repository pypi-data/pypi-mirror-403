# bunker_stats/resampling/config.py
"""
Ergonomic config objects for resampling methods.

These are thin Python wrappers around the Rust kernels that provide:
- Input validation with helpful error messages
- Consistent defaults and parameter naming
- Optional NaN policy handling (pre-filter in Python)
- No performance overhead in "propagate" mode (direct passthrough)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional, Tuple, Union
import numpy as np
import warnings

# Import the Rust extension (same pattern as main __init__.py)
try:
    from bunker_stats import _rs
except ImportError:
    import importlib
    _rs = None
    for module_path in [
        "bunker_stats.bunker_stats_rs",
        "bunker_stats_rs.bunker_stats_rs",
        "bunker_stats_rs"
    ]:
        try:
            _rs = importlib.import_module(module_path)
            break
        except ImportError:
            continue
    
    if _rs is None:
        raise ImportError("Could not import Rust extension for resampling")


# ======================================================================================
# VALIDATION HELPERS
# ======================================================================================

def _validate_array(arr: np.ndarray, name: str, allow_empty: bool = False) -> np.ndarray:
    """Validate and convert to float64 array."""
    arr = np.asarray(arr, dtype=np.float64)
    
    if arr.ndim != 1:
        raise ValueError(
            f"{name}: expected 1D array, got shape {arr.shape}. "
            f"Hint: flatten with .ravel() or select a single column."
        )
    
    if not allow_empty and arr.size == 0:
        raise ValueError(
            f"{name}: array is empty. "
            f"Hint: ensure your data is non-empty before resampling."
        )
    
    return arr


def _validate_conf(conf: float, function_name: str) -> None:
    """Validate confidence level."""
    if not (0.0 < conf < 1.0):
        raise ValueError(
            f"{function_name}: conf must be in (0, 1), got {conf}. "
            f"Hint: use conf=0.95 for a 95% confidence interval."
        )


def _validate_n_resamples(n: int, function_name: str) -> None:
    """Validate number of resamples."""
    if n < 1:
        raise ValueError(
            f"{function_name}: n_resamples must be >= 1, got {n}. "
            f"Hint: typical values are 1000-10000 for bootstrap."
        )


def _validate_n_permutations(n: int, function_name: str) -> None:
    """Validate number of permutations."""
    if n < 1:
        raise ValueError(
            f"{function_name}: n_permutations must be >= 1, got {n}. "
            f"Hint: typical values are 1000-10000 for permutation tests."
        )


def _validate_stat(stat: str, function_name: str, supported: list[str]) -> None:
    """Validate statistic name."""
    if stat not in supported:
        raise ValueError(
            f"{function_name}: stat must be one of {supported}, got '{stat}'. "
            f"Hint: currently supported statistics are: {', '.join(supported)}."
        )


def _validate_alternative(alt: str, function_name: str) -> None:
    """Validate alternative hypothesis."""
    valid = ["two-sided", "greater", "less"]
    if alt not in valid:
        raise ValueError(
            f"{function_name}: alternative must be one of {valid}, got '{alt}'. "
            f"Hint: use 'two-sided' for ≠, 'greater' for >, 'less' for <."
        )


def _validate_random_state(rs: Optional[int], function_name: str) -> Optional[int]:
    """Validate random_state parameter."""
    if rs is None:
        return None
    
    if not isinstance(rs, (int, np.integer)):
        raise TypeError(
            f"{function_name}: random_state must be int or None, got {type(rs).__name__}. "
            f"Hint: use random_state=42 for reproducible results."
        )
    
    # Convert to u64 range
    rs_int = int(rs)
    if rs_int < 0:
        # Allow negative seeds by wrapping to unsigned
        rs_int = rs_int % (2**64)
    
    return rs_int


# ======================================================================================
# NaN FILTERING HELPERS
# ======================================================================================

def _filter_nans_single(x: np.ndarray, function_name: str) -> np.ndarray:
    """
    Filter NaNs from a single array.
    
    Returns a copy with NaNs removed. Raises if result is empty.
    """
    mask = np.isfinite(x)
    n_nan = (~mask).sum()
    
    if n_nan == len(x):
        raise ValueError(
            f"{function_name}: all values are NaN after filtering. "
            f"Hint: check your input data."
        )
    
    x_clean = x[mask]
    
    if n_nan > 0:
        warnings.warn(
            f"{function_name}: removed {n_nan} NaN value(s) from input array "
            f"({100 * n_nan / len(x):.1f}% of data).",
            UserWarning,
            stacklevel=3
        )
    
    return x_clean


def _filter_nans_paired(
    x: np.ndarray, 
    y: np.ndarray, 
    function_name: str
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Filter NaNs from paired arrays (pairwise deletion).
    
    Removes pairs where either x[i] or y[i] is NaN.
    Returns copies with valid pairs only. Raises if result is empty.
    """
    if len(x) != len(y):
        raise ValueError(
            f"{function_name}: x and y must have same length. "
            f"Got len(x)={len(x)}, len(y)={len(y)}."
        )
    
    mask = np.isfinite(x) & np.isfinite(y)
    n_removed = (~mask).sum()
    
    if n_removed == len(x):
        raise ValueError(
            f"{function_name}: all pairs have NaN after filtering. "
            f"Hint: check your input data."
        )
    
    x_clean = x[mask]
    y_clean = y[mask]
    
    if n_removed > 0:
        warnings.warn(
            f"{function_name}: removed {n_removed} pair(s) with NaN "
            f"({100 * n_removed / len(x):.1f}% of data).",
            UserWarning,
            stacklevel=3
        )
    
    return x_clean, y_clean


def _filter_nans_two_sample(
    x: np.ndarray,
    y: np.ndarray,
    function_name: str
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Filter NaNs from two independent samples.
    
    Removes NaNs within each sample independently (not pairwise).
    Returns copies with NaNs removed from each. Raises if either is empty.
    """
    mask_x = np.isfinite(x)
    mask_y = np.isfinite(y)
    
    n_nan_x = (~mask_x).sum()
    n_nan_y = (~mask_y).sum()
    
    if n_nan_x == len(x) or n_nan_y == len(y):
        raise ValueError(
            f"{function_name}: one or both samples are entirely NaN after filtering. "
            f"Hint: check your input data."
        )
    
    x_clean = x[mask_x]
    y_clean = y[mask_y]
    
    if n_nan_x > 0 or n_nan_y > 0:
        warnings.warn(
            f"{function_name}: removed {n_nan_x} NaN(s) from x, {n_nan_y} from y "
            f"({100 * n_nan_x / len(x):.1f}% and {100 * n_nan_y / len(y):.1f}% respectively).",
            UserWarning,
            stacklevel=3
        )
    
    return x_clean, y_clean


# ======================================================================================
# BOOTSTRAP CONFIG
# ======================================================================================

@dataclass
class BootstrapConfig:
    """
    Configuration for bootstrap resampling.
    
    This is a thin wrapper around Rust bootstrap functions that adds:
    - Input validation with helpful error messages
    - Consistent defaults
    - Optional NaN handling (pre-filter in Python, no kernel changes)
    
    Parameters
    ----------
    n_resamples : int, default=1000
        Number of bootstrap resamples to generate.
        Typical values: 1000-10000 for CI estimation.
    
    conf : float, default=0.95
        Confidence level for interval (0, 1).
        Examples: 0.95 for 95% CI, 0.99 for 99% CI.
    
    stat : str, default="mean"
        Statistic to compute. Supported: "mean", "median", "std".
        Note: "median" and "std" are slower than "mean".
    
    random_state : int or None, default=None
        Seed for reproducible results. If None, uses 0 (deterministic default).
        Use same seed for reproducible results across calls.
    
    nan_policy : {"propagate", "omit"}, default="propagate"
        How to handle NaNs:
        - "propagate": pass NaNs to Rust (fast, returns NaN if any NaN present)
        - "omit": filter NaNs in Python before calling Rust (slower, creates copy)
    
    parallel : bool, default=True
        Whether to use parallel execution (currently always True in Rust).
        Future: may add sequential mode for debugging.
    
    Examples
    --------
    >>> config = BootstrapConfig(n_resamples=5000, conf=0.99, random_state=42)
    >>> result = config.run(data)  # Returns (estimate, lower, upper)
    >>> 
    >>> # Equivalent shorthand:
    >>> result = config(data)
    """
    
    n_resamples: int = 1000
    conf: float = 0.95
    stat: Literal["mean", "median", "std"] = "mean"
    random_state: Optional[int] = None
    nan_policy: Literal["propagate", "omit"] = "propagate"
    parallel: bool = True  # Currently not exposed to Rust, documented for future
    
    def __post_init__(self):
        """Validate config parameters on construction."""
        _validate_n_resamples(self.n_resamples, "BootstrapConfig")
        _validate_conf(self.conf, "BootstrapConfig")
        _validate_stat(self.stat, "BootstrapConfig", ["mean", "median", "std"])
        self.random_state = _validate_random_state(self.random_state, "BootstrapConfig")
        
        if self.nan_policy not in ["propagate", "omit"]:
            raise ValueError(
                f"BootstrapConfig: nan_policy must be 'propagate' or 'omit', got '{self.nan_policy}'."
            )
    
    def run(self, x: np.ndarray) -> Tuple[float, float, float]:
        """
        Run bootstrap on data.
        
        Parameters
        ----------
        x : array-like
            1D data array to bootstrap.
        
        Returns
        -------
        estimate : float
            Bootstrap estimate of the statistic (mean of bootstrap distribution).
        lower : float
            Lower confidence bound.
        upper : float
            Upper confidence bound.
        
        Raises
        ------
        ValueError
            If input validation fails or results are invalid.
        """
        # Validate and convert input
        x = _validate_array(x, "BootstrapConfig.run(x)")
        
        # Apply NaN policy
        if self.nan_policy == "omit":
            x = _filter_nans_single(x, "BootstrapConfig")
        
        # Call Rust kernel
        # Note: bootstrap_ci returns (estimate, lower, upper)
        result = _rs.bootstrap_ci(
            x,
            stat=self.stat,
            n_resamples=self.n_resamples,
            conf=self.conf,
            random_state=self.random_state
        )
        
        return result
    
    def __call__(self, x: np.ndarray) -> Tuple[float, float, float]:
        """Shorthand for .run()"""
        return self.run(x)


@dataclass
class BootstrapCorrConfig:
    """
    Configuration for bootstrap correlation with confidence interval.
    
    Parameters
    ----------
    n_resamples : int, default=1000
        Number of bootstrap resamples.
    
    conf : float, default=0.95
        Confidence level (0, 1).
    
    random_state : int or None, default=None
        Seed for reproducibility.
    
    nan_policy : {"propagate", "omit"}, default="propagate"
        How to handle NaNs:
        - "propagate": pass to Rust (returns NaN if any NaN)
        - "omit": pairwise deletion in Python (slower)
    
    parallel : bool, default=True
        Use parallel execution (not yet exposed to Rust).
    
    Examples
    --------
    >>> config = BootstrapCorrConfig(n_resamples=5000, random_state=42)
    >>> r, lower, upper = config.run(x, y)
    """
    
    n_resamples: int = 1000
    conf: float = 0.95
    random_state: Optional[int] = None
    nan_policy: Literal["propagate", "omit"] = "propagate"
    parallel: bool = True
    
    def __post_init__(self):
        _validate_n_resamples(self.n_resamples, "BootstrapCorrConfig")
        _validate_conf(self.conf, "BootstrapCorrConfig")
        self.random_state = _validate_random_state(self.random_state, "BootstrapCorrConfig")
        
        if self.nan_policy not in ["propagate", "omit"]:
            raise ValueError(
                f"BootstrapCorrConfig: nan_policy must be 'propagate' or 'omit', "
                f"got '{self.nan_policy}'."
            )
    
    def run(self, x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float]:
        """
        Compute bootstrap correlation CI.
        
        Parameters
        ----------
        x, y : array-like
            Paired 1D data arrays.
        
        Returns
        -------
        corr : float
            Bootstrap estimate of correlation.
        lower : float
            Lower confidence bound.
        upper : float
            Upper confidence bound.
        """
        x = _validate_array(x, "BootstrapCorrConfig.run(x)")
        y = _validate_array(y, "BootstrapCorrConfig.run(y)")
        
        if len(x) != len(y):
            raise ValueError(
                f"BootstrapCorrConfig: x and y must have same length. "
                f"Got len(x)={len(x)}, len(y)={len(y)}."
            )
        
        # Apply NaN policy
        if self.nan_policy == "omit":
            x, y = _filter_nans_paired(x, y, "BootstrapCorrConfig")
        
        result = _rs.bootstrap_corr(
            x, y,
            n_resamples=self.n_resamples,
            conf=self.conf,
            random_state=self.random_state
        )
        
        return result
    
    def __call__(self, x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float]:
        """Shorthand for .run()"""
        return self.run(x, y)


# ======================================================================================
# PERMUTATION TEST CONFIG
# ======================================================================================

@dataclass
class PermutationConfig:
    """
    Configuration for permutation tests.
    
    Parameters
    ----------
    n_permutations : int, default=1000
        Number of random permutations to generate.
        Typical values: 1000-10000 for accurate p-values.
    
    alternative : {"two-sided", "greater", "less"}, default="two-sided"
        Alternative hypothesis:
        - "two-sided": test if statistic ≠ null
        - "greater": test if statistic > null
        - "less": test if statistic < null
    
    random_state : int or None, default=None
        Seed for reproducibility.
    
    nan_policy : {"propagate", "omit"}, default="propagate"
        How to handle NaNs:
        - "propagate": pass to Rust
        - "omit": pre-filter in Python (semantics depend on test type)
    
    parallel : bool, default=True
        Use parallel execution.
    
    Examples
    --------
    >>> config = PermutationConfig(n_permutations=5000, alternative="greater")
    >>> statistic, pvalue = config.run_mean_diff(group1, group2)
    """
    
    n_permutations: int = 1000
    alternative: Literal["two-sided", "greater", "less"] = "two-sided"
    random_state: Optional[int] = None
    nan_policy: Literal["propagate", "omit"] = "propagate"
    parallel: bool = True
    
    def __post_init__(self):
        _validate_n_permutations(self.n_permutations, "PermutationConfig")
        _validate_alternative(self.alternative, "PermutationConfig")
        self.random_state = _validate_random_state(self.random_state, "PermutationConfig")
        
        if self.nan_policy not in ["propagate", "omit"]:
            raise ValueError(
                f"PermutationConfig: nan_policy must be 'propagate' or 'omit', "
                f"got '{self.nan_policy}'."
            )
    
    def run_corr(self, x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
        """
        Permutation test for correlation.
        
        Parameters
        ----------
        x, y : array-like
            Paired 1D arrays to test for correlation.
        
        Returns
        -------
        observed : float
            Observed correlation.
        pvalue : float
            Two-sided p-value (or one-sided if alternative != "two-sided").
        """
        x = _validate_array(x, "PermutationConfig.run_corr(x)")
        y = _validate_array(y, "PermutationConfig.run_corr(y)")
        
        if len(x) != len(y):
            raise ValueError(
                f"PermutationConfig.run_corr: x and y must have same length. "
                f"Got len(x)={len(x)}, len(y)={len(y)}."
            )
        
        # Apply NaN policy (pairwise for correlation)
        if self.nan_policy == "omit":
            x, y = _filter_nans_paired(x, y, "PermutationConfig.run_corr")
        
        result = _rs.permutation_corr_test(
            x, y,
            n_permutations=self.n_permutations,
            alternative=self.alternative,
            random_state=self.random_state
        )
        
        return result
    
    def run_mean_diff(self, x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
        """
        Permutation test for mean difference (two independent samples).
        
        Parameters
        ----------
        x, y : array-like
            Independent samples to compare.
        
        Returns
        -------
        observed_diff : float
            Observed mean(x) - mean(y).
        pvalue : float
            P-value under permutation null.
        """
        x = _validate_array(x, "PermutationConfig.run_mean_diff(x)")
        y = _validate_array(y, "PermutationConfig.run_mean_diff(y)")
        
        # Apply NaN policy (independent samples: filter each separately)
        if self.nan_policy == "omit":
            x, y = _filter_nans_two_sample(x, y, "PermutationConfig.run_mean_diff")
        
        result = _rs.permutation_mean_diff_test(
            x, y,
            n_permutations=self.n_permutations,
            alternative=self.alternative,
            random_state=self.random_state
        )
        
        return result


# ======================================================================================
# JACKKNIFE CONFIG
# ======================================================================================

@dataclass
class JackknifeConfig:
    """
    Configuration for jackknife resampling.
    
    Jackknife has no random component, so no random_state parameter.
    NaN policy is supported for consistency.
    
    Parameters
    ----------
    conf : float, default=0.95
        Confidence level for CI methods (0, 1).
    
    nan_policy : {"propagate", "omit"}, default="propagate"
        How to handle NaNs.
    
    Examples
    --------
    >>> config = JackknifeConfig(conf=0.99)
    >>> estimate, lower, upper = config.run_mean_ci(data)
    """
    
    conf: float = 0.95
    nan_policy: Literal["propagate", "omit"] = "propagate"
    
    def __post_init__(self):
        _validate_conf(self.conf, "JackknifeConfig")
        
        if self.nan_policy not in ["propagate", "omit"]:
            raise ValueError(
                f"JackknifeConfig: nan_policy must be 'propagate' or 'omit', "
                f"got '{self.nan_policy}'."
            )
    
    def run_mean(self, x: np.ndarray) -> Tuple[float, float, float]:
        """
        Jackknife estimate for the mean.
        
        Returns
        -------
        estimate : float
            Jackknife estimate.
        bias : float
            Estimated bias.
        std_error : float
            Standard error.
        """
        x = _validate_array(x, "JackknifeConfig.run_mean(x)")
        
        if self.nan_policy == "omit":
            x = _filter_nans_single(x, "JackknifeConfig.run_mean")
        
        result = _rs.jackknife_mean(x)
        return result
    
    def run_mean_ci(self, x: np.ndarray) -> Tuple[float, float, float]:
        """
        Jackknife estimate with percentile CI.
        
        Returns
        -------
        estimate : float
            Jackknife estimate.
        lower : float
            Lower confidence bound.
        upper : float
            Upper confidence bound.
        """
        x = _validate_array(x, "JackknifeConfig.run_mean_ci(x)")
        
        if self.nan_policy == "omit":
            x = _filter_nans_single(x, "JackknifeConfig.run_mean_ci")
        
        result = _rs.jackknife_mean_ci(x, conf=self.conf)
        return result


# ======================================================================================
# CONVENIENCE FUNCTIONS (optional - for users who prefer functional API)
# ======================================================================================

def bootstrap(
    x: np.ndarray,
    *,
    stat: str = "mean",
    n_resamples: int = 1000,
    conf: float = 0.95,
    random_state: Optional[int] = None,
    nan_policy: Literal["propagate", "omit"] = "propagate",
) -> Tuple[float, float, float]:
    """
    Bootstrap confidence interval (convenience wrapper).
    
    Equivalent to: BootstrapConfig(...).run(x)
    
    See BootstrapConfig for parameter documentation.
    """
    config = BootstrapConfig(
        n_resamples=n_resamples,
        conf=conf,
        stat=stat,
        random_state=random_state,
        nan_policy=nan_policy,
    )
    return config.run(x)


def bootstrap_corr(
    x: np.ndarray,
    y: np.ndarray,
    *,
    n_resamples: int = 1000,
    conf: float = 0.95,
    random_state: Optional[int] = None,
    nan_policy: Literal["propagate", "omit"] = "propagate",
) -> Tuple[float, float, float]:
    """
    Bootstrap correlation CI (convenience wrapper).
    
    Equivalent to: BootstrapCorrConfig(...).run(x, y)
    """
    config = BootstrapCorrConfig(
        n_resamples=n_resamples,
        conf=conf,
        random_state=random_state,
        nan_policy=nan_policy,
    )
    return config.run(x, y)


def permutation_test(
    x: np.ndarray,
    y: np.ndarray,
    *,
    test: Literal["corr", "mean_diff"] = "mean_diff",
    n_permutations: int = 1000,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
    random_state: Optional[int] = None,
    nan_policy: Literal["propagate", "omit"] = "propagate",
) -> Tuple[float, float]:
    """
    Permutation test (convenience wrapper).
    
    Parameters
    ----------
    test : {"corr", "mean_diff"}
        Which test to run:
        - "corr": correlation test (paired data)
        - "mean_diff": mean difference test (independent samples)
    
    See PermutationConfig for other parameter documentation.
    """
    config = PermutationConfig(
        n_permutations=n_permutations,
        alternative=alternative,
        random_state=random_state,
        nan_policy=nan_policy,
    )
    
    if test == "corr":
        return config.run_corr(x, y)
    elif test == "mean_diff":
        return config.run_mean_diff(x, y)
    else:
        raise ValueError(
            f"permutation_test: test must be 'corr' or 'mean_diff', got '{test}'."
        )


def jackknife(
    x: np.ndarray,
    *,
    method: Literal["mean", "mean_ci"] = "mean_ci",
    conf: float = 0.95,
    nan_policy: Literal["propagate", "omit"] = "propagate",
) -> Tuple[float, ...]:
    """
    Jackknife resampling (convenience wrapper).
    
    Parameters
    ----------
    method : {"mean", "mean_ci"}
        Which jackknife method:
        - "mean": returns (estimate, bias, std_error)
        - "mean_ci": returns (estimate, lower, upper)
    
    See JackknifeConfig for other parameter documentation.
    """
    config = JackknifeConfig(conf=conf, nan_policy=nan_policy)
    
    if method == "mean":
        return config.run_mean(x)
    elif method == "mean_ci":
        return config.run_mean_ci(x)
    else:
        raise ValueError(
            f"jackknife: method must be 'mean' or 'mean_ci', got '{method}'."
        )