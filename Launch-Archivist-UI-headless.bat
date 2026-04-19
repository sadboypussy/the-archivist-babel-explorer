@echo off
REM Même lancement que Launch-Archivist-UI.bat, sans ouverture du navigateur (URLs affichées dans la console).
cd /d "%~dp0"
set "STREAMLIT_SERVER_SHOW_EMAIL_PROMPT=false"
set "STREAMLIT_SERVER_HEADLESS=true"
if exist "%~dp0config\firebase-service-account.json" (
  set "ARCHIVIST_FIREBASE_CREDENTIALS=%~dp0config\firebase-service-account.json"
)
streamlit run archivist_app.py
