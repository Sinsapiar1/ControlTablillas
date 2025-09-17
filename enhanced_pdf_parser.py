"""
Parser mejorado para PDFs de Alsina Forms Co.
Maneja correctamente headers divididos, columnas duplicadas y datos mixtos
"""

import re
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import streamlit as st
import pdfplumber
from pdfplumber.table import Table

class EnhancedAlsinaPDFParser:
    """Parser robusto para el formato complejo de Alsina Forms"""
    
    def __init__(self):
        self.debug_mode = True
        
    def parse_pdf_file(self, pdf_file) -> Optional[pd.DataFrame]:
        """Parsear archivo PDF usando pdfplumber con detección de tablas"""
        try:
            with pdfplumber.open(pdf_file) as pdf:
                all_data = []
                
                for page_num, page in enumerate(pdf.pages):
                    if self.debug_mode:
                        st.write(f"🔍 Procesando página {page_num + 1}...")
                    
                    # Intentar extraer como tabla primero
                    tables = page.extract_tables()
                    
                    if tables:
                        if self.debug_mode:
                            st.write(f"📊 Encontradas {len(tables)} tablas en página {page_num + 1}")
                        
                        for table_num, table in enumerate(tables):
                            if self.debug_mode:
                                st.write(f"📋 Procesando tabla {table_num + 1} con {len(table)} filas")
                            
                            parsed_table = self._parse_table_data(table, page_num, table_num)
                            if parsed_table:
                                all_data.extend(parsed_table)
                    else:
                        # Fallback: extraer como texto y parsear manualmente
                        text = page.extract_text()
                        if text:
                            parsed_text = self._parse_text_content(text, page_num)
                            if parsed_text:
                                all_data.extend(parsed_text)
                
                if all_data:
                    df = pd.DataFrame(all_data)
                    if self.debug_mode:
                        st.write(f"✅ Total de registros extraídos: {len(df)}")
                    return df
                else:
                    if self.debug_mode:
                        st.write("❌ No se encontraron datos válidos")
                    return None
                    
        except Exception as e:
            st.error(f"Error procesando PDF: {str(e)}")
            return None
    
    def _parse_table_data(self, table: List[List[str]], page_num: int, table_num: int) -> List[Dict]:
        """Parsear datos de tabla extraída por pdfplumber"""
        if not table or len(table) < 2:
            return []
        
        # Encontrar fila de headers
        header_row_idx = self._find_header_row(table)
        if header_row_idx == -1:
            if self.debug_mode:
                st.write(f"⚠️ No se encontró header en tabla {table_num + 1}")
            return []
        
        # Procesar headers (pueden estar en múltiples filas)
        headers = self._process_headers(table, header_row_idx)
        
        if self.debug_mode:
            st.write(f"📋 Headers detectados: {headers}")
        
        # Procesar filas de datos
        data_rows = []
        for i in range(header_row_idx + 1, len(table)):
            row_data = self._parse_data_row(table[i], headers, i)
            if row_data:
                data_rows.append(row_data)
        
        return data_rows
    
    def _find_header_row(self, table: List[List[str]]) -> int:
        """Encontrar la fila que contiene los headers"""
        for i, row in enumerate(table):
            if not row:
                continue
            
            # Buscar indicadores de header
            row_text = ' '.join([cell or '' for cell in row]).lower()
            
            # Indicadores de que es una fila de header
            header_indicators = [
                'wh', 'return', 'packing', 'slip', 'date', 'jobsite', 
                'cost', 'center', 'invoice', 'customer', 'name', 'definitive',
                'counted', 'tablets', 'total', 'delay', 'validation'
            ]
            
            matches = sum(1 for indicator in header_indicators if indicator in row_text)
            
            if matches >= 3:  # Al menos 3 indicadores
                return i
        
        return -1
    
    def _process_headers(self, table: List[List[str]], header_row_idx: int) -> List[str]:
        """Procesar headers que pueden estar divididos en múltiples filas"""
        headers = []
        
        # Obtener la fila principal de headers
        main_header_row = table[header_row_idx]
        
        # Verificar si hay filas adicionales de headers arriba
        additional_headers = []
        for i in range(max(0, header_row_idx - 2), header_row_idx):
            if i < len(table) and table[i]:
                additional_headers.append(table[i])
        
        # Combinar headers de múltiples filas
        for col_idx, cell in enumerate(main_header_row):
            if not cell or cell.strip() == '':
                continue
            
            # Buscar headers adicionales en la misma columna
            combined_header = cell.strip()
            
            for additional_row in additional_headers:
                if col_idx < len(additional_row) and additional_row[col_idx]:
                    additional_text = additional_row[col_idx].strip()
                    if additional_text and additional_text not in combined_header:
                        combined_header = f"{additional_text} {combined_header}"
            
            # Limpiar y normalizar header
            clean_header = self._normalize_header(combined_header)
            headers.append(clean_header)
        
        return headers
    
    def _normalize_header(self, header: str) -> str:
        """Normalizar nombres de headers"""
        header = header.strip().lower()
        
        # Mapeo de headers a nombres estándar
        header_mapping = {
            'wh': 'WH',
            'return packing slip': 'Return_Packing_Slip',
            'return p.slip date': 'Return_Date',
            'jobsite': 'Jobsite_ID',
            'cost center': 'Cost_Center',
            'next invoice date': 'Invoice_Date',  # Se manejará la duplicación después
            'customer name': 'Customer_Name',
            'job site name': 'Job_Site_Name',
            'definitive': 'Definitive_Dev',
            'definiti ve de v': 'Definitive_Dev',
            'counted date': 'Counted_Date',
            'tablets': 'Tablets',
            'total i open tablets': 'Open_Tablets_Info',
            'total countin g delay': 'Counting_Delay',
            'validatio n delay': 'Validation_Delay'
        }
        
        # Buscar coincidencia parcial
        for key, value in header_mapping.items():
            if key in header:
                return value
        
        # Si no encuentra coincidencia, limpiar y usar como está
        return header.replace(' ', '_').replace('.', '').replace(',', '')
    
    def _parse_data_row(self, row: List[str], headers: List[str], row_idx: int) -> Optional[Dict]:
        """Parsear una fila de datos"""
        if not row or len(row) < 5:
            return None
        
        # Verificar si es una fila de datos válida
        if not self._is_valid_data_row(row):
            return None
        
        row_data = {}
        
        # Mapear datos a headers
        for col_idx, cell in enumerate(row):
            if col_idx < len(headers) and cell:
                header = headers[col_idx]
                value = cell.strip()
                
                # Procesar valor según el tipo de campo
                processed_value = self._process_field_value(header, value)
                row_data[header] = processed_value
        
        # Validar que tenga campos mínimos requeridos
        required_fields = ['WH', 'Return_Packing_Slip', 'Customer_Name']
        if not all(field in row_data for field in required_fields):
            return None
        
        return row_data
    
    def _is_valid_data_row(self, row: List[str]) -> bool:
        """Verificar si una fila contiene datos válidos"""
        if not row:
            return False
        
        # Debe empezar con 'FL'
        first_cell = row[0] if row[0] else ''
        if not first_cell.strip().startswith('FL'):
            return False
        
        # Debe tener al menos un número de packing slip
        row_text = ' '.join([cell or '' for cell in row])
        if not re.search(r'\d{12}', row_text):
            return False
        
        return True
    
    def _process_field_value(self, header: str, value: str) -> any:
        """Procesar valor según el tipo de campo"""
        if not value or value.strip() == '':
            return None
        
        value = value.strip()
        
        # Fechas
        if 'date' in header.lower():
            return self._parse_date(value)
        
        # Números
        if any(keyword in header.lower() for keyword in ['delay', 'total', 'count']):
            return self._parse_number(value)
        
        # Tablillas (números con comas)
        if 'tablets' in header.lower() and ',' in value:
            return value  # Mantener como string para tablillas
        
        # Valores de sí/no
        if 'definitive' in header.lower():
            return 'Yes' if value.lower() in ['yes', 'yes s', 's'] else 'No'
        
        return value
    
    def _parse_date(self, date_str: str) -> Optional[pd.Timestamp]:
        """Parsear fecha de forma segura"""
        if not date_str or date_str.lower() in ['no', 'yes', '']:
            return None
        
        # Limpiar la fecha
        date_str = re.sub(r'[^\d/]', '', date_str)
        
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
        
        # Extraer solo dígitos
        digits = re.sub(r'[^\d]', '', num_str)
        
        try:
            return int(digits) if digits else 0
        except:
            return 0
    
    def _parse_text_content(self, text: str, page_num: int) -> List[Dict]:
        """Fallback: parsear contenido como texto cuando no se detectan tablas"""
        lines = text.split('\n')
        data_lines = []
        
        # Encontrar líneas de datos
        for line in lines:
            line = line.strip()
            if line.startswith('FL') and len(line.split()) >= 10:
                data_lines.append(line)
        
        # Parsear cada línea
        parsed_data = []
        for i, line in enumerate(data_lines):
            row_data = self._parse_text_line(line, i + 1)
            if row_data:
                parsed_data.append(row_data)
        
        return parsed_data
    
    def _parse_text_line(self, line: str, line_num: int) -> Optional[Dict]:
        """Parsear línea de texto usando regex mejorado"""
        try:
            # Patrón regex más flexible para manejar variaciones
            pattern = r'FL\s+(\w+)\s+(\d{12})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d+)\s+(\w+)\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)(?:\s+(Yes|No|Ye\s+s))?(?:\s+(\d{1,2}/\d{1,2}/\d{4}))?(?:\s+(.+?))?(?:\s+(\d+))?(?:\s+(\d+))?(?:\s+(\d+))?(?:\s+(\d+))?$'
            
            match = re.search(pattern, line)
            
            if not match:
                if self.debug_mode:
                    st.write(f"⚠️ Línea {line_num}: No coincide con patrón")
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
            
            # Extraer nombres
            names_text = groups[7] if groups[7] else ""
            customer_name, job_site_name = self._split_names(names_text)
            
            # Estado definitivo
            definitive_dev = "No"
            if groups[8]:
                definitive_dev = "Yes" if groups[8].lower() in ['yes', 'ye s'] else "No"
            
            # Fecha de conteo
            counted_date = self._parse_date(groups[9]) if groups[9] else None
            
            # Información de tablillas
            tablets_text = groups[10] if groups[10] else ""
            tablets_info = self._extract_tablets_info(tablets_text)
            
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
            
        except Exception as e:
            if self.debug_mode:
                st.write(f"❌ Error parseando línea {line_num}: {str(e)}")
            return None
    
    def _split_names(self, names_text: str) -> Tuple[str, str]:
        """Dividir nombres de cliente y sitio"""
        if not names_text:
            return "Unknown Customer", "Unknown Site"
        
        # Patrones para identificar el final del nombre de la empresa
        company_endings = ['corp', 'llc', 'inc', 'ltd', 'construction', 'builders', 'services', 'group', 'development', 'company', 'co']
        
        words = names_text.split()
        split_point = len(words) // 2  # Punto medio por defecto
        
        # Buscar el último marcador de empresa
        for i, word in enumerate(words):
            if word.lower() in company_endings:
                split_point = i + 1
        
        customer_parts = words[:split_point]
        site_parts = words[split_point:]
        
        customer_name = ' '.join(customer_parts) if customer_parts else "Unknown Customer"
        job_site_name = ' '.join(site_parts) if site_parts else "Unknown Site"
        
        return customer_name.strip(), job_site_name.strip()
    
    def _extract_tablets_info(self, tablets_text: str) -> Dict:
        """Extraer información de tablillas"""
        tablets = []
        open_tablets = []
        
        if not tablets_text:
            return {'tablets': '', 'open_tablets': ''}
        
        # Buscar números de tablillas (con comas)
        tablet_pattern = r'\b\d{3,4}(?:,\s*\d{3,4})*\b'
        tablet_matches = re.findall(tablet_pattern, tablets_text)
        
        for match in tablet_matches:
            numbers = [num.strip() for num in match.split(',')]
            tablets.extend(numbers)
        
        # Buscar tablillas abiertas (números con letras)
        open_pattern = r'\b\d{3,4}[A-Z]+\b'
        open_matches = re.findall(open_pattern, tablets_text)
        open_tablets.extend(open_matches)
        
        return {
            'tablets': ', '.join(tablets),
            'open_tablets': ', '.join(open_tablets)
        }

# Función de prueba
def test_enhanced_parser():
    """Probar el parser mejorado"""
    parser = EnhancedAlsinaPDFParser()
    
    # Datos de ejemplo
    sample_data = """FL 61D 729000018669 9/2/2025 40037739 FL053 8/31/2025 9/30/2025 3c Construction Corp Biscayne Bay Coastal Wetl No 81, 134, 1666, 1708 4 1666M, 1708M 2 15 0
FL 612d 729000018670 9/2/2025 40037740 FL053 8/31/2025 9/30/2025 Caribbean Building Corp Modena 22 No 230, 259, 263, 278 4 230M, 278A 2 15 1"""
    
    result = parser._parse_text_content(sample_data, 0)
    
    if result:
        print("✅ Parser mejorado funcionando")
        print(f"Registros extraídos: {len(result)}")
        for i, record in enumerate(result):
            print(f"\n=== REGISTRO {i+1} ===")
            print(f"Cliente: {record['Customer_Name']}")
            print(f"Sitio: {record['Job_Site_Name']}")
            print(f"Tablillas: {record['Tablets']}")
            print(f"Tablillas Abiertas: {record['Open_Tablets']}")
            print(f"Total: {record['Total_Tablets']}")
            print(f"Abiertas: {record['Total_Open']}")
    else:
        print("❌ Error en el parser mejorado")

if __name__ == "__main__":
    test_enhanced_parser()