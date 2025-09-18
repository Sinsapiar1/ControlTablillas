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
except ImportError:
    CAMELOT_AVAILABLE = False

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
</style>
""", unsafe_allow_html=True)

class ExcelAnalyzer:
    """Analizador de múltiples archivos Excel para comparación"""
    
    def __init__(self, excel_folder: str = "excel_exports"):
        self.excel_folder = excel_folder
        self.ensure_folder_exists()
    
    def ensure_folder_exists(self):
        """Crear carpeta de Excel si no existe"""
        if not os.path.exists(self.excel_folder):
            os.makedirs(self.excel_folder)
    
    def load_excel_files(self, file_paths: List[str]) -> Dict[str, pd.DataFrame]:
        """Cargar múltiples archivos Excel"""
        excel_data = {}
        
        for file_path in file_paths:
            try:
                # Leer Excel
                df = pd.read_excel(file_path)
                
                # Extraer fecha del nombre del archivo o usar fecha de modificación
                file_name = os.path.basename(file_path)
                
                # Intentar extraer fecha del nombre (formato: tablillas_YYYYMMDD_HHMM.xlsx)
                date_match = re.search(r'(\d{8})_(\d{4})', file_name)
                if date_match:
                    date_str = date_match.group(1)
                    file_date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
                else:
                    # Usar fecha de modificación del archivo
                    mod_time = os.path.getmtime(file_path)
                    file_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')
                
                excel_data[file_date] = df
                
            except Exception as e:
                st.error(f"❌ Error cargando {file_path}: {str(e)}")
        
        return excel_data
    
    def compare_excel_files(self, excel_data: Dict[str, pd.DataFrame]) -> Dict:
        """Comparar datos entre archivos Excel"""
        if len(excel_data) < 2:
            return {"error": "Se necesitan al menos 2 archivos para comparar"}
        
        # Ordenar por fecha
        sorted_dates = sorted(excel_data.keys())
        
        comparisons = []
        
        for i in range(1, len(sorted_dates)):
            current_date = sorted_dates[i]
            previous_date = sorted_dates[i-1]
            
            current_df = excel_data[current_date]
            previous_df = excel_data[previous_date]
            
            comparison = self.compare_two_dataframes(
                current_df, previous_df, current_date, previous_date
            )
            comparisons.append(comparison)
        
        # Resumen general
        summary = self.create_comparison_summary(comparisons, excel_data)
        
        return {
            "comparisons": comparisons,
            "summary": summary,
            "dates": sorted_dates
        }
    
    def compare_two_dataframes(self, current_df: pd.DataFrame, previous_df: pd.DataFrame, 
                              current_date: str, previous_date: str) -> Dict:
        """Comparar dos DataFrames específicos"""
        
        # Normalizar nombres de columnas para la comparación
        current_df = self.normalize_dataframe(current_df)
        previous_df = self.normalize_dataframe(previous_df)
        
        # Albaranes actuales y anteriores
        current_albaranes = set(current_df['Return_Packing_Slip'].astype(str))
        previous_albaranes = set(previous_df['Return_Packing_Slip'].astype(str))
        
        # Calcular cambios
        new_albaranes = current_albaranes - previous_albaranes
        closed_albaranes = previous_albaranes - current_albaranes
        continuing_albaranes = current_albaranes.intersection(previous_albaranes)
        
        # Análisis detallado de cambios en albaranes
        closed_tablets = 0
        added_tablets = 0
        changed_albaranes = []
        
        for albaran in continuing_albaranes:
            current_row = current_df[current_df['Return_Packing_Slip'].astype(str) == albaran]
            previous_row = previous_df[previous_df['Return_Packing_Slip'].astype(str) == albaran]
            
            if not current_row.empty and not previous_row.empty:
                # Datos actuales
                current_open = pd.to_numeric(current_row.iloc[0].get('Total_Open', 0), errors='coerce') or 0
                current_total = pd.to_numeric(current_row.iloc[0].get('Total_Tablets', 0), errors='coerce') or 0
                current_tablets_list = str(current_row.iloc[0].get('Tablets', ''))
                
                # Datos anteriores  
                previous_open = pd.to_numeric(previous_row.iloc[0].get('Total_Open', 0), errors='coerce') or 0
                previous_total = pd.to_numeric(previous_row.iloc[0].get('Total_Tablets', 0), errors='coerce') or 0
                previous_tablets_list = str(previous_row.iloc[0].get('Tablets', ''))
                
                # Análisis de cambios
                change_info = {
                    'albaran': albaran,
                    'customer': current_row.iloc[0].get('Customer_Name', 'N/A'),
                    'previous_open': previous_open,
                    'current_open': current_open,
                    'previous_total': previous_total,
                    'current_total': current_total,
                    'changes': []
                }
                
                # 1. Detectar tablillas cerradas (reducción en Open)
                if previous_open > current_open:
                    tablets_closed_count = previous_open - current_open
                    closed_tablets += tablets_closed_count
                    change_info['changes'].append(f"🔒 {tablets_closed_count} tablillas cerradas")
                
                # 2. Detectar tablillas agregadas (aumento en Total)
                if current_total > previous_total:
                    tablets_added_count = current_total - previous_total
                    added_tablets += tablets_added_count
                    change_info['changes'].append(f"➕ {tablets_added_count} tablillas agregadas")
                
                # 3. Detectar cambios en lista de tablillas
                if current_tablets_list != previous_tablets_list and current_tablets_list and previous_tablets_list:
                    change_info['changes'].append(f"📝 Lista de tablillas modificada")
                    change_info['previous_tablets'] = previous_tablets_list
                    change_info['current_tablets'] = current_tablets_list
                
                # Solo agregar si hay cambios
                if change_info['changes']:
                    changed_albaranes.append(change_info)
        
        return {
            'current_date': current_date,
            'previous_date': previous_date,
            'new_albaranes': len(new_albaranes),
            'closed_albaranes': len(closed_albaranes),
            'closed_tablets': closed_tablets,
            'added_tablets': added_tablets,  # NUEVO
            'new_albaranes_list': list(new_albaranes),
            'closed_albaranes_list': list(closed_albaranes),
            'changed_albaranes': changed_albaranes,
            'current_total_open': current_df['Total_Open'].sum() if 'Total_Open' in current_df.columns else 0,
            'previous_total_open': previous_df['Total_Open'].sum() if 'Total_Open' in previous_df.columns else 0,
            'current_total_albaranes': len(current_df),
            'previous_total_albaranes': len(previous_df),
            'albaranes_with_added_tablets': len([c for c in changed_albaranes if any('agregadas' in change for change in c['changes'])])  # NUEVO
        }
    
    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalizar DataFrame para comparación"""
        # Asegurar que las columnas principales existen
        required_columns = ['Return_Packing_Slip', 'Total_Open', 'Customer_Name']
        
        for col in required_columns:
            if col not in df.columns:
                # Buscar columnas similares
                similar_cols = [c for c in df.columns if col.lower() in c.lower() or c.lower() in col.lower()]
                if similar_cols:
                    df[col] = df[similar_cols[0]]
                else:
                    df[col] = 0 if 'Total' in col else 'N/A'
        
        return df
    
    def create_comparison_summary(self, comparisons: List[Dict], excel_data: Dict[str, pd.DataFrame]) -> Dict:
        """Crear resumen de todas las comparaciones"""
        if not comparisons:
            return {}
        
        total_new_albaranes = sum(c['new_albaranes'] for c in comparisons)
        total_closed_albaranes = sum(c['closed_albaranes'] for c in comparisons)
        total_closed_tablets = sum(c['closed_tablets'] for c in comparisons)
        total_added_tablets = sum(c.get('added_tablets', 0) for c in comparisons)  # NUEVO
        
        # Análisis de tendencias
        dates = sorted(excel_data.keys())
        
        # Evolución de tablillas pendientes
        open_evolution = []
        for date in dates:
            df = excel_data[date]
            if 'Total_Open' in df.columns:
                total_open = pd.to_numeric(df['Total_Open'], errors='coerce').fillna(0).sum()
            else:
                total_open = 0
            open_evolution.append({'date': date, 'total_open': total_open})
        
        return {
            'total_new_albaranes': total_new_albaranes,
            'total_closed_albaranes': total_closed_albaranes,
            'total_closed_tablets': total_closed_tablets,
            'total_added_tablets': total_added_tablets,  # NUEVO
            'analysis_period': f"{dates[0]} a {dates[-1]}" if len(dates) >= 2 else dates[0],
            'open_evolution': open_evolution,
            'num_files_analyzed': len(excel_data),
            'most_recent_date': dates[-1] if dates else None,
            'oldest_date': dates[0] if dates else None
        }

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
        self.analyzer = ExcelAnalyzer()
    
    def extract_from_pdf(self, uploaded_file) -> Optional[pd.DataFrame]:
        """Extrae datos usando Camelot (método original perfeccionado)"""
        if not CAMELOT_AVAILABLE:
            st.error("⚠️ Camelot no está instalado. Ejecuta: pip install camelot-py[cv]")
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
            
            if 'Slip_Age_Rank' not in df.columns:
                df['Slip_Age_Rank'] = 0
            
            # Días desde retorno
            if 'Return_Date' in df.columns:
                try:
                    df['Days_Since_Return'] = (current_date - df['Return_Date']).dt.days
                    df['Days_Since_Return'] = df['Days_Since_Return'].fillna(0)
                except Exception as e:
                    st.warning(f"⚠️ Error calculando días desde retorno: {str(e)}")
                    df['Days_Since_Return'] = 0
            
            # Antigüedad del albarán basada en número correlativo
            if 'Return_Packing_Slip' in df.columns:
                try:
                    # Extraer números del albarán para determinar antigüedad
                    df['Slip_Number'] = df['Return_Packing_Slip'].str.extract(r'(\d+)', expand=False).astype(float)
                    max_slip = df['Slip_Number'].max()
                    if pd.notna(max_slip) and max_slip > 0:
                        df['Slip_Age_Rank'] = (max_slip - df['Slip_Number']) / max_slip * 100
                    else:
                        df['Slip_Age_Rank'] = 0
                except Exception as e:
                    st.warning(f"⚠️ Error calculando antigüedad de albarán: {str(e)}")
                    df['Slip_Age_Rank'] = 0
            
            # Asegurar que las columnas numéricas existen
            for col in ['Counting_Delay', 'Validation_Delay', 'Total_Open']:
                if col not in df.columns:
                    df[col] = 0
                else:
                    # Asegurar que son numéricas
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Score de prioridad mejorado
            df['Priority_Score'] = (
                pd.to_numeric(df['Days_Since_Return'], errors='coerce').fillna(0) * 0.3 +
                pd.to_numeric(df['Counting_Delay'], errors='coerce').fillna(0) * 0.25 +
                pd.to_numeric(df['Validation_Delay'], errors='coerce').fillna(0) * 0.2 +
                pd.to_numeric(df['Total_Open'], errors='coerce').fillna(0) * 0.15 +
                pd.to_numeric(df['Slip_Age_Rank'], errors='coerce').fillna(0) * 0.1
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
    
    # Sidebar con opciones
    st.sidebar.header("⚙️ OPCIONES")
    
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
        # Procesar archivos Excel
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

if __name__ == "__main__":
    main()