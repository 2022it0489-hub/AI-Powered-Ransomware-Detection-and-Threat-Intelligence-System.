#!/usr/bin/env python3
"""
Test script to verify which model files load correctly
"""

import os
import pickle
import joblib

models_dir = 'models'

print("=" * 70)
print("TESTING UPLOADED MODEL FILES")
print("=" * 70)

files = [
    'ransomware_detection_model.pkl',
    'ransomware_detection_model_pickle.pkl',
    'feature_scaler.pkl',
    'feature_scaler_pickle.pkl',
    'feature_names.pkl',
    'model_metadata.pkl'
]

results = {}

for filename in files:
    filepath = os.path.join(models_dir, filename)
    
    if not os.path.exists(filepath):
        print(f"\n✗ {filename}: NOT FOUND")
        continue
    
    size = os.path.getsize(filepath)
    print(f"\n{filename}")
    print(f"  Size: {size:,} bytes")
    
    if size < 100:
        print(f"  ✗ File is empty or too small")
        results[filename] = "EMPTY"
        continue
    
    # Try pickle
    try:
        with open(filepath, 'rb') as f:
            obj = pickle.load(f)
        print(f"  ✓ Pickle: OK - Type: {type(obj).__name__}")
        results[filename] = f"PICKLE_OK ({type(obj).__name__})"
    except Exception as e:
        print(f"  ✗ Pickle: {type(e).__name__}")
        
        # Try joblib
        try:
            obj = joblib.load(filepath)
            print(f"  ✓ Joblib: OK - Type: {type(obj).__name__}")
            results[filename] = f"JOBLIB_OK ({type(obj).__name__})"
        except Exception as e2:
            print(f"  ✗ Joblib: {type(e2).__name__}")
            results[filename] = "CORRUPTED"

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

working_files = {k: v for k, v in results.items() if 'OK' in v}
broken_files = {k: v for k, v in results.items() if 'CORRUPTED' in v}

print("\n✓ WORKING FILES:")
for f, status in working_files.items():
    print(f"  {f}: {status}")

if broken_files:
    print("\n✗ BROKEN FILES:")
    for f, status in broken_files.items():
        print(f"  {f}: {status}")

print("\n" + "=" * 70)
print("RECOMMENDATION")
print("=" * 70)

# Check what we need
print("\nFiles needed for app:")
print("  1. ransomware_detection_model.pkl or ransomware_detection_model_pickle.pkl")
print("  2. feature_scaler.pkl or feature_scaler_pickle.pkl")
print("  3. feature_names.pkl")
print("  4. model_metadata.pkl (optional)")

# Check if critical files work
model_ok = any('ransomware_detection_model' in k and 'OK' in v for k, v in working_files.items())
scaler_ok = any('feature_scaler' in k and 'OK' in v for k, v in working_files.items())
features_ok = 'feature_names.pkl' in working_files

print(f"\nModel file working: {'✓ YES' if model_ok else '✗ NO'}")
print(f"Scaler file working: {'✓ YES' if scaler_ok else '✗ NO'}")
print(f"Features file working: {'✓ YES' if features_ok else '✗ NO'}")

if model_ok and scaler_ok and features_ok:
    print("\n✓ All critical files are working!")
    print("  Run: python app.py")
else:
    print("\n✗ Some files are corrupted")
    print("  Follow: MODEL_CORRUPTION_FIX.md for solutions")
