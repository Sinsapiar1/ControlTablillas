import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Configuración de página
st.set_page_config(
    page_title="Control de Tablillas - Alsina Forms",
    page_icon="🏗️",
    layout="wide"
)

# CSS básico
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .success-box { 
        background: #d4edda; 
        padding: 1rem; 
        border-radius: 8px; 
        margin: 1rem 0; 
        border-left: 4px solid #28a745;
    }
    
    .alert-info { 
        background: #d1ecf1; 
        color: #0c5460; 
        padding: 1rem; 
        border-radius: 8px; 
        margin: 1rem 0; 
        border-left: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Función principal de la aplicación"""
    # Header
    st.markdown('''
    <div class="main-header">
        <h1>🏗️ SISTEMA DE CONTROL DE TABLILLAS</h1>
        <h2>Alsina Forms Co.</h2>
        <p>📊 Análisis de datos Excel</p>
        <div style="background: #000; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.8rem; display: inline-block; margin: 1rem 0;">🚀 Powered by Vercel</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Información
    st.markdown("""
    <div class="alert-info">
    <h3>📊 Versión Simplificada</h3>
    <p>Esta es una versión optimizada para Vercel con funcionalidades básicas de análisis de Excel.</p>
    <p><strong>Funcionalidades disponibles:</strong></p>
    <ul>
        <li>📄 Cargar archivos Excel</li>
        <li>📊 Visualizar datos</li>
        <li>📈 Análisis básico</li>
        <li>💾 Exportar reportes</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar archivo
    uploaded_file = st.file_uploader(
        "📂 Seleccionar archivo Excel",
        type=['xlsx', 'xls', 'csv'],
        help="Sube un archivo Excel o CSV con datos de tablillas"
    )
    
    if uploaded_file is not None:
        st.markdown('<div class="success-box">✅ <strong>Archivo cargado correctamente!</strong></div>', 
                    unsafe_allow_html=True)
        
        try:
            # Leer archivo
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Mostrar información básica
            st.subheader("📊 Información del Archivo")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📋 Total Registros", len(df))
            
            with col2:
                st.metric("📊 Columnas", len(df.columns))
            
            with col3:
                st.metric("📅 Fecha", datetime.now().strftime('%Y-%m-%d'))
            
            # Mostrar datos
            st.subheader("📋 Datos")
            st.dataframe(df.head(20), use_container_width=True)
            
            # Mostrar columnas
            st.subheader("📊 Columnas Disponibles")
            for i, col in enumerate(df.columns):
                st.write(f"{i+1}. **{col}** - Tipo: {df[col].dtype}")
            
            # Análisis básico
            st.subheader("📈 Análisis Básico")
            
            # Columnas numéricas
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                st.write("**Columnas Numéricas:**")
                for col in numeric_cols:
                    st.write(f"- **{col}**: Min={df[col].min():.2f}, Max={df[col].max():.2f}, Promedio={df[col].mean():.2f}")
            
            # Columnas de texto
            text_cols = df.select_dtypes(include=['object']).columns
            if len(text_cols) > 0:
                st.write("**Columnas de Texto:**")
                for col in text_cols:
                    unique_count = df[col].nunique()
                    st.write(f"- **{col}**: {unique_count} valores únicos")
            
            # Botón de descarga
            if st.button("💾 Descargar Datos como CSV", type="primary"):
                csv_data = df.to_csv(index=False)
                filename = f"datos_tablillas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv"
                )
                
                st.success(f"✅ Archivo listo para descargar: **{filename}**")
            
        except Exception as e:
            st.error(f"❌ Error procesando archivo: {str(e)}")
            st.write("**Posibles soluciones:**")
            st.write("- Verifica que el archivo no esté corrupto")
            st.write("- Asegúrate de que sea un Excel o CSV válido")
            st.write("- Intenta con un archivo más pequeño")

if __name__ == "__main__":
    main()