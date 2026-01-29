"""
Find exactly which .pyd file Python is loading
"""
import sys
import os
from pathlib import Path

print("=" * 70)
print("BUNKER-STATS MODULE LOADING DIAGNOSTIC")
print("=" * 70)

# Check Python environment
print(f"\n1. Python Executable: {sys.executable}")
print(f"   Environment: {'(base conda)' if 'conda' in sys.executable.lower() else 'venv'}")

# Check bunker_stats package location
try:
    import bunker_stats
    print(f"\n2. bunker_stats package:")
    print(f"   Location: {bunker_stats.__file__}")
    print(f"   Type: {'Source directory' if 'bunker-stats' in bunker_stats.__file__ else 'Installed package'}")
except ImportError as e:
    print(f"\n2. ❌ Cannot import bunker_stats: {e}")
    sys.exit(1)

# Check bunker_stats_rs extension
try:
    import bunker_stats_rs
    print(f"\n3. bunker_stats_rs extension (.pyd):")
    print(f"   Location: {bunker_stats_rs.__file__}")
    
    # Check file timestamp
    pyd_path = bunker_stats_rs.__file__
    if os.path.exists(pyd_path):
        from datetime import datetime
        mtime = os.path.getmtime(pyd_path)
        mod_time = datetime.fromtimestamp(mtime)
        print(f"   Modified: {mod_time}")
    
except ImportError as e:
    print(f"\n3. ❌ Cannot import bunker_stats_rs: {e}")
    sys.exit(1)

# Find ALL .pyd files in project
print(f"\n4. All bunker_stats .pyd files found:")
project_root = Path("C:/Users/adame/bunker-stats")
pyd_files = list(project_root.rglob("bunker_stats_rs*.pyd"))

if pyd_files:
    for pyd in sorted(pyd_files, key=lambda p: os.path.getmtime(p), reverse=True):
        mtime = os.path.getmtime(pyd)
        mod_time = datetime.fromtimestamp(mtime)
        loaded = " ← LOADED" if str(pyd) == bunker_stats_rs.__file__ else ""
        print(f"   {pyd}")
        print(f"   Modified: {mod_time}{loaded}")
else:
    print("   No .pyd files found!")

# Test KPSS
print(f"\n5. Testing KPSS function:")
import numpy as np
np.random.seed(42)
x = np.random.randn(200) * 0.5
stat, _ = bunker_stats.kpss_test(x, 'c')
print(f"   KPSS statistic: {stat:.6f}")

if 0.175 < stat < 0.185:
    print(f"   ✅ CORRECT formula (new bandwidth)")
elif 0.190 < stat < 0.200:
    print(f"   ❌ WRONG formula (old bandwidth)")
    print(f"\n📋 PROBLEM: The loaded .pyd file has the OLD code!")
    print(f"   Loaded from: {bunker_stats_rs.__file__}")
    print(f"\n   SOLUTION: Delete this file and rebuild:")
    print(f"   Remove-Item -Force '{bunker_stats_rs.__file__}'")
    print(f"   maturin develop --release --features parallel")
else:
    print(f"   ⚠️  Unexpected value")

print("\n" + "=" * 70)
