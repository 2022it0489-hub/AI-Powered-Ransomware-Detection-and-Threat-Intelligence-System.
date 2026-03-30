#!/usr/bin/env python3
"""
Script to regenerate valid model files when corruption is detected.
This creates fallback models that allow the app to run in demo mode.
"""

import os
import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

def regenerate_model_files(models_dir):
    """Create valid fallback model files."""
    
    print("=" * 70)
    print("REGENERATING MODEL FILES")
    print("=" * 70)
    
    # Create models directory if it doesn't exist
    os.makedirs(models_dir, exist_ok=True)
    
    try:
        # 1. Create feature names
        print("\n[1] Creating feature names...")
        feature_names = [
            'entropy', 'file_size', 'has_suspicious_extensions',
            'execution_attempts', 'registry_modifications',
            'network_connections', 'file_creation_rate',
            'pe_header_valid', 'digital_signature_valid',
            'suspicious_api_calls'
        ]
        
        features_path = os.path.join(models_dir, 'feature_names.pkl')
        with open(features_path, 'wb') as f:
            pickle.dump(feature_names, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"    ✓ Created {features_path}")
        print(f"      Features: {', '.join(feature_names[:3])}... ({len(feature_names)} total)")
        
        # 2. Create and train scaler
        print("\n[2] Creating feature scaler...")
        scaler = StandardScaler()
        
        # Create dummy training data
        dummy_training_data = np.random.randn(200, len(feature_names))
        scaler.fit(dummy_training_data)
        
        scaler_path = os.path.join(models_dir, 'feature_scaler.pkl')
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"    ✓ Created {scaler_path}")
        print(f"      Fitted on {len(dummy_training_data)} training samples")
        
        # 3. Create and train model
        print("\n[3] Creating Random Forest model...")
        model = RandomForestClassifier(
            n_estimators=50,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        # Create dummy training data
        X_train = np.random.randn(500, len(feature_names))
        y_train = np.random.randint(0, 2, 500)
        
        model.fit(X_train, y_train)
        
        model_path = os.path.join(models_dir, 'ransomware_detection_model.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"    ✓ Created {model_path}")
        print(f"      Trained on {len(X_train)} samples")
        print(f"      Model accuracy on training data: {model.score(X_train, y_train):.2%}")
        
        # 4. Create metadata
        print("\n[4] Creating metadata...")
        metadata = {
            'model_type': 'RandomForestClassifier',
            'num_features': len(feature_names),
            'training_samples': 500,
            'model_status': 'FALLBACK_DEMO_MODEL',
            'note': 'This is a fallback model created to allow the app to run. '
                    'For production use, please retrain with real ransomware datasets.'
        }
        
        metadata_path = os.path.join(models_dir, 'model_metadata.pkl')
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"    ✓ Created {metadata_path}")
        print(f"      Status: {metadata['model_status']}")
        
        print("\n" + "=" * 70)
        print("SUCCESS: All model files regenerated!")
        print("=" * 70)
        print("\nThe app will now work with fallback models.")
        print("For production use, please:")
        print("  1. Collect real ransomware/clean file datasets")
        print("  2. Extract actual features using feature_extractor.py")
        print("  3. Train a production model")
        print("  4. Save models using pickle with protocol=HIGHEST_PROTOCOL")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to regenerate models: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    models_dir = os.path.join(os.getcwd(), 'models')
    success = regenerate_model_files(models_dir)
    exit(0 if success else 1)
