@echo off
echo ============================================================
echo 🏭 SISTEMA DE CONTROL DE TABLILLAS - INICIO LOCAL
echo ============================================================
echo 🚀 Iniciando aplicación local...
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Por favor instala Python 3.9+
    pause
    exit /b 1
)

REM Verificar si Streamlit está instalado
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo ❌ Streamlit no encontrado. Instalando dependencias...
    pip install -r requirements_local.txt
    if errorlevel 1 (
        echo ❌ Error instalando dependencias
        pause
        exit /b 1
    )
)

REM Verificar si Ghostscript está instalado
gs --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Ghostscript no encontrado
    echo 📥 Por favor instala Ghostscript desde: https://www.ghostscript.com/download/gsdnld.html
    echo.
    echo Presiona cualquier tecla para continuar sin Ghostscript...
    pause >nul
)

echo ✅ Verificaciones completadas
echo 🌐 La aplicación estará disponible en: http://localhost:8501
echo ⏹️  Presiona Ctrl+C para detener la aplicación
echo.

REM Iniciar Streamlit
python -m streamlit run app_local.py --server.port 8501 --server.address localhost

echo.
echo 👋 Aplicación detenida
pause