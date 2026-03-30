#!/usr/bin/env python3
"""
COPY THIS FILE FROM YOUR TRAINING ENVIRONMENT
After training your model on your machine, use this script to save it correctly.
"""

import os
import pickle
import sys

def copy_and_save_models(
    model,
    feature_names,
    scaler,
    metadata=None,
    models_dir='models'
):
    """
    Copy trained models from your machine and save them correctly.
    
    This function ensures all files are saved with the correct binary pickle format.
    
    Parameters:
    -----------
    model : sklearn/xgboost model object
        Your trained RandomForest, XGBoost, or other sklearn-compatible model
        
    feature_names : list
        List of feature column names (e.g., ['entropy', 'file_size', ...])
        
    scaler : sklearn.preprocessing.StandardScaler
        Your fitted scaler object
        
    metadata : dict (optional)
        Model metadata like accuracy, training date, etc.
        
    models_dir : str
        Where to save the models (default: 'models')
    
    Returns:
    --------
    bool : True if successful, False if error
    
    Example:
    --------
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    
    # Your trained model
    model = RandomForestClassifier()  # Already trained
    scaler = StandardScaler()  # Already fitted
    features = ['feature1', 'feature2', ...]
    
    # Use this function
    copy_and_save_models(
        model=model,
        feature_names=features,
        scaler=scaler,
        metadata={'accuracy': 0.95}
    )
    """
    
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "SAVING TRAINED MODELS" + " " * 27 + "║")
    print("╚" + "=" * 68 + "╝")
    
    os.makedirs(models_dir, exist_ok=True)
    
    try:
        # 1. SAVE MODEL
        print("\n[1/4] Saving ransomware_detection_model.pkl...")
        model_path = os.path.join(models_dir, 'ransomware_detection_model.pkl')
        with open(model_path, 'wb') as f:  # ← CRITICAL: 'wb' = binary
            pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)
        size1 = os.path.getsize(model_path)
        print(f"      ✓ {size1:,} bytes saved")
        
        # 2. SAVE FEATURE NAMES
        print("\n[2/4] Saving feature_names.pkl...")
        features_path = os.path.join(models_dir, 'feature_names.pkl')
        with open(features_path, 'wb') as f:  # ← CRITICAL: 'wb' = binary
            pickle.dump(feature_names, f, protocol=pickle.HIGHEST_PROTOCOL)
        size2 = os.path.getsize(features_path)
        print(f"      ✓ {size2:,} bytes saved ({len(feature_names)} features)")
        
        # 3. SAVE SCALER
        print("\n[3/4] Saving feature_scaler.pkl...")
        scaler_path = os.path.join(models_dir, 'feature_scaler.pkl')
        with open(scaler_path, 'wb') as f:  # ← CRITICAL: 'wb' = binary
            pickle.dump(scaler, f, protocol=pickle.HIGHEST_PROTOCOL)
        size3 = os.path.getsize(scaler_path)
        print(f"      ✓ {size3:,} bytes saved")
        
        # 4. SAVE METADATA
        if metadata is None:
            metadata = {'model_status': 'production'}
        
        print("\n[4/4] Saving model_metadata.pkl...")
        metadata_path = os.path.join(models_dir, 'model_metadata.pkl')
        with open(metadata_path, 'wb') as f:  # ← CRITICAL: 'wb' = binary
            pickle.dump(metadata, f, protocol=pickle.HIGHEST_PROTOCOL)
        size4 = os.path.getsize(metadata_path)
        print(f"      ✓ {size4:,} bytes saved")
        
        # VERIFICATION
        print("\n" + "─" * 70)
        print("VERIFYING SAVED FILES...")
        print("─" * 70)
        
        # Verify 1
        with open(model_path, 'rb') as f:
            _ = pickle.load(f)
        print("✓ Model file verified - loads correctly")
        
        # Verify 2
        with open(features_path, 'rb') as f:
            _ = pickle.load(f)
        print("✓ Features file verified - loads correctly")
        
        # Verify 3
        with open(scaler_path, 'rb') as f:
            _ = pickle.load(f)
        print("✓ Scaler file verified - loads correctly")
        
        # Verify 4
        with open(metadata_path, 'rb') as f:
            _ = pickle.load(f)
        print("✓ Metadata file verified - loads correctly")
        
        print("\n" + "╔" + "=" * 68 + "╗")
        print("║" + " " * 16 + "SUCCESS - ALL FILES SAVED CORRECTLY! ✓" + " " * 15 + "║")
        print("╚" + "=" * 68 + "╝")
        
        print(f"\nSaved location: {os.path.abspath(models_dir)}")
        print(f"\nNext steps:")
        print(f"  1. Transfer the 'models' folder to your Ransomware Pro directory")
        print(f"  2. Run: python diagnose_models.py (to verify)")
        print(f"  3. Run: python app.py")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# EXAMPLE USAGE - PUT THIS IN YOUR TRAINING SCRIPT
# ============================================================================
if __name__ == '__main__':
    print("""
    HOW TO USE THIS FUNCTION:
    ═════════════════════════════════════════════════════════════════════════
    
    In your Jupyter notebook or training script, after training:
    
    from copy_and_save_models import copy_and_save_models
    
    # Your trained model (example)
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    
    # Assume these are already trained:
    # model = RandomForestClassifier().fit(X_train, y_train)
    # scaler = StandardScaler().fit(X_train)
    # feature_names = X_train.columns.tolist()
    
    # Save them correctly:
    success = copy_and_save_models(
        model=model,
        feature_names=feature_names,
        scaler=scaler,
        metadata={
            'accuracy': 0.95,
            'model_type': 'RandomForest',
            'training_date': '2026-01-28'
        }
    )
    
    if success:
        print("Ready to deploy!")
    else:
        print("Something went wrong - check errors above")
    
    ═════════════════════════════════════════════════════════════════════════
    """)
