@echo off
REM Descarga todo el canal @SemyonSkrepetsky a las carpetas media/ y actualiza el catalogo.
chcp 65001 >nul
cd /d "%~dp0"
echo ====================================================
echo   Archivo en memoria de Semyon Skrepetsky
echo   Descargando el canal completo de Telegram...
echo ====================================================
echo.
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] No se encontro Python.
  echo Instalalo desde https://www.python.org/downloads/
  echo y marca "Add Python to PATH" durante la instalacion.
  pause
  exit /b 1
)
python "scripts\archive_skrepetsky.py" %*
echo.
echo Hecho. Abre web\index.html para ver la galeria.
pause
