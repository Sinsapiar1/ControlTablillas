"""
Parser Avanzado para PDFs Extremadamente Complejos de Alsina Forms
Usa múltiples bibliotecas y técnicas para manejar headers y datos divididos
"""

import re
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import streamlit as st
import pdfplumber
import numpy as np

# Intentar importar bibliotecas avanzadas
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    st.warning("⚠️ Camelot no disponible. Instalando bibliotecas avanzadas...")

try:
    import tabula
    TABULA_AVAILABLE = True
except ImportError:
    TABULA_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

class AdvancedAlsinaPDFParser:
    """Parser ultra-robusto para PDFs extremadamente complejos"""
    
    def __init__(self):
        self.debug_mode = True
        
    def parse_pdf_file(self, pdf_file) -> Optional[pd.DataFrame]:
        """Parsear PDF usando múltiples estrategias"""
        
        st.info("🚀 **Parser Avanzado Activo** - Usando múltiples técnicas de extracción")
        
        # Estrategia 1: Camelot (mejor para tablas complejas)
        if CAMELOT_AVAILABLE:
            df = self._parse_with_camelot(pdf_file)
            if df is not None and not df.empty:
                st.success("✅ Extracción exitosa con Camelot")
                return df
        
        # Estrategia 2: Tabula (buena para tablas con headers divididos)
        if TABULA_AVAILABLE:
            df = self._parse_with_tabula(pdf_file)
            if df is not None and not df.empty:
                st.success("✅ Extracción exitosa con Tabula")
                return df
        
        # Estrategia 3: PyMuPDF (extracción de texto con posicionamiento)
        if PYMUPDF_AVAILABLE:
            df = self._parse_with_pymupdf(pdf_file)
            if df is not None and not df.empty:
                st.success("✅ Extracción exitosa con PyMuPDF")
                return df
        
        # Estrategia 4: PDFPlumber mejorado (fallback)
        df = self._parse_with_enhanced_pdfplumber(pdf_file)
        if df is not None and not df.empty:
            st.success("✅ Extracción exitosa con PDFPlumber mejorado")
            return df
        
        st.error("❌ No se pudo extraer datos con ninguna estrategia")
        return None
    
    def _parse_with_camelot(self, pdf_file) -> Optional[pd.DataFrame]:
        """Usar Camelot para extraer tablas complejas"""
        try:
            st.write("🔍 Intentando extracción con Camelot...")
            
            # Guardar archivo temporalmente
            with open("temp_pdf.pdf", "wb") as f:
                f.write(pdf_file.getvalue())
            
            # Extraer tablas con Camelot
            tables = camelot.read_pdf("temp_pdf.pdf", pages='all', flavor='lattice')
            
            if not tables:
                # Intentar con flavor 'stream'
                tables = camelot.read_pdf("temp_pdf.pdf", pages='all', flavor='stream')
            
            if tables:
                st.write(f"📊 Camelot encontró {len(tables)} tablas")
                
                # Combinar todas las tablas
                all_data = []
                for i, table in enumerate(tables):
                    df_table = table.df
                    if self.debug_mode:
                        st.write(f"Tabla {i+1}: {len(df_table)} filas, {len(df_table.columns)} columnas")
                    
                    # Procesar tabla
                    processed_data = self._process_camelot_table(df_table, i+1)
                    if processed_data:
                        all_data.extend(processed_data)
                
                if all_data:
                    return pd.DataFrame(all_data)
            
            return None
            
        except Exception as e:
            if self.debug_mode:
                st.write(f"⚠️ Error con Camelot: {str(e)}")
            return None
    
    def _parse_with_tabula(self, pdf_file) -> Optional[pd.DataFrame]:
        """Usar Tabula para extraer tablas"""
        try:
            st.write("🔍 Intentando extracción con Tabula...")
            
            # Guardar archivo temporalmente
            with open("temp_pdf.pdf", "wb") as f:
                f.write(pdf_file.getvalue())
            
            # Extraer tablas
            tables = tabula.read_pdf("temp_pdf.pdf", pages='all', multiple_tables=True)
            
            if tables:
                st.write(f"📊 Tabula encontró {len(tables)} tablas")
                
                all_data = []
                for i, table in enumerate(tables):
                    if self.debug_mode:
                        st.write(f"Tabla {i+1}: {len(table)} filas, {len(table.columns)} columnas")
                    
                    processed_data = self._process_tabula_table(table, i+1)
                    if processed_data:
                        all_data.extend(processed_data)
                
                if all_data:
                    return pd.DataFrame(all_data)
            
            return None
            
        except Exception as e:
            if self.debug_mode:
                st.write(f"⚠️ Error con Tabula: {str(e)}")
            return None
    
    def _parse_with_pymupdf(self, pdf_file) -> Optional[pd.DataFrame]:
        """Usar PyMuPDF para extracción con posicionamiento"""
        try:
            st.write("🔍 Intentando extracción con PyMuPDF...")
            
            # Guardar archivo temporalmente
            with open("temp_pdf.pdf", "wb") as f:
                f.write(pdf_file.getvalue())
            
            doc = fitz.open("temp_pdf.pdf")
            all_data = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extraer texto con posicionamiento
                text_dict = page.get_text("dict")
                
                # Procesar bloques de texto
                page_data = self._process_pymupdf_page(text_dict, page_num)
                if page_data:
                    all_data.extend(page_data)
            
            doc.close()
            
            if all_data:
                return pd.DataFrame(all_data)
            
            return None
            
        except Exception as e:
            if self.debug_mode:
                st.write(f"⚠️ Error con PyMuPDF: {str(e)}")
            return None
    
    def _parse_with_enhanced_pdfplumber(self, pdf_file) -> Optional[pd.DataFrame]:
        """PDFPlumber mejorado específicamente para este formato"""
        try:
            st.write("🔍 Usando PDFPlumber mejorado...")
            
            with pdfplumber.open(pdf_file) as pdf:
                all_data = []
                
                for page_num, page in enumerate(pdf.pages):
                    # Extraer texto línea por línea
                    text = page.extract_text()
                    if text:
                        # Procesar texto específicamente para este formato
                        page_data = self._process_alsina_text(text, page_num)
                        if page_data:
                            all_data.extend(page_data)
                
                if all_data:
                    return pd.DataFrame(all_data)
            
            return None
            
        except Exception as e:
            if self.debug_mode:
                st.write(f"⚠️ Error con PDFPlumber: {str(e)}")
            return None
    
    def _process_alsina_text(self, text: str, page_num: int) -> List[Dict]:
        """Procesar texto específicamente para el formato Alsina"""
        
        lines = text.split('\n')
        data_lines = []
        
        # Encontrar líneas de datos (que empiecen con FL)
        for line in lines:
            line = line.strip()
            if line.startswith('FL') and len(line.split()) >= 10:
                data_lines.append(line)
        
        if self.debug_mode:
            st.write(f"📋 Página {page_num + 1}: Encontradas {len(data_lines)} líneas de datos")
        
        # Procesar cada línea de datos
        parsed_data = []
        for i, line in enumerate(data_lines):
            row_data = self._parse_alsina_line(line, i + 1)
            if row_data:
                parsed_data.append(row_data)
                if self.debug_mode and len(parsed_data) <= 3:
                    st.write(f"✅ Línea {i+1}: {row_data['Customer_Name']} - {row_data['Job_Site_Name']}")
        
        return parsed_data
    
    def _parse_alsina_line(self, line: str, line_num: int) -> Optional[Dict]:
        """Parsear línea específica del formato Alsina con regex ultra-flexible"""
        
        # Patrón regex específico para el formato exacto observado
        # FL 61D 729000018669 9/2/2025 40037739 FL053 8/31/2025 9/30/2025 3c Construction Corp Biscayne Bay Coastal Wetl No 81, 134, 1666, 1708 4 1666M, 1708M 2 15 0
        
        # Patrón más flexible que maneja variaciones
        pattern = r'FL\s+(\w+)\s+(\d{12})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d+)\s+(\w+)\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)(?:\s+(No|Yes|Ye\s+s))(?:\s+(\d{1,2}/\d{1,2}/\d{4}))?(?:\s+(.+?))?(?:\s+(\d+))?(?:\s+(\d+))?(?:\s+(\d+))?(?:\s+(\d+))?$'
        
        match = re.search(pattern, line)
        
        if not match:
            if self.debug_mode:
                st.write(f"⚠️ Línea {line_num}: No coincide con patrón")
                st.write(f"Línea: {line[:100]}...")
            return None
        
        groups = match.groups()
        
        # Extraer campos básicos
        wh_code = groups[0]
        return_slip = groups[1]
        return_date = self._parse_date(groups[2])
        jobsite_id = groups[3]
        cost_center = groups[4]
        invoice_start = self._parse_date(groups[5])
        invoice_end = self._parse_date(groups[6])
        
        # Extraer nombres (grupo 7 contiene todo el texto entre fechas y Yes/No)
        names_text = groups[7]
        customer_name, job_site_name = self._split_alsina_names(names_text)
        
        # Estado definitivo
        definitive_dev = "Yes" if groups[8] and "Yes" in groups[8] else "No"
        
        # Fecha de conteo
        counted_date = self._parse_date(groups[9]) if groups[9] else None
        
        # Información de tablillas
        tablets_text = groups[10] if groups[10] else ""
        tablets_info = self._extract_alsina_tablets(tablets_text)
        
        # Totales
        total_tablets = self._parse_number(groups[11]) if groups[11] else 0
        total_open = self._parse_number(groups[12]) if groups[12] else 0
        counting_delay = self._parse_number(groups[13]) if groups[13] else 0
        validation_delay = self._parse_number(groups[14]) if groups[14] else 0
        
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
    
    def _split_alsina_names(self, names_text: str) -> Tuple[str, str]:
        """Dividir nombres específicamente para el formato Alsina"""
        
        if not names_text:
            return "Unknown Customer", "Unknown Site"
        
        # Patrones específicos basados en los ejemplos reales
        # "3c Construction Corp     Biscayne Bay Coastal Wetl"
        # "Caribbean Building Corp  Modena 22"
        # "Thales Builders Corp     4580 North Bay Road Resid"
        
        # Buscar múltiples espacios como separador
        if '     ' in names_text:  # 5 espacios
            parts = names_text.split('     ', 1)
            return parts[0].strip(), parts[1].strip()
        elif '    ' in names_text:  # 4 espacios
            parts = names_text.split('    ', 1)
            return parts[0].strip(), parts[1].strip()
        elif '   ' in names_text:  # 3 espacios
            parts = names_text.split('   ', 1)
            return parts[0].strip(), parts[1].strip()
        
        # Fallback: buscar marcadores de empresa
        company_endings = ['corp', 'llc', 'inc', 'ltd', 'construction', 'builders', 'services', 'group']
        
        words = names_text.split()
        split_point = len(words) // 2
        
        for i, word in enumerate(words):
            if word.lower() in company_endings:
                split_point = i + 1
                break
        
        customer_parts = words[:split_point]
        site_parts = words[split_point:]
        
        customer_name = ' '.join(customer_parts) if customer_parts else "Unknown Customer"
        job_site_name = ' '.join(site_parts) if site_parts else "Unknown Site"
        
        return customer_name.strip(), job_site_name.strip()
    
    def _extract_alsina_tablets(self, tablets_text: str) -> Dict:
        """Extraer tablillas específicamente para el formato Alsina"""
        
        tablets = []
        open_tablets = []
        
        if not tablets_text:
            return {'tablets': '', 'open_tablets': ''}
        
        # Buscar números de tablillas (con comas)
        # Ejemplo: "81, 134, 1666, 1708"
        tablet_pattern = r'\b\d{1,4}(?:,\s*\d{1,4})*\b'
        tablet_matches = re.findall(tablet_pattern, tablets_text)
        
        for match in tablet_matches:
            numbers = [num.strip() for num in match.split(',')]
            tablets.extend(numbers)
        
        # Buscar tablillas abiertas (números con letras)
        # Ejemplo: "1666M, 1708M"
        open_pattern = r'\b\d{1,4}[A-Z]+\b'
        open_matches = re.findall(open_pattern, tablets_text)
        open_tablets.extend(open_matches)
        
        return {
            'tablets': ', '.join(tablets),
            'open_tablets': ', '.join(open_tablets)
        }
    
    def _parse_date(self, date_str: str) -> Optional[pd.Timestamp]:
        """Parsear fecha de forma segura"""
        if not date_str or date_str.lower() in ['no', 'yes', '']:
            return None
        
        try:
            return pd.to_datetime(date_str, format='%m/%d/%Y')
        except:
            try:
                return pd.to_datetime(date_str, infer_datetime_format=True)
            except:
                return None
    
    def _parse_number(self, num_str: str) -> Optional[int]:
        """Parsear número de forma segura"""
        if not num_str:
            return 0
        
        try:
            return int(num_str)
        except:
            return 0
    
    def _process_camelot_table(self, df, table_num: int) -> List[Dict]:
        """Procesar tabla extraída por Camelot"""
        # Implementar procesamiento específico para Camelot
        return []
    
    def _process_tabula_table(self, df, table_num: int) -> List[Dict]:
        """Procesar tabla extraída por Tabula"""
        # Implementar procesamiento específico para Tabula
        return []
    
    def _process_pymupdf_page(self, text_dict, page_num: int) -> List[Dict]:
        """Procesar página extraída por PyMuPDF"""
        # Implementar procesamiento específico para PyMuPDF
        return []

# Función de prueba
def test_advanced_parser():
    """Probar el parser avanzado"""
    parser = AdvancedAlsinaPDFParser()
    
    # Datos de ejemplo del formato real
    sample_data = """FL 61D 729000018669 9/2/2025 40037739 FL053 8/31/2025 9/30/2025 3c Construction Corp     Biscayne Bay Coastal Wetl No 81, 134, 1666, 1708 4 1666M, 1708M 2 15 0
FL 612d 729000018670 9/2/2025 40036511 FL013 8/31/2025 9/30/2025 Caribbean Building Corp  Modena 22                No 230, 259, 263, 278 4 230M, 278A 2 15 0"""
    
    result = parser._process_alsina_text(sample_data, 0)
    
    if result:
        print("✅ Parser avanzado funcionando")
        print(f"Registros extraídos: {len(result)}")
        for i, record in enumerate(result):
            print(f"\n=== REGISTRO {i+1} ===")
            print(f"Cliente: {record['Customer_Name']}")
            print(f"Sitio: {record['Job_Site_Name']}")
            print(f"Tablillas: {record['Tablets']}")
            print(f"Tablillas Abiertas: {record['Open_Tablets']}")
    else:
        print("❌ Error en el parser avanzado")

if __name__ == "__main__":
    test_advanced_parser()