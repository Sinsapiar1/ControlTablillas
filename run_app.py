"""
Archivo principal para ejecutar la aplicación Streamlit
"""

import streamlit as st
import sys
import os

# Agregar el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar y ejecutar la aplicación principal
from app import main

if __name__ == "__main__":
    main()