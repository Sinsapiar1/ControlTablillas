"""
Aplicación simple y rápida usando solo pdfplumber
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import io
from datetime import datetime, timedelta
import re
import numpy as np
from simple_parser import SimpleAlsinaParser

# Configuración de la página
st.set_page_config(
    page_title="Control de Tablillas - Alsina Forms (Simple)",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79, #2e86c1);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem;
    }
    
    .priority-high { color: #dc3545; font-weight: bold; }
    .priority-medium { color: #fd7e14; font-weight: bold; }
    .priority-low { color: #28a745; font-weight: bold; }
    
    .alert-success { background: #d4edda; padding: 0.75rem; border-radius: 0.375rem; }
    .alert-warning { background: #fff3cd; padding: 0.75rem; border-radius: 0.375rem; }
    .alert-danger { background: #f8d7da; padding: 0.75rem; border-radius: 0.375rem; }
    
    .parser-info {
        background: #e8f5e8;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .simple-badge {
        background: #007bff;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        margin: 0.1rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

class SimpleTablillasController:
    """Controlador simple y rápido"""
    
    def __init__(self):
        self.data_file = "tablillas_history.json"
        self.config_file = "config.json"
        self.pdf_parser = SimpleAlsinaParser()
        self.load_history()
        self.load_config()
    
    def load_config(self):
        """Cargar configuración desde JSON"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = self._create_default_config()
            self.save_config()
    
    def _create_default_config(self):
        """Crear configuración por defecto"""
        return {
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
            }
        }
    
    def save_config(self):
        """Guardar configuración en JSON"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def load_history(self):
        """Cargar historial desde JSON"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
        except FileNotFoundError:
            self.history = {"reports": [], "summary": {}}
    
    def save_history(self):
        """Guardar historial en JSON"""
        history_to_save = self._prepare_for_json(self.history)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(history_to_save, f, ensure_ascii=False, indent=2)
    
    def _prepare_for_json(self, data):
        """Preparar datos para serialización JSON"""
        if isinstance(data, dict):
            return {key: self._prepare_for_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._prepare_for_json(item) for item in data]
        elif hasattr(data, 'isoformat'):
            return data.isoformat()
        elif pd.isna(data):
            return None
        else:
            return data
    
    def extract_pdf_data(self, pdf_file):
        """Extraer datos del PDF usando parser simple"""
        try:
            return self.pdf_parser.parse_pdf_file(pdf_file)
                
        except Exception as e:
            st.error(f"Error al procesar PDF: {str(e)}")
            return None
    
    def calculate_priorities(self, df):
        """Calcular prioridades basadas en fechas y delays"""
        if df is None or df.empty:
            return df
            
        df = df.copy()
        current_date = pd.Timestamp.now()
        
        # Asegurar que Return_Date sea datetime
        if 'Return_Date' in df.columns:
            df['Return_Date'] = pd.to_datetime(df['Return_Date'], errors='coerce')
            df['Days_Since_Return'] = (current_date - df['Return_Date']).dt.days
            df['Days_Since_Return'] = df['Days_Since_Return'].fillna(0)
        else:
            df['Days_Since_Return'] = 0
        
        # Asegurar valores numéricos
        numeric_cols = ['Counting_Delay', 'Validation_Delay', 'Total_Open', 'Total_Tablets']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
        
        # Calcular score de prioridad
        weights = self.config.get('priority_weights', {
            'days_since_return': 0.4,
            'counting_delay': 0.3,
            'validation_delay': 0.2,
            'open_tablets': 0.1
        })
        
        df['Priority_Score'] = (
            df['Days_Since_Return'] * weights['days_since_return'] +
            df['Counting_Delay'] * weights['counting_delay'] +
            df['Validation_Delay'] * weights['validation_delay'] +
            df['Total_Open'] * weights['open_tablets']
        )
        
        # Asignar nivel de prioridad
        thresholds = self.config.get('alert_thresholds', {
            'high_priority_days': 25,
            'warning_delay_days': 15
        })
        
        df['Priority_Level'] = pd.cut(
            df['Priority_Score'],
            bins=[0, thresholds['warning_delay_days'], thresholds['high_priority_days'], float('inf')],
            labels=['Baja', 'Media', 'Alta'],
            right=False
        )
        
        return df.sort_values('Priority_Score', ascending=False)

def main():
    st.markdown('<div class="main-header"><h1>⚡ Control de Tablillas - Alsina Forms (Simple)</h1></div>', 
                unsafe_allow_html=True)
    
    # Información sobre el parser simple
    st.markdown("""
    <div class="parser-info">
    <h4>⚡ <strong>Parser Simple Activo</strong></h4>
    <p>Esta versión usa solo pdfplumber para extracción rápida y confiable:</p>
    <div>
        <span class="simple-badge">pdfplumber</span>
        <span class="simple-badge">Rápido</span>
        <span class="simple-badge">Confiable</span>
        <span class="simple-badge">Simple</span>
    </div>
    <p><strong>Características:</strong></p>
    <ul>
        <li>✅ <strong>Extracción rápida</strong> usando solo pdfplumber</li>
        <li>✅ <strong>Sin dependencias complejas</strong> - funciona inmediatamente</li>
        <li>✅ <strong>Procesamiento simple</strong> de líneas que empiezan con 'FL'</li>
        <li>✅ <strong>Detección automática</strong> de fechas y números</li>
        <li>✅ <strong>Interfaz limpia</strong> y fácil de usar</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    controller = SimpleTablillasController()
    
    # Sidebar
    st.sidebar.header("📂 Carga de Datos")
    
    # Upload PDF
    uploaded_file = st.sidebar.file_uploader(
        "Cargar Informe PDF",
        type=['pdf'],
        help="Sube el informe de devoluciones en formato PDF"
    )
    
    # Navigation
    st.sidebar.header("📊 Navegación")
    page = st.sidebar.selectbox(
        "Seleccionar Vista",
        ["Dashboard Principal", "Análisis Detallado", "Verificación de Datos"]
    )
    
    if uploaded_file is not None:
        # Procesar PDF
        with st.spinner("⚡ Procesando PDF..."):
            df = controller.extract_pdf_data(uploaded_file)
        
        if df is not None and not df.empty:
            # Calcular prioridades
            df_prioritized = controller.calculate_priorities(df)
            
            # Guardar en historial
            try:
                report_data = {
                    'date': datetime.now().isoformat(),
                    'total_records': len(df),
                    'warehouses': [str(wh) for wh in df['WH_Code'].unique() if not pd.isna(wh)],
                    'data': df_prioritized.head(50).to_dict('records')
                }
                controller.history['reports'].append(report_data)
                controller.save_history()
            except Exception as e:
                st.warning(f"⚠️ Datos procesados, historial no guardado: {str(e)}")
            
            # Mostrar contenido según la página
            if page == "Dashboard Principal":
                show_main_dashboard(df_prioritized, controller)
            elif page == "Análisis Detallado":
                show_detailed_analysis(df_prioritized)
            elif page == "Verificación de Datos":
                show_data_verification(df_prioritized)
        else:
            st.error("❌ No se pudieron extraer datos válidos del PDF")
            st.info("💡 Verifica que el PDF contenga líneas que empiecen con 'FL'")
    else:
        st.info("👆 Sube un archivo PDF para comenzar el análisis")

def show_main_dashboard(df, controller):
    """Mostrar dashboard principal"""
    st.header("🎯 Dashboard Principal")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Devoluciones", len(df), f"+{len(df)} nuevas")
    
    with col2:
        total_open = int(df['Total_Open'].sum()) if 'Total_Open' in df.columns else 0
        high_priority = len(df[df['Priority_Level'] == 'Alta']) if 'Priority_Level' in df.columns else 0
        st.metric("Tablillas Pendientes", total_open, f"⚠️ {high_priority} alta prioridad")
    
    with col3:
        avg_delay = df['Counting_Delay'].mean() if 'Counting_Delay' in df.columns else 0
        st.metric("Retraso Promedio (días)", f"{avg_delay:.1f}", "📊 Crítico si >15")
    
    with col4:
        warehouses = df['WH_Code'].nunique() if 'WH_Code' in df.columns else 0
        st.metric("Almacenes Activos", warehouses, f"🏢 {warehouses} ubicaciones")
    
    # Gráficos
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Prioridades por Almacén")
        if 'WH_Code' in df.columns and 'Priority_Level' in df.columns:
            priority_data = df.groupby(['WH_Code', 'Priority_Level']).size().reset_index(name='count')
            
            if not priority_data.empty:
                fig = px.bar(
                    priority_data,
                    x='WH_Code',
                    y='count',
                    color='Priority_Level',
                    color_discrete_map={'Alta': '#dc3545', 'Media': '#fd7e14', 'Baja': '#28a745'},
                    title="Distribución de Prioridades"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.subheader("📅 Devoluciones por Fecha")
        if 'Return_Date' in df.columns:
            timeline = df.groupby('Return_Date').size().reset_index(name='count')
            fig = px.line(timeline, x='Return_Date', y='count', markers=True)
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de alta prioridad
    st.subheader("🚨 Devoluciones de Alta Prioridad")
    if 'Priority_Level' in df.columns:
        high_priority = df[df['Priority_Level'] == 'Alta'].head(10)
        
        if not high_priority.empty:
            display_cols = ['WH_Code', 'Return_Date', 'Customer_Name', 'Job_Site_Name',
                           'Total_Open', 'Days_Since_Return', 'Counting_Delay']
            available_cols = [col for col in display_cols if col in high_priority.columns]
            st.dataframe(high_priority[available_cols], use_container_width=True)
        else:
            st.success("✅ No hay devoluciones de alta prioridad")
    
    # Botón de descarga
    current_date = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"tablillas_simple_{current_date}.xlsx"
    
    if st.button("📥 Descargar Reporte Excel", type="primary"):
        download_excel(df, filename)

def show_detailed_analysis(df):
    """Mostrar análisis detallado"""
    st.header("🔍 Análisis Detallado")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'WH_Code' in df.columns:
            warehouses = [wh for wh in df['WH_Code'].unique() if not pd.isna(wh)]
            warehouse_filter = st.multiselect("Filtrar por Almacén", options=warehouses, default=warehouses)
        else:
            warehouse_filter = []
    
    with col2:
        if 'Priority_Level' in df.columns:
            priority_filter = st.multiselect("Filtrar por Prioridad", 
                                           options=['Alta', 'Media', 'Baja'], 
                                           default=['Alta', 'Media', 'Baja'])
        else:
            priority_filter = []
    
    with col3:
        if 'Return_Date' in df.columns and not df['Return_Date'].isna().all():
            min_date = df['Return_Date'].min().date()
            max_date = df['Return_Date'].max().date()
            date_range = st.date_input("Rango de Fechas", value=(min_date, max_date))
    
    # Aplicar filtros
    filtered_df = df.copy()
    
    if warehouse_filter and 'WH_Code' in df.columns:
        filtered_df = filtered_df[filtered_df['WH_Code'].isin(warehouse_filter)]
    
    if priority_filter and 'Priority_Level' in df.columns:
        filtered_df = filtered_df[filtered_df['Priority_Level'].isin(priority_filter)]
    
    st.subheader(f"📋 Resultados Filtrados ({len(filtered_df)} registros)")
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)

def show_data_verification(df):
    """Mostrar verificación de datos extraídos"""
    st.header("🔍 Verificación de Datos Extraídos")
    
    st.markdown("""
    <div class="alert-success">
    <strong>✅ Verificación de Extracción Simple</strong><br>
    Revisa los datos extraídos para asegurar que la información sea correcta.
    </div>
    """, unsafe_allow_html=True)
    
    # Estadísticas de extracción
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Registros", len(df))
    
    with col2:
        complete_records = len(df.dropna(subset=['Customer_Name', 'Return_Packing_Slip']))
        st.metric("Registros Completos", complete_records, f"{complete_records/len(df)*100:.1f}%")
    
    with col3:
        if 'Definitive_Dev' in df.columns:
            definitive_count = len(df[df['Definitive_Dev'] == 'Yes'])
            st.metric("Devoluciones Definitivas", definitive_count)
    
    # Mostrar muestra de datos
    st.subheader("📋 Muestra de Datos Extraídos")
    
    # Seleccionar columnas importantes para mostrar
    important_cols = [
        'WH_Code', 'Return_Packing_Slip', 'Return_Date', 'Customer_Name', 
        'Job_Site_Name', 'Definitive_Dev', 'Counted_Date', 'Tablets', 
        'Total_Tablets', 'Open_Tablets', 'Total_Open', 'Counting_Delay', 'Validation_Delay'
    ]
    
    available_cols = [col for col in important_cols if col in df.columns]
    
    if available_cols:
        st.dataframe(df[available_cols].head(20), use_container_width=True)
        
        # Mostrar estadísticas por columna
        st.subheader("📊 Estadísticas por Campo")
        
        for col in available_cols:
            if col in df.columns:
                with st.expander(f"📈 {col}"):
                    if df[col].dtype == 'object':
                        # Campo de texto
                        unique_count = df[col].nunique()
                        null_count = df[col].isnull().sum()
                        st.write(f"**Valores únicos:** {unique_count}")
                        st.write(f"**Valores nulos:** {null_count}")
                        
                        # Mostrar valores más comunes
                        if unique_count > 0:
                            top_values = df[col].value_counts().head(10)
                            st.write("**Valores más comunes:**")
                            st.write(top_values)
                    else:
                        # Campo numérico
                        st.write(f"**Promedio:** {df[col].mean():.2f}")
                        st.write(f"**Mínimo:** {df[col].min()}")
                        st.write(f"**Máximo:** {df[col].max()}")
                        st.write(f"**Valores nulos:** {df[col].isnull().sum()}")
    else:
        st.warning("⚠️ No se encontraron columnas esperadas en los datos")

def download_excel(df, filename):
    """Generar archivo Excel con formato mejorado"""
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Hoja principal con todos los datos
            df.to_excel(writer, sheet_name='Devoluciones', index=False)
            
            # Hoja de resumen por almacén
            if not df.empty and 'WH_Code' in df.columns:
                summary = df.groupby('WH_Code').agg({
                    'Total_Open': 'sum' if 'Total_Open' in df.columns else lambda x: 0,
                    'Total_Tablets': 'sum' if 'Total_Tablets' in df.columns else lambda x: 0,
                    'Counting_Delay': 'mean' if 'Counting_Delay' in df.columns else lambda x: 0,
                    'Priority_Score': 'mean' if 'Priority_Score' in df.columns else lambda x: 0,
                    'Return_Packing_Slip': 'nunique'
                }).round(2)
                summary.columns = ['Tablillas_Abiertas', 'Total_Tablillas', 'Retraso_Promedio', 'Score_Prioridad', 'Num_Devoluciones']
                summary.to_excel(writer, sheet_name='Resumen_Almacenes')
                
                # Hoja de alta prioridad
                if 'Priority_Level' in df.columns:
                    high_priority = df[df['Priority_Level'] == 'Alta']
                    if not high_priority.empty:
                        high_priority.to_excel(writer, sheet_name='Alta_Prioridad', index=False)
                
                # Hoja de tablillas estancadas (más de 15 días)
                if 'Days_Since_Return' in df.columns:
                    stagnant = df[df['Days_Since_Return'] > 15]
                    if not stagnant.empty:
                        stagnant.to_excel(writer, sheet_name='Estancadas', index=False)
        
        # Botón de descarga
        st.download_button(
            label="📥 Descargar Excel Completo",
            data=output.getvalue(),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Archivo Excel con múltiples hojas para análisis completo"
        )
        
        st.success(f"✅ Excel generado: **{filename}**")
        
    except Exception as e:
        st.error(f"Error generando Excel: {str(e)}")

if __name__ == "__main__":
    main()