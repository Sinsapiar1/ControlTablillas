#!/bin/bash

echo "============================================================"
echo "🏭 SISTEMA DE CONTROL DE TABLILLAS - INICIO LOCAL"
echo "============================================================"
echo "🚀 Iniciando aplicación local..."
echo

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no encontrado. Por favor instala Python 3.9+"
    exit 1
fi

# Verificar versión de Python
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $python_version encontrado"

# Verificar si Streamlit está instalado
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "❌ Streamlit no encontrado. Instalando dependencias..."
    pip3 install -r requirements_local.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error instalando dependencias"
        exit 1
    fi
fi

# Verificar si Ghostscript está instalado
if ! command -v gs &> /dev/null; then
    echo "⚠️  Ghostscript no encontrado"
    echo "📥 Por favor instala Ghostscript:"
    echo "   macOS: brew install ghostscript"
    echo "   Ubuntu/Debian: sudo apt-get install ghostscript"
    echo "   CentOS/RHEL: sudo yum install ghostscript"
    echo
    echo "Presiona Enter para continuar sin Ghostscript..."
    read
fi

echo "✅ Verificaciones completadas"
echo "🌐 La aplicación estará disponible en: http://localhost:8501"
echo "⏹️  Presiona Ctrl+C para detener la aplicación"
echo

# Iniciar Streamlit
python3 -m streamlit run app_local.py --server.port 8501 --server.address localhost

echo
echo "👋 Aplicación detenida"