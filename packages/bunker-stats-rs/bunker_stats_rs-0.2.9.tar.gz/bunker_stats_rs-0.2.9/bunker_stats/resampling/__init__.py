# bunker_stats/resampling/__init__.py
"""
Resampling methods with ergonomic config objects.

This module provides two interfaces:

1. **Config objects** (recommended for complex workflows):
   - BootstrapConfig, BootstrapCorrConfig
   - PermutationConfig
   - JackknifeConfig
   
2. **Convenience functions** (for quick one-liners):
   - bootstrap(), bootstrap_corr()
   - permutation_test()
   - jackknife()

Both interfaces call the same fast Rust kernels. Config objects add:
- Input validation with helpful error messages
- Consistent defaults
- Optional NaN handling (pre-filter in Python)

Examples
--------
Config object approach:
>>> from bunker_stats.resampling import BootstrapConfig
>>> config = BootstrapConfig(n_resamples=5000, conf=0.99, random_state=42)
>>> estimate, lower, upper = config(data)

Functional approach:
>>> from bunker_stats.resampling import bootstrap
>>> estimate, lower, upper = bootstrap(data, n_resamples=5000, conf=0.99, random_state=42)

For backward compatibility, the original flat functions remain available:
>>> import bunker_stats as bsr
>>> bsr.bootstrap_ci(data, stat="mean", n_resamples=1000, conf=0.95)
"""

from .config import (
    # Config dataclasses
    BootstrapConfig,
    BootstrapCorrConfig,
    PermutationConfig,
    JackknifeConfig,
    
    # Convenience functions
    bootstrap,
    bootstrap_corr,
    permutation_test,
    jackknife,
)

__all__ = [
    # Config objects
    "BootstrapConfig",
    "BootstrapCorrConfig",
    "PermutationConfig",
    "JackknifeConfig",
    
    # Convenience functions
    "bootstrap",
    "bootstrap_corr",
    "permutation_test",
    "jackknife",
]
