import os
import pickle
import joblib
import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import warnings

class ModelLoader:
    def __init__(self, models_dir):
        self.models_dir = models_dir
        
        # Random Forest Artifacts
        self.rf_model = None
        self.rf_features = None
        self.rf_scaler = None
        self.rf_metadata = {}
        
        # XGBoost Artifacts
        self.xgb_model = None
        self.xgb_features = None
        self.xgb_scaler = None
        self.xgb_metadata = {}
        
        self.models_loaded_successfully = False
        self.load_models()

    def _load_file(self, file_path, file_name, file_type='pickle'):
        """
        Safely load a file (pickle, joblib, or json) with error reporting.
        """
        if not os.path.exists(file_path):
            print(f"WARNING: {file_name} not found at {file_path}")
            return None

        try:
            if file_type == 'json':
                with open(file_path, 'r') as f:
                    obj = json.load(f)
                print(f"✓ Successfully loaded {file_name} (json)")
                return obj
            
            # Default to pickle/joblib for models/scalers
            try:
                with open(file_path, 'rb') as f:
                    obj = pickle.load(f)
                print(f"✓ Successfully loaded {file_name} (pickle)")
                return obj
            except (pickle.UnpicklingError, EOFError, ValueError):
                print(f"  Pickle failed, trying joblib for {file_name}...")
                obj = joblib.load(file_path)
                print(f"✓ Successfully loaded {file_name} (joblib)")
                return obj
                
        except Exception as e:
            print(f"ERROR: Failed to load {file_name}: {e}")
            return None

    def load_models(self):
        """Loads all model artifacts for RF and XGBoost."""
        print(f"Attempting to load models from {self.models_dir}...")
        
        # --- Load Random Forest ---
        self.rf_model = self._load_file(os.path.join(self.models_dir, 'ransomware_detection_model.pkl'), 'RF Model')
        self.rf_features = self._load_file(os.path.join(self.models_dir, 'feature_names.pkl'), 'RF Features')
        self.rf_scaler = self._load_file(os.path.join(self.models_dir, 'feature_scaler.pkl'), 'RF Scaler')
        self.rf_metadata = self._load_file(os.path.join(self.models_dir, 'model_metadata.pkl'), 'RF Metadata') or {}
        
        # --- Load XGBoost ---
        self.xgb_model = self._load_file(os.path.join(self.models_dir, 'ransomware_detection_model_xgboost.pkl'), 'XGB Model')
        self.xgb_features = self._load_file(os.path.join(self.models_dir, 'feature_names_xgboost.pkl'), 'XGB Features')
        self.xgb_scaler = self._load_file(os.path.join(self.models_dir, 'feature_scaler_xgboost.pkl'), 'XGB Scaler')
        
        # Try JSON first for XGB metadata, fall back to pickle
        xgb_meta_path_json = os.path.join(self.models_dir, 'model_metadata_xgboost.json')
        if os.path.exists(xgb_meta_path_json):
            self.xgb_metadata = self._load_file(xgb_meta_path_json, 'XGB Metadata', 'json') or {}
        else:
            self.xgb_metadata = self._load_file(os.path.join(self.models_dir, 'model_metadata_xgboost.pkl'), 'XGB Metadata') or {}

        # Check success
        if (self.rf_model and self.rf_features) or (self.xgb_model and self.xgb_features):
            self.models_loaded_successfully = True
            print("✓ Models loaded successfully.")
        else:
            print("CRITICAL: No models loaded. Using fallback.")
            self._create_fallback_model()

    def _create_fallback_model(self):
        """Create a basic fallback RF model."""
        self.rf_features = ['test_feature']
        self.rf_model = RandomForestClassifier()
        self.rf_model.fit(np.random.rand(10, 1), [0]*5 + [1]*5)
        self.rf_metadata = {'accuracy': 0.5}
        print("✓ Fallback RF model created.")

    def _predict_single(self, model, scaler, feature_names, features_df, model_name):
        """Helper to run prediction for a single model."""
        if not model or not feature_names:
            return None

        try:
            # Align features
            aligned_df = pd.DataFrame()
            for col in feature_names:
                aligned_df[col] = features_df[col] if col in features_df.columns else 0
            
            # Scale
            X = scaler.transform(aligned_df) if scaler else aligned_df.values
            
            # Predict
            pred = model.predict(X)[0]
            
            # Confidence
            conf = 100.0
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(X)[0]
                conf = max(proba) * 100
            
            classification = "Ransomware" if pred == 1 else "Benign"
            
            # Explicitly cast to native python types to avoid JSON serialization errors with numpy types
            return {
                'algorithm': model_name,
                'prediction': int(pred),
                'label': classification,
                'classification': classification, # Alias for compatibility
                'confidence': float(round(conf, 2))
            }
        except Exception as e:
            print(f"Error predicting with {model_name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def predict_all(self, features_df):
        """
        Returns predictions from all available models.
        Returns a list of result dictionaries.
        """
        results = []
        
        # RF Prediction
        if self.rf_model:
            res = self._predict_single(self.rf_model, self.rf_scaler, self.rf_features, features_df, "Random Forest")
            if res:
                # Add accuracy from metadata
                acc = self.rf_metadata.get('accuracy', self.rf_metadata.get('test_accuracy', 0))
                
                # Convert numpy types to native python if needed
                if hasattr(acc, 'item'):
                    acc = acc.item()
                acc = float(acc)
                
                # Format accuracy as percentage if it's 0-1
                if acc <= 1.0:
                     acc = acc * 100
                     
                res['accuracy'] = float(round(acc, 2))
                results.append(res)
                
        # XGB Prediction
        if self.xgb_model:
            res = self._predict_single(self.xgb_model, self.xgb_scaler, self.xgb_features, features_df, "XGBoost")
            if res:
                acc = self.xgb_metadata.get('accuracy', self.xgb_metadata.get('test_accuracy', 0))
                
                if hasattr(acc, 'item'):
                    acc = acc.item()
                acc = float(acc)
                
                if acc <= 1.0:
                     acc = acc * 100
                     
                res['accuracy'] = float(round(acc, 2))
                results.append(res)
        
        return results

    def predict(self, features_df):
        """Legacy method for backward compatibility - returns best model result."""
        results = self.predict_all(features_df)
        if not results:
            return None, 0.0
            
        # Sort by accuracy to get the "best" one
        def get_acc(r):
            val = r.get('accuracy', 0)
            if isinstance(val, (int, float)): return val
            return 0
            
        best = max(results, key=get_acc)
        return best['prediction'], best['confidence']
