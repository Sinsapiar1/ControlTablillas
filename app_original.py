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
        """Extrae datos usando configuraciones múltiples de Camelot"""
        if not CAMELOT_AVAILABLE:
            st.error("⚠️ Camelot no está instalado. Ejecuta: pip install camelot-py[cv]")
            return None
        
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name
            
            st.info("🔄 Extrayendo datos con múltiples métodos Camelot...")
            
            tables = None
            method_used = ""
            
            # MÉTODO 1: Stream con configuraciones optimizadas
            try:
                tables = camelot.read_pdf(
                    tmp_file_path, 
                    pages='all', 
                    flavor='stream',
                    edge_tol=500,           # Tolerancia para detectar bordes
                    row_tol=10,             # Tolerancia para separar filas
                    column_tol=0,           # Tolerancia estricta para columnas
                    split_text=True,        # Dividir texto en celdas
                    flag_size=True          # Marcar tamaños de fuente
                )
                if len(tables) > 0:
                    method_used = "Stream Optimizado"
                    st.write(f"✅ {method_used}: {len(tables)} tablas encontradas")
            except Exception as e:
                st.write(f"Stream Optimizado falló: {str(e)}")
            
            # MÉTODO 2: Stream básico (fallback)
            if not tables or len(tables) == 0:
                try:
                    tables = camelot.read_pdf(tmp_file_path, pages='all', flavor='stream')
                    if len(tables) > 0:
                        method_used = "Stream Básico"
                        st.write(f"✅ {method_used}: {len(tables)} tablas encontradas")
                except Exception as e:
                    st.write(f"Stream Básico falló: {str(e)}")
            
            # MÉTODO 3: Lattice con configuraciones
            if not tables or len(tables) == 0:
                try:
                    tables = camelot.read_pdf(
                        tmp_file_path, 
                        pages='all', 
                        flavor='lattice',
                        process_background=True,   # Procesar fondo
                        line_scale=15             # Escala de líneas
                    )
                    if len(tables) > 0:
                        method_used = "Lattice Optimizado"
                        st.write(f"✅ {method_used}: {len(tables)} tablas encontradas")
                except Exception as e:
                    st.write(f"Lattice Optimizado falló: {str(e)}")
            
            # Limpiar archivo temporal
            os.unlink(tmp_file_path)
            
            if not tables or len(tables) == 0:
                st.error("❌ No se encontraron tablas en el PDF con ningún método")
                return None
            
            st.info(f"🎯 Método exitoso: {method_used}")
            
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
    
    def _fix_concatenated_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Corregir columnas concatenadas - Solución para el problema específico"""
        try:
            st.info("🔧 Corrigiendo columnas mal separadas...")
            
            # Crear copia para trabajar
            fixed_df = df.copy()
            corrections_made = 0
            
            # Verificar si la primera columna contiene patrones problemáticos
            for idx in fixed_df.index:
                first_col = str(fixed_df.iloc[idx, 0]).strip()
                
                # Patrón: "FL 612D 729000018764" o similar
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
            
            # Mostrar resultados
            if corrections_made > 0:
                st.success(f"✅ {corrections_made} filas corregidas")
                st.write("**Ejemplo de corrección:**")
                
                # Mostrar ejemplo de la primera fila corregida
                example_idx = 0
                if len(df) > example_idx:
                    st.write(f"**Antes:** {df.iloc[example_idx, 0]}")
                    st.write(f"**Después:** Col1='{fixed_df.iloc[example_idx, 0]}' | Col2='{fixed_df.iloc[example_idx, 1]}' | Col3='{fixed_df.iloc[example_idx, 2]}'")
            else:
                st.info("✅ No se encontraron columnas concatenadas para corregir")
            
            return fixed_df
            
        except Exception as e:
            st.warning(f"⚠️ Error corrigiendo columnas: {str(e)}")
            return df
    
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
            
            # Métricas de performance
            efficiency = (total_tablets_closed / max(total_tablets_closed + total_tablets_added, 1)) * 100
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
                    # Calcular métricas adicionales
                    net_change = comp['current_total_open'] - comp['previous_total_open']
                    efficiency = (comp['closed_tablets'] / max(comp['closed_tablets'] + comp.get('added_tablets', 0), 1)) * 100
                    
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