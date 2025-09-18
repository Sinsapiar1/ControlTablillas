import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime, timedelta
import tempfile
import os
from typing import Dict, List

def main():
    """Función principal de la aplicación"""
    # Header profesional
    st.markdown('''
    <div class="main-header">
        <h1>🏗️ SISTEMA PROFESIONAL DE CONTROL DE TABLILLAS</h1>
        <h2>Alsina Forms Co. - Análisis Diario por Excel</h2>
        <p>📄 PDF → Excel perfecto | 📊 Análisis multi-archivo | 🔄 Comparaciones automáticas</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Verificar dependencias
    if not CAMELOT_AVAILABLE:
        st.markdown("""
        <div class="alert-high">
        <h3>❌ Camelot no está instalado</h3>
        <p>Para instalar las dependencias necesarias:</p>
        <code>pip install camelot-py[cv]</code><br>
        <code>pip install opencv-python</code>
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
        from app import TablillasExtractorPro
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
        # Procesar archivos Excel
        from app import ExcelAnalyzer
        analyzer = ExcelAnalyzer()
        
        # Guardar archivos temporalmente y cargarlos
        temp_files = []
        for uploaded_file in uploaded_excel_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(uploaded_file.read())
                temp_files.append(tmp_file.name)
        
        # Cargar datos de Excel
        excel_data = analyzer.load_excel_files(temp_files)
        
        # Limpiar archivos temporales
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        
        if len(excel_data) >= 2:
            st.success(f"✅ {len(excel_data)} archivos cargados correctamente")
            
            # Realizar análisis comparativo
            analysis_results = analyzer.compare_excel_files(excel_data)
            
            if "error" not in analysis_results:
                show_comparative_analysis(analysis_results, excel_data)
            else:
                st.error(analysis_results["error"])
        else:
            st.error("❌ No se pudieron cargar suficientes archivos válidos")
    
    elif uploaded_excel_files and len(uploaded_excel_files) == 1:
        st.warning("⚠️ Se necesitan al menos 2 archivos para hacer comparación")
    
    else:
        st.info("📂 Selecciona múltiples archivos Excel para comenzar el análisis")

def show_comparative_analysis(analysis_results: Dict, excel_data: Dict[str, pd.DataFrame]):
    """Mostrar análisis comparativo completo"""
    
    # Resumen general
    show_analysis_summary(analysis_results["summary"])
    
    # Evolución temporal
    show_temporal_evolution(analysis_results["summary"]["open_evolution"])
    
    # Comparaciones día a día
    show_daily_comparisons(analysis_results["comparisons"])

def show_analysis_summary(summary: Dict):
    """Mostrar resumen del análisis"""
    st.markdown('<div class="section-header">📊 RESUMEN DEL ANÁLISIS</div>', 
                unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📁 Archivos Analizados", summary.get('num_files_analyzed', 0))
    
    with col2:
        st.metric("🆕 Nuevos Albaranes", summary.get('total_new_albaranes', 0))
    
    with col3:
        st.metric("🔒 Tablillas Cerradas", summary.get('total_closed_tablets', 0))
    
    with col4:
        st.metric("➕ Tablillas Agregadas", summary.get('total_added_tablets', 0))
    
    with col5:
        st.metric("📅 Período", summary.get('analysis_period', 'N/A'))

def show_temporal_evolution(open_evolution: List[Dict]):
    """Mostrar evolución temporal"""
    st.subheader("📈 Evolución de Tablillas Pendientes")
    
    if open_evolution:
        df_evolution = pd.DataFrame(open_evolution)
        df_evolution['date'] = pd.to_datetime(df_evolution['date'])
        
        fig = px.line(
            df_evolution,
            x='date',
            y='total_open',
            title='Evolución Diaria de Tablillas Pendientes',
            markers=True,
            color_discrete_sequence=['#dc3545']
        )
        
        fig.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Tablillas Pendientes",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_daily_comparisons(comparisons: List[Dict]):
    """Mostrar comparaciones día a día"""
    st.markdown('<div class="section-header">🔄 CAMBIOS DÍA A DÍA</div>', 
                unsafe_allow_html=True)
    
    for i, comparison in enumerate(comparisons):
        st.subheader(f"📅 {comparison['previous_date']} → {comparison['current_date']}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'''
            <div class="comparison-box">
            <h4>📈 Nuevos Albaranes</h4>
            <h2>{comparison['new_albaranes']}</h2>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'''
            <div class="comparison-box">
            <h4>✅ Albaranes Cerrados</h4>
            <h2>{comparison['closed_albaranes']}</h2>
            </div>
            ''', unsafe_allow_html=True)
        
        with col3:
            st.markdown(f'''
            <div class="comparison-box">
            <h4>🔒 Tablillas Cerradas</h4>
            <h2>{comparison['closed_tablets']}</h2>
            </div>
            ''', unsafe_allow_html=True)
        
        with col4:
            st.markdown(f'''
            <div class="comparison-box">
            <h4>➕ Tablillas Agregadas</h4>
            <h2>{comparison.get('added_tablets', 0)}</h2>
            <small>{comparison.get('albaranes_with_added_tablets', 0)} albaranes</small>
            </div>
            ''', unsafe_allow_html=True)

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