# Model Management Guide

## Problem: CRITICAL ERROR loading models: invalid load key, '\x09'

This error occurs when one or more pickle files in the `models/` directory are corrupted or in an unexpected format.

## Solutions

### Quick Fix (Recommended)

Run the regenerate script to create valid fallback models:

```bash
python regenerate_models.py
```

This will:
1. Create all required pickle files with valid format
2. Generate a demo Random Forest model that allows the app to run
3. Print the results and status

Then restart your Flask app:
```bash
python app.py
```

### Diagnostic Check

If you want to check which files are corrupted:

```bash
python diagnose_models.py
```

This will show you:
- File sizes
- File format validation
- Specific error messages for each corrupted file

### Manual Fix

If you want to manually remove corrupted files:

1. Delete the corrupted model files:
```bash
rm models/ransomware_detection_model.pkl
rm models/feature_names.pkl
rm models/feature_scaler.pkl
rm models/model_metadata.pkl
```

2. Run regenerate_models.py
3. Restart the Flask app

## For Production Use

The fallback models are NOT suitable for production. For real deployment:

1. **Collect Data**: Gather real ransomware and clean file samples
2. **Extract Features**: Use `utils/feature_extractor.py` on your dataset
3. **Train Model**: Create a training script using sklearn, XGBoost, etc.
4. **Save Properly**: Always save models using:
   ```python
   pickle.dump(model, open('path.pkl', 'wb'), protocol=pickle.HIGHEST_PROTOCOL)
   ```

## Model File Requirements

All pickle files must be saved with binary protocol using `protocol=pickle.HIGHEST_PROTOCOL`:

```python
import pickle

# Correct way to save
with open('model.pkl', 'wb') as f:
    pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)

# Load
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)
```

## What Each File Does

| File | Purpose | Type |
|------|---------|------|
| `ransomware_detection_model.pkl` | Trained ML classifier (RandomForest/XGBoost) | Scikit-learn model |
| `feature_names.pkl` | List of feature column names | List of strings |
| `feature_scaler.pkl` | StandardScaler for normalizing features | Scikit-learn scaler |
| `model_metadata.pkl` | Info about the model (type, status, etc) | Dictionary |

## Troubleshooting

### Still getting "Model is not loaded" errors?

1. Ensure Flask app started without errors
2. Check app.py for any exception handling
3. Look at the console output when the app starts - it will show which models loaded
4. Run `diagnose_models.py` to check file integrity

### The fallback model doesn't seem accurate?

That's expected! The fallback model is trained on random data. For accurate predictions:
- Regenerate from real ransomware samples
- Use the production training approach above

### How do I know when models are properly loaded?

When the app starts, you should see:
```
✓ Successfully loaded feature_names.pkl
✓ Successfully loaded feature_scaler.pkl  
✓ Successfully loaded ransomware_detection_model.pkl
✓ All critical models loaded successfully!
```

If you see this, the models are loaded and the app is ready!
