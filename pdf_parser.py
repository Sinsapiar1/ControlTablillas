import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import io
from datetime import datetime, timedelta
import re
import pdfplumber
from typing import List, Dict, Optional
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Control de Tablillas - Alsina Forms",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class AlsinaPDFParserPrecise:
    """Parser de PRECISIÓN EXACTA para el formato Alsina"""
    
    def parse_pdf_content(self, content: str) -> Optional[pd.DataFrame]:
        """Parsear contenido con precisión exacta"""
        lines = content.split('\n')
        data = []
        
        st.write(f"🔍 Analizando {len(lines)} líneas del PDF...")
        
        for i, line in enumerate(lines):
            if line.strip().startswith('FL'):
                row_data = self._parse_line_exact(line.strip())
                if row_data:
                    data.append(row_data)
                    if len(data) <= 5:  # Debug primeras 5
                        st.write(f"✅ {row_data['Return_Packing_Slip']}: {row_data['Customer_Name']} | {row_data['Job_Site_Name']} | {row_data['Definitive_Dev']} | Fecha: {row_data['Counted_Date']} | Tablillas: {row_data['Tablets']}")
        
        st.write(f"📊 Extraídos {len(data)} albaranes")
        return pd.DataFrame(data) if data else None
    
    def _parse_line_exact(self, line: str) -> Optional[Dict]:
        """Parser EXACTO basado en la estructura identificada"""
        try:
            parts = re.split(r'\s+', line)
            
            if len(parts) < 20:  # Mínimo requerido
                return None
            
            # CAMPOS FIJOS (posiciones 0-7)
            wh = parts[0]                    # FL
            wh_code = parts[1]               # 61D, 612d
            return_slip = parts[2]           # 729000018xxx
            return_date = self._parse_date(parts[3])  # 9/2/2025
            jobsite_id = parts[4]            # 40030876
            cost_center = parts[5]           # FL052
            invoice_start = self._parse_date(parts[6])  # 8/31/2025
            invoice_end = self._parse_date(parts[7])    # 9/30/2025
            
            # ENCONTRAR POSICIÓN DE "Ye" + "s" O "No"
            status_pos, definitive_dev = self._find_status_exact(parts)
            
            # EXTRAER NOMBRES (posición 8 hasta status)
            names_section = parts[8:status_pos]
            customer_name, job_site_name = self._split_names_exact(names_section)
            
            # EXTRAER FECHA DE CONTEO si existe (después de Yes)
            counted_date = None
            tablets_start_pos = status_pos + 1
            
            if definitive_dev == "Yes":
                # Buscar fecha después de "s"
                if definitive_dev == "Yes" and tablets_start_pos < len(parts):
                    # Verificar si hay fecha
                    potential_date = parts[tablets_start_pos] if tablets_start_pos < len(parts) else ""
                    if re.match(r'\d{1,2}/\d{1,2}/\d{4}', potential_date):
                        counted_date = self._parse_date(potential_date)
                        tablets_start_pos += 1  # Avanzar después de la fecha
            
            # EXTRAER TABLILLAS Y NÚMEROS FINALES
            tablets_info = self._extract_tablets_exact(parts, tablets_start_pos)
            
            return {
                'WH': wh,
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
                **tablets_info
            }
            
        except Exception as e:
            print(f"Error parseando línea: {str(e)}")
            return None
    
    def _find_status_exact(self, parts: List[str]) -> tuple:
        """Encontrar EXACTAMENTE la posición de No/Yes"""
        # Buscar "No" directamente
        for i, part in enumerate(parts):
            if part == 'No':
                return i, 'No'
        
        # Buscar "Ye" seguido de "s"
        for i, part in enumerate(parts[:-1]):
            if part == 'Ye' and i + 1 < len(parts) and parts[i + 1] == 's':
                return i, 'Yes'  # Retornar posición de "Ye"
        
        # Si no encuentra, asumir posición por defecto
        return len(parts) - 6, 'No'
    
    def _split_names_exact(self, names_section: List[str]) -> tuple:
        """Dividir nombres con PRECISIÓN usando marcadores de empresa"""
        if not names_section:
            return "Unknown Customer", "Unknown Site"
        
        # Marcadores que indican final de nombre de empresa
        company_endings = [
            'corp', 'corporation', 'llc', 'inc', 'incorporated', 'ltd', 'limited',
            'construction', 'builders', 'services', 'group', 'company', 'co',
            'investments', 'investment', 'holdings', 'development'
        ]
        
        # Buscar el marcador más tardío
        split_position = len(names_section) // 2  # Default: mitad
        
        for i, word in enumerate(names_section):
            if word.lower() in company_endings:
                split_position = i + 1
                # No hacer break - queremos el último marcador encontrado
        
        # Separar en customer y job site
        customer_parts = names_section[:split_position]
        site_parts = names_section[split_position:]
        
        customer_name = ' '.join(customer_parts).strip()
        job_site_name = ' '.join(site_parts).strip()
        
        # Validar que no estén vacíos
        if not customer_name:
            customer_name = "Unknown Customer"
        if not job_site_name:
            job_site_name = "Unknown Site"
        
        return customer_name, job_site_name
    
    def _extract_tablets_exact(self, parts: List[str], start_pos: int) -> Dict:
        """Extraer tablillas con PRECISIÓN EXACTA"""
        try:
            # Los últimos 3-4 números son SIEMPRE los totales y delays
            # Buscar desde el final hacia atrás
            end_numbers = []
            for i in range(len(parts) - 1, -1, -1):
                if re.match(r'^\d+$', parts[i]):
                    end_numbers.insert(0, int(parts[i]))
                    if len(end_numbers) >= 4:  # Máximo 4 números finales
                        break
            
            # Determinar fin de sección de tablillas
            tablets_end_pos = len(parts) - len(end_numbers)
            
            # Extraer sección de tablillas
            tablets_section = parts[start_pos:tablets_end_pos]
            
            # Separar números de tablillas de códigos con letras
            tablet_numbers = []
            open_tablet_codes = []
            
            for part in tablets_section:
                # Números simples con comas: tablillas principales
                if re.match(r'^\d+,?$', part):
                    clean_num = re.sub(r'[^\d]', '', part)
                    if len(clean_num) >= 1:  # Cualquier número
                        tablet_numbers.append(clean_num)
                
                # Números con letras: tablillas abiertas
                elif re.match(r'^\d+[A-Z]+,?$', part):
                    clean_code = part.replace(',', '')
                    open_tablet_codes.append(clean_code)
            
            # Asignar números finales con validación
            total_tablets = end_numbers[0] if len(end_numbers) >= 1 else len(tablet_numbers)
            total_open = end_numbers[1] if len(end_numbers) >= 2 else len(open_tablet_codes)
            counting_delay = end_numbers[2] if len(end_numbers) >= 3 else 0
            validation_delay = end_numbers[3] if len(end_numbers) >= 4 else 0
            
            return {
                'Tablets': ', '.join(tablet_numbers),
                'Total_Tablets': total_tablets,
                'Open_Tablets': ', '.join(open_tablet_codes),
                'Total_Open': total_open,
                'Counting_Delay': counting_delay,
                'Validation_Delay': validation_delay
            }
            
        except Exception as e:
            return {
                'Tablets': '',
                'Total_Tablets': 0,
                'Open_Tablets': '',
                'Total_Open': 0,
                'Counting_Delay': 0,
                'Validation_Delay': 0
            }
    
    def _parse_date(self, date_str: str) -> Optional[pd.Timestamp]:
        """Parsear fecha de forma segura"""
        if not date_str or date_str in ['No', 'Yes', 'Ye', 's']:
            return None
        try:
            return pd.to_datetime(date_str, format='%m/%d/%Y')
        except:
            return None

class TablillasController:
    def __init__(self):
        self.pdf_parser = AlsinaPDFParserPrecise()
    
    def extract_pdf_data(self, pdf_file):
        """Extraer datos del PDF"""
        try:
            with pdfplumber.open(pdf_file) as pdf:
                all_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
            
            return self.pdf_parser.parse_pdf_content(all_text)
            
        except Exception as e:
            st.error(f"Error al procesar PDF: {str(e)}")
            return None
    
    def calculate_priorities(self, df):
        """Calcular prioridades"""
        if df is None or df.empty:
            return df
            
        df = df.copy()
        current_date = pd.Timestamp.now()
        
        # Días desde retorno
        df['Days_Since_Return'] = (current_date - df['Return_Date']).dt.days
        df['Days_Since_Return'] = df['Days_Since_Return'].fillna(0)
        
        # Limpiar valores numéricos
        numeric_cols = ['Counting_Delay', 'Validation_Delay', 'Total_Open']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Score de prioridad
        df['Priority_Score'] = (
            df['Days_Since_Return'] * 0.4 +
            df['Counting_Delay'] * 0.3 +
            df['Validation_Delay'] * 0.2 +
            df['Total_Open'] * 0.1
        )
        
        # Niveles de prioridad
        df['Priority_Level'] = pd.cut(
            df['Priority_Score'],
            bins=[0, 15, 25, float('inf')],
            labels=['Baja', 'Media', 'Alta'],
            right=False
        )
        
        return df.sort_values('Priority_Score', ascending=False)

def main():
    st.title("🏗️ Control de Tablillas - Alsina Forms Co.")
    
    controller = TablillasController()
    
    # Sidebar
    st.sidebar.header("📂 Carga de Datos")
    uploaded_file = st.sidebar.file_uploader(
        "Cargar Informe PDF",
        type=['pdf'],
        help="Sube el informe de devoluciones PDF"
    )
    
    if uploaded_file is not None:
        with st.spinner('Procesando PDF con precisión...'):
            df = controller.extract_pdf_data(uploaded_file)
        
        if df is not None and not df.empty:
            st.success(f"✅ PDF procesado: {len(df)} albaranes extraídos")
            
            # Calcular prioridades
            df_prioritized = controller.calculate_priorities(df)
            
            # Mostrar datos
            show_dashboard(df_prioritized)
        else:
            st.error("❌ No se pudieron extraer datos del PDF")
    else:
        st.info("👆 Sube un archivo PDF para comenzar")

def show_dashboard(df):
    """Dashboard con datos corregidos"""
    st.header("📊 Dashboard - Datos Corregidos")
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Albaranes", len(df))
    
    with col2:
        total_open = int(df['Total_Open'].sum())
        st.metric("Tablillas Pendientes", total_open)
    
    with col3:
        avg_delay = df['Counting_Delay'].mean()
        st.metric("Retraso Promedio", f"{avg_delay:.1f} días")
    
    # Tabla principal - VERIFICAR CORRECCIÓN
    st.subheader("🔍 Verificación de Datos Extraídos")
    
    # Mostrar columnas clave para verificar que esté bien
    verification_cols = [
        'Return_Packing_Slip', 'Customer_Name', 'Job_Site_Name', 
        'Definitive_Dev', 'Counted_Date', 'Tablets', 'Total_Tablets', 
        'Open_Tablets', 'Total_Open', 'Counting_Delay', 'Validation_Delay'
    ]
    
    available_cols = [col for col in verification_cols if col in df.columns]
    st.dataframe(df[available_cols], use_container_width=True)
    
    # Botón de descarga
    if st.button("📥 Descargar Excel Corregido"):
        download_excel_corrected(df)

def download_excel_corrected(df):
    """Descargar Excel con datos corregidos"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Albaranes_Corregidos', index=False)
    
    current_date = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"tablillas_corregido_{current_date}.xlsx"
    
    st.download_button(
        label="📥 Descargar Excel Corregido",
        data=output.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.success(f"✅ Excel corregido generado: {filename}")

if __name__ == "__main__":
    main()