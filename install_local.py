#!/usr/bin/env python3
"""
🏭 Script de Instalación Automática - Sistema de Control de Tablillas
Versión Local para Alsina Forms Co.

Este script automatiza la instalación y configuración del sistema local.
"""

import subprocess
import sys
import os
import platform

def print_header():
    """Imprimir encabezado del script"""
    print("=" * 60)
    print("🏭 SISTEMA DE CONTROL DE TABLILLAS - INSTALACIÓN LOCAL")
    print("=" * 60)
    print("📋 Versión: 1.0.0")
    print("🎯 Plataforma: Local")
    print("🐍 Python: 3.11.9+")
    print("=" * 60)

def check_python_version():
    """Verificar versión de Python"""
    print("\n🔍 Verificando versión de Python...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requiere Python 3.9+")
        return False

def check_ghostscript():
    """Verificar si Ghostscript está instalado"""
    print("\n🔍 Verificando Ghostscript...")
    try:
        result = subprocess.run(['gs', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Ghostscript {version} - Instalado correctamente")
            return True
        else:
            print("❌ Ghostscript no encontrado")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Ghostscript no encontrado")
        return False

def install_requirements():
    """Instalar dependencias de Python"""
    print("\n📦 Instalando dependencias de Python...")
    try:
        # Actualizar pip primero
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      check=True, capture_output=True)
        print("✅ pip actualizado")
        
        # Instalar requirements
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements_local.txt'], 
                      check=True, capture_output=True)
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def test_imports():
    """Probar importaciones críticas"""
    print("\n🧪 Probando importaciones...")
    modules = ['streamlit', 'pandas', 'plotly', 'camelot', 'openpyxl']
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module} - OK")
        except ImportError:
            print(f"❌ {module} - Error")
            return False
    return True

def create_sample_data():
    """Crear carpeta de datos de muestra"""
    print("\n📁 Creando estructura de datos...")
    try:
        os.makedirs('data', exist_ok=True)
        print("✅ Carpeta 'data' creada")
        return True
    except Exception as e:
        print(f"❌ Error creando carpeta: {e}")
        return False

def print_ghostscript_instructions():
    """Imprimir instrucciones para Ghostscript"""
    system = platform.system().lower()
    
    print("\n" + "=" * 60)
    print("⚠️  GHOSTSCRIPT REQUERIDO")
    print("=" * 60)
    
    if system == "windows":
        print("🪟 Windows:")
        print("1. Descargar desde: https://www.ghostscript.com/download/gsdnld.html")
        print("2. Instalar con configuración por defecto")
        print("3. Reiniciar terminal/IDE")
    elif system == "darwin":  # macOS
        print("🍎 macOS:")
        print("Con Homebrew: brew install ghostscript")
        print("Con MacPorts: sudo port install ghostscript")
    else:  # Linux
        print("🐧 Linux:")
        print("Ubuntu/Debian: sudo apt-get install ghostscript")
        print("CentOS/RHEL: sudo yum install ghostscript")
    
    print("\nDespués de instalar Ghostscript, ejecuta este script nuevamente.")

def print_success():
    """Imprimir mensaje de éxito"""
    print("\n" + "=" * 60)
    print("🎉 ¡INSTALACIÓN COMPLETADA!")
    print("=" * 60)
    print("✅ Python verificado")
    print("✅ Dependencias instaladas")
    print("✅ Importaciones probadas")
    print("✅ Estructura creada")
    print("\n🚀 Para ejecutar la aplicación:")
    print("   streamlit run app_local.py")
    print("\n🌐 La aplicación estará disponible en:")
    print("   http://localhost:8501")
    print("\n📚 Para más información, consulta README_LOCAL.md")
    print("=" * 60)

def main():
    """Función principal"""
    print_header()
    
    # Verificar Python
    if not check_python_version():
        print("\n❌ Instalación cancelada - Python 3.9+ requerido")
        return False
    
    # Verificar Ghostscript
    if not check_ghostscript():
        print_ghostscript_instructions()
        return False
    
    # Instalar dependencias
    if not install_requirements():
        print("\n❌ Instalación cancelada - Error en dependencias")
        return False
    
    # Probar importaciones
    if not test_imports():
        print("\n❌ Instalación cancelada - Error en importaciones")
        return False
    
    # Crear estructura
    if not create_sample_data():
        print("\n⚠️  Advertencia - Error creando estructura de datos")
    
    # Éxito
    print_success()
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Instalación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)