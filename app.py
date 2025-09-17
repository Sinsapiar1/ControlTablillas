import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import io
from datetime import datetime, timedelta
import re
import pdfplumber
import base64
from typing import List, Dict, Optional, Tuple
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Control de Tablillas - Alsina Forms",
    page_icon="📊",
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
</style>
""", unsafe_allow_html=True)

class AlsinaPDFParser:
    """Parser específico para los reportes PDF de Alsina Forms Co."""
    
    def parse_pdf_content(self, content: str) -> Optional[pd.DataFrame]:
        """Parsear el contenido completo del PDF con el nuevo algoritmo mejorado"""
        lines = content.split('\n')
        
        st.write(f"🔍 Analizando {len(lines)} líneas del PDF...")
        
        # Encontrar la sección de datos
        data_lines = self._extract_data_lines(lines)
        
        st.write(f"📊 Encontradas {len(data_lines)} líneas de datos")
        
        # Parsear cada línea de datos
        parsed_data = []
        for i, line in enumerate(data_lines):
            parsed_row = self._parse_data_line(line, i + 1)
            if parsed_row:
                parsed_data.append(parsed_row)
                if len(parsed_data) <= 3:  # Mostrar las primeras 3 para debug
                    st.write(f"✅ Línea {i+1}: {parsed_row['Customer_Name']} - Tablets: {parsed_row['Tablets']}")
        
        st.write(f"📋 Extraídos {len(parsed_data)} registros válidos")
        return pd.DataFrame(parsed_data) if parsed_data else None
    
    def _extract_data_lines(self, lines: List[str]) -> List[str]:
        """Extraer solo las líneas que contienen datos de devoluciones"""
        data_lines = []
        in_data_section = False
        
        st.write("🔍 **Debug: Analizando líneas del PDF...**")
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Mostrar las primeras 10 líneas para debug
            if i < 10:
                st.write(f"Línea {i+1}: `{line[:100]}{'...' if len(line) > 100 else ''}`")
            
            # Detectar inicio de sección de datos
            if 'FL' in line and any(char.isdigit() for char in line):
                in_data_section = True
                st.write(f"🎯 **Inicio de datos detectado en línea {i+1}:** `{line[:100]}`")
            
            # Si estamos en la sección de datos y la línea parece contener datos
            if in_data_section and self._is_data_line(line):
                data_lines.append(line)
                st.write(f"✅ **Línea de datos {len(data_lines)}:** `{line[:100]}`")
            
            # Detectar fin de sección de datos
            if in_data_section and line.startswith('Alsina Forms Co., Inc.'):
                st.write(f"🏁 **Fin de datos detectado en línea {i+1}**")
                break
        
        return data_lines
    
    def _is_data_line(self, line: str) -> bool:
        """Verificar si una línea contiene datos de devolución"""
        # Debe empezar con FL y contener números de packing slip
        return (line.startswith('FL') and 
                len(line.split()) >= 10 and
                any(re.search(r'\d{12}', part) for part in line.split()))
    
    def _parse_data_line(self, line: str, line_number: int) -> Optional[Dict]:
        """Parsear una línea individual de datos con algoritmo mejorado"""
        try:
            # Limpiar la línea
            line = line.strip()
            
            # Usar regex para extraer campos de manera precisa
            parsed_data = self._extract_with_perfect_regex(line, line_number)
            
            return parsed_data
            
        except Exception as e:
            st.write(f"❌ Error en línea {line_number}: {str(e)}")
            return None
    
    def _extract_with_perfect_regex(self, line: str, line_number: int) -> Optional[Dict]:
        """Extraer campos usando regex perfecto para el formato específico"""
        
        # Patrón regex que coincide exactamente con el formato
        pattern = r'FL\s+(\w+)\s+(\d{12})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d+)\s+(\w+)\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+(Yes|No)\s+(\d{1,2}/\d{1,2}/\d{4})?\s*(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
        
        match = re.search(pattern, line)
        
        if not match:
            st.write(f"⚠️ Línea {line_number}: No coincide con el patrón")
            return None
        
        # Extraer grupos
        groups = match.groups()
        
        wh_code = groups[0]
        return_slip = groups[1]
        return_date = self._parse_date(groups[2])
        jobsite_id = groups[3]
        cost_center = groups[4]
        invoice_start = self._parse_date(groups[5])
        invoice_end = self._parse_date(groups[6])
        
        # Extraer nombres (grupo 7 contiene todo el texto entre fechas y Yes/No)
        names_text = groups[7]
        customer_name, job_site_name = self._split_names_perfect(names_text)
        
        definitive_dev = groups[8]
        counted_date = self._parse_date(groups[9]) if groups[9] else None
        
        # Extraer información de tablillas (grupo 10)
        tablets_text = groups[10]
        tablets_info = self._extract_tablets_perfect(tablets_text)
        
        # Totales
        total_tablets = int(groups[11])
        total_open = int(groups[12])
        counting_delay = int(groups[13])
        validation_delay = int(groups[14])
        
        return {
            'WH': 'FL',
            'WH_Code': wh_code,
            'Return_Packing_Slip': return_slip,
            'Return_Date': return_date,
            'Jobsite_ID': jobsite_id,
            'Cost_Center': cost_center,
            'Invoice_Start_Date': invoice_start,
            'Invoice_End_Date': invoice_end,
            'Customer_Name': customer_name,
            'Job_Site_Name': job_site_name,
            'Definitive_Dev': definitive_dev,
            'Counted_Date': counted_date,
            'Tablets': tablets_info['tablets'],
            'Total_Tablets': total_tablets,
            'Open_Tablets': tablets_info['open_tablets'],
            'Total_Open': total_open,
            'Counting_Delay': counting_delay,
            'Validation_Delay': validation_delay
        }
    
    def _split_names_perfect(self, names_text: str) -> Tuple[str, str]:
        """Dividir nombres de manera perfecta basándose en el formato real"""
        # Limpiar el texto
        names_text = names_text.strip()
        
        # Patrones específicos basados en los ejemplos reales
        patterns = [
            # Patrón 1: "Phorcys Builders Corp The Villages at East Ocea"
            r'(.+?)\s+(Corp|LLC|Inc|Ltd)\s+(.+)',
            # Patrón 2: "Delta Construction Group 2060 New Single Family Re"
            r'(.+?)\s+(Group|Construction|Builders)\s+(.+)',
            # Patrón 3: "Thales Builders Corp Heritage"
            r'(.+?)\s+(Corp|LLC|Inc|Ltd)\s+(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, names_text, re.IGNORECASE)
            if match:
                customer_name = match.group(1).strip()
                company_type = match.group(2).strip()
                job_site_name = match.group(3).strip()
                
                # Reconstruir nombre completo del cliente
                full_customer_name = f"{customer_name} {company_type}"
                
                return full_customer_name, job_site_name
        
        # Si no encuentra patrón, dividir por la mitad
        words = names_text.split()
        if len(words) <= 1:
            return names_text, "Unknown Site"
        
        mid_point = len(words) // 2
        customer_name = ' '.join(words[:mid_point])
        job_site_name = ' '.join(words[mid_point:])
        
        return customer_name, job_site_name
    
    def _extract_tablets_perfect(self, tablets_text: str) -> Dict:
        """Extraer información de tablillas de manera perfecta"""
        tablets = []
        open_tablets = []
        
        # Buscar números de tablillas (secuencia de números con comas)
        # Ejemplo: "1662, 1674, 1718" o "1323" o "1480, 1481"
        tablet_pattern = r'\b\d{3,4}(?:,\s*\d{3,4})*\b'
        tablet_matches = re.findall(tablet_pattern, tablets_text)
        
        for match in tablet_matches:
            # Dividir por comas y limpiar
            numbers = [num.strip() for num in match.split(',')]
            tablets.extend(numbers)
        
        # Buscar tablillas abiertas (números con letras)
        # Ejemplo: "1491T" o "163A" o "1321M"
        open_pattern = r'\b\d{3,4}[A-Z]+\b'
        open_matches = re.findall(open_pattern, tablets_text)
        open_tablets.extend(open_matches)
        
        return {
            'tablets': ', '.join(tablets),
            'open_tablets': ', '.join(open_tablets)
        }
    
    
    def _parse_date(self, date_str: str) -> Optional[pd.Timestamp]:
        """Parsear fecha de forma segura"""
        if not date_str or date_str in ['No', 'Yes', '']:
            return None
        try:
            return pd.to_datetime(date_str, format='%m/%d/%Y')
        except:
            try:
                return pd.to_datetime(date_str, infer_datetime_format=True)
            except:
                return None

class TablillasHistoricalAnalyzer:
    """Analizador histórico para seguimiento día a día de tablillas"""
    
    def __init__(self):
        self.historical_data = []
        self.comparison_df = None
        
    def load_excel_files(self, excel_files: List) -> bool:
        """Cargar múltiples archivos Excel históricos"""
        try:
            self.historical_data = []
            
            for uploaded_file in excel_files:
                df = pd.read_excel(uploaded_file, sheet_name='Devoluciones')
                
                file_date = self._extract_date_from_filename(uploaded_file.name)
                df['Report_Date'] = file_date
                df['File_Source'] = uploaded_file.name
                
                self.historical_data.append(df)
                
            st.success(f"✅ Cargados {len(self.historical_data)} archivos históricos")
            return True
            
        except Exception as e:
            st.error(f"Error cargando archivos: {str(e)}")
            return False
    
    def _extract_date_from_filename(self, filename: str) -> datetime:
        """Extraer fecha del nombre del archivo"""
        date_match = re.search(r'(\d{8})', filename)
        if date_match:
            date_str = date_match.group(1)
            return pd.to_datetime(date_str, format='%Y%m%d')
        
        # Buscar formato DDMMYYYY
        date_match = re.search(r'(\d{2})(\d{2})(\d{4})', filename)
        if date_match:
            day, month, year = date_match.groups()
            return pd.to_datetime(f"{year}{month}{day}", format='%Y%m%d')
        
        return pd.Timestamp.now()
    
    def create_comparison_dataset(self) -> pd.DataFrame:
        """Crear dataset comparativo consolidado"""
        if not self.historical_data:
            return None
            
        combined_df = pd.concat(self.historical_data, ignore_index=True)
        
        # Limpiar datos
        combined_df['Return_Date'] = pd.to_datetime(combined_df['Return_Date'])
        combined_df['Report_Date'] = pd.to_datetime(combined_df['Report_Date'])
        
        # ID único para seguimiento
        combined_df['Tablilla_ID'] = (
            combined_df['Return_Packing_Slip'].astype(str) + "_" + 
            combined_df['WH_Code'].astype(str)
        )
        
        # Métricas adicionales
        combined_df['Days_Since_Return'] = (combined_df['Report_Date'] - combined_df['Return_Date']).dt.days
        
        self.comparison_df = combined_df
        return combined_df
    
    def analyze_closure_trends(self) -> Dict:
        """Análisis de tendencias de cierre"""
        if self.comparison_df is None:
            return {}
        
        df = self.comparison_df.copy()
        
        daily_summary = df.groupby('Report_Date').agg({
            'Total_Open': 'sum',
            'Total_Tablets': 'sum',
            'Tablilla_ID': 'nunique',
            'Counting_Delay': 'mean',
            'Validation_Delay': 'mean'
        }).reset_index()
        
        daily_summary['Closure_Rate'] = (
            (daily_summary['Total_Tablets'] - daily_summary['Total_Open']) / 
            daily_summary['Total_Tablets'] * 100
        ).fillna(0)
        
        daily_summary = daily_summary.sort_values('Report_Date')
        daily_summary['Open_Change'] = daily_summary['Total_Open'].diff()
        daily_summary['Closure_Trend'] = daily_summary['Closure_Rate'].diff()
        
        return {
            'daily_summary': daily_summary,
            'total_days': len(daily_summary),
            'avg_closure_rate': daily_summary['Closure_Rate'].mean()
        }
    
    def identify_stagnant_tablets(self, days_threshold: int = 10) -> pd.DataFrame:
        """Identificar tablillas estancadas"""
        if self.comparison_df is None:
            return pd.DataFrame()
        
        latest_report = self.comparison_df.groupby('Tablilla_ID').agg({
            'Report_Date': 'max',
            'Return_Date': 'first',
            'Customer_Name': 'first',
            'Job_Site_Name': 'first',
            'WH_Code': 'first',
            'Total_Open': 'last',
            'Definitive_Dev': 'last',
            'Days_Since_Return': 'max',
            'Return_Packing_Slip': 'first'
        }).reset_index()
        
        stagnant = latest_report[
            (latest_report['Total_Open'] > 0) & 
            (latest_report['Days_Since_Return'] > days_threshold) &
            (latest_report['Definitive_Dev'] == 'No')
        ].sort_values('Days_Since_Return', ascending=False)
        
        return stagnant
    
    def warehouse_performance_comparison(self) -> Dict:
        """Comparación de performance entre almacenes"""
        if self.comparison_df is None:
            return {}
        
        warehouse_perf = self.comparison_df.groupby(['Report_Date', 'WH_Code']).agg({
            'Total_Open': 'sum',
            'Total_Tablets': 'sum',
            'Counting_Delay': 'mean',
            'Validation_Delay': 'mean',
            'Tablilla_ID': 'nunique'
        }).reset_index()
        
        warehouse_perf['Efficiency'] = (
            (warehouse_perf['Total_Tablets'] - warehouse_perf['Total_Open']) / 
            warehouse_perf['Total_Tablets'] * 100
        ).fillna(0)
        
        latest_date = warehouse_perf['Report_Date'].max()
        latest_perf = warehouse_perf[warehouse_perf['Report_Date'] == latest_date]
        ranking = latest_perf.sort_values('Efficiency', ascending=False)
        
        return {
            'historical_performance': warehouse_perf,
            'current_ranking': ranking,
            'best_warehouse': ranking.iloc[0]['WH_Code'] if not ranking.empty else None,
            'worst_warehouse': ranking.iloc[-1]['WH_Code'] if not ranking.empty else None
        }
    
    def calculate_kpis(self) -> Dict:
        """Calcular KPIs clave"""
        if self.comparison_df is None:
            return {}
        
        latest_date = self.comparison_df['Report_Date'].max()
        oldest_date = self.comparison_df['Report_Date'].min()
        analysis_period = (latest_date - oldest_date).days
        
        latest_data = self.comparison_df[self.comparison_df['Report_Date'] == latest_date]
        
        kpis = {
            'analysis_period_days': analysis_period,
            'total_active_returns': latest_data['Tablilla_ID'].nunique(),
            'total_open_tablets': latest_data['Total_Open'].sum(),
            'total_tablets_in_system': latest_data['Total_Tablets'].sum(),
            'overall_closure_rate': (
                (latest_data['Total_Tablets'].sum() - latest_data['Total_Open'].sum()) / 
                latest_data['Total_Tablets'].sum() * 100
            ) if latest_data['Total_Tablets'].sum() > 0 else 0,
            'avg_processing_time': latest_data['Days_Since_Return'].mean(),
            'oldest_return': latest_data['Days_Since_Return'].max(),
            'active_warehouses': latest_data['WH_Code'].nunique(),
            'high_priority_returns': len(latest_data[latest_data['Days_Since_Return'] > 15]),
            'critical_returns': len(latest_data[latest_data['Days_Since_Return'] > 30])
        }
        
        return kpis

class TablillasController:
    def __init__(self):
        self.data_file = "tablillas_history.json"
        self.config_file = "config.json"
        self.pdf_parser = AlsinaPDFParser()
        self.historical_analyzer = TablillasHistoricalAnalyzer()
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
        """Extraer datos del PDF"""
        try:
            with pdfplumber.open(pdf_file) as pdf:
                all_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
            
            if not all_text.strip():
                st.error("El PDF no contiene texto extraíble")
                return None
            
            return self.pdf_parser.parse_pdf_content(all_text)
            
        except Exception as e:
            st.error(f"Error al procesar PDF: {str(e)}")
            return None
    
    def calculate_priorities(self, df):
        """Calcular prioridades basadas en fechas y delays"""
        if df is None or df.empty:
            return df
            
        df = df.copy()
        current_date = pd.Timestamp.now()
        
        df['Days_Since_Return'] = (current_date - df['Return_Date']).dt.days
        df['Days_Since_Return'] = df['Days_Since_Return'].fillna(0)
        
        # Asegurar valores numéricos
        numeric_cols = ['Counting_Delay', 'Validation_Delay', 'Total_Open']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
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
    st.markdown('<div class="main-header"><h1>🏗️ Control de Tablillas - Alsina Forms Co.</h1></div>', 
                unsafe_allow_html=True)
    
    controller = TablillasController()
    
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
        ["Dashboard Principal", "Análisis Detallado", "Análisis Histórico", "Configuración"]
    )
    
    if uploaded_file is not None:
        # Procesar PDF
        with st.spinner('🔄 Procesando archivo PDF...'):
            df = controller.extract_pdf_data(uploaded_file)
        
        if df is not None and not df.empty:
            st.success(f"✅ PDF procesado exitosamente: {len(df)} registros extraídos")
            
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
            elif page == "Análisis Histórico":
                show_historical_analysis(controller.historical_analyzer)
            elif page == "Configuración":
                show_configuration()
        else:
            if page == "Análisis Histórico":
                show_historical_analysis(controller.historical_analyzer)
            else:
                st.error("❌ No se pudieron extraer datos válidos del PDF")
                st.info("💡 Verifica que el PDF contenga el formato correcto de Alsina Forms")
    else:
        if page == "Análisis Histórico":
            show_historical_analysis(controller.historical_analyzer)
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
        total_open = int(df['Total_Open'].sum())
        high_priority = len(df[df['Priority_Level'] == 'Alta'])
        st.metric("Tablillas Pendientes", total_open, f"⚠️ {high_priority} alta prioridad")
    
    with col3:
        avg_delay = df['Counting_Delay'].mean()
        st.metric("Retraso Promedio (días)", f"{avg_delay:.1f}", "📊 Crítico si >15")
    
    with col4:
        warehouses = df['WH_Code'].nunique()
        st.metric("Almacenes Activos", warehouses, f"🏢 {warehouses} ubicaciones")
    
    # Gráficos
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Prioridades por Almacén")
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
        if not df['Return_Date'].isna().all():
            timeline = df.groupby('Return_Date').size().reset_index(name='count')
            fig = px.line(timeline, x='Return_Date', y='count', markers=True)
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de alta prioridad
    st.subheader("🚨 Devoluciones de Alta Prioridad")
    high_priority = df[df['Priority_Level'] == 'Alta'].head(10)
    
    if not high_priority.empty:
        display_cols = ['WH_Code', 'Return_Date', 'Customer_Name', 'Job_Site_Name',
                       'Total_Open', 'Days_Since_Return', 'Counting_Delay']
        available_cols = [col for col in display_cols if col in high_priority.columns]
        st.dataframe(high_priority[available_cols], use_container_width=True)
    else:
        st.success("✅ No hay devoluciones de alta prioridad")
    
    # Botón de descarga mejorado con fecha
    current_date = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"tablillas_{current_date}.xlsx"
    
    if st.button("📥 Descargar Reporte Excel", type="primary"):
        download_excel(df, filename)
    
    # Instrucciones para análisis histórico
    st.info(f"""
    💡 **Para análisis histórico:** 
    1. Descarga este Excel como `{filename}`
    2. Guárdalo en tu carpeta diaria
    3. Ve a "Análisis Histórico" para comparar múltiples días
    """)

def show_detailed_analysis(df):
    """Mostrar análisis detallado"""
    st.header("🔍 Análisis Detallado")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        warehouses = [wh for wh in df['WH_Code'].unique() if not pd.isna(wh)]
        warehouse_filter = st.multiselect("Filtrar por Almacén", options=warehouses, default=warehouses)
    
    with col2:
        priority_filter = st.multiselect("Filtrar por Prioridad", 
                                       options=['Alta', 'Media', 'Baja'], 
                                       default=['Alta', 'Media', 'Baja'])
    
    with col3:
        if not df['Return_Date'].isna().all():
            min_date = df['Return_Date'].min().date()
            max_date = df['Return_Date'].max().date()
            date_range = st.date_input("Rango de Fechas", value=(min_date, max_date))
    
    # Aplicar filtros
    filtered_df = df[
        (df['WH_Code'].isin(warehouse_filter)) &
        (df['Priority_Level'].isin(priority_filter))
    ]
    
    st.subheader(f"📋 Resultados Filtrados ({len(filtered_df)} registros)")
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)

def show_historical_analysis(analyzer: TablillasHistoricalAnalyzer):
    """Mostrar análisis histórico"""
    st.header("📈 Análisis Histórico de Tablillas")
    
    # Instrucciones
    st.markdown("""
    <div class="alert-success">
    <strong>🔄 Flujo de Análisis Histórico:</strong><br>
    1. Cada día: PDF → Procesar → Descargar Excel con fecha<br>
    2. Guardar Excel diario: <code>tablillas_YYYYMMDD.xlsx</code><br>
    3. Subir múltiples Excel aquí para análisis comparativo<br>
    4. Ver tendencias, tablillas estancadas y performance de almacenes
    </div>
    """, unsafe_allow_html=True)
    
    # Carga de archivos históricos
    st.subheader("📁 Cargar Archivos Excel Históricos")
    
    uploaded_files = st.file_uploader(
        "Selecciona archivos Excel de reportes diarios",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="Sube todos los archivos Excel generados día a día (mínimo 2 para comparación)"
    )
    
    if uploaded_files and len(uploaded_files) >= 2:
        if st.button("🔄 Analizar Histórico", type="primary"):
            with st.spinner('📊 Procesando archivos históricos...'):
                if analyzer.load_excel_files(uploaded_files):
                    analyzer.create_comparison_dataset()
                    
                    # Mostrar análisis
                    show_historical_dashboard(analyzer)
    
    elif uploaded_files and len(uploaded_files) == 1:
        st.warning("⚠️ Necesitas al menos 2 archivos para análisis comparativo")
    
    else:
        st.info("""
        👆 **Sube archivos Excel históricos para comenzar el análisis**
        
        **Ejemplo de nombres recomendados:**
        - `tablillas_20250915.xlsx`
        - `tablillas_20250916.xlsx`  
        - `tablillas_20250917.xlsx`
        
        **El análisis te mostrará:**
        - Tendencias de cierre día a día
        - Tablillas que permanecen abiertas entre reportes
        - Almacenes con mejor/peor performance
        - Identificación de cuellos de botella
        """)

def show_historical_dashboard(analyzer: TablillasHistoricalAnalyzer):
    """Dashboard de análisis histórico"""
    
    # KPIs generales
    kpis = analyzer.calculate_kpis()
    
    st.subheader("🎯 Resumen del Período")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Período Analizado", f"{kpis.get('analysis_period_days', 0)} días")
    
    with col2:
        closure_rate = kpis.get('overall_closure_rate', 0)
        st.metric("Tasa de Cierre", f"{closure_rate:.1f}%")
    
    with col3:
        st.metric("Tablillas Abiertas", f"{kpis.get('total_open_tablets', 0):,}")
    
    with col4:
        st.metric("Devoluciones Críticas", f"{kpis.get('critical_returns', 0)}")
    
    # Tendencias de cierre
    st.subheader("📈 Tendencias de Cierre")
    trends = analyzer.analyze_closure_trends()
    
    if trends and 'daily_summary' in trends:
        daily_data = trends['daily_summary']
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.line(
                daily_data,
                x='Report_Date',
                y='Closure_Rate',
                title='Tasa de Cierre Diaria (%)',
                markers=True,
                line_shape='linear'
            )
            fig1.update_traces(line_color='#2e86c1')
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.bar(
                daily_data,
                x='Report_Date',
                y='Total_Open',
                title='Tablillas Abiertas por Día',
                color='Total_Open',
                color_continuous_scale='Reds_r'
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    # Tablillas estancadas
    st.subheader("⚠️ Tablillas Estancadas (>10 días)")
    stagnant = analyzer.identify_stagnant_tablets()
    
    if not stagnant.empty:
        st.markdown(f"""
        <div class="alert-warning">
        <strong>📊 {len(stagnant)} tablillas sin progreso significativo</strong><br>
        Estas devoluciones requieren atención inmediata para evitar acumulación.
        </div>
        """, unsafe_allow_html=True)
        
        # Top 15 tablillas más antiguas
        display_stagnant = stagnant[[
            'Customer_Name', 'Job_Site_Name', 'WH_Code', 
            'Days_Since_Return', 'Total_Open', 'Return_Packing_Slip'
        ]].head(15)
        
        st.dataframe(display_stagnant, use_container_width=True)
        
    else:
        st.markdown("""
        <div class="alert-success">
        <strong>✅ No hay tablillas estancadas</strong><br>
        Todas las devoluciones están progresando según los tiempos esperados.
        </div>
        """, unsafe_allow_html=True)
    
    # Performance por almacén
    st.subheader("🏢 Comparación de Almacenes")
    warehouse_perf = analyzer.warehouse_performance_comparison()
    
    if warehouse_perf and 'historical_performance' in warehouse_perf:
        perf_data = warehouse_perf['historical_performance']
        
        fig3 = px.line(
            perf_data,
            x='Report_Date',
            y='Efficiency',
            color='WH_Code',
            title='Eficiencia por Almacén en el Tiempo (%)',
            markers=True
        )
        fig3.update_layout(yaxis_title="Eficiencia (%)")
        st.plotly_chart(fig3, use_container_width=True)
        
        # Ranking actual
        if 'current_ranking' in warehouse_perf:
            st.write("**Ranking Actual de Almacenes:**")
            ranking_display = warehouse_perf['current_ranking'][[
                'WH_Code', 'Efficiency', 'Total_Open', 'Counting_Delay'
            ]].round(2)
            
            st.dataframe(ranking_display, use_container_width=True)

def show_configuration():
    """Mostrar configuración"""
    st.header("⚙️ Configuración")
    st.info("Configuración de pesos de prioridad y umbrales de alerta")
    
    st.markdown("""
    **Parámetros actuales del sistema:**
    
    - **Prioridad Alta:** Devoluciones con 25+ días o score alto
    - **Prioridad Media:** Devoluciones con 15-24 días  
    - **Prioridad Baja:** Devoluciones con menos de 15 días
    
    **Tablillas Estancadas:** Sin progreso por más de 10 días
    **Devoluciones Críticas:** Más de 30 días en el sistema
    """)

def download_excel(df, filename):
    """Generar archivo Excel con formato mejorado"""
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Hoja principal con todos los datos
            df.to_excel(writer, sheet_name='Devoluciones', index=False)
            
            # Hoja de resumen por almacén
            if not df.empty:
                summary = df.groupby('WH_Code').agg({
                    'Total_Open': 'sum',
                    'Total_Tablets': 'sum',
                    'Counting_Delay': 'mean',
                    'Priority_Score': 'mean',
                    'Return_Packing_Slip': 'nunique'
                }).round(2)
                summary.columns = ['Tablillas_Abiertas', 'Total_Tablillas', 'Retraso_Promedio', 'Score_Prioridad', 'Num_Devoluciones']
                summary.to_excel(writer, sheet_name='Resumen_Almacenes')
                
                # Hoja de alta prioridad
                high_priority = df[df['Priority_Level'] == 'Alta']
                if not high_priority.empty:
                    high_priority.to_excel(writer, sheet_name='Alta_Prioridad', index=False)
                
                # Hoja de tablillas estancadas (más de 15 días)
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