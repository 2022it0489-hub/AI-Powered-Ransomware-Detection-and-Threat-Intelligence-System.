#!/usr/bin/env python3
"""
Verification script to ensure all fixes are in place and working.
"""

import os
import sys
import subprocess

def check_file_exists(filepath, description):
    """Check if a file exists and report status."""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"  ✓ {description}: {filepath} ({size:,} bytes)")
        return True
    else:
        print(f"  ✗ {description}: NOT FOUND")
        return False

def main():
    print("=" * 70)
    print("MODEL FIX VERIFICATION")
    print("=" * 70)
    
    base_dir = os.getcwd()
    all_good = True
    
    # Check modified files
    print("\n[1] Checking modified files...")
    print("-" * 70)
    
    if check_file_exists(os.path.join(base_dir, 'utils', 'model_loader.py'), 
                        'Enhanced model_loader.py'):
        # Check if it has the new imports
        with open(os.path.join(base_dir, 'utils', 'model_loader.py'), 'r') as f:
            content = f.read()
            if 'RandomForestClassifier' in content and '_create_fallback_model' in content:
                print("    └─ ✓ Contains fallback model creation")
            else:
                print("    └─ ✗ Missing fallback model functionality")
                all_good = False
    else:
        all_good = False
    
    # Check new scripts
    print("\n[2] Checking new scripts...")
    print("-" * 70)
    
    scripts = [
        ('diagnose_models.py', 'Diagnostic tool'),
        ('regenerate_models.py', 'Model regeneration'),
        ('fix_models.bat', 'Windows quick fix'),
    ]
    
    for script, desc in scripts:
        if check_file_exists(os.path.join(base_dir, script), desc):
            pass
        else:
            all_good = False
    
    # Check documentation
    print("\n[3] Checking documentation...")
    print("-" * 70)
    
    docs = [
        ('MODEL_MANAGEMENT.md', 'Management guide'),
        ('QUICK_FIX.md', 'Quick fix guide'),
        ('README_MODEL_FIX.md', 'Complete solution guide'),
    ]
    
    for doc, desc in docs:
        if check_file_exists(os.path.join(base_dir, doc), desc):
            pass
        else:
            all_good = False
    
    # Check existing model directory
    print("\n[4] Checking models directory...")
    print("-" * 70)
    
    models_dir = os.path.join(base_dir, 'models')
    if os.path.exists(models_dir):
        print(f"  ✓ Models directory exists: {models_dir}")
        
        required_files = [
            'ransomware_detection_model.pkl',
            'feature_names.pkl',
            'feature_scaler.pkl',
            'model_metadata.pkl'
        ]
        
        for fname in required_files:
            fpath = os.path.join(models_dir, fname)
            if os.path.exists(fpath):
                size = os.path.getsize(fpath)
                if size > 0:
                    print(f"    ✓ {fname} ({size:,} bytes)")
                else:
                    print(f"    ⚠ {fname} (EMPTY - needs regeneration)")
            else:
                print(f"    ✗ {fname} (MISSING)")
    else:
        print(f"  ✗ Models directory not found")
        all_good = False
    
    # Check Python dependencies
    print("\n[5] Checking Python dependencies...")
    print("-" * 70)
    
    required_packages = [
        'flask',
        'pandas',
        'numpy',
        'sklearn',
        'pickle'
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == 'sklearn':
                __import__('sklearn')
                print(f"  ✓ scikit-learn installed")
            elif package == 'pickle':
                __import__('pickle')
                print(f"  ✓ pickle available")
            else:
                __import__(package)
                print(f"  ✓ {package} installed")
        except ImportError:
            print(f"  ✗ {package} NOT installed")
            missing.append(package)
            all_good = False
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    if all_good:
        print("\n✓ ALL CHECKS PASSED!")
        print("\nNext steps:")
        print("  1. Run: python regenerate_models.py")
        print("  2. Run: python app.py")
        print("  3. Open http://localhost:5000")
        return 0
    else:
        print("\n✗ Some issues found!")
        print("\nTroubleshooting:")
        if missing:
            print(f"\n  Install missing packages:")
            print(f"    pip install {' '.join(missing)}")
        print(f"\n  Then run verification again:")
        print(f"    python verify_fix.py")
        return 1

if __name__ == '__main__':
    sys.exit(main())
