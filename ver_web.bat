@echo off
REM Abre la galeria con un pequeno servidor local para que las imagenes y
REM videos carguen bien (al abrir el HTML directamente, algunos navegadores
REM -sobre todo Firefox- bloquean las imagenes de la carpeta media/).
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] No se encontro Python. Instalalo desde https://www.python.org/downloads/
  pause
  exit /b 1
)
echo ====================================================
echo   Galeria en memoria de Semyon Skrepetsky
echo   Abriendo en: http://localhost:8000/index.html
echo.
echo   DEJA ESTA VENTANA ABIERTA mientras ves la galeria.
echo   Cierrala (o pulsa Ctrl+C) para detener el servidor.
echo ====================================================
start "" "http://localhost:8000/index.html"
python -m http.server 8000
