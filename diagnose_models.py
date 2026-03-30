#!/usr/bin/env python3
"""
Diagnostic script to check and repair corrupted model files.
Run this to diagnose issues with your model pickle files.
"""

import os
import pickle
import sys

def diagnose_model_files(models_dir):
    """Diagnose the status of all model files."""
    
    print("=" * 70)
    print("MODEL FILES DIAGNOSTIC TOOL")
    print("=" * 70)
    
    files_to_check = {
        'ransomware_detection_model.pkl': 'Main ML Model',
        'feature_names.pkl': 'Feature Names',
        'feature_scaler.pkl': 'Feature Scaler',
        'model_metadata.pkl': 'Model Metadata'
    }
    
    results = {}
    
    for filename, description in files_to_check.items():
        filepath = os.path.join(models_dir, filename)
        print(f"\n[Checking] {description}: {filename}")
        print("-" * 70)
        
        if not os.path.exists(filepath):
            print(f"  ✗ FILE NOT FOUND: {filepath}")
            results[filename] = 'NOT_FOUND'
            continue
        
        file_size = os.path.getsize(filepath)
        print(f"  File size: {file_size} bytes")
        
        try:
            with open(filepath, 'rb') as f:
                # Try to read first few bytes to check file format
                header = f.read(10)
                f.seek(0)
                
                # Check if it looks like a pickle file
                if header.startswith(b'\x80\x03'):  # Protocol 3
                    print(f"  File format: Pickle Protocol 3 ✓")
                elif header.startswith(b'\x80\x04'):  # Protocol 4
                    print(f"  File format: Pickle Protocol 4 ✓")
                elif header.startswith(b'\x80\x02'):  # Protocol 2
                    print(f"  File format: Pickle Protocol 2 ✓")
                else:
                    print(f"  ⚠ WARNING: File doesn't appear to be a valid pickle (header: {header[:4]})")
                
                # Try to load the pickle
                try:
                    obj = pickle.load(f)
                    print(f"  ✓ Successfully loaded!")
                    print(f"  Object type: {type(obj).__name__}")
                    results[filename] = 'OK'
                except pickle.UnpicklingError as e:
                    print(f"  ✗ Unpickling Error: {e}")
                    results[filename] = 'CORRUPTED'
                except EOFError:
                    print(f"  ✗ EOF Error: File appears to be truncated/incomplete")
                    results[filename] = 'TRUNCATED'
                
        except Exception as e:
            print(f"  ✗ Error: {type(e).__name__}: {e}")
            results[filename] = 'ERROR'
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for filename, status in results.items():
        symbol = "✓" if status == "OK" else "✗"
        print(f"{symbol} {filename}: {status}")
    
    # Recommendations
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    if all(v == 'OK' for v in results.values()):
        print("✓ All model files are healthy! No action needed.")
    else:
        print("Model files have issues. Here's what you can do:")
        print("\n1. DELETE CORRUPTED FILES:")
        for filename, status in results.items():
            if status != 'OK':
                filepath = os.path.join(models_dir, filename)
                print(f"   rm \"{filepath}\"")
        print("\n2. RESTART THE APPLICATION")
        print("   The app will automatically create fallback models.")
        print("   Then retrain or restore your original model files.")
        print("\n3. RETRAIN YOUR MODEL")
        print("   Create a new training script to generate valid model files.")

if __name__ == '__main__':
    models_dir = os.path.join(os.getcwd(), 'models')
    
    if not os.path.exists(models_dir):
        print(f"ERROR: Models directory not found: {models_dir}")
        sys.exit(1)
    
    diagnose_model_files(models_dir)
