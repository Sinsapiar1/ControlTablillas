import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
from datetime import datetime, timedelta
import re
import tempfile
import os
import glob
from typing import Optional, List, Dict, Tuple
import hashlib

# Intentar importar Camelot
try:
    import camelot
    CAMELOT_AVAILABLE = True
    st.success("🐪 Camelot cargado correctamente!")
except ImportError:
    CAMELOT_AVAILABLE = False
    st.error("❌ Camelot no disponible")

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
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #2a5298;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .kpi-container {
        background: linear-gradient(45deg, #f8f9fa, #e9ecef);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        border: 1px solid #dee2e6;
    }
    
    .alert-high { 
        background: linear-gradient(45deg, #dc3545, #c82333); 
        color: white; 
        padding: 1rem; 
        border-radius: 8px; 
        margin: 1rem 0; 
        font-weight: bold;
    }
    
    .alert-medium { 
        background: linear-gradient(45deg, #fd7e14, #e85d04); 
        color: white; 
        padding: 1rem; 
        border-radius: 8px; 
        margin: 1rem 0; 
        font-weight: bold;
    }
    
    .alert-low { 
        background: linear-gradient(45deg, #28a745, #20c997); 
        color: white; 
        padding: 1rem; 
        border-radius: 8px; 
        margin: 1rem 0; 
        font-weight: bold;
    }
    
    .success-box { 
        background: linear-gradient(45deg, #d4edda, #c3e6cb); 
        padding: 1.5rem; 
        border-radius: 12px; 
        margin: 1rem 0; 
        border-left: 4px solid #28a745;
    }
    
    .comparison-box {
        background: linear-gradient(45deg, #fff3cd, #ffeaa7);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid #ffc107;
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
    
    .file-info {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #2196f3;
    }
    
    .vercel-badge {
        background: linear-gradient(45deg, #000, #333);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class TablillasExtractorPro:
    """Extractor profesional mejorado"""
    
    def __init__(self):
        self.expected_columns = [
            'WH', 'WH_Code', 'Return_Packing_Slip', 'Return_Date', 'Jobsite_ID',
            'Cost_Center', 'Invoice_Start_Date', 'Invoice_End_Date', 
            'Customer_Name', 'Job_Site_Name', 'Definitive_Dev', 'Counted_Date',
            'Tablets', 'Total_Tablets', 'Open_Tablets', 'Total_Open',
            'Counting_Delay', 'Validation_Delay'
        ]
    
    def extract_from_pdf(self, uploaded_file) -> Optional[pd.DataFrame]:
        """Extrae datos usando Camelot (método original perfeccionado)"""
        if not CAMELOT_AVAILABLE:
            st.error("⚠️ Camelot no está disponible en este entorno")
            return None
        
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name
            
            st.info("🔄 Extrayendo datos con Camelot...")
            
            # Probar diferentes configuraciones de Camelot
            tables = None
            
            try:
                # Método 1: Stream (mejor para tablas sin bordes definidos)
                tables = camelot.read_pdf(tmp_file_path, pages='all', flavor='stream')
                st.write(f"📊 Método Stream: {len(tables)} tablas encontradas")
            except Exception as e:
                st.write(f"Stream falló: {str(e)}")
                
            if not tables or len(tables) == 0:
                try:
                    # Método 2: Lattice (mejor para tablas con bordes)
                    tables = camelot.read_pdf(tmp_file_path, pages='all', flavor='lattice')
                    st.write(f"📊 Método Lattice: {len(tables)} tablas encontradas")
                except Exception as e:
                    st.write(f"Lattice falló: {str(e)}")
            
            # Limpiar archivo temporal
            os.unlink(tmp_file_path)
            
            if not tables or len(tables) == 0:
                st.error("❌ No se encontraron tablas en el PDF")
                return None
            
            # Procesar tablas encontradas
            return self._process_tables_advanced(tables)
            
        except Exception as e:
            st.error(f"❌ Error procesando PDF: {str(e)}")
            return None
    
    def _process_tables_advanced(self, tables) -> pd.DataFrame:
        """Procesamiento avanzado de tablas extraídas"""
        all_data = []
        
        for i, table in enumerate(tables):
            st.write(f"🔍 Procesando tabla {i+1}: {table.shape[0]} filas, {table.shape[1]} columnas")
            
            df = table.df
            
            # Filtrar solo filas que empiecen con FL (datos de Alsina Forms)
            fl_rows = df[df.iloc[:, 0].astype(str).str.contains('FL', na=False)]
            
            if len(fl_rows) > 0:
                st.write(f"✅ {len(fl_rows)} filas FL encontradas en tabla {i+1}")
                all_data.append(fl_rows)
        
        if not all_data:
            st.error("❌ No se encontraron filas con datos FL")
            return None
        
        # Combinar todas las tablas FL
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Limpiar y estandarizar
        return self._clean_and_standardize_advanced(combined_df)
    
    def _clean_and_standardize_advanced(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpieza y estandarización avanzada"""
        try:
            # Eliminar filas completamente vacías
            df = df.dropna(how='all').reset_index(drop=True)
            
            # Asignar nombres de columna estándar
            num_cols = len(df.columns)
            if num_cols >= len(self.expected_columns):
                df.columns = self.expected_columns[:num_cols]
            else:
                # Usar los nombres que tenemos y completar con genéricos
                column_names = self.expected_columns[:num_cols]
                df.columns = column_names
            
            # Limpiar tipos de datos
            df = self._clean_data_types_advanced(df)
            
            # Calcular métricas avanzadas
            df = self._calculate_advanced_metrics(df)
            
            st.success(f"✅ Datos procesados correctamente: {len(df)} registros válidos")
            return df
            
        except Exception as e:
            st.error(f"❌ Error limpiando datos: {str(e)}")
            return df
    
    def _clean_data_types_advanced(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpieza avanzada de tipos de datos"""
        # Limpiar fechas con manejo robusto de errores
        date_columns = ['Return_Date', 'Invoice_Start_Date', 'Invoice_End_Date', 'Counted_Date']
        for col in date_columns:
            if col in df.columns:
                # Convertir a datetime con manejo de errores
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Limpiar números con validación
        numeric_columns = ['Total_Tablets', 'Total_Open', 'Counting_Delay', 'Validation_Delay']
        for col in numeric_columns:
            if col in df.columns:
                # Convertir a numérico, rellenar NaN con 0
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Limpiar strings
        string_columns = ['Customer_Name', 'Job_Site_Name', 'WH_Code', 'Return_Packing_Slip']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        return df
    
    def _calculate_advanced_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular métricas avanzadas para análisis"""
        try:
            current_date = pd.Timestamp.now()
            
            # Inicializar columnas con valores por defecto si no existen
            if 'Days_Since_Return' not in df.columns:
                df['Days_Since_Return'] = 0
            
            # Días desde retorno
            if 'Return_Date' in df.columns:
                try:
                    df['Days_Since_Return'] = (current_date - df['Return_Date']).dt.days
                    df['Days_Since_Return'] = df['Days_Since_Return'].fillna(0)
                except Exception as e:
                    st.warning(f"⚠️ Error calculando días desde retorno: {str(e)}")
                    df['Days_Since_Return'] = 0
            
            # Asegurar que las columnas numéricas existen
            for col in ['Counting_Delay', 'Validation_Delay', 'Total_Open']:
                if col not in df.columns:
                    df[col] = 0
                else:
                    # Asegurar que son numéricas
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Score de prioridad mejorado
            df['Priority_Score'] = (
                pd.to_numeric(df['Days_Since_Return'], errors='coerce').fillna(0) * 0.4 +
                pd.to_numeric(df['Counting_Delay'], errors='coerce').fillna(0) * 0.3 +
                pd.to_numeric(df['Validation_Delay'], errors='coerce').fillna(0) * 0.2 +
                pd.to_numeric(df['Total_Open'], errors='coerce').fillna(0) * 0.1
            )
            
            # Asegurar que Priority_Score es numérico
            df['Priority_Score'] = pd.to_numeric(df['Priority_Score'], errors='coerce').fillna(0)
            
            # Niveles de prioridad más granulares
            try:
                df['Priority_Level'] = pd.cut(
                    df['Priority_Score'],
                    bins=[0, 10, 20, 35, float('inf')],
                    labels=['Baja', 'Media', 'Alta', 'Crítica'],
                    right=False
                ).astype(str)
            except Exception as e:
                st.warning(f"⚠️ Error asignando niveles de prioridad: {str(e)}")
                df['Priority_Level'] = 'Baja'
            
            # Categoría de urgencia visual
            try:
                df['Urgency_Category'] = '⚪ SIN DATOS'
                
                # Condiciones para urgencia
                urgent_mask = (df['Priority_Score'] >= 35) | (df['Days_Since_Return'] >= 30)
                attention_mask = (df['Priority_Score'] >= 20) | (df['Days_Since_Return'] >= 15)
                normal_mask = (df['Priority_Score'] >= 10) | (df['Days_Since_Return'] >= 7)
                
                df.loc[normal_mask, 'Urgency_Category'] = '🟢 NORMAL'
                df.loc[attention_mask, 'Urgency_Category'] = '🟡 ATENCIÓN'
                df.loc[urgent_mask, 'Urgency_Category'] = '🔴 URGENTE'
                
            except Exception as e:
                st.warning(f"⚠️ Error asignando categorías de urgencia: {str(e)}")
                df['Urgency_Category'] = '⚪ SIN DATOS'
            
            st.info(f"✅ Métricas calculadas correctamente. Priority_Score: min={df['Priority_Score'].min():.2f}, max={df['Priority_Score'].max():.2f}")
            return df
            
        except Exception as e:
            st.error(f"❌ Error general calculando métricas: {str(e)}")
            # En caso de error, asegurar que las columnas básicas existen
            if 'Priority_Score' not in df.columns:
                df['Priority_Score'] = 0
            if 'Priority_Level' not in df.columns:
                df['Priority_Level'] = 'Baja'
            if 'Urgency_Category' not in df.columns:
                df['Urgency_Category'] = '⚪ SIN DATOS'
            return df

def main():
    """Función principal de la aplicación"""
    # Header profesional
    st.markdown('''
    <div class="main-header">
        <h1>🏗️ SISTEMA PROFESIONAL DE CONTROL DE TABLILLAS</h1>
        <h2>Alsina Forms Co. - Análisis Diario por Excel</h2>
        <p>📄 PDF → Excel perfecto | 📊 Análisis multi-archivo | 🔄 Comparaciones automáticas</p>
        <div class="vercel-badge">🚀 Powered by Vercel</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Verificar dependencias
    if not CAMELOT_AVAILABLE:
        st.markdown("""
        <div class="alert-high">
        <h3>❌ Camelot no está disponible</h3>
        <p>Este entorno no soporta Camelot. Considera usar:</p>
        <ul>
            <li>🚀 <strong>Vercel</strong> - Soporte completo para Camelot</li>
            <li>🚂 <strong>Railway</strong> - Docker completo</li>
            <li>🎨 <strong>Render</strong> - Docker support</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    
    # Pestañas principales
    tab1, tab2 = st.tabs(["📄 PROCESAR PDF", "📊 ANÁLISIS MULTI-EXCEL"])
    
    with tab1:
        show_pdf_processing_tab()
    
    with tab2:
        show_excel_analysis_tab()

def show_pdf_processing_tab():
    """Pestaña para procesar PDF a Excel"""
    st.markdown('<div class="section-header">📄 PROCESAR PDF DIARIO</div>', 
                unsafe_allow_html=True)
    
    # Cargar PDF
    uploaded_file = st.file_uploader(
        "📂 Seleccionar archivo PDF",
        type=['pdf'],
        help="Sube el reporte de Outstanding Count Returns del día"
    )
    
    if uploaded_file is not None:
        st.markdown('<div class="file-info">📄 <strong>Procesando PDF...</strong></div>', 
                    unsafe_allow_html=True)
        
        # Extraer datos
        extractor = TablillasExtractorPro()
        df = extractor.extract_from_pdf(uploaded_file)
        
        if df is not None and not df.empty:
            st.markdown('<div class="success-box">✅ <strong>¡Extracción exitosa!</strong></div>', 
                        unsafe_allow_html=True)
            
            # Mostrar resumen de datos extraídos
            show_extraction_summary(df)
            
            # Mostrar datos principales
            show_main_data_table(df)
            
            # Generar Excel automático
            generate_daily_excel(df)
        else:
            show_extraction_error()

def show_extraction_summary(df: pd.DataFrame):
    """Mostrar resumen de extracción"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Total Albaranes", len(df))
    
    with col2:
        if 'Total_Open' in df.columns:
            total_open = int(pd.to_numeric(df['Total_Open'], errors='coerce').fillna(0).sum())
        else:
            total_open = 0
        st.metric("🔓 Tablillas Pendientes", total_open)
    
    with col3:
        if 'Counting_Delay' in df.columns:
            avg_delay = pd.to_numeric(df['Counting_Delay'], errors='coerce').fillna(0).mean()
        else:
            avg_delay = 0
        st.metric("⏱️ Retraso Promedio", f"{avg_delay:.1f} días")
    
    with col4:
        if 'Priority_Level' in df.columns:
            critical_items = len(df[df['Priority_Level'] == 'Crítica'])
        else:
            critical_items = 0
        st.metric("🚨 Items Críticos", critical_items)

def show_main_data_table(df: pd.DataFrame):
    """Mostrar tabla principal de datos"""
    st.subheader("📋 Datos Extraídos")
    
    # Seleccionar columnas principales para mostrar
    display_columns = [
        'Return_Packing_Slip', 'Return_Date', 'Customer_Name', 'Job_Site_Name',
        'WH_Code', 'Total_Tablets', 'Total_Open', 'Days_Since_Return', 
        'Priority_Level', 'Urgency_Category'
    ]
    
    available_columns = [col for col in display_columns if col in df.columns]
    
    if available_columns:
        # Mostrar datos ordenados por prioridad
        display_df = df[available_columns].copy()
        
        # Verificar qué columna usar para ordenar
        if 'Priority_Score' in df.columns:
            # Agregar Priority_Score a las columnas mostradas si existe
            if 'Priority_Score' not in available_columns:
                display_df['Priority_Score'] = df['Priority_Score']
            display_df = display_df.sort_values('Priority_Score', ascending=False)
        elif 'Days_Since_Return' in df.columns:
            display_df = display_df.sort_values('Days_Since_Return', ascending=False)
        elif 'Total_Open' in df.columns:
            display_df = display_df.sort_values('Total_Open', ascending=False)
        
        st.dataframe(display_df, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

def generate_daily_excel(df: pd.DataFrame):
    """Generar Excel diario automático"""
    st.subheader("💾 Generar Excel Diario")
    
    today = datetime.now().strftime('%Y%m%d_%H%M')
    default_filename = f"tablillas_{today}.xlsx"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        filename = st.text_input("📝 Nombre del archivo:", value=default_filename)
    
    with col2:
        if st.button("📥 Generar Excel", type="primary"):
            excel_data = create_comprehensive_excel(df)
            
            st.download_button(
                label="💾 Descargar Excel Completo",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.success(f"✅ Excel generado: **{filename}**")
            
            # Información para el usuario
            st.info("""
            💡 **Guarda este archivo localmente** con la fecha del día.
            Luego usa la pestaña "ANÁLISIS MULTI-EXCEL" para comparar múltiples días.
            """)

def create_comprehensive_excel(df: pd.DataFrame) -> bytes:
    """Crear Excel completo con múltiples hojas"""
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja 1: Datos completos
            df.to_excel(writer, sheet_name='Datos_Completos', index=False)
            
            # Hoja 2: Solo alta prioridad y críticos
            if 'Priority_Level' in df.columns:
                priority_df = df[df['Priority_Level'].isin(['Alta', 'Crítica'])]
                if not priority_df.empty:
                    priority_df.to_excel(writer, sheet_name='Alta_Prioridad', index=False)
            
            # Hoja 3: Resumen por almacén
            if 'WH_Code' in df.columns:
                wh_summary = df.groupby('WH_Code').agg({
                    'Total_Open': 'sum',
                    'Total_Tablets': 'sum',
                    'Counting_Delay': 'mean',
                    'Return_Packing_Slip': 'count'
                }).round(2)
                wh_summary.columns = ['Tablillas_Pendientes', 'Total_Tablillas', 'Retraso_Promedio', 'Num_Albaranes']
                wh_summary.to_excel(writer, sheet_name='Resumen_Almacenes')
            
            # Hoja 4: Métricas del día
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Calcular métricas de forma segura
            total_open = pd.to_numeric(df.get('Total_Open', pd.Series([0])), errors='coerce').fillna(0).sum()
            avg_delay = pd.to_numeric(df.get('Counting_Delay', pd.Series([0])), errors='coerce').fillna(0).mean()
            critical_count = len(df[df.get('Priority_Level', '') == 'Crítica']) if 'Priority_Level' in df.columns else 0
            high_count = len(df[df.get('Priority_Level', '') == 'Alta']) if 'Priority_Level' in df.columns else 0
            unique_wh = df.get('WH_Code', pd.Series([''])).nunique() if 'WH_Code' in df.columns else 0
            avg_score = pd.to_numeric(df.get('Priority_Score', pd.Series([0])), errors='coerce').fillna(0).mean()
            
            metrics_data = {
                'Métrica': [
                    'Fecha Procesamiento',
                    'Total Albaranes',
                    'Tablillas Pendientes',
                    'Retraso Promedio',
                    'Items Críticos',
                    'Items Alta Prioridad',
                    'Almacenes Activos',
                    'Score Promedio'
                ],
                'Valor': [
                    today,
                    len(df),
                    int(total_open),
                    f"{avg_delay:.1f}",
                    critical_count,
                    high_count,
                    unique_wh,
                    f"{avg_score:.2f}"
                ]
            }
            metrics_df = pd.DataFrame(metrics_data)
            metrics_df.to_excel(writer, sheet_name='Métricas_Día', index=False)
        
        return output.getvalue()
        
    except Exception as e:
        st.error(f"❌ Error generando Excel: {str(e)}")
        return b''

def show_excel_analysis_tab():
    """Pestaña para análisis multi-Excel"""
    st.markdown('<div class="section-header">📊 ANÁLISIS MULTI-EXCEL</div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    ### 🔄 Cargar múltiples archivos Excel para análisis comparativo
    
    Sube **2 o más archivos Excel** generados en días diferentes para:
    - 📈 Ver tendencias y evolución
    - 🔄 Detectar cambios día a día  
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
    elif uploaded_excel_files and len(uploaded_excel_files) == 1:
        st.warning("⚠️ Se necesitan al menos 2 archivos para hacer comparación")
    else:
        st.info("📂 Selecciona múltiples archivos Excel para comenzar el análisis")

def show_extraction_error():
    """Mostrar error de extracción con soluciones"""
    st.markdown("""
    <div class="alert-high">
    <h3>❌ No se pudieron extraer datos</h3>
    <p><strong>Posibles soluciones:</strong></p>
    <ul>
        <li>✅ Verificar que el PDF contenga tablas estructuradas</li>
        <li>🔐 Asegurar que el archivo no esté protegido con contraseña</li>
        <li>📄 Confirmar que el formato sea el esperado de Alsina Forms</li>
        <li>🔄 Intentar con un archivo PDF de ejemplo conocido</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()