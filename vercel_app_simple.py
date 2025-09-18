import streamlit as st
import pandas as pd
import plotly.express as px
import io
from datetime import datetime
import tempfile
import os

# Configuración de página
st.set_page_config(
    page_title="Control Profesional de Tablillas - Alsina Forms",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Profesional
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .success-box { 
        background: linear-gradient(45deg, #d4edda, #c3e6cb); 
        padding: 1.5rem; 
        border-radius: 12px; 
        margin: 1rem 0; 
        border-left: 4px solid #28a745;
    }
    
    .alert-info { 
        background: linear-gradient(45deg, #d1ecf1, #bee5eb); 
        color: #0c5460; 
        padding: 1rem; 
        border-radius: 8px; 
        margin: 1rem 0; 
        border-left: 4px solid #17a2b8;
    }
    
    .section-header {
        background: linear-gradient(90deg, #495057, #6c757d);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 2rem 0 1rem 0;
        font-size: 1.2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Función principal de la aplicación"""
    # Header profesional
    st.markdown('''
    <div class="main-header">
        <h1>🏗️ SISTEMA PROFESIONAL DE CONTROL DE TABLILLAS</h1>
        <h2>Alsina Forms Co. - Análisis Diario por Excel</h2>
        <p>📄 PDF → Excel perfecto | 📊 Análisis multi-archivo | 🔄 Comparaciones automáticas</p>
        <div style="background: linear-gradient(45deg, #000, #333); color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.8rem; display: inline-block; margin: 1rem 0;">🚀 Powered by Vercel</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Información sobre Camelot
    st.markdown("""
    <div class="alert-info">
    <h3>🐪 Camelot en Vercel</h3>
    <p><strong>Estado:</strong> Camelot requiere dependencias muy pesadas (OpenCV + Ghostscript) que exceden el límite de 250MB de Vercel.</p>
    <p><strong>Solución:</strong> Para usar Camelot, considera desplegar en:</p>
    <ul>
        <li>🚂 <strong>Railway</strong> - Soporte completo para Docker</li>
        <li>🎨 <strong>Render</strong> - Docker support</li>
        <li>☁️ <strong>Google Cloud Run</strong> - Contenedores ilimitados</li>
        <li>🐳 <strong>Docker local</strong> - Para desarrollo</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Pestañas principales
    tab1, tab2 = st.tabs(["📄 PROCESAR EXCEL", "📊 ANÁLISIS MULTI-EXCEL"])
    
    with tab1:
        show_excel_processing_tab()
    
    with tab2:
        show_excel_analysis_tab()

def show_excel_processing_tab():
    """Pestaña para procesar archivos Excel directamente"""
    st.markdown('<div class="section-header">📄 PROCESAR ARCHIVOS EXCEL</div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    ### 📊 Cargar archivos Excel directamente
    
    Como alternativa a Camelot, puedes:
    - 📄 **Subir archivos Excel** ya procesados
    - 📊 **Analizar datos** existentes
    - 🔄 **Comparar múltiples archivos**
    - 📈 **Generar reportes** automáticos
    """)
    
    # Cargar Excel
    uploaded_file = st.file_uploader(
        "📂 Seleccionar archivo Excel",
        type=['xlsx', 'xls'],
        help="Sube un archivo Excel con datos de tablillas"
    )
    
    if uploaded_file is not None:
        st.markdown('<div class="success-box">✅ <strong>Archivo cargado correctamente!</strong></div>', 
                    unsafe_allow_html=True)
        
        try:
            # Leer Excel
            df = pd.read_excel(uploaded_file)
            
            # Mostrar resumen
            show_excel_summary(df)
            
            # Mostrar datos
            show_excel_data(df)
            
            # Generar reporte
            generate_excel_report(df)
            
        except Exception as e:
            st.error(f"❌ Error procesando Excel: {str(e)}")

def show_excel_summary(df: pd.DataFrame):
    """Mostrar resumen del Excel"""
    st.subheader("📊 Resumen de Datos")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Total Registros", len(df))
    
    with col2:
        st.metric("📊 Columnas", len(df.columns))
    
    with col3:
        if 'Total_Open' in df.columns:
            total_open = int(pd.to_numeric(df['Total_Open'], errors='coerce').fillna(0).sum())
        else:
            total_open = 0
        st.metric("🔓 Tablillas Pendientes", total_open)
    
    with col4:
        if 'Customer_Name' in df.columns:
            unique_customers = df['Customer_Name'].nunique()
        else:
            unique_customers = 0
        st.metric("👥 Clientes Únicos", unique_customers)

def show_excel_data(df: pd.DataFrame):
    """Mostrar datos del Excel"""
    st.subheader("📋 Datos del Archivo")
    
    # Mostrar primeras filas
    st.dataframe(df.head(10), use_container_width=True)
    
    # Mostrar información de columnas
    st.subheader("📊 Información de Columnas")
    col_info = pd.DataFrame({
        'Columna': df.columns,
        'Tipo': df.dtypes,
        'Valores Únicos': [df[col].nunique() for col in df.columns],
        'Valores Nulos': [df[col].isnull().sum() for col in df.columns]
    })
    st.dataframe(col_info, use_container_width=True)

def generate_excel_report(df: pd.DataFrame):
    """Generar reporte Excel"""
    st.subheader("💾 Generar Reporte")
    
    if st.button("📥 Generar Reporte Excel", type="primary"):
        try:
            # Crear reporte
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Hoja 1: Datos completos
                df.to_excel(writer, sheet_name='Datos_Completos', index=False)
                
                # Hoja 2: Resumen por cliente (si existe)
                if 'Customer_Name' in df.columns:
                    customer_summary = df.groupby('Customer_Name').agg({
                        'Total_Open': 'sum' if 'Total_Open' in df.columns else lambda x: 0,
                        'Total_Tablets': 'sum' if 'Total_Tablets' in df.columns else lambda x: 0,
                    }).round(2)
                    customer_summary.to_excel(writer, sheet_name='Resumen_Clientes')
                
                # Hoja 3: Métricas
                today = datetime.now().strftime('%Y-%m-%d')
                metrics_data = {
                    'Métrica': [
                        'Fecha Procesamiento',
                        'Total Registros',
                        'Total Columnas',
                        'Clientes Únicos' if 'Customer_Name' in df.columns else 'N/A'
                    ],
                    'Valor': [
                        today,
                        len(df),
                        len(df.columns),
                        df['Customer_Name'].nunique() if 'Customer_Name' in df.columns else 'N/A'
                    ]
                }
                metrics_df = pd.DataFrame(metrics_data)
                metrics_df.to_excel(writer, sheet_name='Métricas', index=False)
            
            # Descargar
            filename = f"reporte_tablillas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            
            st.download_button(
                label="💾 Descargar Reporte",
                data=output.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.success(f"✅ Reporte generado: **{filename}**")
            
        except Exception as e:
            st.error(f"❌ Error generando reporte: {str(e)}")

def show_excel_analysis_tab():
    """Pestaña para análisis multi-Excel"""
    st.markdown('<div class="section-header">📊 ANÁLISIS MULTI-EXCEL</div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    ### 🔄 Cargar múltiples archivos Excel para análisis comparativo
    
    Sube **2 o más archivos Excel** para:
    - 📈 Ver tendencias y evolución
    - 🔄 Detectar cambios entre archivos  
    - 📊 Analizar performance histórica
    - 🎯 Identificar patrones
    """)
    
    # Cargar múltiples archivos Excel
    uploaded_excel_files = st.file_uploader(
        "📂 Seleccionar archivos Excel (múltiples)",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="Selecciona 2 o más archivos Excel de diferentes días"
    )
    
    if uploaded_excel_files and len(uploaded_excel_files) >= 2:
        st.info("📊 Análisis multi-Excel disponible próximamente")
        st.write(f"Archivos cargados: {len(uploaded_excel_files)}")
        
        for i, file in enumerate(uploaded_excel_files):
            st.write(f"📄 Archivo {i+1}: {file.name}")
    
    elif uploaded_excel_files and len(uploaded_excel_files) == 1:
        st.warning("⚠️ Se necesitan al menos 2 archivos para hacer comparación")
    
    else:
        st.info("📂 Selecciona múltiples archivos Excel para comenzar el análisis")

if __name__ == "__main__":
    main()