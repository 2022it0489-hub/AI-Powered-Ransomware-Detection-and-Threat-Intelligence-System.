@echo off
REM Quick fix script for model loading errors
REM Run this batch file to regenerate model files and restart the app

echo.
echo ========================================
echo Ransomware Pro - Model Recovery Tool
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Regenerating model files...
echo.
python regenerate_models.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to regenerate models
    pause
    exit /b 1
)

echo.
echo ========================================
echo Model regeneration complete!
echo ========================================
echo.
echo Next steps:
echo 1. Start the Flask app: python app.py
echo 2. Open http://localhost:5000 in your browser
echo 3. Test the CSV analysis and scanner features
echo.
echo For more information, see MODEL_MANAGEMENT.md
echo.
pause
