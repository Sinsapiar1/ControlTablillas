"""
Archivo de entrada específico para Vercel con Streamlit
Este archivo maneja la configuración específica de Vercel para aplicaciones Streamlit
"""

import os
import sys
import subprocess

def main():
    """Función principal para Vercel"""
    # Configurar variables de entorno para Streamlit
    os.environ['STREAMLIT_SERVER_PORT'] = os.environ.get('PORT', '8501')
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    # Ejecutar Streamlit
    subprocess.run([
        sys.executable, '-m', 'streamlit', 'run', 
        'vercel_app.py',
        '--server.port', os.environ.get('PORT', '8501'),
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--browser.gatherUsageStats', 'false'
    ])

if __name__ == '__main__':
    main()