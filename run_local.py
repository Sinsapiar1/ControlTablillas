#!/usr/bin/env python3
"""
🏭 Script de Inicio Rápido - Sistema de Control de Tablillas
Versión Local para Alsina Forms Co.

Este script inicia la aplicación local con configuración optimizada.
"""

import subprocess
import sys
import os
import webbrowser
import time
import threading

def print_header():
    """Imprimir encabezado"""
    print("=" * 60)
    print("🏭 SISTEMA DE CONTROL DE TABLillas - INICIO LOCAL")
    print("=" * 60)
    print("🚀 Iniciando aplicación...")
    print("=" * 60)

def check_files():
    """Verificar que los archivos necesarios existan"""
    required_files = ['app_local.py', 'requirements_local.txt']
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Archivo requerido no encontrado: {file}")
            return False
    
    print("✅ Archivos verificados")
    return True

def open_browser():
    """Abrir navegador después de un delay"""
    time.sleep(3)  # Esperar a que Streamlit inicie
    try:
        webbrowser.open('http://localhost:8501')
        print("🌐 Navegador abierto automáticamente")
    except Exception as e:
        print(f"⚠️  No se pudo abrir navegador automáticamente: {e}")
        print("🌐 Abre manualmente: http://localhost:8501")

def start_streamlit():
    """Iniciar Streamlit"""
    print("\n🚀 Iniciando Streamlit...")
    print("📱 La aplicación estará disponible en: http://localhost:8501")
    print("⏹️  Presiona Ctrl+C para detener la aplicación")
    print("-" * 60)
    
    try:
        # Iniciar Streamlit
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'app_local.py',
            '--server.port', '8501',
            '--server.address', 'localhost',
            '--server.headless', 'false',
            '--browser.gatherUsageStats', 'false'
        ])
    except KeyboardInterrupt:
        print("\n\n⏹️  Aplicación detenida por el usuario")
    except Exception as e:
        print(f"\n❌ Error iniciando aplicación: {e}")

def main():
    """Función principal"""
    print_header()
    
    # Verificar archivos
    if not check_files():
        print("\n❌ Error: Archivos requeridos no encontrados")
        print("💡 Asegúrate de estar en el directorio correcto")
        return False
    
    # Iniciar navegador en hilo separado
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Iniciar Streamlit
    start_streamlit()
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print("💡 Consulta README_LOCAL.md para ayuda")