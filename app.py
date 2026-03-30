from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
import os
import zipfile
import shutil
import pandas as pd
from utils.model_loader import ModelLoader
from utils.feature_extractor import FeatureExtractor
from utils.alert_system import AlertSystem
from utils.logging_utils import log_threat, get_recent_logs
from utils.chatbot import CybersecurityChatbot
from utils.file_watcher import FolderMonitor
import threading
from pathlib import Path
import tempfile
import config

app = Flask(__name__)
app.secret_key = "academic_project_secret"
socketio = SocketIO(app, cors_allowed_origins="*")

# -- Configuration --
MODELS_DIR = os.path.join(os.getcwd(), 'models')
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Supported PE file extensions
SUPPORTED_EXTENSIONS = ('.exe', '.dll', '.sys', '.ocx', '.drv', '.scr')

# -- Initialize Modules --
try:
    model_loader = ModelLoader(MODELS_DIR)
    print("✓ Model loaded successfully")
except Exception as e:
    print(f"⨯ Server Start Error: {e}")
    model_loader = None

feature_extractor = FeatureExtractor()

# Initialize Alert System with email configuration
if config.EMAIL_ALERTS_ENABLED:
    alert_system = AlertSystem(
        smtp_server=config.SMTP_SERVER,
        smtp_port=config.SMTP_PORT,
        email_user=config.EMAIL_USER,
        email_pass=config.EMAIL_PASSWORD
    )
    print("✓ Alert System initialized with email support")
else:
    alert_system = AlertSystem()
    print("✓ Alert System initialized (email disabled)")

chatbot = CybersecurityChatbot()

# Initialize Folder Monitor for real-time scanning
folder_monitor = FolderMonitor()
print("✓ Folder Monitor initialized")

# -- Helper Functions --

def normalize_path(raw_path):
    """
    Robust path normalization for Windows and Unix systems.
    Handles quotes, backslashes, and various path formats.
    """
    if not raw_path:
        return None
    
    # Remove surrounding quotes (single, double, or mixed)
    path = raw_path.strip()
    
    # Handle different quote combinations
    if (path.startswith('"') and path.endswith('"')) or \
       (path.startswith("'") and path.endswith("'")):
        path = path[1:-1]
    
    # Remove any remaining quotes
    path = path.replace('"', '').replace("'", '')
    
    # Normalize path separators (convert to OS-appropriate format)
    path = os.path.normpath(path)
    
    # Convert to absolute path if relative
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    
    return path


def is_pe_file(filepath):
    """Check if file has a PE executable extension."""
    return filepath.lower().endswith(SUPPORTED_EXTENSIONS)


def validate_path(path):
    """
    Validate that a path exists and is accessible.
    Returns (is_valid, error_message, normalized_path)
    """
    if not path:
        return False, "Path cannot be empty", None
    
    normalized = normalize_path(path)
    
    if not normalized:
        return False, "Invalid path format", None
    
    # Check if path exists
    if not os.path.exists(normalized):
        return False, f"Path does not exist: {normalized}", None
    
    # Check if path is accessible
    try:
        # Test read access
        if os.path.isfile(normalized):
            with open(normalized, 'rb') as f:
                f.read(1)
        elif os.path.isdir(normalized):
            os.listdir(normalized)
    except PermissionError:
        return False, f"Permission denied: {normalized}", None
    except Exception as e:
        return False, f"Cannot access path: {str(e)}", None
    
    return True, None, normalized


# -- Routes --

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard/scanner')
def dashboard_scanner():
    recent_logs = get_recent_logs(10)
    return render_template('dashboard_scanner.html', logs=recent_logs)


@app.route('/dashboard/csv')
def dashboard_csv():
    return render_template('dashboard_csv.html')


@app.route('/dashboard/chat')
def dashboard_chat():
    return render_template('dashboard_chat.html')


# -- API Endpoints --

@app.route('/api/scan_path', methods=['POST'])
def scan_path():
    """
    Scans a single file, directory, or ZIP file recursively.
    Input: {'path': 'C:/...'}
    Output: {'status': 'success', 'results': [...]}
    """
    try:
        data = request.json
        raw_path = data.get('path', '')
        
        print(f"[SCAN REQUEST] Raw path received: {raw_path}")
        
        # Validate and normalize path
        is_valid, error_msg, target_path = validate_path(raw_path)
        
        if not is_valid:
            print(f"[SCAN ERROR] Path validation failed: {error_msg}")
            return jsonify({
                'status': 'error',
                'message': error_msg
            })
        
        print(f"[SCAN START] Normalized path: {target_path}")
        
        # Initialize results
        results = []
        scan_type = None
        
        # Determine scan type
        if os.path.isfile(target_path):
            if zipfile.is_zipfile(target_path):
                scan_type = "ZIP"
                print(f"[SCAN TYPE] ZIP file detected")
                results = scan_zip_file(target_path)
            elif is_pe_file(target_path):
                scan_type = "SINGLE_FILE"
                print(f"[SCAN TYPE] Single PE file detected")
                result = scan_single_file(target_path)
                if result:
                    results.append(result)
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Unsupported file type. Expected: {", ".join(SUPPORTED_EXTENSIONS)} or ZIP'
                })
        
        elif os.path.isdir(target_path):
            scan_type = "DIRECTORY"
            print(f"[SCAN TYPE] Directory detected")
            results = scan_directory(target_path)
        
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid path type'
            })
        
        # Prepare summary
        ransomware_count = sum(1 for r in results if r.get('classification') == 'Ransomware')
        benign_count = sum(1 for r in results if r.get('classification') == 'Benign')
        error_count = sum(1 for r in results if r.get('status') == 'error')
        
        print(f"[SCAN COMPLETE] Total: {len(results)}, Ransomware: {ransomware_count}, Benign: {benign_count}, Errors: {error_count}")
        
        return jsonify({
            'status': 'success',
            'scan_type': scan_type,
            'summary': {
                'total_scanned': len(results),
                'ransomware': ransomware_count,
                'benign': benign_count,
                'errors': error_count
            },
            'results': results
        })
    
    except Exception as e:
        print(f"[SCAN ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Scan failed: {str(e)}'
        })


def scan_single_file(filepath):
    """
    Scan a single PE file and return results using ALL available models.
    """
    try:
        print(f"  [SCANNING] {filepath}")
        
        # 1. Extract features
        features_dict = feature_extractor.extract_features(filepath)
        
        if 'error' in features_dict:
            print(f"  [ERROR] Feature extraction failed: {features_dict['error']}")
            return {
                'file': os.path.basename(filepath),
                'full_path': filepath,
                'status': 'error',
                'message': features_dict['error']
            }
        
        # 2. Predict with ALL models
        features_df = pd.DataFrame([features_dict])
        model_results = model_loader.predict_all(features_df)
        
        if not model_results:
             return {
                'file': os.path.basename(filepath),
                'full_path': filepath,
                'status': 'error',
                'message': "No models available for prediction"
            }

        # 3. Determine selected model (by highest confidence)
        def get_conf(r):
            val = r.get('confidence', 0)
            if isinstance(val, (int, float)): return val
            return 0

        selected_model = max(model_results, key=get_conf)

        # Mark selected flag on each model comparison row
        for m in model_results:
            m['selected'] = (m.get('algorithm') == selected_model.get('algorithm'))

        # Use the model with highest confidence as the final prediction
        final_result = selected_model

        # 4. Construct Final Result Object
        result = {
            'file': os.path.basename(filepath),
            'full_path': filepath,
            'md5': features_dict.get('MD5', 'N/A'),
            'timestamp': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'success',

            # Primary Classification (Based on highest confidence model)
            'classification': final_result['label'],
            'confidence': final_result.get('confidence', 0),
            'best_model': selected_model['algorithm'],  # "Selected" model (by confidence)
            'rf_selected': (selected_model.get('algorithm') == 'Random Forest'),

            # Detailed Breakdown for Table (each model contains algorithm, accuracy, confidence, selected)
            'model_comparisons': model_results
        }
        
        # 5. Alert & Log if malicious (based on the final prediction which is from Random Forest)
        if final_result.get('prediction') == 1:
            log_threat(filepath, result['md5'], final_result.get('confidence', 0), "Ransomware")
            # Send email alert if configured
            email_recipient = config.ALERT_RECIPIENT if config.EMAIL_ALERTS_ENABLED else None
            alert_system.trigger_alert(filepath, "Ransomware", final_result.get('confidence', 0), email_recipient)
            print(f"  [THREAT DETECTED] {filepath} - {final_result.get('algorithm')} Confidence: {final_result.get('confidence'):.2%}")
        else:
            print(f"  [BENIGN] {filepath}")
        
        return result
    
    except Exception as e:
        print(f"  [ERROR] Failed to scan {filepath}: {str(e)}")
        # import traceback
        # traceback.print_exc()
        return {
            'file': os.path.basename(filepath),
            'full_path': filepath,
            'status': 'error',
            'message': str(e)
        }


def scan_directory(dir_path, max_files=100):
    """
    Recursively scan a directory for PE files.
    """
    results = []
    scanned_count = 0
    
    print(f"  [DIRECTORY SCAN] Starting scan of: {dir_path}")
    
    try:
        for root, dirs, files in os.walk(dir_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if scanned_count >= max_files:
                    print(f"  [LIMIT REACHED] Maximum {max_files} files scanned")
                    break
                
                full_path = os.path.join(root, file)
                
                # Only scan PE files
                if is_pe_file(full_path):
                    result = scan_single_file(full_path)
                    if result:
                        results.append(result)
                        scanned_count += 1
            
            if scanned_count >= max_files:
                break
        
        print(f"  [DIRECTORY SCAN] Completed: {scanned_count} PE files scanned")
    
    except Exception as e:
        print(f"  [DIRECTORY SCAN ERROR] {str(e)}")
    
    return results


def scan_zip_file(zip_path):
    """
    Extract and scan PE files from a ZIP archive.
    """
    results = []
    temp_dir = None
    
    try:
        print(f"  [ZIP SCAN] Processing: {zip_path}")
        
        # Create temporary extraction directory
        temp_dir = tempfile.mkdtemp(prefix="ransomware_scan_", dir=UPLOAD_FOLDER)
        print(f"  [ZIP SCAN] Extracting to: {temp_dir}")
        
        # Extract ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get list of files in ZIP
            file_list = zip_ref.namelist()
            print(f"  [ZIP SCAN] Found {len(file_list)} files in archive")
            
            # Extract all files
            zip_ref.extractall(temp_dir)
            print(f"  [ZIP SCAN] Extraction complete")
        
        # Scan the extracted directory
        results = scan_directory(temp_dir, max_files=100)
        
        print(f"  [ZIP SCAN] Scan complete: {len(results)} PE files processed")
    
    except zipfile.BadZipFile:
        print(f"  [ZIP ERROR] Invalid or corrupted ZIP file: {zip_path}")
        results.append({
            'file': os.path.basename(zip_path),
            'full_path': zip_path,
            'status': 'error',
            'message': 'Invalid or corrupted ZIP file'
        })
    
    except Exception as e:
        print(f"  [ZIP ERROR] Failed to process ZIP file: {str(e)}")
        results.append({
            'file': os.path.basename(zip_path),
            'full_path': zip_path,
            'status': 'error',
            'message': f'ZIP processing failed: {str(e)}'
        })
    
    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"  [ZIP SCAN] Cleaned up temporary files")
            except Exception as e:
                print(f"  [ZIP CLEANUP ERROR] {str(e)}")
    
    return results


@app.route('/api/analyze_csv', methods=['POST'])
def analyze_csv():
    """
    Analyze a CSV file containing pre-extracted PE features.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'})
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'})
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'Only CSV files are supported'})
        
        # Save uploaded file
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        
        print(f"[CSV ANALYSIS] Processing file: {filepath}")
        
        # Read CSV
        df = pd.read_csv(filepath)
        print(f"[CSV ANALYSIS] Loaded {len(df)} rows")
        
        # Drop identifier columns if present
        columns_to_drop = ['FileName', 'md5Hash', 'MD5']
        existing_cols_to_drop = [col for col in columns_to_drop if col in df.columns]
        if existing_cols_to_drop:
             df_features = df.drop(columns=existing_cols_to_drop)
        else:
             df_features = df
        
        # Predict for each row
        predictions = []
        
        for index, row in df_features.iterrows():
            try:
                row_df = pd.DataFrame([row])
                
                # Get all predictions
                model_results = model_loader.predict_all(row_df)

                # Determine selected model by confidence
                def get_conf(r):
                     val = r.get('confidence', 0)
                     if isinstance(val, (int, float)): return val
                     return 0
                selected_model = max(model_results, key=get_conf) if model_results else None

                # Mark selected flag on each model
                for m in (model_results or []):
                    m['selected'] = (selected_model and m.get('algorithm') == selected_model.get('algorithm'))

                # Use the model with highest confidence as the final result
                final_result = selected_model

                if final_result:
                    feature_dict = row.to_dict()
                    for k, v in feature_dict.items():
                        if pd.isna(v):
                            feature_dict[k] = None
                        elif isinstance(v, (int, float)):
                            feature_dict[k] = float(v) if isinstance(v, float) else int(v)

                    predictions.append({
                        'index': int(index),
                        'classification': final_result['label'],
                        'confidence': final_result.get('confidence', 0),
                        'best_model': selected_model['algorithm'] if selected_model else (final_result.get('algorithm') if final_result else None),
                        'rf_selected': (selected_model and selected_model.get('algorithm') == 'Random Forest'),
                        'model_comparisons': model_results,
                        'features': feature_dict
                    })
                else:
                     predictions.append({
                        'index': int(index),
                        'classification': "Error",
                        'confidence': 0,
                        'error': "No models available"
                    })
                    
            except Exception as e:
                print(f"[CSV ERROR] Row {index}: {str(e)}")
                predictions.append({
                    'index': int(index),
                    'classification': "Error",
                    'confidence': 0,
                    'error': str(e)
                })
        
        # Calculate summary based on BEST result
        ransomware_count = sum(1 for p in predictions if p.get('classification') == 'Ransomware')
        benign_count = sum(1 for p in predictions if p.get('classification') == 'Benign')
        error_count = sum(1 for p in predictions if p.get('classification') == 'Error')
        
        print(f"[CSV ANALYSIS] Complete - Total: {len(predictions)}, Ransomware: {ransomware_count}, Benign: {benign_count}")
        
        # Trigger Batch Summary Alert (Single beep + Single summary email)
        if ransomware_count > 0:
            alert_system.trigger_batch_alert(
                len(predictions), 
                ransomware_count, 
                email_recipient=config.ALERT_RECIPIENT
            )

        # Clean up uploaded file
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify({
            'status': 'success',
            'summary': {
                'total': len(predictions),
                'ransomware': ransomware_count,
                'benign': benign_count,
                'errors': error_count
            },
            'details': predictions[:500]  # Return up to 500 rows for display
        })
    
    except Exception as e:
        print(f"[CSV ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'CSV analysis failed: {str(e)}'
        })


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    AI-powered cybersecurity chatbot endpoint.
    """
    try:
        data = request.json
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({'response': 'Please enter a question.'})
        
        print(f"[CHATBOT] Query: {user_query}")
        
        response = chatbot.get_response(user_query)
        
        return jsonify({'response': response})
    
    except Exception as e:
        print(f"[CHATBOT ERROR] {str(e)}")
        return jsonify({
            'response': f'Sorry, I encountered an error: {str(e)}'
        })


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify system status.
    """
    status = {
        'status': 'ok',
        'model_loaded': model_loader is not None,
        'feature_extractor': feature_extractor is not None,
        'alert_system': alert_system is not None,
        'chatbot': chatbot is not None
    }
    
    return jsonify(status)


# -- Real-Time Monitoring Endpoints --

@app.route('/api/start_monitoring', methods=['POST'])
def start_monitoring():
    """
    Start real-time folder monitoring.
    Input: {'path': 'C:/...'}
    Output: {'status': 'success/error', 'message': '...'}
    """
    try:
        data = request.json
        raw_path = data.get('path', '')
        
        # Validate and normalize path
        is_valid, error_msg, target_path = validate_path(raw_path)
        
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': error_msg
            })
        
        # Define callback function for when new files are detected
        def on_new_file_detected(filepath):
            """Callback to scan new files and emit results via WebSocket"""
            try:
                print(f"[MONITORING] Scanning new file: {filepath}")
                result = scan_single_file(filepath)
                
                # Emit result via WebSocket
                socketio.emit('scan_result', result)
                
            except Exception as e:
                print(f"[MONITORING ERROR] Failed to scan {filepath}: {e}")
                socketio.emit('scan_error', {
                    'file': filepath,
                    'error': str(e)
                })
        
        # Start monitoring
        success, message = folder_monitor.start_monitoring(
            target_path, 
            on_new_file_detected,
            socketio
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'path': target_path
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            })
            
    except Exception as e:
        print(f"[START MONITORING ERROR] {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to start monitoring: {str(e)}'
        })


@app.route('/api/stop_monitoring', methods=['POST'])
def stop_monitoring():
    """
    Stop real-time folder monitoring.
    Output: {'status': 'success/error', 'message': '...'}
    """
    try:
        success, message = folder_monitor.stop_monitoring()
        
        if success:
            # Notify clients via WebSocket
            socketio.emit('monitoring_stopped', {'message': message})
            
            return jsonify({
                'status': 'success',
                'message': message
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            })
            
    except Exception as e:
        print(f"[STOP MONITORING ERROR] {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to stop monitoring: {str(e)}'
        })


@app.route('/api/monitoring_status', methods=['GET'])
def monitoring_status():
    """
    Get current monitoring status.
    Output: {'is_monitoring': bool, 'monitored_path': str, 'files_scanned': int}
    """
    try:
        status = folder_monitor.get_status()
        return jsonify(status)
    except Exception as e:
        print(f"[MONITORING STATUS ERROR] {e}")
        return jsonify({
            'is_monitoring': False,
            'monitored_path': None,
            'files_scanned': 0,
            'error': str(e)
        })


# -- Error Handlers --

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


if __name__ == '__main__':
    print("="*70)
    print("RANSOMWARE DETECTION SYSTEM - SERVER STARTING")
    print("="*70)
    print(f"Models Directory: {MODELS_DIR}")
    print(f"Upload Directory: {UPLOAD_FOLDER}")
    print(f"Supported Extensions: {', '.join(SUPPORTED_EXTENSIONS)}")
    print("="*70)
    
    socketio.run(app, debug=True, port=5000, host='127.0.0.1')