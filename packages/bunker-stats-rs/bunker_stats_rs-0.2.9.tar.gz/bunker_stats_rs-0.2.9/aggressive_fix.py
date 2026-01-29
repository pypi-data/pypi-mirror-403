"""
AGGRESSIVE FIX: Delete all old .pyd files and rebuild
This handles the multiple venv issue
"""
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

def run_cmd(cmd, description):
    """Run a PowerShell command"""
    print(f"\n🔧 {description}")
    print(f"   $ {cmd}\n")
    result = subprocess.run(
        f'powershell.exe -Command "{cmd}"',
        capture_output=True,
        text=True,
        shell=True
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(f"   Error: {result.stderr}")
    return result.returncode == 0

def main():
    print("=" * 70)
    print("AGGRESSIVE KPSS FIX - Handles Multiple Venvs")
    print("=" * 70)
    
    project_root = Path("C:/Users/adame/bunker-stats")
    
    # Find all bunker_stats .pyd files
    print("\n1. Finding all bunker_stats .pyd files...")
    pyd_files = list(project_root.rglob("bunker_stats_rs*.pyd"))
    
    if not pyd_files:
        print("   No .pyd files found!")
    else:
        print(f"   Found {len(pyd_files)} .pyd file(s):")
        for pyd in pyd_files:
            mtime = os.path.getmtime(pyd)
            mod_time = datetime.fromtimestamp(mtime)
            print(f"   - {pyd}")
            print(f"     Modified: {mod_time}")
    
    # Delete ALL .pyd files
    if pyd_files:
        print(f"\n2. Deleting ALL bunker_stats .pyd files...")
        for pyd in pyd_files:
            try:
                pyd.unlink()
                print(f"   ✅ Deleted: {pyd}")
            except Exception as e:
                print(f"   ❌ Could not delete {pyd}: {e}")
    
    # Clean build artifacts
    print(f"\n3. Cleaning build artifacts...")
    os.chdir(project_root)
    
    run_cmd("cargo clean", "Running cargo clean")
    
    # Delete target directory
    target_dir = project_root / "target"
    if target_dir.exists():
        print(f"\n4. Removing target directory...")
        run_cmd(f"Remove-Item -Recurse -Force '{target_dir}'", "Deleting target/")
    
    # Rebuild
    print(f"\n5. Rebuilding with maturin...")
    success = run_cmd(
        "maturin develop --release --features parallel",
        "Building bunker-stats"
    )
    
    if not success:
        print("\n❌ Build failed!")
        return False
    
    # Verify the new .pyd was created
    print(f"\n6. Verifying new .pyd was created...")
    new_pyd_files = list(project_root.rglob("bunker_stats_rs*.pyd"))
    
    if not new_pyd_files:
        print("   ❌ No .pyd file created!")
        return False
    
    print(f"   ✅ Found {len(new_pyd_files)} new .pyd file(s):")
    for pyd in new_pyd_files:
        mtime = os.path.getmtime(pyd)
        mod_time = datetime.fromtimestamp(mtime)
        print(f"   - {pyd}")
        print(f"     Created: {mod_time}")
    
    # Test it
    print(f"\n7. Testing KPSS implementation...")
    test_code = """
import numpy as np
import bunker_stats as bs
import bunker_stats_rs

print(f'Loaded .pyd from: {bunker_stats_rs.__file__}')

np.random.seed(42)
x = np.random.randn(200) * 0.5
stat, _ = bs.kpss_test(x, 'c')

print(f'KPSS statistic: {stat:.6f}')

if 0.175 < stat < 0.185:
    print('✅ CORRECT: Using new formula!')
    exit(0)
elif 0.190 < stat < 0.200:
    print('❌ WRONG: Still using old formula!')
    print('The .pyd file still has old code compiled in.')
    exit(1)
else:
    print(f'⚠️  Unexpected value: {stat:.6f}')
    exit(2)
"""
    
    with open("_test.py", "w") as f:
        f.write(test_code)
    
    result = subprocess.run(
        "python _test.py",
        shell=True,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    os.remove("_test.py")
    
    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("✅ SUCCESS! KPSS fix is working!")
        print("=" * 70)
        print("\nYou can now run your pytest:")
        print("pytest tests/test_tsa_comprehensive.py::TestStationarity::test_kpss_stationary -vv")
        return True
    else:
        print("\n" + "=" * 70)
        print("❌ TEST FAILED - Old code still running")
        print("=" * 70)
        print("\nThe .pyd file was rebuilt but still has old code.")
        print("This means the SOURCE FILE doesn't have the fix!")
        print("\nVerify line 251 in src/kernels/tsa/stationarity.rs:")
        print("Get-Content src\\kernels\\tsa\\stationarity.rs | Select-Object -Skip 249 -First 3")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
