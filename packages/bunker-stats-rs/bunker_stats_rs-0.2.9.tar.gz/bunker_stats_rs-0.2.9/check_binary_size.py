"""
Check the compiled binary details
"""

import os
import bunker_stats_rs as bsr

module_dir = os.path.dirname(bsr.__file__)
pyd_file = os.path.join(module_dir, "bunker_stats_rs.cp310-win_amd64.pyd")

if os.path.exists(pyd_file):
    size = os.path.getsize(pyd_file)
    size_mb = size / (1024 * 1024)
    
    print("=" * 70)
    print("BINARY ANALYSIS")
    print("=" * 70)
    print(f"\nFile: {pyd_file}")
    print(f"Size: {size:,} bytes ({size_mb:.2f} MB)")
    print()
    
    # Analyze size
    if size_mb < 1.0:
        print("⚠️  VERY SMALL - Likely a stub or minimal build")
        print("   Expected: 2-8 MB for release build")
        status = "STUB"
    elif size_mb < 3.0:
        print("✓ REASONABLE SIZE - Likely release build")
        status = "RELEASE_MAYBE"
    elif size_mb < 8.0:
        print("⚡ GOOD SIZE - Typical release build")
        status = "RELEASE_PROBABLE"
    elif size_mb < 20.0:
        print("⚠️  LARGE - Might be debug build")
        print("   Release builds are typically 2-8 MB")
        print("   Debug builds can be 20-100+ MB")
        status = "DEBUG_MAYBE"
    else:
        print("❌ VERY LARGE - Almost certainly debug build!")
        print("   Release: 2-8 MB")
        print("   Debug: 20-100+ MB")
        status = "DEBUG_CERTAIN"
    
    print()
    print("=" * 70)
    print("DIAGNOSIS & NEXT STEPS")
    print("=" * 70)
    print()
    
    if status == "DEBUG_CERTAIN" or status == "DEBUG_MAYBE":
        print("❌ DEBUG BUILD DETECTED")
        print()
        print("FIX:")
        print("1. cd C:\\Users\\adame\\bunker-stats")
        print("2. pip uninstall bunker-stats-rs -y")
        print("3. maturin clean")
        print("4. maturin build --release")
        print("5. pip install target/wheels/bunker_stats_rs-*.whl")
        print()
        print("Or use maturin develop:")
        print("1. pip uninstall bunker-stats-rs -y")
        print("2. maturin clean") 
        print("3. maturin develop --release")
        print()
        
    elif status == "RELEASE_MAYBE" or status == "RELEASE_PROBABLE":
        print("✓ Likely a RELEASE build, but performance is still slow.")
        print()
        print("Possible issues:")
        print("1. Rayon not using all cores")
        print("2. Code not parallelized")
        print("3. Windows threading issues")
        print()
        print("NEXT STEPS:")
        print()
        print("A) Force Rayon to use all cores:")
        print("   $env:RAYON_NUM_THREADS=8")
        print("   python diagnostic_bootstrap.py")
        print()
        print("B) Check Rust source code:")
        print("   - Look at bootstrap.rs")
        print("   - Verify it uses .into_par_iter() not .into_iter()")
        print("   - Check if rayon is in dependencies")
        print()
        print("C) Try rebuilding with explicit parallel flag:")
        print("   maturin clean")
        print("   maturin develop --release")
        print()
        
    else:  # STUB
        print("❌ BINARY TOO SMALL - Likely incomplete installation")
        print()
        print("FIX:")
        print("1. pip uninstall bunker-stats-rs -y")
        print("2. maturin clean")
        print("3. maturin develop --release")
        print()
    
else:
    print(f"❌ File not found: {pyd_file}")
    print("Run: python find_binary.py")
