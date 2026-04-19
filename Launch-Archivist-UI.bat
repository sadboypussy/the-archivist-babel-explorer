@echo off
REM Dev launcher — requires Python on PATH with streamlit installed (see requirements-app.txt).
cd /d "%~dp0"
REM Galerie Firestore : si ce fichier existe, publication depuis l’UI (voir requirements-community.txt).
if exist "%~dp0config\firebase-service-account.json" (
  set "ARCHIVIST_FIREBASE_CREDENTIALS=%~dp0config\firebase-service-account.json"
)
streamlit run archivist_app.py
