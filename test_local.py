#!/usr/bin/env python3
"""
Script para probar la aplicación localmente antes del despliegue
"""

import subprocess
import sys
import os

def test_imports():
    """Probar que todas las dependencias se importan correctamente"""
    print("🔍 Probando importaciones...")
    
    try:
        import streamlit as st
        print("✅ Streamlit importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando Streamlit: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ Pandas importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando Pandas: {e}")
        return False
    
    try:
        import plotly.express as px
        print("✅ Plotly importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando Plotly: {e}")
        return False
    
    try:
        import camelot
        print("✅ Camelot importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando Camelot: {e}")
        return False
    
    try:
        import openpyxl
        print("✅ OpenPyXL importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando OpenPyXL: {e}")
        return False
    
    return True

def test_app_syntax():
    """Probar que la aplicación no tiene errores de sintaxis"""
    print("\n🔍 Probando sintaxis de la aplicación...")
    
    try:
        with open('vercel_app.py', 'r') as f:
            code = f.read()
        
        compile(code, 'vercel_app.py', 'exec')
        print("✅ Sintaxis de vercel_app.py correcta")
        return True
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en vercel_app.py: {e}")
        return False
    except FileNotFoundError:
        print("❌ Archivo vercel_app.py no encontrado")
        return False

def test_vercel_config():
    """Probar configuración de Vercel"""
    print("\n🔍 Probando configuración de Vercel...")
    
    try:
        import json
        with open('vercel.json', 'r') as f:
            config = json.load(f)
        
        required_keys = ['version', 'builds', 'routes']
        for key in required_keys:
            if key not in config:
                print(f"❌ Clave '{key}' faltante en vercel.json")
                return False
        
        print("✅ Configuración de Vercel válida")
        return True
    except FileNotFoundError:
        print("❌ Archivo vercel.json no encontrado")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error en vercel.json: {e}")
        return False

def main():
    """Función principal de prueba"""
    print("🚀 Iniciando pruebas para despliegue en Vercel...\n")
    
    tests = [
        test_imports,
        test_app_syntax,
        test_vercel_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Resultados: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! Tu aplicación está lista para Vercel.")
        print("\n📋 Próximos pasos:")
        print("1. Sube tu código a GitHub")
        print("2. Conecta tu repo con Vercel")
        print("3. ¡Deploy automático!")
    else:
        print("❌ Algunas pruebas fallaron. Revisa los errores antes de desplegar.")
        sys.exit(1)

if __name__ == "__main__":
    main()