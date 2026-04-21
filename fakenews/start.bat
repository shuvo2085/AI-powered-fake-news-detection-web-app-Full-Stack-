@echo off
echo ╔═══════════════════════════════════════╗
echo ║       TruthLens — Fake News Detector  ║
echo ╚═══════════════════════════════════════╝
echo.
echo Installing Python dependencies...
pip install -r backend\requirements.txt
echo.
echo Starting API server on http://localhost:5000
echo Open frontend\index.html in your browser
echo Press Ctrl+C to stop
echo.
cd backend && python app.py
pause
