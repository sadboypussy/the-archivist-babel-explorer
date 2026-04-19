@echo off
REM Dev launcher — requires Python on PATH with streamlit installed (see requirements-app.txt).
cd /d "%~dp0"
REM Jamais l’invite « Welcome to Streamlit! / Email: » dans la console (redondant avec .streamlit/config.toml).
set "STREAMLIT_SERVER_SHOW_EMAIL_PROMPT=false"
REM Mode sans ouverture du navigateur (serveur / CI / SSH) — l’un des deux suffit :
REM   • variable d’environnement ARCHIVIST_STREAMLIT_HEADLESS=1 avant ce script, ou
REM   • fichier vide .streamlit\headless.flag (voir .gitignore).
if /i "%ARCHIVIST_STREAMLIT_HEADLESS%"=="1" set "STREAMLIT_SERVER_HEADLESS=true"
if exist "%~dp0.streamlit\headless.flag" set "STREAMLIT_SERVER_HEADLESS=true"
REM Galerie Firestore : si ce fichier existe, publication depuis l’UI (voir requirements-community.txt).
if exist "%~dp0config\firebase-service-account.json" (
  set "ARCHIVIST_FIREBASE_CREDENTIALS=%~dp0config\firebase-service-account.json"
)
streamlit run archivist_app.py
