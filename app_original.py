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
import time
import signal

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
    /* Evitar problemas de transparencia después de descargas */
    .stApp {
        opacity: 1 !important;
        background-color: #ffffff !important;
    }
    
    .stApp > div {
        opacity: 1 !important;
    }
    
    /* Forzar visibilidad de todos los elementos */
    .main .block-container {
        opacity: 1 !important;
        background-color: #ffffff !important;
    }
    
    /* Evitar transparencia en elementos específicos */
    .stMarkdown, .stButton, .stDownloadButton {
        opacity: 1 !important;
    }
    
    /* Forzar visibilidad del contenido principal */
    .stApp > div > div > div {
        opacity: 1 !important;
    }
    
    /* JavaScript para forzar visibilidad */
    .stApp {
        visibility: visible !important;
    }
    
    /* Evitar que elementos se oculten */
    .stApp * {
        visibility: visible !important;
    }
    
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
        """Comparar datos entre archivos Excel - VERSIÓN MEJORADA"""
        if len(excel_data) < 2:
            return {"error": "Se necesitan al menos 2 archivos para comparar"}
        
        try:
            # Ordenar por fecha
            sorted_dates = sorted(excel_data.keys())
            st.write(f"📊 Analizando fechas: {sorted_dates}")
            
            comparisons = []
            
            for i in range(1, len(sorted_dates)):
                current_date = sorted_dates[i]
                previous_date = sorted_dates[i-1]
                
                current_df = excel_data[current_date]
                previous_df = excel_data[previous_date]
                
                st.write(f"🔍 Comparando {previous_date} ({len(previous_df)} filas) vs {current_date} ({len(current_df)} filas)")
                
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
            
        except Exception as e:
            st.error(f"❌ Error en análisis comparativo: {str(e)}")
            return {"error": f"Error en análisis: {str(e)}"}
    
    def compare_two_dataframes(self, current_df: pd.DataFrame, previous_df: pd.DataFrame, 
                              current_date: str, previous_date: str) -> Dict:
        """Comparar dos DataFrames específicos - VERSIÓN ROBUSTA"""
        
        try:
            # Normalizar nombres de columnas para la comparación
            current_df = self.normalize_dataframe(current_df)
            previous_df = self.normalize_dataframe(previous_df)
            
            # Verificar que tenemos las columnas necesarias
            if 'Return_Packing_Slip' not in current_df.columns:
                st.warning(f"⚠️ {current_date}: No se encontró columna Return_Packing_Slip")
                return self._create_empty_comparison(current_date, previous_date)
            
            if 'Return_Packing_Slip' not in previous_df.columns:
                st.warning(f"⚠️ {previous_date}: No se encontró columna Return_Packing_Slip")
                return self._create_empty_comparison(current_date, previous_date)
            
            # Albaranes actuales y anteriores
            current_albaranes = set(current_df['Return_Packing_Slip'].astype(str))
            previous_albaranes = set(previous_df['Return_Packing_Slip'].astype(str))
            
            # Calcular cambios
            new_albaranes = current_albaranes - previous_albaranes
            continuing_albaranes = current_albaranes.intersection(previous_albaranes)
            
            # CORREGIDO: Albaranes cerrados son los que tienen Total_Open = 0 en el archivo actual
            # No los que desaparecen del archivo
            closed_albaranes = set()
            for albaran in current_albaranes:
                albaran_row = current_df[current_df['Return_Packing_Slip'].astype(str) == albaran]
                if not albaran_row.empty:
                    total_open = pd.to_numeric(albaran_row.iloc[0].get('Total_Open', 0), errors='coerce') or 0
                    if total_open == 0:
                        closed_albaranes.add(albaran)
            
            # Análisis detallado de cambios en albaranes
            closed_tablets = 0
            added_tablets = 0
            changed_albaranes = []
            
            # CORREGIDO: Contar tablillas de albaranes nuevos
            for albaran in new_albaranes:
                albaran_row = current_df[current_df['Return_Packing_Slip'].astype(str) == albaran]
                if not albaran_row.empty:
                    total_tablets = pd.to_numeric(albaran_row.iloc[0].get('Total_Tablets', 0), errors='coerce') or 0
                    added_tablets += total_tablets
                    
                    # Agregar información del albarán nuevo
                    change_info = {
                        'albaran': albaran,
                        'customer': albaran_row.iloc[0].get('Customer_Name', 'N/A'),
                        'previous_open': 0,
                        'current_open': pd.to_numeric(albaran_row.iloc[0].get('Total_Open', 0), errors='coerce') or 0,
                        'previous_total': 0,
                        'current_total': total_tablets,
                        'changes': [f"🆕 Albarán nuevo con {total_tablets} tablillas"]
                    }
                    changed_albaranes.append(change_info)
            
            # Analizar cambios en albaranes que continúan
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
                'added_tablets': added_tablets,
                'new_albaranes_list': list(new_albaranes),
                'closed_albaranes_list': list(closed_albaranes),
                'changed_albaranes': changed_albaranes,
                'current_total_open': current_df['Total_Open'].sum() if 'Total_Open' in current_df.columns else 0,
                'previous_total_open': previous_df['Total_Open'].sum() if 'Total_Open' in previous_df.columns else 0,
                'current_total_albaranes': len(current_df),
                'previous_total_albaranes': len(previous_df),
                'albaranes_with_added_tablets': len([c for c in changed_albaranes if any('agregadas' in change for change in c['changes'])])
            }
        
        except Exception as e:
            st.error(f"❌ Error comparando {previous_date} vs {current_date}: {str(e)}")
            return self._create_empty_comparison(current_date, previous_date)
    
    def _create_empty_comparison(self, current_date: str, previous_date: str) -> Dict:
        """Crear comparación vacía en caso de error"""
        return {
            'current_date': current_date,
            'previous_date': previous_date,
            'new_albaranes': 0,
            'closed_albaranes': 0,
            'closed_tablets': 0,
            'added_tablets': 0,
            'new_albaranes_list': [],
            'closed_albaranes_list': [],
            'changed_albaranes': [],
            'current_total_open': 0,
            'previous_total_open': 0,
            'current_total_albaranes': 0,
            'previous_total_albaranes': 0,
            'albaranes_with_added_tablets': 0
        }
    
    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalizar DataFrame para comparación - VERSIÓN ROBUSTA"""
        try:
            # Asegurar que las columnas principales existen
            required_columns = ['Return_Packing_Slip', 'Total_Open', 'Customer_Name']
            
            for col in required_columns:
                if col not in df.columns:
                    # Buscar columnas similares
                    similar_cols = [c for c in df.columns if col.lower() in c.lower() or c.lower() in col.lower()]
                    if similar_cols:
                        df[col] = df[similar_cols[0]]
                        st.info(f"🔄 Usando '{similar_cols[0]}' como '{col}'")
                    else:
                        df[col] = 0 if 'Total' in col else 'N/A'
                        st.warning(f"⚠️ Columna '{col}' no encontrada, usando valor por defecto")
            
            # NUEVO: Normalizar códigos de almacén en comparaciones
            if 'WH_Code' in df.columns:
                df['WH_Code'] = df['WH_Code'].str.upper()
                st.info(f"🔧 Normalizados códigos de almacén para comparación")
            
            return df
        except Exception as e:
            st.error(f"❌ Error normalizando DataFrame: {str(e)}")
            return df
    
    def create_comparison_summary(self, comparisons: List[Dict], excel_data: Dict[str, pd.DataFrame]) -> Dict:
        """Crear resumen de todas las comparaciones - VERSIÓN ROBUSTA"""
        try:
            if not comparisons:
                return {}
            
            total_new_albaranes = sum(c['new_albaranes'] for c in comparisons)
            total_closed_albaranes = sum(c['closed_albaranes'] for c in comparisons)
            total_closed_tablets = sum(c['closed_tablets'] for c in comparisons)
            total_added_tablets = sum(c.get('added_tablets', 0) for c in comparisons)
            
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
                'total_added_tablets': total_added_tablets,
                'analysis_period': f"{dates[0]} a {dates[-1]}" if len(dates) >= 2 else dates[0],
                'open_evolution': open_evolution,
                'num_files_analyzed': len(excel_data),
                'most_recent_date': dates[-1] if dates else None,
                'oldest_date': dates[0] if dates else None
            }
        except Exception as e:
            st.error(f"❌ Error creando resumen: {str(e)}")
            return {}

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
        """Extrae datos usando configuraciones múltiples de Camelot con manejo inteligente de páginas"""
        if not CAMELOT_AVAILABLE:
            st.error("⚠️ Camelot no está instalado. Ejecuta: pip install camelot-py[cv]")
            return None
        
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name
            
            st.info("🔄 Extrayendo datos con métodos Camelot mejorados...")
            
            # NUEVO: Extracción inteligente por páginas
            all_tables = []
            successful_methods = []
            
            # Primero, intentar extraer todas las páginas con métodos optimizados
            all_tables, successful_methods = self._extract_with_multiple_methods(tmp_file_path)
            
            # Si no se encontraron tablas, intentar extracción página por página
            if not all_tables:
                st.warning("⚠️ Métodos globales fallaron. Intentando extracción página por página...")
                all_tables, successful_methods = self._extract_page_by_page(tmp_file_path)
            
            # Limpiar archivo temporal
            os.unlink(tmp_file_path)
            
            if not all_tables:
                st.error("❌ No se encontraron tablas en el PDF con ningún método")
                return None
            
            st.success(f"🎯 Extracción exitosa: {len(all_tables)} tablas encontradas con métodos: {', '.join(successful_methods)}")
            
            # Procesar tablas encontradas con manejo mejorado
            return self._process_tables_advanced(all_tables)
            
        except Exception as e:
            st.error(f"❌ Error procesando PDF: {str(e)}")
            return None
    
    def _extract_with_multiple_methods(self, tmp_file_path: str) -> Tuple[List, List[str]]:
        """Extraer con métodos adaptativos - ADAPTADO DE APP LOCAL"""
        all_tables = []
        successful_methods = []
        
        # MÉTODO 1: Lattice Conservador (mejor para PDFs bien estructurados)
        try:
            st.info("🔄 Probando método Lattice Conservador...")
            tables = camelot.read_pdf(
                tmp_file_path, 
                pages='all', 
                flavor='lattice',
                process_background=True,
                line_scale=40
            )
            if len(tables) > 0:
                all_tables.extend(tables)
                successful_methods.append("Lattice Conservador")
                st.success(f"✅ Lattice Conservador: {len(tables)} tablas encontradas")
                return all_tables, successful_methods
            else:
                st.warning("⚠️ Lattice Conservador: No se encontraron tablas")
        except Exception as e:
            st.warning(f"⚠️ Error en Lattice Conservador: {str(e)}")
        
        # MÉTODO 2: Stream Balanceado (parámetros equilibrados)
        try:
            st.info("🔄 Probando método Stream Balanceado...")
            tables = camelot.read_pdf(
                tmp_file_path, 
                pages='all', 
                flavor='stream',
                edge_tol=350,
                row_tol=12,
                column_tol=5
            )
            if len(tables) > 0:
                all_tables.extend(tables)
                successful_methods.append("Stream Balanceado")
                st.success(f"✅ Stream Balanceado: {len(tables)} tablas encontradas")
                return all_tables, successful_methods
            else:
                st.warning("⚠️ Stream Balanceado: No se encontraron tablas")
        except Exception as e:
            st.warning(f"⚠️ Error en Stream Balanceado: {str(e)}")
        
        # MÉTODO 3: Stream Estándar (el que funciona consistentemente)
        try:
            st.info("🔄 Probando método Stream Estándar...")
            tables = camelot.read_pdf(
                tmp_file_path, 
                pages='all', 
                flavor='stream'
            )
            if len(tables) > 0:
                all_tables.extend(tables)
                successful_methods.append("Stream Estándar")
                st.success(f"✅ Stream Estándar: {len(tables)} tablas encontradas")
                return all_tables, successful_methods
            else:
                st.warning("⚠️ Stream Estándar: No se encontraron tablas")
        except Exception as e:
            st.warning(f"⚠️ Error en Stream Estándar: {str(e)}")
        
        # MÉTODO 4: Stream Agresivo (fallback)
        try:
            st.info("🔄 Probando método Stream Agresivo...")
            tables = camelot.read_pdf(
                tmp_file_path, 
                pages='all', 
                flavor='stream',
                edge_tol=500,
                row_tol=10,
                column_tol=0,
                split_text=True,
                flag_size=True
            )
            if len(tables) > 0:
                all_tables.extend(tables)
                successful_methods.append("Stream Agresivo")
                st.success(f"✅ Stream Agresivo: {len(tables)} tablas encontradas")
                return all_tables, successful_methods
            else:
                st.warning("⚠️ Stream Agresivo: No se encontraron tablas")
        except Exception as e:
            st.warning(f"⚠️ Error en Stream Agresivo: {str(e)}")
        
        return all_tables, successful_methods
    
    def _separate_merged_row(self, merged_text: str) -> Optional[pd.DataFrame]:
        """Separa una fila que está toda junta en una sola celda - DE APP LOCAL"""
        try:
            import re
            # Buscar patrones específicos para separar
            parts = []
            
            # 1. FL
            parts.append('FL')
            
            # 2. Warehouse code (612D, 61D, 28D, 252D, etc.) - MEJORADO
            wh_match = re.search(r'(\d+[dD])', merged_text, re.IGNORECASE)
            if wh_match:
                wh_code = wh_match.group(1).upper()  # Normalizar a mayúsculas
                parts.append(wh_code)
            else:
                parts.append('612D')  # Default
            
            # 3. Slip number
            slip_match = re.search(r'(729000018\d{3})', merged_text)
            parts.append(slip_match.group(1) if slip_match else '')
            
            # 4. Fechas
            dates = re.findall(r'(\d{1,2}/\d{1,2}/\d{4})', merged_text)
            parts.extend(dates[:4])  # Primeras 4 fechas
            while len(parts) < 7:  # Asegurar al menos 7 elementos
                parts.append('')
            
            # 5. Jobsite (8 dígitos empezando con 4)
            jobsite_match = re.search(r'(4\d{7})', merged_text)
            if jobsite_match:
                parts.append(jobsite_match.group(1))
            else:
                parts.append('')
            
            # 6. Cost Center (FLXXX)
            cost_center_match = re.search(r'(FL\d{3})', merged_text)
            if cost_center_match:
                parts.append(cost_center_match.group(1))
            else:
                parts.append('')
            
            # 7. Customer name (texto entre fechas y números)
            customer_match = re.search(r'([A-Za-z\s&,\.]+(?:Corp|Inc|LLC|Ltd|Co))', merged_text)
            if customer_match:
                parts.append(customer_match.group(1).strip())
            else:
                parts.append('')
            
            # 8. Job name (después del customer)
            remaining = merged_text
            for part in parts:
                if part:
                    remaining = remaining.replace(str(part), '', 1)
            
            # Separar por patrones comunes
            remaining_parts = remaining.split()[:10]  # Máximo 10 partes más
            parts.extend(remaining_parts)
            
            # Asegurar 18 columnas
            while len(parts) < 18:
                parts.append('')
            
            return pd.DataFrame([parts[:18]])
            
        except Exception as e:
            st.warning(f"Error separando fila concatenada: {e}")
            return None
    
    def _evaluate_extraction_quality(self, tables) -> float:
        """Evalúa la calidad de la extracción - ADAPTADO DEL CÓDIGO DE CLAUDE"""
        try:
            if not tables:
                return 0.0
            
            total_score = 0.0
            total_tables = len(tables)
            
            for table in tables:
                try:
                    df = table.df
                    if df is None or df.empty:
                        continue
                    
                    # Score basado en estructura
                    score = 0.0
                    
                    # 1. Verificar columnas (18 es ideal)
                    col_count = len(df.columns)
                    if col_count >= 15:
                        score += 0.3  # Estructura buena
                    elif col_count >= 10:
                        score += 0.2  # Estructura aceptable
                    else:
                        score += 0.1  # Estructura básica
                    
                    # 2. Verificar filas con datos válidos
                    valid_rows = 0
                    total_rows = len(df)
                    
                    for idx in df.index:
                        row_text = ' '.join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
                        if '729000018' in row_text and 'FL' in row_text:
                            # Evitar headers
                            if not any(skip in row_text for skip in ['Outstanding count', 'Page', 'Return packing', 'Customer name', 'Alsina Forms']):
                                valid_rows += 1
                    
                    if total_rows > 0:
                        valid_ratio = valid_rows / total_rows
                        score += valid_ratio * 0.4  # Hasta 0.4 puntos por filas válidas
                    
                    # 3. Verificar secuencia de slips
                    slip_numbers = []
                    for idx in df.index:
                        row_text = ' '.join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
                        slip_match = re.search(r'(729000018\d{3})', row_text)
                        if slip_match:
                            slip_numbers.append(int(slip_match.group(1)[-3:]))
                    
                    if len(slip_numbers) > 1:
                        slip_numbers.sort()
                        first_slip = slip_numbers[0]
                        last_slip = slip_numbers[-1]
                        expected_count = last_slip - first_slip + 1
                        actual_count = len(slip_numbers)
                        
                        if actual_count == expected_count:
                            score += 0.3  # Secuencia perfecta
                        elif actual_count >= expected_count * 0.8:
                            score += 0.2  # Secuencia buena
                        else:
                            score += 0.1  # Secuencia parcial
                    
                    total_score += min(score, 1.0)  # Cap en 1.0 por tabla
                    
                except Exception as e:
                    continue
            
            return total_score / total_tables if total_tables > 0 else 0.0
            
        except Exception as e:
            return 0.0
    
    def _get_page_specific_config(self, page_num: int) -> Dict:
        """Obtener configuración específica para cada página"""
        configs = {
            1: {
                'edge_tol': 500,
                'row_tol': 10,
                'column_tol': 0,
                'description': 'Página 1 - Configuración estándar'
            },
            2: {
                'edge_tol': 400,
                'row_tol': 8,
                'column_tol': 5,
                'description': 'Página 2 - Configuración intermedia'
            },
            3: {
                'edge_tol': 350,
                'row_tol': 6,
                'column_tol': 8,
                'description': 'Página 3 - Configuración estricta'
            },
            4: {
                'edge_tol': 200,
                'row_tol': 3,
                'column_tol': 10,
                'description': 'Página 4 - Configuración muy estricta para columnas concatenadas'
            },
            5: {
                'edge_tol': 250,
                'row_tol': 4,
                'column_tol': 12,
                'description': 'Página 5 - Configuración para futuras páginas'
            }
        }
        
        # Para páginas 6+, usar configuración similar a página 4
        if page_num > 5:
            return {
                'edge_tol': 200,
                'row_tol': 3,
                'column_tol': 10,
                'description': f'Página {page_num} - Configuración adaptativa'
            }
        
        return configs.get(page_num, configs[4])  # Default a página 4
    
    def _extract_page_by_page(self, tmp_file_path: str) -> Tuple[List, List[str]]:
        """Extraer página por página con métodos específicos para cada página"""
        all_tables = []
        successful_methods = []
        
        # Primero, detectar cuántas páginas tiene el PDF
        try:
            # Intentar extraer la primera página para detectar el número total
            test_tables = camelot.read_pdf(tmp_file_path, pages='1', flavor='stream')
            if test_tables:
                # Si funciona, intentar detectar el número total de páginas
                max_pages = 10  # Asumir máximo 10 páginas inicialmente
                st.info(f"🔍 Intentando extracción página por página (máximo {max_pages} páginas)...")
                
                for page_num in range(1, max_pages + 1):
                    page_tables = self._extract_single_page(tmp_file_path, page_num)
                    if page_tables:
                        all_tables.extend(page_tables)
                        successful_methods.append(f"Página {page_num}")
                        st.write(f"✅ Página {page_num}: {len(page_tables)} tablas encontradas")
                    else:
                        # Si no encontramos tablas en esta página, probablemente no hay más páginas
                        if page_num > 3:  # Solo después de la página 3
                            break
        except Exception as e:
            st.write(f"Error en extracción página por página: {str(e)}")
        
        return all_tables, successful_methods
    
    def _extract_single_page(self, tmp_file_path: str, page_num: int) -> List:
        """Extraer una página específica con configuraciones optimizadas por página"""
        page_tables = []
        
        # Obtener configuración específica para esta página
        config = self._get_page_specific_config(page_num)
        st.write(f"🔧 {config['description']}")
        
        # Método 1: Stream con configuración específica de la página
        try:
            tables = camelot.read_pdf(
                tmp_file_path, 
                pages=str(page_num), 
                flavor='stream',
                edge_tol=config['edge_tol'],
                row_tol=config['row_tol'],
                column_tol=config['column_tol'],
                split_text=True,
                flag_size=True
            )
            if len(tables) > 0:
                page_tables.extend(tables)
                st.write(f"✅ Página {page_num} - Stream específico exitoso: {len(tables)} tablas")
        except Exception as e:
            st.write(f"Página {page_num} - Stream específico falló: {str(e)}")
        
        # Método 2: Stream con configuraciones más permisivas (fallback)
        if not page_tables:
            try:
                tables = camelot.read_pdf(
                    tmp_file_path, 
                    pages=str(page_num), 
                    flavor='stream',
                    edge_tol=800,           # Tolerancia más permisiva
                    row_tol=20,             # Tolerancia más permisiva para filas
                    column_tol=0,           # Sin tolerancia para columnas
                    split_text=True,
                    flag_size=True
                )
                if len(tables) > 0:
                    page_tables.extend(tables)
                    st.write(f"✅ Página {page_num} - Stream permisivo exitoso: {len(tables)} tablas")
            except Exception as e:
                st.write(f"Página {page_num} - Stream permisivo falló: {str(e)}")
        
        # Método 3: Lattice para páginas con líneas definidas
        if not page_tables:
            try:
                tables = camelot.read_pdf(
                    tmp_file_path, 
                    pages=str(page_num), 
                    flavor='lattice',
                    process_background=True,
                    line_scale=20,          # Escala más alta para líneas más visibles
                    copy_text=['v']         # Copiar texto vertical
                )
                if len(tables) > 0:
                    page_tables.extend(tables)
                    st.write(f"✅ Página {page_num} - Lattice exitoso: {len(tables)} tablas")
            except Exception as e:
                st.write(f"Página {page_num} - Lattice falló: {str(e)}")
        
        # Método 4: Stream con configuración ultra-estricta para páginas problemáticas (especialmente página 4+)
        if not page_tables and page_num >= 4:
            try:
                tables = camelot.read_pdf(
                    tmp_file_path, 
                    pages=str(page_num), 
                    flavor='stream',
                    edge_tol=100,           # Tolerancia ultra-estricta
                    row_tol=1,              # Tolerancia ultra-estricta para filas
                    column_tol=15,          # Tolerancia alta para columnas
                    split_text=True,
                    flag_size=True,
                    table_areas=['0,1000,1000,0']  # Área específica
                )
                if len(tables) > 0:
                    page_tables.extend(tables)
                    st.write(f"✅ Página {page_num} - Stream ultra-estricto exitoso: {len(tables)} tablas")
            except Exception as e:
                st.write(f"Página {page_num} - Stream ultra-estricto falló: {str(e)}")
        
        return page_tables
    
    def _is_duplicate_table(self, new_table, existing_tables: List) -> bool:
        """Verificar si una tabla es duplicada"""
        if not existing_tables:
            return False
        
        # Comparar dimensiones y contenido básico
        for existing_table in existing_tables:
            if (new_table.shape == existing_table.shape and 
                new_table.df.equals(existing_table.df)):
                return True
        return False
    
    def _filter_valid_fl_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtrar filas FL válidas con separación de filas concatenadas y normalización - MEJORADO"""
        try:
            if df.empty:
                return df
            
            valid_rows = []
            
            for idx in df.index:
                first_col = str(df.iloc[idx, 0]).strip()
                
                # NUEVO: Verificar si toda la fila está concatenada en una sola celda
                if len(first_col) > 100 and '729000018' in first_col and 'FL' in first_col:
                    st.warning(f"⚠️ Fila concatenada detectada, separando...")
                    separated_row = self._separate_merged_row(first_col)
                    if separated_row is not None:
                        # Agregar la fila separada como una nueva fila válida
                        valid_rows.append(separated_row)
                        st.success(f"✅ Fila concatenada separada exitosamente")
                    continue
                
                # Verificar si la fila empieza con FL
                if not first_col.startswith('FL'):
                    continue
                
                # NUEVO: Validar que la fila tenga datos suficientes
                if self._is_valid_fl_row(df.iloc[idx]):
                    # NUEVO: Normalizar warehouse codes antes de agregar
                    row_data = df.iloc[idx:idx+1].copy()
                    
                    # Normalizar warehouse en columna 1 (índice 1) - buscar 612d y convertir a 612D
                    if len(row_data.columns) > 1:
                        wh_cell = str(row_data.iloc[0, 1])
                        # Buscar cualquier patrón de warehouse code y normalizar
                        wh_match = re.search(r'(\d+[dD])', wh_cell, re.IGNORECASE)
                        if wh_match:
                            normalized_wh = wh_match.group(1).upper()
                            wh_cell = wh_cell.replace(wh_match.group(1), normalized_wh)
                            row_data.iloc[0, 1] = wh_cell
                    
                    valid_rows.append(row_data)
                else:
                    st.write(f"⚠️ Fila FL incompleta descartada: {first_col}")
            
            if valid_rows:
                # Si tenemos filas separadas (DataFrames), concatenarlas
                if isinstance(valid_rows[0], pd.DataFrame):
                    return pd.concat(valid_rows, ignore_index=True)
                else:
                    return df.loc[valid_rows].reset_index(drop=True)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            st.warning(f"⚠️ Error filtrando filas FL: {str(e)}")
            # Fallback: usar método original
            return df[df.iloc[:, 0].astype(str).str.contains('FL', na=False)]
    
    def _is_valid_fl_row(self, row) -> bool:
        """Validar si una fila FL tiene datos suficientes y válidos"""
        try:
            first_col = str(row.iloc[0]).strip()
            
            # Verificar que empiece con FL
            if not first_col.startswith('FL'):
                return False
            
            # Verificar que tenemos suficientes columnas con datos para una fila válida
            non_empty_cols = 0
            for i in range(min(10, len(row))):  # Revisar primeras 10 columnas
                if pd.notna(row.iloc[i]) and str(row.iloc[i]).strip() != '' and str(row.iloc[i]).strip() != 'nan':
                    non_empty_cols += 1
            
            # NUEVO: Criterio más flexible - mínimo 3 columnas con datos
            # Esto permite que páginas con menos columnas (como página 4) sean válidas
            if non_empty_cols < 3:
                return False
            
            # NUEVO: Validación más flexible para páginas con menos columnas
            # Verificar que la segunda columna no esté vacía (debería ser WH_Code)
            if len(row) > 1:
                second_col = str(row.iloc[1]).strip()
                if not second_col or second_col == '' or second_col == 'nan':
                    return False
            
            # Verificar que la tercera columna no esté vacía (debería ser Return_Packing_Slip)
            if len(row) > 2:
                third_col = str(row.iloc[2]).strip()
                if not third_col or third_col == '' or third_col == 'nan':
                    return False
            
            # NUEVO: Solo verificar Return_Date si hay suficientes columnas
            # Esto permite que páginas con menos columnas (como página 4) sean válidas
            if len(row) > 3:
                fourth_col = str(row.iloc[3]).strip()
                # Solo rechazar si la columna existe pero está vacía
                if fourth_col == '' or fourth_col == 'nan':
                    return False
            
            # NUEVO: Validación más flexible para patrones FL
            # Verificar que no sea solo "FL" con muy pocos datos
            if first_col == 'FL' and non_empty_cols < 3:  # Reducido de 5 a 3
                return False
            
            # NUEVO: Validación más flexible para patrones FL052, etc.
            # Verificar que no sea un patrón como "FL052" sin datos reales
            if first_col in ['FL052', 'FL051', 'FL050'] and non_empty_cols < 4:  # Reducido de 6 a 4
                return False
            
            # NUEVO: Detectar patrones problemáticos con saltos de línea
            if '\n' in first_col or '\r' in first_col:
                return False
            
            # NUEVO: Detectar patrones con comillas dobles (datos mal formateados)
            if first_col.startswith('"') and first_col.endswith('"'):
                # Verificar si el contenido dentro de las comillas es válido
                inner_content = first_col[1:-1].strip()
                if '\n' in inner_content or len(inner_content.split()) > 3:
                    return False
            
            return True
            
        except Exception as e:
            st.warning(f"⚠️ Error validando fila FL: {str(e)}")
            return False
    
    def _validate_and_improve_extraction(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validar y mejorar la calidad de la extracción"""
        try:
            st.info("🔍 Validando calidad de extracción...")
            
            # Contar filas FL válidas
            fl_rows = df[df.iloc[:, 0].astype(str).str.contains('FL', na=False)]
            total_rows = len(df)
            fl_count = len(fl_rows)
            
            st.write(f"📊 Estadísticas de extracción:")
            st.write(f"   - Total de filas: {total_rows}")
            st.write(f"   - Filas FL válidas: {fl_count}")
            st.write(f"   - Tasa de éxito: {(fl_count/total_rows*100):.1f}%" if total_rows > 0 else "   - Tasa de éxito: 0%")
            
            # Si la tasa de éxito es muy baja, intentar correcciones adicionales
            if fl_count < total_rows * 0.5:  # Menos del 50% de filas válidas
                st.warning("⚠️ Tasa de éxito baja. Aplicando correcciones adicionales...")
                df = self._apply_additional_corrections(df)
            
            # Validar estructura de columnas
            expected_min_cols = 10
            if len(df.columns) < expected_min_cols:
                st.warning(f"⚠️ Pocas columnas detectadas ({len(df.columns)}). Esperado: {expected_min_cols}+")
                # Intentar expandir columnas si es necesario
                df = self._expand_columns_if_needed(df)
            
            return df
            
        except Exception as e:
            st.warning(f"⚠️ Error en validación: {str(e)}")
            return df
    
    def _apply_additional_corrections(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplicar correcciones adicionales para mejorar la extracción"""
        try:
            st.info("🔧 Aplicando correcciones adicionales...")
            
            corrections_made = 0
            
            # Buscar patrones que podrían ser FL pero no fueron detectados
            for idx in df.index:
                first_col = str(df.iloc[idx, 0]).strip()
                
                # Patrón: números largos que podrían ser Return_Packing_Slip
                if first_col.isdigit() and len(first_col) >= 9:
                    # Verificar si hay un WH_Code en la columna siguiente
                    if len(df.columns) > 1:
                        second_col = str(df.iloc[idx, 1]).strip()
                        if len(second_col) <= 4 and not second_col.isdigit():
                            # Reorganizar: FL, WH_Code, Return_Packing_Slip
                            df.iloc[idx, 0] = "FL"
                            df.iloc[idx, 1] = second_col
                            df.iloc[idx, 2] = first_col
                            corrections_made += 1
            
            if corrections_made > 0:
                st.success(f"✅ {corrections_made} correcciones adicionales aplicadas")
            
            return df
            
        except Exception as e:
            st.warning(f"⚠️ Error en correcciones adicionales: {str(e)}")
            return df
    
    def _expand_columns_if_needed(self, df: pd.DataFrame) -> pd.DataFrame:
        """Expandir columnas si se detectan pocas columnas"""
        try:
            # Si tenemos muy pocas columnas, podría ser que los datos estén concatenados
            if len(df.columns) < 8:
                st.info("🔧 Detectadas pocas columnas. Verificando si hay datos concatenados...")
                
                # Buscar filas con datos muy largos en la primera columna
                for idx in df.index:
                    first_col = str(df.iloc[idx, 0]).strip()
                    if len(first_col) > 20:  # Datos muy largos
                        # Intentar separar por espacios
                        parts = first_col.split()
                        if len(parts) >= 3:
                            # Expandir a más columnas
                            for i, part in enumerate(parts[:min(8, len(parts))]):
                                if i < len(df.columns):
                                    df.iloc[idx, i] = part
                                else:
                                    # Agregar nueva columna si es necesario
                                    df[f'Col_{i+1}'] = ''
                                    df.iloc[idx, i] = part
            
            return df
            
        except Exception as e:
            st.warning(f"⚠️ Error expandiendo columnas: {str(e)}")
            return df
    
    def _process_tables_advanced(self, tables) -> pd.DataFrame:
        """Procesamiento avanzado de tablas extraídas"""
        all_data = []
        
        for i, table in enumerate(tables):
            st.write(f"🔍 Procesando tabla {i+1}: {table.shape[0]} filas, {table.shape[1]} columnas")
            
            df = table.df
            
            # NUEVO: Análisis detallado de la estructura de columnas
            if i == 0:  # Solo mostrar para la primera tabla
                st.info("📋 **Análisis de estructura de columnas:**")
                st.write(f"- **Página 1**: {table.shape[1]} columnas")
                # Guardar estructura de referencia
                self._reference_columns = list(df.columns)
            elif i == 3:  # Página 4
                st.write(f"- **Página 4**: {table.shape[1]} columnas ⚠️ (Estructura diferente)")
                self._analyze_column_differences(df, i+1)
            elif i == 4:  # Página 5
                st.write(f"- **Página 5**: {table.shape[1]} columnas")
                self._analyze_column_differences(df, i+1)
            elif i == 5:  # Página 6
                st.write(f"- **Página 6**: {table.shape[1]} columnas")
                self._analyze_column_differences(df, i+1)
            elif i == 6:  # Página 7
                st.write(f"- **Página 7**: {table.shape[1]} columnas")
                self._analyze_column_differences(df, i+1)
            elif i == 7:  # Página 8
                st.write(f"- **Página 8**: {table.shape[1]} columnas")
                self._analyze_column_differences(df, i+1)
            
            # NUEVO: Filtrar y validar filas FL con criterios más estrictos
            fl_rows = self._filter_valid_fl_rows(df)
            
            if len(fl_rows) > 0:
                st.write(f"✅ {len(fl_rows)} filas FL válidas encontradas en tabla {i+1}")
                all_data.append(fl_rows)
        
        if not all_data:
            st.error("❌ No se encontraron filas con datos FL")
            return None
        
        # Combinar todas las tablas FL
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # NUEVO: Validar y mejorar la extracción antes de limpiar
        combined_df = self._validate_and_improve_extraction(combined_df)
        
        # Limpiar y estandarizar
        return self._clean_and_standardize_advanced(combined_df)
    
    def _fix_concatenated_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Corregir columnas concatenadas - Solución mejorada para páginas problemáticas"""
        try:
            st.info("🔧 Corrigiendo columnas mal separadas...")
            
            # Crear copia para trabajar
            fixed_df = df.copy()
            corrections_made = 0
            
            # Verificar si la primera columna contiene patrones problemáticos
            for idx in fixed_df.index:
                first_col = str(fixed_df.iloc[idx, 0]).strip()
                
                # NUEVO: Patrón específico para 4ta página - "FL61D729040036567"
                if first_col.startswith('FL') and len(first_col) > 10 and not ' ' in first_col:
                    # Extraer componentes usando regex
                    import re
                    
                    # Patrón: FL + WH_Code (2-4 caracteres) + Return_Packing_Slip (9+ dígitos)
                    pattern = r'^FL([A-Za-z0-9]{2,4})(\d{9,})$'
                    match = re.match(pattern, first_col)
                    
                    if match:
                        wh_code = match.group(1)
                        return_slip = match.group(2)
                        
                        # Separar correctamente
                        fixed_df.iloc[idx, 0] = "FL"
                        
                        if len(fixed_df.columns) > 1:
                            fixed_df.iloc[idx, 1] = wh_code
                        
                        if len(fixed_df.columns) > 2:
                            fixed_df.iloc[idx, 2] = return_slip
                        
                        corrections_made += 1
                        continue
                
                # NUEVO: Patrón para filas incompletas como "FL052" sin más datos
                if first_col == 'FL' or (first_col.startswith('FL') and len(first_col) <= 6):
                    # Verificar si las columnas siguientes están vacías
                    has_data = False
                    for col_idx in range(1, min(5, len(fixed_df.columns))):
                        if pd.notna(fixed_df.iloc[idx, col_idx]) and str(fixed_df.iloc[idx, col_idx]).strip() != '':
                            has_data = True
                            break
                    
                    if not has_data:
                        # Esta fila está incompleta, marcarla para descarte posterior
                        st.write(f"⚠️ Fila incompleta detectada: {first_col} - será descartada")
                        continue
                
                # Patrón original: "FL 612D 729000018764" o similar
                if first_col.startswith('FL '):
                    parts = first_col.split()
                    
                    if len(parts) >= 3:
                        # Separar correctamente
                        fixed_df.iloc[idx, 0] = parts[0]  # "FL"
                        
                        # Si tenemos suficientes columnas, distribuir
                        if len(fixed_df.columns) > 1:
                            fixed_df.iloc[idx, 1] = parts[1]  # WH_Code como "612D"
                        
                        if len(fixed_df.columns) > 2:
                            fixed_df.iloc[idx, 2] = parts[2]  # Return_Packing_Slip como "729000018764"
                        
                        # Mover el resto de contenido hacia la derecha si es necesario
                        remaining_parts = parts[3:] if len(parts) > 3 else []
                        for i, part in enumerate(remaining_parts, start=3):
                            if i < len(fixed_df.columns):
                                # Solo reemplazar si la celda está vacía
                                current_val = fixed_df.iloc[idx, i]
                                if pd.isna(current_val) or str(current_val).strip() == '':
                                    fixed_df.iloc[idx, i] = part
                                else:
                                    # Insertar nuevo contenido desplazando el existente
                                    break
                        
                        corrections_made += 1
                
                # Patrón alternativo: Primera columna solo tiene "612D 729000018764" sin FL
                elif ' ' in first_col and len(first_col.split()) == 2:
                    parts = first_col.split()
                    
                    # Verificar si parece WH_Code + Return_Packing_Slip
                    if (len(parts[0]) <= 4 and  # WH_Code corto
                        len(parts[1]) >= 10 and parts[1].isdigit()):  # Return_Packing_Slip largo
        
                        # Insertar FL al principio y separar
                        fixed_df.iloc[idx, 0] = "FL"
                        
                        # Mover contenido hacia la derecha
                        if len(fixed_df.columns) > 1:
                            # Guardar contenido actual de las columnas siguientes
                            old_content = [fixed_df.iloc[idx, i] for i in range(1, len(fixed_df.columns))]
                            
                            # Colocar WH_Code en segunda posición
                            fixed_df.iloc[idx, 1] = parts[0]
                            
                            # Colocar Return_Packing_Slip en tercera posición
                            if len(fixed_df.columns) > 2:
                                fixed_df.iloc[idx, 2] = parts[1]
                                
                                # Mover el contenido restante una posición a la derecha
                                for i, val in enumerate(old_content[1:], start=3):
                                    if i < len(fixed_df.columns) and not pd.isna(val) and str(val).strip():
                                        fixed_df.iloc[idx, i] = val
                        
                        corrections_made += 1
                
                # NUEVO: Patrón para columnas con datos concatenados en otras posiciones
                for col_idx in range(1, min(5, len(fixed_df.columns))):  # Revisar primeras 5 columnas
                    cell_value = str(fixed_df.iloc[idx, col_idx]).strip()
                    
                    # Detectar patrones como "4992226M 2" o "11671M 1"
                    if 'M ' in cell_value or 'T ' in cell_value:
                        parts = cell_value.split()
                        if len(parts) == 2:
                            # Separar valor y sufijo
                            fixed_df.iloc[idx, col_idx] = parts[0]  # "4992226M"
                            
                            # Si hay una columna siguiente, poner el número
                            if col_idx + 1 < len(fixed_df.columns):
                                current_next = str(fixed_df.iloc[idx, col_idx + 1]).strip()
                                if pd.isna(fixed_df.iloc[idx, col_idx + 1]) or current_next == '' or current_next == '0':
                                    fixed_df.iloc[idx, col_idx + 1] = parts[1]  # "2"
                                    corrections_made += 1
            
            # NUEVO: Limpiar columnas con datos mixtos como "1674, 1711"
            for col_idx in range(len(fixed_df.columns)):
                for idx in fixed_df.index:
                    cell_value = str(fixed_df.iloc[idx, col_idx]).strip()
                    
                    # Detectar patrones con comas y múltiples números
                    if ',' in cell_value and any(char.isdigit() for char in cell_value):
                        # Para columnas con múltiples valores, tomar el primero
                        first_value = cell_value.split(',')[0].strip()
                        if first_value and first_value != '0':
                            fixed_df.iloc[idx, col_idx] = first_value
                            corrections_made += 1
            
            # Mostrar resultados
            if corrections_made > 0:
                st.success(f"✅ {corrections_made} correcciones aplicadas")
                st.write("**Ejemplos de corrección:**")
                
                # Mostrar ejemplos de correcciones
                examples_shown = 0
                for idx in range(min(3, len(df))):
                    if str(df.iloc[idx, 0]) != str(fixed_df.iloc[idx, 0]):
                        st.write(f"**Fila {idx+1} - Antes:** {df.iloc[idx, 0]}")
                        st.write(f"**Fila {idx+1} - Después:** Col1='{fixed_df.iloc[idx, 0]}' | Col2='{fixed_df.iloc[idx, 1]}' | Col3='{fixed_df.iloc[idx, 2]}'")
                        examples_shown += 1
                        if examples_shown >= 2:
                            break
            else:
                st.info("✅ No se encontraron columnas concatenadas para corregir")
            
            # NUEVO: Limpiar filas incompletas después de las correcciones
            fixed_df = self._remove_incomplete_rows(fixed_df)
            
            # NUEVO: Limpiar datos con saltos de línea y caracteres especiales
            fixed_df = self._clean_special_characters(fixed_df)
            
            # NUEVO: Eliminar filas duplicadas
            fixed_df = self._remove_duplicate_rows(fixed_df)
            
            # NUEVO: Corregir patrones específicos problemáticos
            fixed_df = self._fix_specific_problematic_patterns(fixed_df)
            
            # NUEVO: Expandir columnas para páginas con menos columnas
            fixed_df = self._expand_columns_for_short_pages(fixed_df)
            
            return fixed_df
            
        except Exception as e:
            st.warning(f"⚠️ Error corrigiendo columnas: {str(e)}")
            return df
    
    def _remove_incomplete_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remover filas incompletas o mal estructuradas"""
        try:
            if df.empty:
                return df
            
            st.info("🧹 Limpiando filas incompletas...")
            
            valid_rows = []
            removed_count = 0
            
            for idx in df.index:
                row = df.iloc[idx]
                
                # Verificar si la fila es válida
                if self._is_valid_fl_row(row):
                    valid_rows.append(idx)
                else:
                    removed_count += 1
                    first_col = str(row.iloc[0]).strip()
                    st.write(f"🗑️ Fila incompleta removida: {first_col}")
            
            if removed_count > 0:
                st.success(f"✅ {removed_count} filas incompletas removidas")
            
            if valid_rows:
                return df.loc[valid_rows].reset_index(drop=True)
            else:
                st.warning("⚠️ No quedaron filas válidas después de la limpieza")
                return pd.DataFrame()
                
        except Exception as e:
            st.warning(f"⚠️ Error limpiando filas: {str(e)}")
            return df
    
    def _clean_special_characters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpiar caracteres especiales, saltos de línea y datos mal formateados"""
        try:
            st.info("🧹 Limpiando caracteres especiales y saltos de línea...")
            
            cleaned_df = df.copy()
            corrections_made = 0
            
            for idx in cleaned_df.index:
                for col_idx in range(len(cleaned_df.columns)):
                    cell_value = str(cleaned_df.iloc[idx, col_idx]).strip()
                    
                    # Limpiar saltos de línea y caracteres especiales
                    if '\n' in cell_value or '\r' in cell_value:
                        # Reemplazar saltos de línea con espacios
                        cleaned_value = cell_value.replace('\n', ' ').replace('\r', ' ')
                        # Limpiar espacios múltiples
                        cleaned_value = ' '.join(cleaned_value.split())
                        cleaned_df.iloc[idx, col_idx] = cleaned_value
                        corrections_made += 1
                    
                    # Limpiar comillas dobles al inicio y final
                    if cell_value.startswith('"') and cell_value.endswith('"'):
                        cleaned_value = cell_value[1:-1].strip()
                        cleaned_df.iloc[idx, col_idx] = cleaned_value
                        corrections_made += 1
                    
                    # Limpiar valores que contienen solo espacios o caracteres especiales
                    if cell_value in ['', ' ', 'nan', 'None', 'null']:
                        cleaned_df.iloc[idx, col_idx] = ''
                        corrections_made += 1
            
            if corrections_made > 0:
                st.success(f"✅ {corrections_made} celdas limpiadas de caracteres especiales")
            
            return cleaned_df
            
        except Exception as e:
            st.warning(f"⚠️ Error limpiando caracteres especiales: {str(e)}")
            return df
    
    def _remove_duplicate_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Eliminar filas duplicadas basándose en Return_Packing_Slip"""
        try:
            st.info("🔍 Detectando y eliminando filas duplicadas...")
            
            if df.empty:
                return df
            
            # Crear una columna temporal para identificar duplicados
            # Usar Return_Packing_Slip como identificador único
            if len(df.columns) > 2:
                # Usar la tercera columna como Return_Packing_Slip
                df['_temp_id'] = df.iloc[:, 2].astype(str)
                
                # Contar duplicados antes de eliminar
                duplicates_before = len(df)
                df_unique = df.drop_duplicates(subset=['_temp_id'], keep='first')
                duplicates_removed = duplicates_before - len(df_unique)
                
                # Eliminar columna temporal
                df_unique = df_unique.drop('_temp_id', axis=1)
                
                if duplicates_removed > 0:
                    st.success(f"✅ {duplicates_removed} filas duplicadas eliminadas")
                else:
                    st.info("✅ No se encontraron filas duplicadas")
                
                return df_unique
            else:
                st.warning("⚠️ No hay suficientes columnas para detectar duplicados")
                return df
                
        except Exception as e:
            st.warning(f"⚠️ Error eliminando duplicados: {str(e)}")
            return df
    
    def _fix_specific_problematic_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Corregir patrones específicos problemáticos encontrados en los datos"""
        try:
            st.info("🔧 Corrigiendo patrones específicos problemáticos...")
            
            fixed_df = df.copy()
            corrections_made = 0
            
            for idx in fixed_df.index:
                first_col = str(fixed_df.iloc[idx, 0]).strip()
                
                # Patrón problemático: "FL\n61D\n729000018785\n9/23/2025"
                if first_col.startswith('"FL') and '\n' in first_col:
                    # Extraer componentes del patrón problemático
                    import re
                    
                    # Limpiar comillas y saltos de línea
                    clean_content = first_col.replace('"', '').replace('\n', ' ').strip()
                    parts = clean_content.split()
                    
                    if len(parts) >= 4:
                        # Reorganizar: FL, WH_Code, Return_Packing_Slip, Return_Date
                        fixed_df.iloc[idx, 0] = parts[0]  # "FL"
                        
                        if len(fixed_df.columns) > 1:
                            fixed_df.iloc[idx, 1] = parts[1]  # WH_Code
                        
                        if len(fixed_df.columns) > 2:
                            fixed_df.iloc[idx, 2] = parts[2]  # Return_Packing_Slip
                        
                        if len(fixed_df.columns) > 3:
                            # Convertir fecha al formato correcto
                            date_str = parts[3]
                            try:
                                from datetime import datetime
                                if '/' in date_str:
                                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                                    fixed_df.iloc[idx, 3] = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                                else:
                                    fixed_df.iloc[idx, 3] = date_str
                            except:
                                fixed_df.iloc[idx, 3] = date_str
                        
                        corrections_made += 1
                        continue
                
                # Patrón problemático: datos con saltos de línea en Customer_Name
                for col_idx in range(5, min(10, len(fixed_df.columns))):  # Revisar columnas de texto
                    cell_value = str(fixed_df.iloc[idx, col_idx]).strip()
                    
                    if '\n' in cell_value and len(cell_value.split('\n')) > 2:
                        # Limpiar saltos de línea y tomar solo la primera línea
                        first_line = cell_value.split('\n')[0].strip()
                        fixed_df.iloc[idx, col_idx] = first_line
                        corrections_made += 1
            
            if corrections_made > 0:
                st.success(f"✅ {corrections_made} patrones problemáticos corregidos")
            else:
                st.info("✅ No se encontraron patrones problemáticos específicos")
            
            return fixed_df
            
        except Exception as e:
            st.warning(f"⚠️ Error corrigiendo patrones específicos: {str(e)}")
            return df
    
    def _expand_columns_for_short_pages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Expandir columnas para páginas que tienen menos columnas (como página 4)"""
        try:
            st.info("📊 Expandindo columnas para páginas con menos columnas...")
            
            if df.empty:
                return df
            
            # Si la tabla tiene menos de 15 columnas, intentar expandir
            if len(df.columns) < 15:
                st.info(f"📋 Tabla detectada con {len(df.columns)} columnas - expandiendo...")
                
                expanded_df = df.copy()
                corrections_made = 0
                
                for idx in expanded_df.index:
                    # Buscar patrones de datos concatenados en las primeras columnas
                    for col_idx in range(min(5, len(expanded_df.columns))):
                        cell_value = str(expanded_df.iloc[idx, col_idx]).strip()
                        
                        # Patrón: datos separados por comas o espacios múltiples
                        if ',' in cell_value and len(cell_value.split(',')) > 1:
                            parts = [part.strip() for part in cell_value.split(',')]
                            
                            # Si encontramos datos separados por comas, expandir
                            if len(parts) >= 2:
                                # Reemplazar el valor original con la primera parte
                                expanded_df.iloc[idx, col_idx] = parts[0]
                                
                                # Agregar las partes restantes en columnas siguientes
                                for i, part in enumerate(parts[1:], 1):
                                    if col_idx + i < len(expanded_df.columns):
                                        expanded_df.iloc[idx, col_idx + i] = part
                                        corrections_made += 1
                                
                                continue
                        
                        # Patrón: datos con espacios múltiples (como "226, 1499")
                        if ' ' in cell_value and len(cell_value.split()) > 1:
                            parts = cell_value.split()
                            
                            # Verificar si parece ser datos numéricos separados
                            numeric_parts = []
                            for part in parts:
                                # Limpiar comas y verificar si es numérico
                                clean_part = part.replace(',', '').strip()
                                if clean_part.isdigit() or (clean_part.endswith('M') and clean_part[:-1].isdigit()):
                                    numeric_parts.append(clean_part)
                            
                            if len(numeric_parts) >= 2:
                                # Reemplazar con la primera parte
                                expanded_df.iloc[idx, col_idx] = numeric_parts[0]
                                
                                # Agregar las partes restantes
                                for i, part in enumerate(numeric_parts[1:], 1):
                                    if col_idx + i < len(expanded_df.columns):
                                        expanded_df.iloc[idx, col_idx + i] = part
                                        corrections_made += 1
                
                if corrections_made > 0:
                    st.success(f"✅ {corrections_made} columnas expandidas para páginas cortas")
                else:
                    st.info("✅ No se encontraron patrones para expandir")
                
                return expanded_df
            else:
                st.info("✅ Tabla ya tiene suficientes columnas")
                return df
                
        except Exception as e:
            st.warning(f"⚠️ Error expandiendo columnas: {str(e)}")
            return df
    
    def _analyze_column_differences(self, df: pd.DataFrame, page_num: int):
        """Analizar diferencias en la estructura de columnas entre páginas"""
        try:
            if hasattr(self, '_reference_columns') and self._reference_columns:
                current_columns = list(df.columns)
                ref_columns = self._reference_columns
                
                # Mostrar diferencias
                if len(current_columns) != len(ref_columns):
                    st.write(f"  📊 **Página {page_num}**: {len(current_columns)} columnas vs {len(ref_columns)} de referencia")
                    
                    # Mostrar primeras columnas para comparar
                    st.write(f"  🔍 **Primeras 5 columnas de Página {page_num}:**")
                    for j, col in enumerate(current_columns[:5]):
                        st.write(f"    {j+1}. {col}")
                    
                    if len(current_columns) < len(ref_columns):
                        st.write(f"  ⚠️ **Página {page_num} tiene {len(ref_columns) - len(current_columns)} columnas menos**")
                    else:
                        st.write(f"  ℹ️ **Página {page_num} tiene {len(current_columns) - len(ref_columns)} columnas más**")
                        
        except Exception as e:
            st.warning(f"⚠️ Error analizando diferencias de columnas: {str(e)}")
    
    def _validate_simple_extraction(self, df: pd.DataFrame):
        """Validación simple basada en el extractor pro"""
        if df is None or df.empty:
            st.error("❌ DataFrame vacío")
            return
        
        try:
            total_rows = len(df)
            slip_count = 0
            
            for idx in df.index:
                row_text = ' '.join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
                if '729000018' in row_text:
                    slip_count += 1
            
            st.info(f"📊 Filas extraídas: {total_rows}")
            st.info(f"📊 Slips encontrados: {slip_count}")
            
            # Calcular totales si es posible
            if len(df.columns) > 15:
                try:
                    total_13 = 0
                    total_15 = 0
                    
                    for idx in df.index:
                        val_13 = str(df.iloc[idx, 13])
                        val_15 = str(df.iloc[idx, 15])
                        
                        if val_13.isdigit():
                            total_13 += int(val_13)
                        if val_15.isdigit():
                            total_15 += int(val_15)
                    
                    st.success(f"📊 Totales calculados: Columna 13 = {total_13}, Columna 15 = {total_15}")
                    
                except:
                    pass
            
        except Exception as e:
            st.warning(f"Error en validación: {e}")
    
    def _process_single_row_page(self, df: pd.DataFrame, page_num: int):
        """Procesa páginas con una sola fila de datos usando parsing manual - DEL EXTRACTOR PRO"""
        processed_rows = []
        
        try:
            # Obtener todo el texto de la página
            full_text = ""
            for row in df.values:
                for cell in row:
                    if pd.notna(cell):
                        full_text += str(cell) + " "
            
            full_text = full_text.strip()
            st.write(f"🔍 Texto completo encontrado: {full_text[:100]}...")
            
            # Verificar si contiene datos válidos
            if '729000018' in full_text and 'FL' in full_text:
                # Parsear manualmente la fila
                parsed_row = self._parse_single_row_manually(full_text)
                
                if parsed_row is not None:
                    processed_rows.append(parsed_row)
                    st.success(f"✅ Fila parseada manualmente en página {page_num}")
                else:
                    st.warning(f"⚠️ No se pudo parsear la fila en página {page_num}")
            
        except Exception as e:
            st.error(f"Error procesando fila única: {e}")
        
        return processed_rows
    
    def _parse_single_row_manually(self, text: str):
        """Parsea manualmente una fila cuando Camelot falla - DEL EXTRACTOR PRO"""
        try:
            import re
            
            # Crear una fila fake de pandas con los datos distribuidos
            # Buscar patrones específicos en el texto
            
            # 1. Return slip number
            slip_match = re.search(r'(729000018\d{3})', text)
            slip_num = slip_match.group(1) if slip_match else ''
            
            # 2. Fechas
            dates = re.findall(r'(\d{1,2}/\d{1,2}/\d{4})', text)
            
            # 3. Jobsite y Cost center
            jobsite_match = re.search(r'(4\d{7})', text)
            jobsite = jobsite_match.group(1) if jobsite_match else ''
            
            cost_match = re.search(r'(FL\d{3})', text)
            cost_center = cost_match.group(1) if cost_match else ''
            
            # 4. Customer name (buscar patrones conocidos)
            customer = ''
            customer_patterns = [
                r'(Phorcys Builders Corp)',
                r'(Laz Construction)', 
                r'(Pedreiras Construction[^0-9]*)',
                r'(JGR Construction)',
                r'(Caribbean Building Corp)',
                r'(Thales Builders Corp)'
            ]
            
            for pattern in customer_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    customer = match.group(1)
                    break
            
            # 5. Job name (después del customer)
            job_name = ''
            if customer:
                job_pattern = f"{re.escape(customer)}\\s+([^\\n]+?)\\s+(?:No|Yes)"
                job_match = re.search(job_pattern, text, re.IGNORECASE)
                if job_match:
                    job_name = job_match.group(1).strip()
            
            # 6. Tablets y totales (buscar números y códigos)
            tablets_match = re.search(r'(\d+,\s*\d+)', text)
            tablets = tablets_match.group(1) if tablets_match else ''
            
            # Buscar códigos como 226M, 1499M
            codes_match = re.search(r'(\d+M,?\s*\d+M)', text)
            open_codes = codes_match.group(1) if codes_match else ''
            
            # Buscar números finales (delays)
            final_numbers = re.findall(r'\b(\d{1,2})\b', text[-50:])  # Últimos 50 caracteres
            
            # Crear una fila estructurada manualmente
            manual_row_data = [
                'FL',                                    # 0: Wh
                '61D',                                   # 1: Return prefix (por defecto)
                slip_num,                                # 2: Return slip
                dates[0] if dates else '',               # 3: Return date
                jobsite,                                 # 4: Jobsite
                cost_center,                             # 5: Cost center
                dates[1] if len(dates) > 1 else '',      # 6: Invoice date 1
                dates[2] if len(dates) > 2 else '',      # 7: Invoice date 2
                customer,                                # 8: Customer
                job_name,                                # 9: Job name
                'No',                                    # 10: Definitive (por defecto)
                '',                                      # 11: Counted date
                tablets,                                 # 12: Tablets
                final_numbers[-3] if len(final_numbers) >= 3 else '1',  # 13: Total
                open_codes,                              # 14: Open
                final_numbers[-2] if len(final_numbers) >= 2 else '1',  # 15: Tablets total
                final_numbers[-1] if len(final_numbers) >= 1 else '0',  # 16: Counting delay
                '0'                                      # 17: Validation delay
            ]
            
            # Crear DataFrame de una sola fila
            manual_df = pd.DataFrame([manual_row_data])
            
            st.write(f"📝 Fila manual creada: Slip={slip_num}, Customer={customer[:20]}, Tablets={tablets}")
            
            return manual_df
            
        except Exception as e:
            st.error(f"Error en parsing manual: {e}")
            return None
    
    def _show_extraction_summary_robust(self, df: pd.DataFrame):
        """Mostrar resumen de extracción con validación robusta - DEL EXTRACTOR PRO"""
        if df is None or df.empty:
            st.warning("⚠️ No hay datos para mostrar en el resumen")
            return
        
        try:
            st.header("🔍 Validación Completa del Sistema")
            
            # 1. Conteos básicos
            total_rows = len(df)
            slip_count = 0
            valid_slips = []
            
            import re
            for idx in df.index:
                row_text = ' '.join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
                if '729000018' in row_text:
                    slip_match = re.search(r'(729000018\d{3})', row_text)
                    if slip_match:
                        slip_count += 1
                        valid_slips.append(slip_match.group(1))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Filas Totales", total_rows)
            with col2:
                st.metric("📊 Slips Válidos", slip_count)
            with col3:
                completeness = (slip_count / total_rows * 100) if total_rows > 0 else 0
                st.metric("📊 Completitud", f"{completeness:.1f}%")
            
            # 2. Validar secuencia de slips
            if len(valid_slips) > 1:
                first_slip = int(valid_slips[0][-3:])
                last_slip = int(valid_slips[-1][-3:])
                expected_count = last_slip - first_slip + 1
                
                if len(valid_slips) == expected_count:
                    st.success(f"✅ Secuencia completa: {first_slip} a {last_slip} ({len(valid_slips)} slips)")
                else:
                    missing = expected_count - len(valid_slips)
                    st.warning(f"⚠️ Secuencia incompleta: Faltan {missing} slips")
            
            # 3. Calcular totales con validación robusta
            total_13, total_15, valid_totals = self._calculate_robust_totals(df)
            
            st.subheader("📊 Análisis de Totales")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Columna 13 (Total):** {total_13}")
                st.write(f"**Filas con totales válidos:** {valid_totals['col_13']}/{total_rows}")
            with col2:
                st.write(f"**Columna 15 (Tablets Total):** {total_15}")
                st.write(f"**Filas con tablets válidos:** {valid_totals['col_15']}/{total_rows}")
            
            # 4. Detectar totales del PDF automáticamente
            pdf_totals = self._extract_pdf_totals_from_text(df)
            if pdf_totals['found']:
                st.subheader("🎯 Comparación con PDF")
                col1, col2 = st.columns(2)
                
                with col1:
                    match_13 = total_13 == pdf_totals['total_13']
                    icon_13 = "✅" if match_13 else "❌"
                    st.write(f"{icon_13} **Total calculado:** {total_13}")
                    st.write(f"**Total del PDF:** {pdf_totals['total_13']}")
                    
                with col2:
                    match_15 = total_15 == pdf_totals['total_15']
                    icon_15 = "✅" if match_15 else "❌"
                    st.write(f"{icon_15} **Tablets calculado:** {total_15}")
                    st.write(f"**Tablets del PDF:** {pdf_totals['total_15']}")
                
                # Resultado final
                if match_13 and match_15:
                    st.success("🎉 **EXTRACCIÓN PERFECTA** - Totales coinciden 100%")
                else:
                    st.error("❌ **EXTRACCIÓN INCOMPLETA** - Revisar datos faltantes")
            
            # Mostrar muestra de datos
            st.subheader("👁️ Vista Previa de Datos")
            st.dataframe(df.head(10))
            
        except Exception as e:
            st.error(f"Error en validación robusta: {e}")
    
    def _calculate_robust_totals(self, df: pd.DataFrame):
        """Calcula totales de manera robusta verificando múltiples columnas - DEL EXTRACTOR PRO"""
        total_13 = 0
        total_15 = 0
        valid_counts = {'col_13': 0, 'col_15': 0}
        
        # Buscar totales en las columnas esperadas y alternativas
        for idx in df.index:
            # Para columna 13 (Total)
            found_13 = False
            for col_idx in [13, 12, 14]:  # Columnas probables
                if col_idx < len(df.columns):
                    val = str(df.iloc[idx, col_idx])
                    if val.isdigit() and 1 <= int(val) <= 20:  # Rango típico
                        total_13 += int(val)
                        valid_counts['col_13'] += 1
                        found_13 = True
                        break
            
            # Para columna 15 (Tablets Total)  
            found_15 = False
            for col_idx in [15, 14, 16]:  # Columnas probables
                if col_idx < len(df.columns):
                    val = str(df.iloc[idx, col_idx])
                    if val.isdigit() and 1 <= int(val) <= 20:  # Rango típico
                        total_15 += int(val)
                        valid_counts['col_15'] += 1
                        found_15 = True
                        break
        
        return total_13, total_15, valid_counts
    
    def _extract_pdf_totals_from_text(self, df: pd.DataFrame):
        """Extrae los totales finales del PDF desde el propio DataFrame - DEL EXTRACTOR PRO"""
        result = {'found': False, 'total_13': 0, 'total_15': 0}
        
        try:
            import re
            
            # Buscar en las últimas filas números que podrían ser totales
            last_rows_text = ""
            for idx in df.tail(5).index:  # Últimas 5 filas
                row_text = ' '.join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
                last_rows_text += row_text + " "
            
            # Buscar patrón de totales (dos números grandes al final)
            # Patrón: número de 2-3 dígitos seguido de otro número de 2-3 dígitos
            total_pattern = r'\b(\d{2,3})\s+(\d{2,3})\b'
            matches = re.findall(total_pattern, last_rows_text)
            
            if matches:
                # Tomar el último match como los totales finales
                last_match = matches[-1]
                total_13 = int(last_match[0])
                total_15 = int(last_match[1])
                
                # Validar que sean números razonables (no fechas, etc.)
                if 50 <= total_13 <= 500 and 20 <= total_15 <= 200:
                    result['found'] = True
                    result['total_13'] = total_13
                    result['total_15'] = total_15
            
        except Exception as e:
            st.warning(f"No se pudieron extraer totales del PDF: {e}")
        
        return result
    
    def _clean_and_standardize_advanced(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpieza y estandarización avanzada"""
        try:
            # Eliminar filas completamente vacías
            df = df.dropna(how='all').reset_index(drop=True)
            
            # *** NUEVA FUNCIÓN - CORREGIR COLUMNAS CONCATENADAS ***
            df = self._fix_concatenated_columns(df)
            
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
            
            # NUEVO: Mostrar resumen de mejoras aplicadas
            self._show_extraction_summary(df)
            
            return df
            
        except Exception as e:
            st.error(f"❌ Error limpiando datos: {str(e)}")
            return df
    
    def _show_extraction_summary(self, df: pd.DataFrame):
        """Mostrar resumen de la extracción y mejoras aplicadas"""
        try:
            st.markdown("### 📊 Resumen de Extracción Mejorada")
            
            # Estadísticas básicas
            total_rows = len(df)
            fl_rows = len(df[df.iloc[:, 0].astype(str).str.contains('FL', na=False)])
            success_rate = (fl_rows / total_rows * 100) if total_rows > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📋 Total Filas", total_rows)
            
            with col2:
                st.metric("✅ Filas FL Válidas", fl_rows)
            
            with col3:
                st.metric("📊 Tasa de Éxito", f"{success_rate:.1f}%")
            
            with col4:
                st.metric("📏 Columnas", len(df.columns))
            
            # Información sobre mejoras aplicadas
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 15px; border-radius: 10px; margin: 10px 0; color: white;">
                <h4 style="margin: 0 0 10px 0; color: white;">🚀 Mejoras Aplicadas</h4>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>✅ <strong>Extracción inteligente por páginas</strong> con configuraciones específicas</li>
                    <li>✅ <strong>Corrección automática</strong> de columnas concatenadas (ej: FL61D729040036567)</li>
                    <li>✅ <strong>Múltiples métodos Camelot</strong> con fallbacks automáticos</li>
                    <li>✅ <strong>Validación de calidad</strong> con correcciones adicionales</li>
                    <li>✅ <strong>Preparado para futuras páginas</strong> (5, 6, 7, etc.)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar ejemplos de datos extraídos
            if not df.empty:
                st.markdown("### 📋 Muestra de Datos Extraídos")
                
                # Mostrar primeras 5 filas con columnas principales
                display_columns = list(df.columns[:8])  # Primeras 8 columnas
                sample_df = df[display_columns].head(5)
                
                st.dataframe(sample_df, use_container_width=True)
                
                # Información sobre columnas detectadas
                st.info(f"""
                📊 **Columnas detectadas:** {len(df.columns)} columnas
                🎯 **Columnas principales:** {', '.join(display_columns[:5])}...
                💡 **Tip:** Los datos han sido procesados y corregidos automáticamente para manejar las complejidades de la página 4 y futuras páginas.
                """)
            
        except Exception as e:
            st.warning(f"⚠️ Error mostrando resumen: {str(e)}")
    
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
        
        # NUEVO: Normalizar códigos de almacén a MAYÚSCULAS
        if 'WH_Code' in df.columns:
            df['WH_Code'] = df['WH_Code'].str.upper()
            st.info(f"🔧 Normalizados códigos de almacén a mayúsculas (ej: 612d → 612D)")
        
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
            
            # Días desde retorno - NUEVA LÓGICA CON Counted_Date
            if 'Return_Date' in df.columns:
                try:
                    # Para albaranes cerrados (Total_Open = 0): usar Counted_Date - Return_Date
                    # Para albaranes abiertos (Total_Open > 0): usar current_date - Return_Date
                    df['Days_Since_Return'] = 0
                    
                    # Albaranes cerrados: usar Counted_Date si está disponible
                    closed_mask = df.get('Total_Open', pd.Series([0])) == 0
                    if 'Counted_Date' in df.columns:
                        # Para albaranes cerrados con Counted_Date válida
                        closed_with_counted = closed_mask & df['Counted_Date'].notna()
                        df.loc[closed_with_counted, 'Days_Since_Return'] = (
                            df.loc[closed_with_counted, 'Counted_Date'] - 
                            df.loc[closed_with_counted, 'Return_Date']
                        ).dt.days
                        
                        # Para albaranes cerrados sin Counted_Date, usar current_date
                        closed_without_counted = closed_mask & df['Counted_Date'].isna()
                        df.loc[closed_without_counted, 'Days_Since_Return'] = (
                            current_date - df.loc[closed_without_counted, 'Return_Date']
                        ).dt.days
                    else:
                        # Si no hay Counted_Date, usar current_date para cerrados
                        df.loc[closed_mask, 'Days_Since_Return'] = (
                            current_date - df.loc[closed_mask, 'Return_Date']
                        ).dt.days
                    
                    # Albaranes abiertos: siempre usar current_date
                    open_mask = df.get('Total_Open', pd.Series([0])) > 0
                    df.loc[open_mask, 'Days_Since_Return'] = (
                        current_date - df.loc[open_mask, 'Return_Date']
                    ).dt.days
                    
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
            
            # Score de prioridad mejorado - VERSIÓN ROBUSTA
            # Calcular score basado en datos disponibles
            score_components = []
            weights = []
            
            # Días desde retorno (siempre disponible)
            if 'Days_Since_Return' in df.columns:
                days_score = pd.to_numeric(df['Days_Since_Return'], errors='coerce').fillna(0)
                score_components.append(days_score)
                weights.append(0.4)
            
            # Tablillas abiertas (siempre disponible)
            if 'Total_Open' in df.columns:
                open_score = pd.to_numeric(df['Total_Open'], errors='coerce').fillna(0)
                score_components.append(open_score)
                weights.append(0.3)
            
            # Delays (si están disponibles)
            if 'Counting_Delay' in df.columns:
                counting_score = pd.to_numeric(df['Counting_Delay'], errors='coerce').fillna(0)
                score_components.append(counting_score)
                weights.append(0.2)
            
            if 'Validation_Delay' in df.columns:
                validation_score = pd.to_numeric(df['Validation_Delay'], errors='coerce').fillna(0)
                score_components.append(validation_score)
                weights.append(0.1)
            
            # Calcular score ponderado
            if score_components:
                df['Priority_Score'] = sum(comp * weight for comp, weight in zip(score_components, weights))
            else:
                # Fallback: usar solo días desde retorno
                df['Priority_Score'] = pd.to_numeric(df.get('Days_Since_Return', pd.Series([0])), errors='coerce').fillna(0)
            
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
    # Inicializar session_state para evitar problemas de transparencia
    if 'pdf_excel_generated' not in st.session_state:
        st.session_state['pdf_excel_generated'] = False
    if 'pdf_excel_data' not in st.session_state:
        st.session_state['pdf_excel_data'] = None
    if 'pdf_filename' not in st.session_state:
        st.session_state['pdf_filename'] = None
    
    # JavaScript para forzar visibilidad y evitar transparencia
    st.markdown("""
    <script>
    // Forzar visibilidad de la aplicación
    function forceVisibility() {
        const app = document.querySelector('.stApp');
        if (app) {
            app.style.opacity = '1';
            app.style.visibility = 'visible';
            app.style.backgroundColor = '#ffffff';
        }
        
        // Forzar visibilidad de todos los elementos
        const allElements = document.querySelectorAll('.stApp *');
        allElements.forEach(el => {
            el.style.opacity = '1';
            el.style.visibility = 'visible';
        });
    }
    
    // Ejecutar inmediatamente
    forceVisibility();
    
    // Ejecutar después de cada cambio
    const observer = new MutationObserver(forceVisibility);
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """, unsafe_allow_html=True)
    
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
        # Limpiar estado anterior al procesar nuevo PDF
        if st.session_state.get('pdf_excel_generated', False):
            st.session_state['pdf_excel_generated'] = False
            st.session_state['pdf_excel_data'] = None
            st.session_state['pdf_filename'] = None
        
        st.markdown('<div class="file-info">📄 <strong>Procesando PDF...</strong></div>', 
                    unsafe_allow_html=True)
        
        # Información sobre tiempo de procesamiento
        st.info("""
        ⏱️ **Tiempo de procesamiento adaptativo:**
        - 📄 PDF pequeño (< 1MB): 30-60 segundos
        - 📄 PDF mediano (1-5MB): 1-2 minutos  
        - 📄 PDF grande (> 5MB): 2-4 minutos
        
        🧠 **Método inteligente** que prueba múltiples estrategias y separa filas concatenadas
        """)
        
        # Extraer datos
        start_time = time.time()
        extractor = TablillasExtractorPro()
        df = extractor.extract_from_pdf(uploaded_file)
        end_time = time.time()
        
        processing_time = end_time - start_time
        st.success(f"⏱️ Tiempo de procesamiento: {processing_time:.1f} segundos")
        
        if df is not None and not df.empty:
            st.markdown('<div class="success-box">✅ <strong>¡Extracción exitosa!</strong></div>', 
                        unsafe_allow_html=True)
            
            # Mostrar resumen de datos extraídos
            show_extraction_summary(df)
            
            # NUEVO: Análisis visual profesional
            show_visual_analysis_dashboard(df)
            
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
        'Counted_Date', 'Priority_Level', 'Urgency_Category'
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
            
            # Guardar en session_state para evitar recarga
            st.session_state['pdf_excel_data'] = excel_data
            st.session_state['pdf_filename'] = filename
            st.session_state['pdf_excel_generated'] = True
            
            st.success(f"✅ Excel generado: **{filename}**")
            
            # Información para el usuario
            st.info("""
            💡 **Guarda este archivo localmente** con la fecha del día.
            Luego usa la pestaña "ANÁLISIS MULTI-EXCEL" para comparar múltiples días.
            """)
    
    # NUEVO: Mostrar botón de descarga automáticamente si se generó Excel
    if st.session_state.get('pdf_excel_generated', False):
        # Usar st.empty() para mantener el contenido visible
        download_container = st.container()
        
        with download_container:
            st.markdown('<div class="section-header">💾 DESCARGAR EXCEL GENERADO</div>', 
                        unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.success("✅ Excel listo para descargar")
            
            with col2:
                st.download_button(
                    label="💾 Descargar Excel Completo",
                    data=st.session_state.get('pdf_excel_data'),
                    file_name=st.session_state.get('pdf_filename', 'tablillas_procesadas.xlsx'),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
    
    # Botón para limpiar estado y evitar problemas de transparencia
    if st.session_state.get('pdf_excel_generated', False):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔄 Limpiar Estado", help="Limpia el estado para evitar problemas de transparencia"):
                st.session_state['pdf_excel_generated'] = False
                st.session_state['pdf_excel_data'] = None
                st.session_state['pdf_filename'] = None
                st.success("✅ Estado limpiado correctamente")
        
        with col2:
            if st.button("🔄 Recargar Página", help="Recarga la página para limpiar completamente"):
                st.session_state.clear()
                st.experimental_rerun()

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
    """Pestaña para análisis multi-Excel - VERSIÓN CORREGIDA"""
    st.markdown('<div class="section-header">📊 ANÁLISIS MULTI-EXCEL</div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    ### 📄 Cargar múltiples archivos Excel para análisis comparativo
    
    Sube **2 o más archivos Excel** generados en días diferentes para:
    - 📈 Ver tendencias y evolución
    - 📄 Detectar cambios día a día  
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
        st.info(f"📂 {len(uploaded_excel_files)} archivos seleccionados. Procesando...")
        
        # NUEVA FUNCIÓN - Procesar directamente sin archivos temporales
        analyzer = ExcelAnalyzer()
        excel_data = load_excel_files_direct(uploaded_excel_files)
        
        if len(excel_data) >= 2:
            st.success(f"✅ {len(excel_data)} archivos cargados correctamente")
            
            # Mostrar información de archivos cargados
            st.write("**Archivos procesados:**")
            for date, df in excel_data.items():
                st.write(f"- **{date}**: {len(df)} albaranes, {df['Total_Open'].sum() if 'Total_Open' in df.columns else 0} tablillas pendientes")
            
            # Realizar análisis comparativo
            analysis_results = analyzer.compare_excel_files(excel_data)
            
            if "error" not in analysis_results:
                show_comparative_analysis(analysis_results, excel_data)
                
                # Opción de exportar informe profesional - VERSIÓN MEJORADA
                st.markdown('<div class="section-header">💾 EXPORTAR INFORME PROFESIONAL</div>', 
                            unsafe_allow_html=True)
                
                # NUEVO: Usar st.download_button para evitar recarga de página
                col1, col2 = st.columns(2)
                
                with col1:
                    # Generar el Excel en memoria
                    excel_data_bytes = export_professional_multi_day_report(analysis_results, excel_data)
                    
                    st.download_button(
                        label="📊 Descargar Informe Ejecutivo Multi-Días",
                        data=excel_data_bytes,
                        file_name=f"Informe_Ejecutivo_MultiDias_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        help="Descarga el informe ejecutivo sin perder el dashboard"
                    )
                
                with col2:
                    # Generar el Excel de tendencias en memoria
                    trends_data_bytes = export_comprehensive_trends_report(analysis_results, excel_data)
                    
                    st.download_button(
                        label="📈 Descargar Análisis Completo de Tendencias",
                        data=trends_data_bytes,
                        file_name=f"Analisis_Tendencias_Completo_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="secondary",
                        help="Descarga el análisis completo sin perder el dashboard"
                    )
                
                # NUEVO: Mensaje informativo
                st.info("💡 **Tip:** Los archivos se descargan directamente sin afectar el dashboard. ¡Puedes seguir analizando mientras descargas!")
            else:
                st.error(analysis_results["error"])
        else:
            st.error("❌ No se pudieron cargar suficientes archivos válidos")
    
    elif uploaded_excel_files and len(uploaded_excel_files) == 1:
        st.warning("⚠️ Se necesitan al menos 2 archivos para hacer comparación")
    
    else:
        st.info("📂 Selecciona múltiples archivos Excel para comenzar el análisis")

def load_excel_files_direct(uploaded_files) -> Dict[str, pd.DataFrame]:
    """Cargar archivos Excel directamente sin archivos temporales - NUEVA FUNCIÓN"""
    excel_data = {}
    
    for uploaded_file in uploaded_files:
        try:
            st.write(f"🔍 Procesando: {uploaded_file.name}")
            
            # Leer directamente del objeto UploadedFile
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            st.write(f"✅ Leído correctamente: {len(df)} filas, {len(df.columns)} columnas")
            
            # Extraer fecha del nombre del archivo
            file_name = uploaded_file.name
            
            # Intentar extraer fecha del nombre (formato: tablillas_YYYYMMDD_HHMM.xlsx)
            date_match = re.search(r'(\d{8})_(\d{4})', file_name)
            if date_match:
                date_str = date_match.group(1)
                file_date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
                st.write(f"📅 Fecha extraída: {file_date}")
            else:
                # Usar timestamp actual como fallback
                file_date = datetime.now().strftime('%Y-%m-%d_%H%M')
                st.write(f"📅 Usando fecha actual: {file_date}")
            
            # NUEVO: Normalizar códigos de almacén en archivos Excel
            if 'WH_Code' in df.columns:
                df['WH_Code'] = df['WH_Code'].str.upper()
                st.info(f"🔧 Normalizados códigos de almacén en {file_name}")
            
            # Verificar que el DataFrame tiene las columnas esperadas
            if 'Return_Packing_Slip' in df.columns or 'WH_Code' in df.columns:
                excel_data[file_date] = df
                st.success(f"✅ {file_name} cargado como {file_date}")
            else:
                st.warning(f"⚠️ {file_name} no parece tener el formato esperado")
                
                # Mostrar columnas disponibles para debug
                st.write(f"Columnas disponibles: {list(df.columns[:10])}")  # Mostrar solo las primeras 10
                
                # Intentar cargar de todos modos
                excel_data[file_date] = df
                st.info(f"ℹ️ Cargado de todos modos para análisis")
                
        except Exception as e:
            st.error(f"❌ Error cargando {uploaded_file.name}: {str(e)}")
            
            # Información adicional para debug
            st.write(f"Tipo de archivo: {type(uploaded_file)}")
            st.write(f"Tamaño: {uploaded_file.size} bytes")
            
            # Intentar con otro engine
            try:
                st.write("🔄 Intentando con engine alternativo...")
                uploaded_file.seek(0)  # Reset file pointer
                df = pd.read_excel(uploaded_file, engine='xlrd')
                
                # Extraer fecha
                file_name = uploaded_file.name
                date_match = re.search(r'(\d{8})_(\d{4})', file_name)
                if date_match:
                    date_str = date_match.group(1)
                    file_date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
                else:
                    file_date = datetime.now().strftime('%Y-%m-%d_%H%M')
                
                # NUEVO: Normalizar códigos de almacén también en engine alternativo
                if 'WH_Code' in df.columns:
                    df['WH_Code'] = df['WH_Code'].str.upper()
                    st.info(f"🔧 Normalizados códigos de almacén en {file_name} (engine alternativo)")
                
                excel_data[file_date] = df
                st.success(f"✅ {file_name} cargado con engine alternativo")
                
            except Exception as e2:
                st.error(f"❌ Error también con engine alternativo: {str(e2)}")
                continue
    
    return excel_data

def show_comparative_analysis(analysis_results: Dict, excel_data: Dict[str, pd.DataFrame]):
    """Mostrar análisis comparativo completo"""
    
    # Resumen general
    show_analysis_summary(analysis_results["summary"])
    
    # Evolución temporal
    show_temporal_evolution(analysis_results["summary"]["open_evolution"])
    
    # Comparaciones día a día
    show_daily_comparisons(analysis_results["comparisons"])
    
    # Análisis de tendencias
    show_trend_analysis(excel_data)

def show_analysis_summary(summary: Dict):
    """Mostrar resumen del análisis - VERSIÓN MEJORADA"""
    st.markdown('<div class="section-header">📊 RESUMEN DEL ANÁLISIS</div>', 
                unsafe_allow_html=True)
    
    # NUEVO: Dashboard visual profesional
    show_executive_dashboard(summary)
    
    # Métricas tradicionales (mantenidas)
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

def show_executive_dashboard(summary: Dict):
    """NUEVA FUNCIÓN: Dashboard ejecutivo visual profesional"""
    
    # CSS personalizado para cards profesionales
    st.markdown("""
    <style>
    .executive-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .kpi-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 5px;
    }
    .success-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 5px;
    }
    .warning-card {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header ejecutivo
    st.markdown("""
    <div class="executive-card">
        <h2 style="margin: 0; text-align: center;">🎯 DASHBOARD EJECUTIVO</h2>
        <p style="margin: 5px 0; text-align: center; opacity: 0.9;">Análisis Comparativo de Tablillas - Alsina Forms Co.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # KPIs principales en cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <h3 style="margin: 0; font-size: 2em;">{summary.get('total_new_albaranes', 0)}</h3>
            <p style="margin: 5px 0; font-size: 0.9em;">📈 NUEVOS ALBARANES</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="success-card">
            <h3 style="margin: 0; font-size: 2em;">{summary.get('total_closed_albaranes', 0)}</h3>
            <p style="margin: 5px 0; font-size: 0.9em;">✅ ALBARANES CERRADOS</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="warning-card">
            <h3 style="margin: 0; font-size: 2em;">{summary.get('total_closed_tablets', 0)}</h3>
            <p style="margin: 5px 0; font-size: 0.9em;">🔒 TABLILLAS CERRADAS</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <h3 style="margin: 0; font-size: 2em;">{summary.get('total_added_tablets', 0)}</h3>
            <p style="margin: 5px 0; font-size: 0.9em;">➕ TABLILLAS AGREGADAS</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Información adicional
    st.markdown(f"""
    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 10px 0;">
        <h4 style="color: #495057; margin: 0 0 10px 0;">📊 INFORMACIÓN DEL ANÁLISIS</h4>
        <p style="margin: 5px 0; color: #6c757d;"><strong>📅 Período:</strong> {summary.get('analysis_period', 'N/A')}</p>
        <p style="margin: 5px 0; color: #6c757d;"><strong>📁 Archivos analizados:</strong> {summary.get('num_files_analyzed', 0)}</p>
        <p style="margin: 5px 0; color: #6c757d;"><strong>📈 Fecha más reciente:</strong> {summary.get('most_recent_date', 'N/A')}</p>
        <p style="margin: 5px 0; color: #6c757d;"><strong>📉 Fecha más antigua:</strong> {summary.get('oldest_date', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)

def show_temporal_evolution(open_evolution: List[Dict]):
    """Mostrar evolución temporal - VERSIÓN MEJORADA"""
    st.subheader("📈 Evolución de Tablillas Pendientes")
    
    if open_evolution:
        df_evolution = pd.DataFrame(open_evolution)
        df_evolution['date'] = pd.to_datetime(df_evolution['date'])
        
        # NUEVO: Gráfico más profesional con colores corporativos
        fig = px.line(
            df_evolution,
            x='date',
            y='total_open',
            title='📊 Evolución Diaria de Tablillas Pendientes',
            markers=True,
            color_discrete_sequence=['#667eea']
        )
        
        # Mejoras visuales
        fig.update_layout(
            xaxis_title="📅 Fecha",
            yaxis_title="🔢 Tablillas Pendientes",
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            title_font_size=16,
            title_x=0.5,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        # Línea más gruesa y puntos
        fig.update_traces(
            line=dict(width=4),
            marker=dict(size=8, color='#667eea'),
            hovertemplate='<b>%{x}</b><br>Tablillas: %{y}<extra></extra>'
        )
        
        # Grid más sutil
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # NUEVO: Métricas adicionales
        if len(df_evolution) > 1:
            show_evolution_metrics(df_evolution)

def show_evolution_metrics(df_evolution: pd.DataFrame):
    """NUEVA FUNCIÓN: Métricas de evolución temporal"""
    
    # Calcular métricas
    total_change = df_evolution['total_open'].iloc[-1] - df_evolution['total_open'].iloc[0]
    max_open = df_evolution['total_open'].max()
    min_open = df_evolution['total_open'].min()
    avg_open = df_evolution['total_open'].mean()
    
    # Determinar tendencia
    if total_change > 0:
        trend_icon = "📈"
        trend_text = "CRECIENTE"
        trend_color = "#dc3545"
    elif total_change < 0:
        trend_icon = "📉"
        trend_text = "DECRECIENTE"
        trend_color = "#28a745"
    else:
        trend_icon = "➡️"
        trend_text = "ESTABLE"
        trend_color = "#ffc107"
    
    # Mostrar métricas en cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 15px; border-radius: 10px; color: white; text-align: center;">
            <h4 style="margin: 0; font-size: 1.5em;">{trend_icon}</h4>
            <p style="margin: 5px 0; font-size: 0.9em;">TENDENCIA</p>
            <p style="margin: 0; font-weight: bold;">{trend_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 15px; border-radius: 10px; color: white; text-align: center;">
            <h4 style="margin: 0; font-size: 1.5em;">{max_open}</h4>
            <p style="margin: 5px 0; font-size: 0.9em;">MÁXIMO</p>
            <p style="margin: 0; font-weight: bold;">TABLILLAS</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                    padding: 15px; border-radius: 10px; color: white; text-align: center;">
            <h4 style="margin: 0; font-size: 1.5em;">{min_open}</h4>
            <p style="margin: 5px 0; font-size: 0.9em;">MÍNIMO</p>
            <p style="margin: 0; font-weight: bold;">TABLILLAS</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 15px; border-radius: 10px; color: white; text-align: center;">
            <h4 style="margin: 0; font-size: 1.5em;">{avg_open:.0f}</h4>
            <p style="margin: 5px 0; font-size: 0.9em;">PROMEDIO</p>
            <p style="margin: 0; font-weight: bold;">TABLILLAS</p>
        </div>
        """, unsafe_allow_html=True)

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

def show_visual_analysis_dashboard(df: pd.DataFrame):
    """Dashboard visual profesional para análisis del día"""
    st.markdown('<div class="section-header">📊 ANÁLISIS VISUAL PROFESIONAL</div>', 
                unsafe_allow_html=True)
    
    # Verificar que tenemos datos para analizar
    if df.empty:
        st.warning("⚠️ No hay datos para analizar")
        return
    
    # Análisis por almacén
    show_warehouse_analysis(df)
    
    # Análisis de antigüedad
    show_aging_analysis(df)
    
    # Análisis de eficiencia y performance
    show_performance_analysis(df)

def show_warehouse_analysis(df: pd.DataFrame):
    """Análisis comparativo por almacén"""
    st.subheader("🏢 Análisis por Almacén")
    
    if 'WH_Code' not in df.columns:
        st.info("📋 No hay información de almacenes para analizar")
        return
    
    # Preparar datos por almacén - CORREGIDO para incluir albaranes cerrados
    wh_summary = df.groupby('WH_Code').agg({
        'Total_Open': ['sum', lambda x: (x == 0).sum()],  # Suma de pendientes + conteo de cerrados
        'Total_Tablets': 'sum',
        'Counting_Delay': ['mean', 'max'],
        'Validation_Delay': 'mean',
        'Return_Packing_Slip': 'count',
        'Days_Since_Return': 'mean',
        'Priority_Score': 'mean'
    }).round(2)
    
    # Aplanar columnas multinivel
    wh_summary.columns = ['Pendientes', 'Albaranes_Cerrados', 'Total_Tablillas', 'Retraso_Prom', 'Retraso_Max', 
                         'Val_Delay_Prom', 'Num_Albaranes', 'Días_Prom', 'Score_Prom']
    wh_summary = wh_summary.reset_index()
    
    # Calcular métricas adicionales - CORREGIDO para usar lógica de albaranes cerrados
    # Eficiencia = Albaranes cerrados / Total albaranes
    wh_summary['Eficiencia'] = (wh_summary['Albaranes_Cerrados'] / wh_summary['Num_Albaranes'] * 100).round(1)
    wh_summary['Urgencia'] = (wh_summary['Días_Prom'] + wh_summary['Retraso_Prom']).round(1)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de tablillas pendientes por almacén
        fig1 = px.bar(
            wh_summary,
            x='WH_Code',
            y='Pendientes',
            title='📊 Tablillas Pendientes por Almacén',
            color='Eficiencia',
            color_continuous_scale='RdYlGn',
            text='Pendientes',
            hover_data=['Num_Albaranes', 'Retraso_Prom']
        )
        
        fig1.update_traces(texttemplate='%{text}', textposition='outside')
        fig1.update_layout(
            xaxis_title="Almacén",
            yaxis_title="Tablillas Pendientes",
            showlegend=False
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Gráfico de eficiencia por almacén
        fig2 = px.scatter(
            wh_summary,
            x='Retraso_Prom',
            y='Eficiencia',
            size='Num_Albaranes',
            color='WH_Code',
            title='🎯 Eficiencia vs Retraso por Almacén',
            hover_data=['Pendientes', 'Total_Tablillas'],
            size_max=60
        )
        
        fig2.update_layout(
            xaxis_title="Retraso Promedio (días)",
            yaxis_title="Eficiencia (%)",
            legend_title="Almacén"
        )
        
        # Líneas de referencia
        fig2.add_hline(y=80, line_dash="dash", line_color="green", 
                      annotation_text="Meta Eficiencia 80%")
        fig2.add_vline(x=10, line_dash="dash", line_color="red", 
                      annotation_text="Límite Retraso 10 días")
        
        st.plotly_chart(fig2, use_container_width=True)
    
    # Tabla resumen por almacén
    st.subheader("📋 Resumen Detallado por Almacén")
    
    # Colorear filas según performance
    def color_efficiency(val):
        if val >= 80:
            return 'background-color: #d4edda'  # Verde
        elif val >= 60:
            return 'background-color: #fff3cd'  # Amarillo
        else:
            return 'background-color: #f8d7da'  # Rojo
    
    # Mostrar tabla con formato
    styled_summary = wh_summary.style.applymap(
        color_efficiency, subset=['Eficiencia']
    ).format({
        'Eficiencia': '{:.1f}%',
        'Retraso_Prom': '{:.1f} días',
        'Retraso_Max': '{:.1f} días',
        'Días_Prom': '{:.1f} días',
        'Score_Prom': '{:.2f}'
    })
    
    st.dataframe(styled_summary, use_container_width=True)
    
    # Rankings de almacenes
    col1, col2, col3 = st.columns(3)
    
    with col1:
        best_efficiency = wh_summary.loc[wh_summary['Eficiencia'].idxmax()]
        st.metric("🏆 Mejor Eficiencia", 
                 f"{best_efficiency['WH_Code']}", 
                 f"{best_efficiency['Eficiencia']:.1f}%")
    
    with col2:
        worst_delay = wh_summary.loc[wh_summary['Retraso_Prom'].idxmax()]
        st.metric("⚠️ Mayor Retraso", 
                 f"{worst_delay['WH_Code']}", 
                 f"{worst_delay['Retraso_Prom']:.1f} días")
    
    with col3:
        most_pending = wh_summary.loc[wh_summary['Pendientes'].idxmax()]
        st.metric("📊 Más Pendientes", 
                 f"{most_pending['WH_Code']}", 
                 f"{most_pending['Pendientes']} tablillas")

def show_aging_analysis(df: pd.DataFrame):
    """Análisis de antigüedad de albaranes"""
    st.subheader("⏰ Análisis de Antigüedad de Albaranes")
    
    if 'Days_Since_Return' not in df.columns or 'Return_Date' not in df.columns:
        st.info("📅 No hay información de fechas para analizar antigüedad")
        return
    
    # Filtrar solo albaranes con tablillas pendientes
    pending_df = df[df.get('Total_Open', 0) > 0].copy()
    
    if pending_df.empty:
        st.success("🎉 ¡Excelente! No hay albaranes pendientes para analizar")
        return
    
    # Categorizar por antigüedad
    def categorize_age(days):
        if days <= 7:
            return '📗 Reciente (≤7 días)'
        elif days <= 15:
            return '📙 Moderado (8-15 días)'
        elif days <= 30:
            return '📕 Antiguo (16-30 días)'
        else:
            return '🚨 Crítico (>30 días)'
    
    pending_df['Age_Category'] = pending_df['Days_Since_Return'].apply(categorize_age)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución por antigüedad
        age_dist = pending_df['Age_Category'].value_counts()
        
        colors = {
            '📗 Reciente (≤7 días)': '#28a745',
            '📙 Moderado (8-15 días)': '#ffc107', 
            '📕 Antiguo (16-30 días)': '#fd7e14',
            '🚨 Crítico (>30 días)': '#dc3545'
        }
        
        fig3 = px.pie(
            values=age_dist.values,
            names=age_dist.index,
            title='📊 Distribución por Antigüedad',
            color=age_dist.index,
            color_discrete_map=colors
        )
        
        fig3.update_traces(textinfo='percent+label')
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        # Timeline de albaranes más antiguos
        oldest_15 = pending_df.nlargest(15, 'Days_Since_Return')[
            ['Return_Packing_Slip', 'Customer_Name', 'Days_Since_Return', 'Total_Open', 'WH_Code']
        ].copy()
        
        fig4 = px.bar(
            oldest_15,
            x='Days_Since_Return',
            y='Return_Packing_Slip',
            orientation='h',
            title='⏱️ Top 15 Albaranes Más Antiguos',
            color='Total_Open',
            color_continuous_scale='Reds',
            hover_data=['Customer_Name', 'WH_Code']
        )
        
        fig4.update_layout(
            xaxis_title="Días desde Retorno",
            yaxis_title="Albarán",
            height=500
        )
        
        st.plotly_chart(fig4, use_container_width=True)
    
    # Análisis del mes actual
    current_month = pd.Timestamp.now().replace(day=1)
    
    # Asegurar que Return_Date sea datetime
    if 'Return_Date' in pending_df.columns:
        try:
            pending_df['Return_Date'] = pd.to_datetime(pending_df['Return_Date'], errors='coerce')
            month_old = pending_df[pending_df['Return_Date'] < current_month]
        except Exception as e:
            st.warning(f"⚠️ Error procesando fechas: {str(e)}")
            month_old = pd.DataFrame()  # DataFrame vacío si hay error
    else:
        month_old = pd.DataFrame()  # DataFrame vacío si no hay columna de fecha
    
    if not month_old.empty:
        st.markdown("### 🚨 Albaranes NO Resueltos del Mes Anterior")
        
        month_summary = month_old.groupby('WH_Code').agg({
            'Total_Open': 'sum',
            'Return_Packing_Slip': 'count',
            'Days_Since_Return': 'mean'
        }).round(1)
        
        month_summary.columns = ['Tablillas_Pendientes', 'Num_Albaranes', 'Días_Promedio']
        month_summary = month_summary.sort_values('Días_Promedio', ascending=False)
        
        st.dataframe(month_summary, use_container_width=True)
        
        total_old_tablets = month_old['Total_Open'].sum()
        total_old_albaranes = len(month_old)
        avg_age = month_old['Days_Since_Return'].mean()
        
        st.error(f"""
        ⚠️ **ATENCIÓN REQUERIDA**: {total_old_albaranes} albaranes del mes anterior siguen pendientes
        - 🔓 **{total_old_tablets} tablillas** sin resolver
        - ⏰ **{avg_age:.1f} días** de antigüedad promedio
        - 🎯 **Acción recomendada**: Priorizar resolución inmediata
        """)

def show_performance_analysis(df: pd.DataFrame):
    """Análisis de performance y tendencias"""
    st.subheader("📈 Análisis de Performance")
    
    # Análisis de prioridades por almacén
    if 'Priority_Level' in df.columns and 'WH_Code' in df.columns:
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribución de prioridades por almacén
            priority_by_wh = df.groupby(['WH_Code', 'Priority_Level']).size().reset_index(name='count')
            
            fig5 = px.bar(
                priority_by_wh,
                x='WH_Code',
                y='count',
                color='Priority_Level',
                title='🎯 Distribución de Prioridades por Almacén',
                color_discrete_map={
                    'Baja': '#28a745',
                    'Media': '#ffc107',
                    'Alta': '#fd7e14', 
                    'Crítica': '#dc3545'
                }
            )
            
            fig5.update_layout(
                xaxis_title="Almacén",
                yaxis_title="Cantidad de Albaranes",
                legend_title="Prioridad"
            )
            
            st.plotly_chart(fig5, use_container_width=True)
        
        with col2:
            # Correlación entre días y tablillas pendientes
            if 'Days_Since_Return' in df.columns:
                fig6 = px.scatter(
                    df[df['Total_Open'] > 0],
                    x='Days_Since_Return',
                    y='Total_Open',
                    color='WH_Code',
                    size='Priority_Score',
                    title='📊 Relación: Antigüedad vs Tablillas Pendientes',
                    hover_data=['Customer_Name', 'Return_Packing_Slip']
                )
                
                fig6.update_layout(
                    xaxis_title="Días desde Retorno",
                    yaxis_title="Tablillas Pendientes"
                )
                
                st.plotly_chart(fig6, use_container_width=True)
    
    # Métricas de performance
    show_performance_metrics(df)

def show_performance_metrics(df: pd.DataFrame):
    """Mostrar métricas clave de performance"""
    st.subheader("🎯 Métricas Clave de Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calcular métricas
    total_albaranes = len(df)
    total_pending = df.get('Total_Open', pd.Series([0])).sum()
    total_tablets = df.get('Total_Tablets', pd.Series([0])).sum()
    
    # CORREGIDO: Tasa de Finalización = Albaranes cerrados / Total albaranes
    # Un albarán está cerrado cuando Total_Open = 0
    closed_albaranes = len(df[df.get('Total_Open', pd.Series([0])) == 0])
    
    if total_albaranes > 0:
        completion_rate = (closed_albaranes / total_albaranes * 100)
    else:
        completion_rate = 0
    
    avg_age = df.get('Days_Since_Return', pd.Series([0])).mean()
    
    critical_count = len(df[df.get('Priority_Level', '') == 'Crítica'])
    
    old_month_count = 0
    if 'Return_Date' in df.columns:
        current_month = pd.Timestamp.now().replace(day=1)
        old_month_count = len(df[df['Return_Date'] < current_month])
    
    with col1:
        st.metric("📊 Tasa de Finalización", 
                 f"{completion_rate:.1f}%",
                 help="Porcentaje de albaranes cerrados (Total_Open = 0) vs total de albaranes")
    
    with col2:
        st.metric("⏰ Antigüedad Promedio", 
                 f"{avg_age:.1f} días",
                 help="Días promedio para cerrar albaranes: cerrados (Counted_Date - Return_Date), abiertos (hoy - Return_Date)")
    
    with col3:
        st.metric("🚨 Items Críticos", 
                 critical_count,
                 help="Albaranes que requieren atención inmediata")
    
    with col4:
        st.metric("📅 Del Mes Anterior", 
                 old_month_count,
                 help="Albaranes que vienen del mes anterior")
    
    # Nota explicativa sobre el cálculo de antigüedad
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 15px; border-radius: 10px; margin: 10px 0; color: white;">
        <h4 style="margin: 0 0 10px 0; color: white;">📊 ¿Cómo se calcula la Antigüedad Promedio?</h4>
        <p style="margin: 0; font-size: 14px;">
            <strong>🎯 Lógica Inteligente:</strong><br>
            • <strong>Albaranes Cerrados</strong> (Total_Open = 0): Días entre <em>Return_Date</em> y <em>Counted_Date</em><br>
            • <strong>Albaranes Abiertos</strong> (Total_Open > 0): Días entre <em>Return_Date</em> y hoy<br>
            <em>💡 Counted_Date = Fecha definitiva de cierre (no se puede reabrir)</em>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Alertas de rendimiento
    if completion_rate < 70:
        st.warning(f"⚠️ **Tasa de finalización baja**: {completion_rate:.1f}% - Meta recomendada: >80%")
    
    if avg_age > 15:
        st.warning(f"⚠️ **Antigüedad alta**: {avg_age:.1f} días promedio - Meta recomendada: <10 días")
    
    if old_month_count > 0:
        st.error(f"🚨 **Rezago del mes anterior**: {old_month_count} albaranes requieren atención prioritaria")

def show_trend_analysis(excel_data: Dict[str, pd.DataFrame]):
    """Análisis de tendencias avanzado"""
    st.markdown('<div class="section-header">📊 ANÁLISIS DE TENDENCIAS</div>', 
                unsafe_allow_html=True)
    
    dates = sorted(excel_data.keys())
    
    # Análisis por almacén
    if len(dates) >= 2:
        wh_trends = analyze_warehouse_trends(excel_data, dates)
        show_warehouse_trends(wh_trends)

def analyze_warehouse_trends(excel_data: Dict[str, pd.DataFrame], dates: List[str]) -> Dict:
    """Analizar tendencias por almacén"""
    wh_data = {}
    
    for date in dates:
        df = excel_data[date]
        
        if 'WH_Code' in df.columns and 'Total_Open' in df.columns:
            wh_summary = df.groupby('WH_Code')['Total_Open'].sum()
            
            for wh, total_open in wh_summary.items():
                if wh not in wh_data:
                    wh_data[wh] = []
                wh_data[wh].append({'date': date, 'total_open': total_open})
    
    return wh_data

def show_warehouse_trends(wh_trends: Dict):
    """Mostrar tendencias por almacén"""
    if wh_trends:
        st.subheader("🏢 Tendencias por Almacén")
        
        # Crear gráfico de líneas múltiples
        fig = go.Figure()
        
        for wh, data in wh_trends.items():
            if len(data) >= 2:  # Solo mostrar almacenes con al menos 2 puntos de datos
                df_wh = pd.DataFrame(data)
                df_wh['date'] = pd.to_datetime(df_wh['date'])
                
                fig.add_trace(go.Scatter(
                    x=df_wh['date'],
                    y=df_wh['total_open'],
                    mode='lines+markers',
                    name=f"Almacén {wh}",
                    line=dict(width=3)
                ))
        
        fig.update_layout(
            title="Evolución de Tablillas Pendientes por Almacén",
            xaxis_title="Fecha",
            yaxis_title="Tablillas Pendientes",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)

def export_professional_multi_day_report(analysis_results: Dict, excel_data: Dict[str, pd.DataFrame]):
    """Exportar informe profesional multi-días - VERSIÓN MEJORADA Y OPTIMIZADA"""
    output = io.BytesIO()
    
    # NUEVO: Mostrar progreso de generación
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔄 Generando informe ejecutivo...")
        progress_bar.progress(10)
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # HOJA 1: Dashboard Ejecutivo (MEJORADO)
            summary = analysis_results.get('summary', {})
            
            # Calcular métricas avanzadas
            total_new = summary.get('total_new_albaranes', 0)
            total_closed = summary.get('total_closed_albaranes', 0)
            total_tablets_closed = summary.get('total_closed_tablets', 0)
            total_tablets_added = summary.get('total_added_tablets', 0)
            num_files = summary.get('num_files_analyzed', 1)
            
            # Métricas de performance - CORREGIDO para usar lógica de albaranes cerrados
            # Eficiencia = Albaranes cerrados / (Albaranes cerrados + Albaranes nuevos)
            efficiency = (total_closed / max(total_closed + total_new, 1)) * 100
            activity_score = (total_tablets_closed + total_tablets_added) / max(num_files, 1)
            closure_rate = (total_closed / max(total_new + total_closed, 1)) * 100
            
            executive_data = {
                '📊 MÉTRICA': [
                    '📅 Período de Análisis',
                    '📁 Archivos Analizados',
                    '📉 Fecha Más Antigua',
                    '📈 Fecha Más Reciente',
                    '',
                    '🆕 NUEVOS ALBARANES',
                    '✅ ALBARANES CERRADOS',
                    '🔒 TABLILLAS CERRADAS',
                    '➕ TABLILLAS AGREGADAS',
                    '',
                    '📊 EFICIENCIA DE CIERRE (%)',
                    '🎯 SCORE DE ACTIVIDAD',
                    '⚡ TASA DE CIERRE (%)',
                    '📈 NETO TABLILLAS',
                    '🔄 RATIO CIERRE/NUEVO'
                ],
                '📈 VALOR': [
                    summary.get('analysis_period', 'N/A'),
                    summary.get('num_files_analyzed', 0),
                    summary.get('oldest_date', 'N/A'),
                    summary.get('most_recent_date', 'N/A'),
                    '',
                    total_new,
                    total_closed,
                    total_tablets_closed,
                    total_tablets_added,
                    '',
                    f"{efficiency:.1f}%",
                    f"{activity_score:.1f}",
                    f"{closure_rate:.1f}%",
                    total_tablets_closed - total_tablets_added,
                    f"{total_closed / max(total_new, 1):.2f}" if total_new > 0 else "N/A"
                ],
                '💡 INTERPRETACIÓN': [
                    'Período analizado',
                    'Cantidad de archivos procesados',
                    'Fecha del primer archivo',
                    'Fecha del último archivo',
                    '',
                    'Albaranes nuevos en el período',
                    'Albaranes completamente cerrados',
                    'Tablillas cerradas en total',
                    'Tablillas agregadas en total',
                    '',
                    'Porcentaje de tablillas cerradas vs agregadas',
                    'Actividad promedio por archivo',
                    'Porcentaje de albaranes cerrados vs nuevos',
                    'Balance neto de tablillas',
                    'Relación entre cierres y nuevos albaranes'
                ]
            }
            executive_df = pd.DataFrame(executive_data)
            executive_df.to_excel(writer, sheet_name='🎯 Dashboard_Ejecutivo', index=False)
            
            status_text.text("📊 Procesando evolución diaria...")
            progress_bar.progress(30)
            
            # HOJA 2: Evolución Diaria (MEJORADA)
            if 'open_evolution' in summary:
                evolution_df = pd.DataFrame(summary['open_evolution'])
                evolution_df['date'] = pd.to_datetime(evolution_df['date'])
                
                # Agregar métricas calculadas
                evolution_df['cambio_diario'] = evolution_df['total_open'].diff()
                evolution_df['cambio_porcentual'] = (evolution_df['total_open'].pct_change() * 100).round(2)
                evolution_df['tendencia'] = evolution_df['cambio_diario'].apply(
                    lambda x: '📈 CRECIENTE' if x > 0 else '📉 DECRECIENTE' if x < 0 else '➡️ ESTABLE'
                )
                
                # Renombrar columnas para mejor presentación
                evolution_df = evolution_df.rename(columns={
                    'date': '📅 FECHA',
                    'total_open': '🔢 TABLILLAS PENDIENTES',
                    'cambio_diario': '📊 CAMBIO DIARIO',
                    'cambio_porcentual': '📈 CAMBIO %',
                    'tendencia': '🎯 TENDENCIA'
                })
                
                evolution_df.to_excel(writer, sheet_name='📈 Evolución_Diaria', index=False)
            
            status_text.text("🔄 Procesando cambios diarios...")
            progress_bar.progress(60)
            
            # HOJA 3: Cambios Día a Día (MEJORADA)
            if 'comparisons' in analysis_results:
                daily_changes = []
                for comp in analysis_results['comparisons']:
                    # Calcular métricas adicionales - CORREGIDO para usar lógica de albaranes cerrados
                    net_change = comp['current_total_open'] - comp['previous_total_open']
                    # Eficiencia = Albaranes cerrados / (Albaranes cerrados + Albaranes nuevos)
                    efficiency = (comp['closed_albaranes'] / max(comp['closed_albaranes'] + comp['new_albaranes'], 1)) * 100
                    
                    daily_changes.append({
                        '📅 FECHA ANTERIOR': comp['previous_date'],
                        '📅 FECHA ACTUAL': comp['current_date'],
                        '🆕 NUEVOS ALBARANES': comp['new_albaranes'],
                        '✅ ALBARANES CERRADOS': comp['closed_albaranes'],
                        '🔒 TABLILLAS CERRADAS': comp['closed_tablets'],
                        '➕ TABLILLAS AGREGADAS': comp.get('added_tablets', 0),
                        '📊 NETO TABLILLAS': comp['closed_tablets'] - comp.get('added_tablets', 0),
                        '📈 EFICIENCIA (%)': f"{efficiency:.1f}%",
                        '🔢 TOTAL PENDIENTES ANTERIOR': comp['previous_total_open'],
                        '🔢 TOTAL PENDIENTES ACTUAL': comp['current_total_open'],
                        '📊 VARIACIÓN PENDIENTES': net_change,
                        '🎯 TENDENCIA': '📈 CRECIENTE' if net_change > 0 else '📉 DECRECIENTE' if net_change < 0 else '➡️ ESTABLE',
                        '⚡ ALBARANES CON AGREGADOS': comp.get('albaranes_with_added_tablets', 0)
                    })
                
                daily_changes_df = pd.DataFrame(daily_changes)
                daily_changes_df.to_excel(writer, sheet_name='🔄 Cambios_Diarios', index=False)
            
            status_text.text("📋 Procesando detalles de cambios...")
            progress_bar.progress(80)
            
            # HOJA 4: Detalles de Cambios
            all_changes = []
            for comp in analysis_results.get('comparisons', []):
                for change in comp.get('changed_albaranes', []):
                    all_changes.append({
                        'Fecha': comp['current_date'],
                        'Albarán': change['albaran'],
                        'Cliente': change['customer'],
                        'Open_Anterior': change['previous_open'],
                        'Open_Actual': change['current_open'],
                        'Total_Anterior': change['previous_total'],
                        'Total_Actual': change['current_total'],
                        'Cambios': ' | '.join(change['changes'])
                    })
            
            if all_changes:
                changes_detail_df = pd.DataFrame(all_changes)
                changes_detail_df.to_excel(writer, sheet_name='Detalles_Cambios', index=False)
            
            status_text.text("🏢 Procesando análisis por almacén...")
            progress_bar.progress(90)
            
            # HOJA 5: Análisis por Almacén
            warehouse_analysis = []
            dates = sorted(excel_data.keys())
            
            for date in dates:
                df = excel_data[date]
                if 'WH_Code' in df.columns and 'Total_Open' in df.columns:
                    wh_summary = df.groupby('WH_Code').agg({
                        'Total_Open': 'sum',
                        'Total_Tablets': 'sum',
                        'Return_Packing_Slip': 'count'
                    }).reset_index()
                    
                    for _, row in wh_summary.iterrows():
                        warehouse_analysis.append({
                            'Fecha': date,
                            'Almacén': row['WH_Code'],
                            'Tablillas_Pendientes': row['Total_Open'],
                            'Total_Tablillas': row['Total_Tablets'],
                            'Número_Albaranes': row['Return_Packing_Slip']
                        })
            
            if warehouse_analysis:
                warehouse_df = pd.DataFrame(warehouse_analysis)
                warehouse_df.to_excel(writer, sheet_name='Análisis_Almacenes', index=False)
        
        # NUEVO: Completar progreso y limpiar indicadores
        status_text.text("✅ Informe generado exitosamente!")
        progress_bar.progress(100)
        
        # Limpiar indicadores después de un momento
        import time
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
        return output.getvalue()
        
    except Exception as e:
        # Limpiar indicadores en caso de error
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Error generando Excel: {str(e)}")
        return b''

def export_comprehensive_trends_report(analysis_results: Dict, excel_data: Dict[str, pd.DataFrame]):
    """Exportar análisis completo de tendencias - VERSIÓN CORREGIDA"""
    st.info("🔄 Generando análisis completo de tendencias...")
    
    # NUEVO: Devolver los datos binarios de la función principal
    return export_professional_multi_day_report(analysis_results, excel_data)

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