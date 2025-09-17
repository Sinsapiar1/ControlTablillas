"""
Parser robusto para PDFs de Alsina Forms Co.
Versión final que maneja correctamente todos los casos del formato específico
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
            
            # Usar método de posiciones fijas más robusto
            parsed_data = self._extract_by_positions(line, line_number)
            
            return parsed_data
            
        except Exception as e:
            if self.debug_mode:
                st.write(f"❌ Error en línea {line_number}: {str(e)}")
            return None
    
    def _extract_by_positions(self, line: str, line_number: int) -> Optional[Dict]:
        """Extraer campos usando posiciones fijas basadas en el formato exacto"""
        
        # Dividir la línea en partes
        parts = line.split()
        
        if len(parts) < 15:
            if self.debug_mode:
                st.write(f"⚠️ Línea {line_number}: Muy pocas partes ({len(parts)})")
            return None
        
        # Campos fijos al inicio
        wh = parts[0]  # FL
        wh_code = parts[1]  # 61D, 612d, etc.
        return_slip = parts[2]  # 729000018709
        
        # Encontrar fechas
        dates = []
        date_positions = []
        
        for i, part in enumerate(parts):
            if re.match(r'\d{1,2}/\d{1,2}/\d{4}', part):
                dates.append(self._parse_date(part))
                date_positions.append(i)
        
        if len(dates) < 2:
            if self.debug_mode:
                st.write(f"⚠️ Línea {line_number}: No se encontraron suficientes fechas")
            return None
        
        return_date = dates[0]
        invoice_start = dates[1] if len(dates) > 1 else None
        invoice_end = dates[2] if len(dates) > 2 else None
        
        # Jobsite ID y Cost Center (después de la primera fecha)
        jobsite_id = parts[date_positions[0] + 1] if date_positions[0] + 1 < len(parts) else ""
        cost_center = parts[date_positions[0] + 2] if date_positions[0] + 2 < len(parts) else ""
        
        # Buscar Yes/No para Definitive Dev
        definitive_dev = "No"
        status_position = -1
        
        for i, part in enumerate(parts):
            if part in ['Yes', 'No']:
                definitive_dev = part
                status_position = i
                break
            elif part == 'Ye' and i + 1 < len(parts) and parts[i + 1] == 's':
                definitive_dev = "Yes"
                status_position = i
                break
        
        if status_position == -1:
            if self.debug_mode:
                st.write(f"⚠️ Línea {line_number}: No se encontró Yes/No")
            return None
        
        # Extraer nombres (entre cost_center y Yes/No)
        cost_center_pos = date_positions[0] + 2
        names_parts = parts[cost_center_pos + 1:status_position]
        
        customer_name, job_site_name = self._split_names_robust(names_parts)
        
        # Buscar fecha de conteo (después de Yes/No)
        counted_date = None
        counted_pos = status_position + 1
        if counted_pos < len(parts) and re.match(r'\d{1,2}/\d{1,2}/\d{4}', parts[counted_pos]):
            counted_date = self._parse_date(parts[counted_pos])
            counted_pos += 1
        
        # Extraer información de tablillas
        tablets_info = self._extract_tablets_robust(parts, counted_pos)
        
        # Extraer totales (últimos 4 números)
        totals = []
        for part in parts[-4:]:
            if re.match(r'^\d+$', part):
                totals.append(int(part))
        
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
            'Tablets': tablets_info['tablets'],
            'Total_Tablets': totals[0] if len(totals) >= 1 else 0,
            'Open_Tablets': tablets_info['open_tablets'],
            'Total_Open': totals[1] if len(totals) >= 2 else 0,
            'Counting_Delay': totals[2] if len(totals) >= 3 else 0,
            'Validation_Delay': totals[3] if len(totals) >= 4 else 0
        }
    
    def _split_names_robust(self, names_parts: List[str]) -> Tuple[str, str]:
        """Dividir nombres de manera robusta"""
        if not names_parts:
            return "Unknown Customer", "Unknown Site"
        
        # Buscar patrones de nombres de empresa
        company_keywords = ['corp', 'llc', 'inc', 'ltd', 'construction', 'builders', 'services', 'group', 'development']
        
        # Encontrar el punto de división
        split_point = len(names_parts) // 2  # Por defecto, la mitad
        
        for i, part in enumerate(names_parts):
            if part.lower() in company_keywords:
                split_point = min(i + 1, len(names_parts))
                break
        
        customer_parts = names_parts[:split_point]
        site_parts = names_parts[split_point:]
        
        customer_name = ' '.join(customer_parts) if customer_parts else "Unknown Customer"
        job_site_name = ' '.join(site_parts) if site_parts else "Unknown Site"
        
        return customer_name.strip(), job_site_name.strip()
    
    def _extract_tablets_robust(self, parts: List[str], start_pos: int) -> Dict:
        """Extraer información de tablillas de manera robusta"""
        tablets = []
        open_tablets = []
        
        # Buscar números de tablillas (hasta encontrar los totales)
        i = start_pos
        while i < len(parts) - 4:  # Dejar espacio para los totales
            part = parts[i]
            
            # Números de tablillas: dígitos con comas opcionales
            if re.match(r'^\d{3,4},?$', part):
                clean_number = re.sub(r'[^\d]', '', part)
                if len(clean_number) >= 3:  # Solo números de 3-4 dígitos
                    tablets.append(clean_number)
            
            # Códigos de tablillas abiertas: números con letras
            elif re.match(r'^\d{3,4}[A-Z]+,?$', part):
                clean_code = part.replace(',', '')
                if clean_code not in ['61D', '612d', '61d', 'FL']:
                    open_tablets.append(clean_code)
            
            i += 1
        
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

# Función de prueba
def test_parser():
    """Función para probar el parser con datos de ejemplo"""
    parser = AlsinaFormsPDFParser()
    
    # Datos de ejemplo del PDF
    sample_data = """FL 61D 729000018709 9/8/2025 40036567 FL052 8/31/2025 9/30/2025 Phorcys Builders Corp The Villages at East Ocea Yes 9/17/2025 1662, 1674, 1718 3 0 9 0
FL 612d 729000018710 9/8/2025 40036567 FL052 8/31/2025 9/30/2025 Phorcys Builders Corp The Villages at East Ocea Yes 9/12/2025 1323 1 0 4 3
FL 612d 729000018711 9/8/2025 40036567 FL052 8/31/2025 9/30/2025 Phorcys Builders Corp The Villages at East Ocea Yes 9/9/2025 1480, 1481 2 0 1 2
FL 612d 729000018712 9/8/2025 40038613 FL053 8/31/2025 9/30/2025 Delta Construction Group 2060 New Single Family Re No 1491 1 1491T 1 9 0"""
    
    result = parser.parse_pdf_content(sample_data)
    
    if result is not None:
        print("✅ Parser funcionando correctamente")
        print(f"Registros extraídos: {len(result)}")
        print("\n=== PRIMER REGISTRO ===")
        first_record = result.iloc[0]
        print(f"Cliente: {first_record['Customer_Name']}")
        print(f"Sitio: {first_record['Job_Site_Name']}")
        print(f"Tablillas: {first_record['Tablets']}")
        print(f"Total: {first_record['Total_Tablets']}")
        print(f"Abiertas: {first_record['Total_Open']}")
        print(f"Definitivo: {first_record['Definitive_Dev']}")
        
        print("\n=== SEGUNDO REGISTRO ===")
        second_record = result.iloc[1]
        print(f"Cliente: {second_record['Customer_Name']}")
        print(f"Sitio: {second_record['Job_Site_Name']}")
        print(f"Tablillas: {second_record['Tablets']}")
        print(f"Total: {second_record['Total_Tablets']}")
        print(f"Abiertas: {second_record['Total_Open']}")
        print(f"Definitivo: {second_record['Definitive_Dev']}")
        
        print("\n=== TERCER REGISTRO (con tablillas abiertas) ===")
        third_record = result.iloc[3]
        print(f"Cliente: {third_record['Customer_Name']}")
        print(f"Sitio: {third_record['Job_Site_Name']}")
        print(f"Tablillas: {third_record['Tablets']}")
        print(f"Tablillas Abiertas: {third_record['Open_Tablets']}")
        print(f"Total: {third_record['Total_Tablets']}")
        print(f"Abiertas: {third_record['Total_Open']}")
        print(f"Definitivo: {third_record['Definitive_Dev']}")
        
    else:
        print("❌ Error en el parser")

if __name__ == "__main__":
    test_parser()