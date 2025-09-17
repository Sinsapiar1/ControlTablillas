"""
Parser final optimizado para PDFs de Alsina Forms Co.
Versión mejorada que maneja correctamente la extracción de columnas
"""

import re
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import streamlit as st

class AlsinaFormsPDFParser:
    """Parser especializado para el formato exacto de Alsina Forms"""
    
    def __init__(self):
        self.debug_mode = True
        
    def parse_pdf_content(self, content: str) -> Optional[pd.DataFrame]:
        """Parsear el contenido completo del PDF con el nuevo algoritmo"""
        lines = content.split('\n')
        
        if self.debug_mode:
            st.write(f"🔍 Analizando {len(lines)} líneas del PDF...")
        
        # Encontrar la sección de datos
        data_lines = self._extract_data_lines(lines)
        
        if self.debug_mode:
            st.write(f"📊 Encontradas {len(data_lines)} líneas de datos")
        
        # Parsear cada línea de datos
        parsed_data = []
        for i, line in enumerate(data_lines):
            parsed_row = self._parse_data_line(line, i + 1)
            if parsed_row:
                parsed_data.append(parsed_row)
                if self.debug_mode and len(parsed_data) <= 3:
                    st.write(f"✅ Línea {i+1}: {parsed_row['Customer_Name']} - Tablets: {parsed_row['Tablets']}")
        
        if self.debug_mode:
            st.write(f"📋 Extraídos {len(parsed_data)} registros válidos")
        
        return pd.DataFrame(parsed_data) if parsed_data else None
    
    def _extract_data_lines(self, lines: List[str]) -> List[str]:
        """Extraer solo las líneas que contienen datos de devoluciones"""
        data_lines = []
        in_data_section = False
        
        for line in lines:
            line = line.strip()
            
            # Detectar inicio de sección de datos
            if 'FL' in line and any(char.isdigit() for char in line):
                in_data_section = True
            
            # Si estamos en la sección de datos y la línea parece contener datos
            if in_data_section and self._is_data_line(line):
                data_lines.append(line)
            
            # Detectar fin de sección de datos
            if in_data_section and line.startswith('Alsina Forms Co., Inc.'):
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
            
            # Usar regex para extraer campos de manera más precisa
            parsed_data = self._extract_with_regex(line, line_number)
            
            return parsed_data
            
        except Exception as e:
            if self.debug_mode:
                st.write(f"❌ Error en línea {line_number}: {str(e)}")
            return None
    
    def _extract_with_regex(self, line: str, line_number: int) -> Optional[Dict]:
        """Extraer campos usando regex para mayor precisión"""
        
        # Patrón para extraer todos los campos de una vez
        pattern = r'FL\s+(\w+)\s+(\d{12})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d+)\s+(\w+)\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+(Yes|No)\s+(\d{1,2}/\d{1,2}/\d{4})?\s*(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
        
        match = re.search(pattern, line)
        
        if not match:
            if self.debug_mode:
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
        customer_name, job_site_name = self._split_names_precise(names_text)
        
        definitive_dev = groups[8]
        counted_date = self._parse_date(groups[9]) if groups[9] else None
        
        # Extraer información de tablillas (grupo 10)
        tablets_text = groups[10]
        tablets_info = self._extract_tablets_from_text(tablets_text)
        
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
    
    def _split_names_precise(self, names_text: str) -> Tuple[str, str]:
        """Dividir nombres de manera más precisa"""
        # Limpiar el texto
        names_text = names_text.strip()
        
        # Buscar patrones comunes de nombres de empresa
        company_patterns = [
            r'(.+?)\s+(Corp|LLC|Inc|Ltd|Construction|Builders|Services|Group|Development)',
            r'(.+?)\s+(of|at|in)\s+(.+)',
            r'(.+?)\s+(\d+.*)',  # Para nombres con números
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, names_text, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2:
                    customer_name = match.group(1).strip()
                    job_site_name = names_text[len(match.group(0)):].strip()
                    if not job_site_name:
                        job_site_name = match.group(2).strip()
                    return customer_name, job_site_name
        
        # Si no encuentra patrón, dividir por la mitad
        words = names_text.split()
        if len(words) <= 1:
            return names_text, "Unknown Site"
        
        mid_point = len(words) // 2
        customer_name = ' '.join(words[:mid_point])
        job_site_name = ' '.join(words[mid_point:])
        
        return customer_name, job_site_name
    
    def _extract_tablets_from_text(self, tablets_text: str) -> Dict:
        """Extraer información de tablillas del texto"""
        tablets = []
        open_tablets = []
        
        # Buscar números de tablillas (secuencia de números con comas)
        tablet_pattern = r'\b\d{3,4}(?:,\s*\d{3,4})*\b'
        tablet_matches = re.findall(tablet_pattern, tablets_text)
        
        for match in tablet_matches:
            # Dividir por comas y limpiar
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

# Función de prueba mejorada
def test_parser():
    """Función para probar el parser con datos de ejemplo"""
    parser = AlsinaFormsPDFParser()
    
    # Datos de ejemplo del PDF
    sample_data = """FL 61D 729000018709 9/8/2025 40036567 FL052 8/31/2025 9/30/2025 Phorcys Builders Corp The Villages at East Ocea Yes 9/17/2025 1662, 1674, 1718 3 0 9 0
FL 612d 729000018710 9/8/2025 40036567 FL052 8/31/2025 9/30/2025 Phorcys Builders Corp The Villages at East Ocea Yes 9/12/2025 1323 1 0 4 3
FL 612d 729000018711 9/8/2025 40036567 FL052 8/31/2025 9/30/2025 Phorcys Builders Corp The Villages at East Ocea Yes 9/9/2025 1480, 1481 2 0 1 2"""
    
    result = parser.parse_pdf_content(sample_data)
    
    if result is not None:
        print("✅ Parser funcionando correctamente")
        print(f"Registros extraídos: {len(result)}")
        print("\nPrimer registro:")
        first_record = result.iloc[0]
        print(f"Cliente: {first_record['Customer_Name']}")
        print(f"Sitio: {first_record['Job_Site_Name']}")
        print(f"Tablillas: {first_record['Tablets']}")
        print(f"Total: {first_record['Total_Tablets']}")
        print(f"Abiertas: {first_record['Total_Open']}")
    else:
        print("❌ Error en el parser")

if __name__ == "__main__":
    test_parser()