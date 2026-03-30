#!/usr/bin/env python3
"""
CORRECT MODEL SAVING SCRIPT
Use this to properly save your trained models!

This ensures all pickle files are saved with the correct binary protocol.
"""

import pickle
import os
import sys

def save_model_files(model, feature_names, scaler, metadata=None, models_dir='models'):
    """
    Save trained model and components with correct pickle protocol.
    
    Args:
        model: Trained ML model (sklearn/xgboost)
        feature_names: List of feature column names
        scaler: Fitted StandardScaler or similar
        metadata: Dict with model metadata (optional)
        models_dir: Directory to save models
    """
    
    print("=" * 70)
    print("SAVING MODEL FILES - CORRECT METHOD")
    print("=" * 70)
    
    # Create directory if needed
    os.makedirs(models_dir, exist_ok=True)
    print(f"\nModels directory: {models_dir}")
    
    try:
        # 1. Save the main model
        print("\n[1] Saving ransomware_detection_model.pkl...")
        model_path = os.path.join(models_dir, 'ransomware_detection_model.pkl')
        with open(model_path, 'wb') as f:  # IMPORTANT: 'wb' = write BINARY
            pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)
        size = os.path.getsize(model_path)
        print(f"    ✓ Saved: {size:,} bytes")
        print(f"    Protocol: {pickle.HIGHEST_PROTOCOL} (binary)")
        
        # 2. Save feature names
        print("\n[2] Saving feature_names.pkl...")
        features_path = os.path.join(models_dir, 'feature_names.pkl')
        with open(features_path, 'wb') as f:  # IMPORTANT: 'wb' = write BINARY
            pickle.dump(feature_names, f, protocol=pickle.HIGHEST_PROTOCOL)
        size = os.path.getsize(features_path)
        print(f"    ✓ Saved: {size:,} bytes")
        print(f"    Features: {len(feature_names)} total")
        
        # 3. Save scaler
        print("\n[3] Saving feature_scaler.pkl...")
        scaler_path = os.path.join(models_dir, 'feature_scaler.pkl')
        with open(scaler_path, 'wb') as f:  # IMPORTANT: 'wb' = write BINARY
            pickle.dump(scaler, f, protocol=pickle.HIGHEST_PROTOCOL)
        size = os.path.getsize(scaler_path)
        print(f"    ✓ Saved: {size:,} bytes")
        print(f"    Type: {type(scaler).__name__}")
        
        # 4. Save metadata
        if metadata is None:
            metadata = {'model_status': 'production'}
        
        print("\n[4] Saving model_metadata.pkl...")
        metadata_path = os.path.join(models_dir, 'model_metadata.pkl')
        with open(metadata_path, 'wb') as f:  # IMPORTANT: 'wb' = write BINARY
            pickle.dump(metadata, f, protocol=pickle.HIGHEST_PROTOCOL)
        size = os.path.getsize(metadata_path)
        print(f"    ✓ Saved: {size:,} bytes")
        
        print("\n" + "=" * 70)
        print("SUCCESS: All model files saved correctly!")
        print("=" * 70)
        print("\nVerify files with:")
        print("  python diagnose_models.py")
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to save models: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# USAGE EXAMPLE - Copy and adapt to your training code
# ============================================================================
if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║  HOW TO USE THIS SCRIPT                                              ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
    Option 1: From your training script
    ────────────────────────────────────
    
    # After training your model:
    from save_models_correct import save_model_files
    
    # Your training code...
    model = RandomForestClassifier().fit(X_train, y_train)
    scaler = StandardScaler().fit(X_train)
    feature_names = X_train.columns.tolist()
    
    # Save with this function:
    save_model_files(
        model=model,
        feature_names=feature_names,
        scaler=scaler,
        metadata={'accuracy': 0.95, 'model_type': 'RandomForest'},
        models_dir='models'
    )
    
    ────────────────────────────────────
    Option 2: Standalone verification
    ────────────────────────────────────
    
    # Just run:
    python save_models_correct.py
    
    This will show you the correct way to save your models.
    """)
