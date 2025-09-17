"""
Parser mejorado para PDFs de Alsina Forms Co.
Diseñado específicamente para el formato exacto de los reportes de devoluciones
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
            
            # Dividir por espacios pero preservar fechas y nombres
            parts = self._smart_split(line)
            
            if len(parts) < 15:
                if self.debug_mode:
                    st.write(f"⚠️ Línea {line_number}: Muy pocas partes ({len(parts)})")
                return None
            
            # Extraer campos usando posiciones fijas
            parsed_data = self._extract_fields_by_position(parts, line_number)
            
            return parsed_data
            
        except Exception as e:
            if self.debug_mode:
                st.write(f"❌ Error en línea {line_number}: {str(e)}")
            return None
    
    def _smart_split(self, line: str) -> List[str]:
        """Dividir línea preservando fechas y nombres compuestos"""
        # Primero, proteger las fechas
        date_pattern = r'\d{1,2}/\d{1,2}/\d{4}'
        dates = re.findall(date_pattern, line)
        
        # Reemplazar fechas con placeholders
        protected_line = line
        for i, date in enumerate(dates):
            protected_line = protected_line.replace(date, f"__DATE_{i}__")
        
        # Dividir por espacios
        parts = protected_line.split()
        
        # Restaurar fechas
        for i, date in enumerate(dates):
            for j, part in enumerate(parts):
                if part == f"__DATE_{i}__":
                    parts[j] = date
        
        return parts
    
    def _extract_fields_by_position(self, parts: List[str], line_number: int) -> Dict:
        """Extraer campos usando posiciones fijas basadas en el formato"""
        
        # Encontrar fechas para usar como puntos de referencia
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
        
        # Extraer campos básicos (posiciones fijas)
        wh = parts[0] if len(parts) > 0 else ""
        wh_code = parts[1] if len(parts) > 1 else ""
        return_slip = parts[2] if len(parts) > 2 else ""
        
        # Fechas
        return_date = dates[0]
        invoice_start = dates[1] if len(dates) > 1 else None
        invoice_end = dates[2] if len(dates) > 2 else None
        
        # Jobsite ID y Cost Center (después de la primera fecha)
        jobsite_id = parts[date_positions[0] + 1] if len(date_positions) > 0 and date_positions[0] + 1 < len(parts) else ""
        cost_center = parts[date_positions[0] + 2] if len(date_positions) > 0 and date_positions[0] + 2 < len(parts) else ""
        
        # Extraer nombres de cliente y sitio
        customer_name, job_site_name, definitive_dev = self._extract_names_and_status(parts, date_positions)
        
        # Extraer información de tablillas
        tablets_info = self._extract_tablets_info(parts, date_positions)
        
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
            'Counted_Date': tablets_info.get('Counted_Date'),
            'Tablets': tablets_info.get('Tablets', ''),
            'Total_Tablets': tablets_info.get('Total_Tablets', 0),
            'Open_Tablets': tablets_info.get('Open_Tablets', ''),
            'Total_Open': tablets_info.get('Total_Open', 0),
            'Counting_Delay': tablets_info.get('Counting_Delay', 0),
            'Validation_Delay': tablets_info.get('Validation_Delay', 0)
        }
    
    def _extract_names_and_status(self, parts: List[str], date_positions: List[int]) -> Tuple[str, str, str]:
        """Extraer nombres de cliente, sitio y estado definitivo"""
        try:
            # Buscar después de la segunda fecha (invoice dates)
            if len(date_positions) >= 2:
                start_search = date_positions[1] + 1
            else:
                start_search = 8
            
            # Buscar "Yes" o "No" para Definitive Dev
            definitive_dev = "No"
            status_position = -1
            
            for i in range(start_search, len(parts)):
                if parts[i] in ['Yes', 'No']:
                    definitive_dev = parts[i]
                    status_position = i
                    break
                elif parts[i] == 'Ye' and i + 1 < len(parts) and parts[i + 1] == 's':
                    definitive_dev = "Yes"
                    status_position = i
                    break
            
            if status_position == -1:
                # Si no encuentra, asumir posición aproximada
                status_position = len(parts) - 8
            
            # Extraer nombres entre start_search y status_position
            names_parts = parts[start_search:status_position]
            
            if len(names_parts) < 1:
                return "Unknown Customer", "Unknown Site", definitive_dev
            
            # Dividir nombres inteligentemente
            customer_name, job_site_name = self._split_customer_and_site(names_parts)
            
            return customer_name, job_site_name, definitive_dev
            
        except Exception:
            return "Parse Error", "Parse Error", "No"
    
    def _split_customer_and_site(self, names_parts: List[str]) -> Tuple[str, str]:
        """Dividir nombres en cliente y sitio de trabajo"""
        if len(names_parts) <= 1:
            return " ".join(names_parts), "Unknown Site"
        
        # Buscar marcadores típicos del final de nombres de empresa
        company_endings = ['corp', 'llc', 'inc', 'ltd', 'construction', 'builders', 'services', 'group', 'development']
        
        split_point = len(names_parts) // 2  # Punto medio por defecto
        
        for i, part in enumerate(names_parts):
            if part.lower() in company_endings:
                split_point = min(i + 1, len(names_parts))
                break
        
        customer_parts = names_parts[:split_point]
        site_parts = names_parts[split_point:]
        
        customer_name = ' '.join(customer_parts) if customer_parts else "Unknown Customer"
        job_site_name = ' '.join(site_parts) if site_parts else "Unknown Site"
        
        return customer_name.strip(), job_site_name.strip()
    
    def _extract_tablets_info(self, parts: List[str], date_positions: List[int]) -> Dict:
        """Extraer información de tablillas con algoritmo mejorado"""
        try:
            # Buscar después del status (Yes/No)
            status_position = -1
            for i, part in enumerate(parts):
                if part in ['Yes', 'No']:
                    status_position = i
                    break
            
            if status_position == -1:
                status_position = len(parts) - 8
            
            start_pos = status_position + 1
            
            # Buscar fecha de conteo
            counted_date = None
            if start_pos < len(parts) and re.match(r'\d{1,2}/\d{1,2}/\d{4}', parts[start_pos]):
                counted_date = self._parse_date(parts[start_pos])
                start_pos += 1
            
            # Extraer números de tablillas (hasta encontrar los totales)
            tablet_numbers = []
            open_tablet_codes = []
            
            # Buscar números de tablillas (secuencia de números con comas)
            i = start_pos
            while i < len(parts) - 4:  # Dejar espacio para los totales al final
                part = parts[i]
                
                # Números de tablillas: dígitos con comas opcionales
                if re.match(r'^\d+,?$', part):
                    clean_number = re.sub(r'[^\d]', '', part)
                    if len(clean_number) >= 2:
                        tablet_numbers.append(clean_number)
                
                # Códigos de tablillas abiertas: números con letras
                elif re.match(r'^\d+[A-Z]+,?$', part):
                    clean_code = part.replace(',', '')
                    if clean_code not in ['61D', '612d', '61d', 'FL']:
                        open_tablet_codes.append(clean_code)
                
                i += 1
            
            # Extraer totales (últimos 4 números)
            totals = []
            for part in parts[-4:]:
                if re.match(r'^\d+$', part):
                    totals.append(int(part))
            
            return {
                'Tablets': ', '.join(tablet_numbers),
                'Total_Tablets': totals[0] if len(totals) >= 1 else 0,
                'Open_Tablets': ', '.join(open_tablet_codes),
                'Total_Open': totals[1] if len(totals) >= 2 else 0,
                'Counting_Delay': totals[2] if len(totals) >= 3 else 0,
                'Validation_Delay': totals[3] if len(totals) >= 4 else 0,
                'Counted_Date': counted_date
            }
            
        except Exception as e:
            if self.debug_mode:
                st.write(f"⚠️ Error extrayendo tablillas: {str(e)}")
            return {
                'Tablets': '',
                'Total_Tablets': 0,
                'Open_Tablets': '',
                'Total_Open': 0,
                'Counting_Delay': 0,
                'Validation_Delay': 0,
                'Counted_Date': None
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
FL 612d 729000018710 9/8/2025 40036567 FL052 8/31/2025 9/30/2025 Phorcys Builders Corp The Villages at East Ocea Yes 9/12/2025 1323 1 0 4 3"""
    
    result = parser.parse_pdf_content(sample_data)
    
    if result is not None:
        print("✅ Parser funcionando correctamente")
        print(f"Registros extraídos: {len(result)}")
        print("\nPrimer registro:")
        print(result.iloc[0].to_dict())
    else:
        print("❌ Error en el parser")

if __name__ == "__main__":
    test_parser()