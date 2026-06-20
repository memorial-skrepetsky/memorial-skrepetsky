@echo off
REM Quita fecha, vistas y enlaces del catalogo y regenera la web.
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] No se encontro Python. Instalalo desde https://www.python.org/downloads/
  pause
  exit /b 1
)
python "scripts\limpiar_pie.py"
echo.
pause
