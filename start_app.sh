#!/bin/bash

# 🏗️ Script de Inicio - Control de Tablillas Alsina Forms
# Este script configura y ejecuta la aplicación de control de tablillas

echo "=========================================="
echo "🏗️  CONTROL DE TABLILLAS - ALSINA FORMS"
echo "=========================================="
echo ""

# Verificar si estamos en el directorio correcto
if [ ! -f "app.py" ]; then
    echo "❌ Error: No se encuentra app.py en el directorio actual"
    echo "💡 Asegúrate de ejecutar este script desde el directorio del proyecto"
    exit 1
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 no está instalado"
    echo "💡 Instala Python 3.8 o superior"
    exit 1
fi

echo "✅ Python3 encontrado: $(python3 --version)"

# Verificar si el entorno virtual existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Error al crear entorno virtual"
        echo "💡 Instala python3-venv: sudo apt install python3-venv"
        exit 1
    fi
    echo "✅ Entorno virtual creado"
fi

# Activar entorno virtual
echo "🔄 Activando entorno virtual..."
source venv/bin/activate

# Verificar dependencias
echo "🔍 Verificando dependencias..."
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Instalando dependencias..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error al instalar dependencias"
        exit 1
    fi
    echo "✅ Dependencias instaladas"
else
    echo "✅ Dependencias ya instaladas"
fi

# Crear directorios necesarios
echo "📁 Creando directorios necesarios..."
mkdir -p data exports logs
echo "✅ Directorios creados"

# Verificar configuración
if [ ! -f "config.json" ]; then
    echo "⚙️  Creando archivo de configuración..."
    cat > config.json << 'EOF'
{
  "priority_weights": {
    "days_since_return": 0.4,
    "counting_delay": 0.3,
    "validation_delay": 0.2,
    "open_tablets": 0.1
  },
  "alert_thresholds": {
    "high_priority_days": 15,
    "critical_open_tablets": 50,
    "warning_delay_days": 10
  }
}
EOF
    echo "✅ Archivo de configuración creado"
fi

# Obtener puerto
PORT=${1:-8501}
echo "🌐 Iniciando aplicación en puerto $PORT..."

# Mostrar información de acceso
echo ""
echo "🚀 APLICACIÓN INICIADA"
echo "=========================================="
echo "🌐 URL Local: http://localhost:$PORT"
echo "🌐 URL Red:   http://$(hostname -I | awk '{print $1}'):$PORT"
echo ""
echo "⏹️  Para detener: Ctrl+C"
echo "=========================================="
echo ""

# Ejecutar aplicación
streamlit run app.py --server.port=$PORT --server.headless=false --browser.gatherUsageStats=false