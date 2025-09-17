#!/usr/bin/env python3
"""
Script de inicio para la aplicación de Control de Tablillas
Alsina Forms Co., Inc.

Uso:
    python run_app.py

O para desarrollo:
    streamlit run run_app.py
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def check_dependencies():
    """Verificar que todas las dependencias estén instaladas"""
    required_packages = [
        'streamlit', 'pandas', 'plotly', 'pdfplumber', 
        'openpyxl', 'xlsxwriter'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Faltan las siguientes dependencias:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Instálalas ejecutando:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True

def setup_directories():
    """Crear directorios necesarios"""
    directories = ['data', 'exports', 'logs']
    
    for directory in directories:
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"📁 Directorio creado: {directory}")
            else:
                print(f"📁 Directorio ya existe: {directory}")
        except FileExistsError:
            print(f"📁 Directorio ya existe: {directory}")
        except Exception as e:
            print(f"⚠️ No se pudo crear directorio {directory}: {str(e)}")

def create_initial_config():
    """Crear archivo de configuración inicial"""
    config = {
        "app_settings": {
            "title": "Control de Tablillas - Alsina Forms",
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat()
        },
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
        },
        "export_settings": {
            "default_format": "xlsx",
            "include_charts": True,
            "max_records_per_sheet": 10000
        }
    }
    
    config_file = "config.json"
    if not os.path.exists(config_file):
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"⚙️  Archivo de configuración creado: {config_file}")

def run_streamlit_app():
    """Ejecutar la aplicación Streamlit"""
    try:
        # Obtener la ruta del archivo principal
        main_app = os.path.join(os.path.dirname(__file__), "app.py")
        
        if not os.path.exists(main_app):
            print("❌ No se encuentra el archivo app.py")
            print("💡 Asegúrate de que todos los archivos estén en el mismo directorio")
            return False
        
        # Ejecutar Streamlit
        print("🚀 Iniciando aplicación...")
        print("📱 La aplicación se abrirá en tu navegador web")
        print("🌐 URL local: http://localhost:8501")
        print("\n⏹️  Para detener la aplicación presiona Ctrl+C")
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", main_app,
            "--server.port=8501",
            "--server.headless=false",
            "--browser.gatherUsageStats=false"
        ])
        
        return True
        
    except KeyboardInterrupt:
        print("\n👋 Aplicación detenida por el usuario")
        return True
    except Exception as e:
        print(f"❌ Error al iniciar la aplicación: {str(e)}")
        return False

def main():
    """Función principal"""
    print("=" * 60)
    print("🏗️  CONTROL DE TABLILLAS - ALSINA FORMS CO.")
    print("=" * 60)
    print()
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Configurar directorios
    setup_directories()
    
    # Crear configuración inicial
    create_initial_config()
    
    # Ejecutar aplicación
    if not run_streamlit_app():
        sys.exit(1)

if __name__ == "__main__":
    main()