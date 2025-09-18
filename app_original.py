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
            
            # Mostrar progreso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🔄 Iniciando extracción con Camelot...")
            progress_bar.progress(10)
            
            # Probar diferentes configuraciones de Camelot
            tables = None
            
            try:
                status_text.text("📊 Probando método Stream (más rápido)...")
                progress_bar.progress(30)
                
                # Método 1: Stream (mejor para tablas sin bordes definidos)
                tables = camelot.read_pdf(tmp_file_path, pages='1-3', flavor='stream')  # Solo primeras 3 páginas
                st.write(f"📊 Método Stream: {len(tables)} tablas encontradas")
                progress_bar.progress(60)
                
            except Exception as e:
                st.write(f"Stream falló: {str(e)}")
                
            if not tables or len(tables) == 0:
                try:
                    status_text.text("📊 Probando método Lattice...")
                    progress_bar.progress(70)
                    
                    # Método 2: Lattice (mejor para tablas con bordes)
                    tables = camelot.read_pdf(tmp_file_path, pages='1-3', flavor='lattice')  # Solo primeras 3 páginas
                    st.write(f"📊 Método Lattice: {len(tables)} tablas encontradas")
                    progress_bar.progress(80)
                    
                except Exception as e:
                    st.write(f"Lattice falló: {str(e)}")
            
            # Si ambos métodos fallan, intentar con páginas específicas
            if not tables or len(tables) == 0:
                try:
                    status_text.text("🔄 Buscando en páginas específicas...")
                    progress_bar.progress(85)
                    
                    # Intentar página por página (solo primeras 3 páginas)
                    for page_num in range(1, 4):  # Solo primeras 3 páginas
                        try:
                            status_text.text(f"📄 Procesando página {page_num}...")
                            page_tables = camelot.read_pdf(tmp_file_path, pages=str(page_num), flavor='stream')
                            if page_tables and len(page_tables) > 0:
                                st.write(f"📊 Página {page_num}: {len(page_tables)} tablas encontradas")
                                if tables is None:
                                    tables = page_tables
                                else:
                                    tables.extend(page_tables)
                        except Exception as e:
                            st.write(f"Página {page_num} falló: {str(e)}")
                            continue
                    
                    progress_bar.progress(95)
                    
                except Exception as e:
                    st.write(f"Búsqueda por páginas falló: {str(e)}")
            
            progress_bar.progress(100)
            status_text.text("✅ Procesamiento completado")
            
            # Limpiar archivo temporal
            os.unlink(tmp_file_path)
            
            if not tables or len(tables) == 0:
                st.error("❌ No se encontraron tablas en el PDF")
                st.info("💡 **Sugerencias:**")
                st.write("- Verifica que el PDF contenga tablas estructuradas")
                st.write("- Asegúrate de que el archivo no esté protegido")
                st.write("- Intenta con un PDF de ejemplo conocido")
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
            
            # Mostrar tabla raw para debugging
            st.write(f"📋 **Tabla {i+1} RAW (primeras 3 filas):**")
            st.dataframe(table.df.head(3), use_container_width=True)
            
            df = table.df
            
            # Filtrar solo filas que empiecen con FL (datos de Alsina Forms)
            fl_rows = df[df.iloc[:, 0].astype(str).str.contains('FL', na=False)]
            
            if len(fl_rows) > 0:
                st.write(f"✅ {len(fl_rows)} filas FL encontradas en tabla {i+1}")
                
                # Procesar cada fila FL individualmente para corregir columnas mezcladas
                processed_fl_rows = self._fix_mixed_columns(fl_rows)
                all_data.append(processed_fl_rows)
        
        if not all_data:
            st.error("❌ No se encontraron filas con datos FL")
            return None
        
        # Combinar todas las tablas FL
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Limpiar y estandarizar
        return self._clean_and_standardize_advanced(combined_df)
    
    def _fix_mixed_columns(self, fl_rows: pd.DataFrame) -> pd.DataFrame:
        """Corregir columnas mezcladas en filas FL"""
        corrected_rows = []
        
        for idx, row in fl_rows.iterrows():
            try:
                # Convertir toda la fila a string y unir
                row_text = ' '.join([str(cell) for cell in row if pd.notna(cell) and str(cell).strip()])
                
                # Patrón para extraer datos de fila FL
                # FL 612D 729000018764 9/18/2025 40036645 FL052 8/31/2025 9/30/2025 Thales Builders Corp Residences at Martin Mano No 279, 282, 287 3 279A, 282T, 287T 3 0 0
                pattern = r'FL\s+(\w+)\s+(\d+)\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d+)\s+(\w+)\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+No\s+(.+?)\s+(\d+)\s+(.+?)\s+(\d+)\s+(\d+)\s+(\d+)'
                
                match = re.search(pattern, row_text)
                
                if match:
                    # Extraer datos usando regex
                    wh_code = match.group(1)
                    albaran = match.group(2)
                    return_date = match.group(3)
                    customer_id = match.group(4)
                    fl_code = match.group(5)
                    counting_date = match.group(6)
                    validation_date = match.group(7)
                    customer_name = match.group(8).strip()
                    tablet_numbers = match.group(9).strip()
                    total_tablets = int(match.group(10))
                    tablet_codes = match.group(11).strip()
                    total_open = int(match.group(12))
                    counting_delay = int(match.group(13))
                    validation_delay = int(match.group(14))
                    
                    # Convertir fechas a formato datetime
                    try:
                        return_date_dt = pd.to_datetime(return_date, format='%m/%d/%Y')
                        counting_date_dt = pd.to_datetime(counting_date, format='%m/%d/%Y')
                        validation_date_dt = pd.to_datetime(validation_date, format='%m/%d/%Y')
                    except:
                        # Si falla la conversión, usar las fechas como string
                        return_date_dt = return_date
                        counting_date_dt = counting_date
                        validation_date_dt = validation_date
                    
                    # Crear fila corregida con todas las columnas necesarias
                    corrected_row = {
                        'WH_Code': wh_code,
                        'Return_Packing_Slip': albaran,
                        'Return_Date': return_date_dt,
                        'Customer_ID': customer_id,
                        'FL_Code': fl_code,
                        'Counting_Date': counting_date_dt,
                        'Validation_Date': validation_date_dt,
                        'Customer_Name': customer_name,
                        'Tablet_Numbers': tablet_numbers,
                        'Total_Tablets': total_tablets,
                        'Tablet_Codes': tablet_codes,
                        'Total_Open': total_open,
                        'Counting_Delay': counting_delay,
                        'Validation_Delay': validation_delay,
                        # Agregar columnas calculadas que necesita el análisis visual
                        'Days_Since_Return': 0,  # Se calculará después
                        'Priority_Score': 0,     # Se calculará después
                        'Slip_Age_Rank': 0,      # Se calculará después
                        'Priority_Level': 'Media' # Valor por defecto
                    }
                    
                    corrected_rows.append(corrected_row)
                    st.write(f"✅ Fila corregida: {albaran} - {customer_name}")
                    
                else:
                    # Si no coincide el patrón, intentar extraer datos básicos
                    st.write(f"⚠️ No se pudo corregir fila: {row_text[:100]}...")
                    
                    # Intentar extraer al menos el albarán
                    albaran_match = re.search(r'(\d{12})', row_text)
                    if albaran_match:
                        albaran = albaran_match.group(1)
                        # Usar datos originales pero con albarán corregido
                        original_row = row.to_dict()
                        original_row['Return_Packing_Slip'] = albaran
                        
                        # Asegurar que tiene las columnas necesarias
                        if 'Days_Since_Return' not in original_row:
                            original_row['Days_Since_Return'] = 0
                        if 'Priority_Score' not in original_row:
                            original_row['Priority_Score'] = 0
                        if 'Slip_Age_Rank' not in original_row:
                            original_row['Slip_Age_Rank'] = 0
                        if 'Priority_Level' not in original_row:
                            original_row['Priority_Level'] = 'Media'
                            
                        corrected_rows.append(original_row)
                        st.write(f"🔄 Fila parcialmente corregida: {albaran}")
                    
            except Exception as e:
                st.write(f"❌ Error corrigiendo fila {idx}: {str(e)}")
                continue
        
        if corrected_rows:
            return pd.DataFrame(corrected_rows)
        else:
            return fl_rows  # Devolver original si no se pudo corregir nada
    
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
        
        # Información sobre tiempo de procesamiento
        st.info("""
        ⏱️ **Tiempo de procesamiento esperado:**
        - 📄 PDF pequeño (< 1MB): 30-60 segundos
        - 📄 PDF mediano (1-5MB): 1-3 minutos  
        - 📄 PDF grande (> 5MB): 3-5 minutos
        
        💡 **Consejo:** Si se demora mucho, puedes cancelar y probar con un PDF más pequeño.
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
                
                # NUEVA: Opción de exportar informe profesional
                st.markdown('<div class="section-header">💾 EXPORTAR INFORME PROFESIONAL</div>', 
                            unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📊 Informe Ejecutivo Multi-Días", type="primary"):
                        export_professional_multi_day_report(analysis_results, excel_data)
                
                with col2:
                    if st.button("📈 Análisis Completo de Tendencias", type="secondary"):
                        export_comprehensive_trends_report(analysis_results, excel_data)
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
    
    # Análisis de tendencias
    show_trend_analysis(excel_data)

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
    
    # Preparar datos por almacén
    wh_summary = df.groupby('WH_Code').agg({
        'Total_Open': 'sum',
        'Total_Tablets': 'sum',
        'Counting_Delay': ['mean', 'max'],
        'Validation_Delay': 'mean',
        'Return_Packing_Slip': 'count',
        'Days_Since_Return': 'mean',
        'Priority_Score': 'mean'
    }).round(2)
    
    # Aplanar columnas multinivel
    wh_summary.columns = ['Pendientes', 'Total_Tablillas', 'Retraso_Prom', 'Retraso_Max', 
                         'Val_Delay_Prom', 'Num_Albaranes', 'Días_Prom', 'Score_Prom']
    wh_summary = wh_summary.reset_index()
    
    # Calcular métricas adicionales
    wh_summary['Eficiencia'] = ((wh_summary['Total_Tablillas'] - wh_summary['Pendientes']) / 
                               wh_summary['Total_Tablillas'] * 100).round(1)
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
    
    if total_tablets > 0:
        completion_rate = ((total_tablets - total_pending) / total_tablets * 100)
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
                 help="Porcentaje de tablillas completadas vs total")
    
    with col2:
        st.metric("⏰ Antigüedad Promedio", 
                 f"{avg_age:.1f} días",
                 help="Días promedio desde retorno")
    
    with col3:
        st.metric("🚨 Items Críticos", 
                 critical_count,
                 help="Albaranes que requieren atención inmediata")
    
    with col4:
        st.metric("📅 Del Mes Anterior", 
                 old_month_count,
                 help="Albaranes que vienen del mes anterior")
    
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
    """Exportar informe profesional multi-días"""
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # HOJA 1: Resumen Ejecutivo
            summary = analysis_results.get('summary', {})
            executive_data = {
                'Métrica': [
                    'Período de Análisis',
                    'Archivos Analizados',
                    'Fecha Más Antigua',
                    'Fecha Más Reciente',
                    '🆕 Total Nuevos Albaranes',
                    '✅ Total Albaranes Cerrados', 
                    '🔒 Total Tablillas Cerradas',
                    '➕ Total Tablillas Agregadas',
                    '📊 Eficiencia de Cierre (%)',
                    '🎯 Score de Actividad'
                ],
                'Valor': [
                    summary.get('analysis_period', 'N/A'),
                    summary.get('num_files_analyzed', 0),
                    summary.get('oldest_date', 'N/A'),
                    summary.get('most_recent_date', 'N/A'),
                    summary.get('total_new_albaranes', 0),
                    summary.get('total_closed_albaranes', 0),
                    summary.get('total_closed_tablets', 0),
                    summary.get('total_added_tablets', 0),
                    f"{(summary.get('total_closed_tablets', 0) / max(summary.get('total_added_tablets', 0) + summary.get('total_closed_tablets', 0), 1) * 100):.1f}%",
                    f"{(summary.get('total_closed_tablets', 0) + summary.get('total_added_tablets', 0)) / max(summary.get('num_files_analyzed', 1), 1):.1f}"
                ]
            }
            executive_df = pd.DataFrame(executive_data)
            executive_df.to_excel(writer, sheet_name='Resumen_Ejecutivo', index=False)
            
            # HOJA 2: Evolución Diaria
            if 'open_evolution' in summary:
                evolution_df = pd.DataFrame(summary['open_evolution'])
                evolution_df.to_excel(writer, sheet_name='Evolución_Diaria', index=False)
            
            # HOJA 3: Cambios Día a Día
            if 'comparisons' in analysis_results:
                daily_changes = []
                for comp in analysis_results['comparisons']:
                    daily_changes.append({
                        'Fecha_Anterior': comp['previous_date'],
                        'Fecha_Actual': comp['current_date'],
                        'Nuevos_Albaranes': comp['new_albaranes'],
                        'Albaranes_Cerrados': comp['closed_albaranes'],
                        'Tablillas_Cerradas': comp['closed_tablets'],
                        'Tablillas_Agregadas': comp.get('added_tablets', 0),
                        'Albaranes_con_Agregados': comp.get('albaranes_with_added_tablets', 0),
                        'Total_Pendientes_Anterior': comp['previous_total_open'],
                        'Total_Pendientes_Actual': comp['current_total_open'],
                        'Variación_Pendientes': comp['current_total_open'] - comp['previous_total_open']
                    })
                
                daily_changes_df = pd.DataFrame(daily_changes)
                daily_changes_df.to_excel(writer, sheet_name='Cambios_Diarios', index=False)
            
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
        
        # Descargar
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"informe_profesional_tablillas_{timestamp}.xlsx"
        
        st.download_button(
            label="📥 Descargar Informe Profesional",
            data=output.getvalue(),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success(f"✅ Informe profesional generado: **{filename}**")
        st.info("📊 Incluye: Resumen ejecutivo, evolución diaria, cambios detallados, análisis por almacén")
        
    except Exception as e:
        st.error(f"❌ Error generando informe: {str(e)}")

def export_comprehensive_trends_report(analysis_results: Dict, excel_data: Dict[str, pd.DataFrame]):
    """Exportar análisis completo de tendencias"""
    st.info("🔄 Generando análisis completo de tendencias...")
    
    # Esta función puede expandirse para análisis más profundos
    # Por ahora, usar la función principal con datos adicionales
    export_professional_multi_day_report(analysis_results, excel_data)

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