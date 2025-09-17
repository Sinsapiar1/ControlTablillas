"""
Parser Ultra-Preciso para el Formato Exacto de Alsina Forms
Basado en el análisis detallado del PDF real vs Excel
"""

import re
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import streamlit as st
import pdfplumber

class UltraPreciseAlsinaParser:
    """Parser ultra-preciso para el formato exacto de Alsina Forms"""
    
    def __init__(self):
        self.debug_mode = True
        
    def parse_pdf_file(self, pdf_file) -> Optional[pd.DataFrame]:
        """Parsear PDF con precisión absoluta"""
        
        st.info("🎯 **Parser Ultra-Preciso Activo** - Diseñado específicamente para el formato exacto de Alsina")
        
        try:
            with pdfplumber.open(pdf_file) as pdf:
                all_data = []
                
                for page_num, page in enumerate(pdf.pages):
                    if self.debug_mode:
                        st.write(f"🔍 Procesando página {page_num + 1}...")
                    
                    text = page.extract_text()
                    if text:
                        page_data = self._parse_page_text(text, page_num)
                        if page_data:
                            all_data.extend(page_data)
                
                if all_data:
                    df = pd.DataFrame(all_data)
                    if self.debug_mode:
                        st.write(f"✅ Total de registros extraídos: {len(df)}")
                    return df
                else:
                    st.error("❌ No se encontraron datos válidos")
                    return None
                    
        except Exception as e:
            st.error(f"Error procesando PDF: {str(e)}")
            return None
    
    def _parse_page_text(self, text: str, page_num: int) -> List[Dict]:
        """Parsear texto de página con precisión absoluta"""
        
        lines = text.split('\n')
        data_lines = []
        
        # Procesar líneas para manejar "Ye s" dividido
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('FL') and len(line.split()) >= 10:
                # Verificar si la siguiente línea contiene solo "s" (parte de "Ye s")
                if (i + 1 < len(lines) and 
                    lines[i + 1].strip() == 's' and 
                    'Ye' in line):
                    # Combinar la línea con el "s" de la siguiente línea
                    combined_line = line + ' s'
                    data_lines.append(combined_line)
                    i += 2  # Saltar la línea del "s"
                else:
                    data_lines.append(line)
                    i += 1
            else:
                i += 1
        
        if self.debug_mode:
            st.write(f"📋 Página {page_num + 1}: Encontradas {len(data_lines)} líneas de datos")
        
        # Procesar cada línea de datos
        parsed_data = []
        for i, line in enumerate(data_lines):
            row_data = self._parse_ultra_precise_line(line, i + 1)
            if row_data:
                parsed_data.append(row_data)
                if self.debug_mode and len(parsed_data) <= 3:
                    st.write(f"✅ Línea {i+1}: {row_data['Customer_Name']} - {row_data['Job_Site_Name']}")
        
        return parsed_data
    
    def _parse_ultra_precise_line(self, line: str, line_num: int) -> Optional[Dict]:
        """Parsear línea con precisión absoluta basada en el formato exacto"""
        
        if self.debug_mode:
            st.write(f"🔍 **Analizando línea {line_num}:** `{line[:100]}...`")
        
        try:
            # Patrón ultra-específico basado en el formato exacto observado
            # FL 61D 729000018669 9/2/2025 40037739 FL053 8/31/2025 9/30/2025 3c Construction Corp     Biscayne Bay Coastal Wetl No 81, 134, 1666, 1708 4 1666M, 1708M 2 15 0
            
            # Usar regex más específico que maneja el espaciado exacto
            pattern = r'FL\s+(\w+)\s+(\d{12})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d+)\s+(\w+)\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)(?:\s+(No|Yes|Ye\s+s))(?:\s+(\d{1,2}/\d{1,2}/\d{4}))?(?:\s+(.+?))?(?:\s+(\d+))?(?:\s+(\d+))?(?:\s+(\d+))?(?:\s+(\d+))?$'
            
            match = re.search(pattern, line)
            
            if not match:
                if self.debug_mode:
                    st.write(f"⚠️ Línea {line_num}: No coincide con el patrón principal")
                # Intentar con patrón más flexible
                return self._parse_flexible_line(line, line_num)
            
            groups = match.groups()
            
            # Extraer campos básicos
            wh_code = groups[0]
            return_slip = groups[1]
            return_date = self._parse_date(groups[2])
            jobsite_id = groups[3]
            cost_center = groups[4]
            invoice_start = self._parse_date(groups[5])
            invoice_end = self._parse_date(groups[6])
            
            # Extraer nombres con precisión absoluta
            names_text = groups[7]
            customer_name, job_site_name = self._split_names_ultra_precise(names_text)
            
            # Estado definitivo
            definitive_dev = "Yes" if groups[8] and ("Yes" in groups[8] or "Ye s" in groups[8]) else "No"
            
            # Fecha de conteo
            counted_date = self._parse_date(groups[9]) if groups[9] else None
            
            # Información de tablillas
            tablets_text = groups[10] if groups[10] else ""
            tablets_info = self._extract_tablets_ultra_precise(tablets_text)
            
            # Totales
            total_tablets = self._parse_number(groups[11]) if groups[11] else 0
            total_open = self._parse_number(groups[12]) if groups[12] else 0
            counting_delay = self._parse_number(groups[13]) if groups[13] else 0
            validation_delay = self._parse_number(groups[14]) if groups[14] else 0
            
            result = {
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
            
            if self.debug_mode:
                st.write(f"✅ **Línea {line_num} parseada correctamente:** {customer_name} - {job_site_name}")
            
            return result
            
        except Exception as e:
            if self.debug_mode:
                st.write(f"❌ Error en línea {line_num}: {str(e)}")
            return None
    
    def _parse_flexible_line(self, line: str, line_num: int) -> Optional[Dict]:
        """Parser flexible para líneas que no coinciden con el patrón principal"""
        
        if self.debug_mode:
            st.write(f"🔄 Intentando parsing flexible para línea {line_num}")
        
        try:
            # Dividir por espacios pero preservar fechas
            parts = self._smart_split_preserving_dates(line)
            
            if len(parts) < 15:
                if self.debug_mode:
                    st.write(f"⚠️ Línea {line_num}: Muy pocas partes ({len(parts)})")
                return None
            
            # Extraer campos por posición
            wh_code = parts[1] if len(parts) > 1 else ""
            return_slip = parts[2] if len(parts) > 2 else ""
            return_date = self._parse_date(parts[3]) if len(parts) > 3 else None
            jobsite_id = parts[4] if len(parts) > 4 else ""
            cost_center = parts[5] if len(parts) > 5 else ""
            invoice_start = self._parse_date(parts[6]) if len(parts) > 6 else None
            invoice_end = self._parse_date(parts[7]) if len(parts) > 7 else None
            
            # Encontrar posición de Yes/No
            status_pos = -1
            definitive_dev = "No"
            
            for i, part in enumerate(parts[8:], 8):
                if part in ['Yes', 'No']:
                    definitive_dev = part
                    status_pos = i
                    break
                elif part == 'Ye' and i + 1 < len(parts) and parts[i + 1] == 's':
                    definitive_dev = "Yes"
                    status_pos = i
                    break
            
            if status_pos == -1:
                status_pos = len(parts) - 6
            
            # Extraer nombres
            names_parts = parts[8:status_pos]
            customer_name, job_site_name = self._split_names_from_parts(names_parts)
            
            # Fecha de conteo
            counted_date = None
            if status_pos + 1 < len(parts):
                potential_date = parts[status_pos + 1]
                if re.match(r'\d{1,2}/\d{1,2}/\d{4}', potential_date):
                    counted_date = self._parse_date(potential_date)
            
            # Extraer tablillas
            tablets_start = status_pos + (2 if counted_date else 1)
            tablets_info = self._extract_tablets_from_parts(parts, tablets_start)
            
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
                'Total_Tablets': tablets_info['total_tablets'],
                'Open_Tablets': tablets_info['open_tablets'],
                'Total_Open': tablets_info['total_open'],
                'Counting_Delay': tablets_info['counting_delay'],
                'Validation_Delay': tablets_info['validation_delay']
            }
            
        except Exception as e:
            if self.debug_mode:
                st.write(f"❌ Error en parsing flexible línea {line_num}: {str(e)}")
            return None
    
    def _smart_split_preserving_dates(self, line: str) -> List[str]:
        """Dividir línea preservando fechas"""
        # Encontrar fechas
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
    
    def _split_names_ultra_precise(self, names_text: str) -> Tuple[str, str]:
        """Dividir nombres con precisión absoluta basada en el formato exacto"""
        
        if not names_text:
            return "Unknown Customer", "Unknown Site"
        
        # Patrones específicos basados en los ejemplos reales del PDF
        # "3c Construction Corp     Biscayne Bay Coastal Wetl" (5 espacios)
        # "Caribbean Building Corp  Modena 22" (2 espacios)
        # "Thales Builders Corp     4580 North Bay Road Resid" (5 espacios)
        
        # Buscar múltiples espacios como separador principal
        if '     ' in names_text:  # 5 espacios
            parts = names_text.split('     ', 1)
            return parts[0].strip(), parts[1].strip()
        elif '    ' in names_text:  # 4 espacios
            parts = names_text.split('    ', 1)
            return parts[0].strip(), parts[1].strip()
        elif '   ' in names_text:  # 3 espacios
            parts = names_text.split('   ', 1)
            return parts[0].strip(), parts[1].strip()
        elif '  ' in names_text:  # 2 espacios
            parts = names_text.split('  ', 1)
            return parts[0].strip(), parts[1].strip()
        
        # Fallback: buscar marcadores de empresa
        company_endings = ['corp', 'llc', 'inc', 'ltd', 'construction', 'builders', 'services', 'group', 'corporation']
        
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
    
    def _split_names_from_parts(self, names_parts: List[str]) -> Tuple[str, str]:
        """Dividir nombres desde una lista de partes"""
        
        if not names_parts:
            return "Unknown Customer", "Unknown Site"
        
        # Buscar marcadores de empresa
        company_endings = ['corp', 'llc', 'inc', 'ltd', 'construction', 'builders', 'services', 'group', 'corporation']
        
        split_point = len(names_parts) // 2
        
        for i, part in enumerate(names_parts):
            if part.lower() in company_endings:
                split_point = i + 1
                break
        
        customer_parts = names_parts[:split_point]
        site_parts = names_parts[split_point:]
        
        customer_name = ' '.join(customer_parts) if customer_parts else "Unknown Customer"
        job_site_name = ' '.join(site_parts) if site_parts else "Unknown Site"
        
        return customer_name.strip(), job_site_name.strip()
    
    def _extract_tablets_ultra_precise(self, tablets_text: str) -> Dict:
        """Extraer tablillas con precisión absoluta"""
        
        tablets = []
        open_tablets = []
        
        if not tablets_text:
            return {'tablets': '', 'open_tablets': ''}
        
        # Buscar números de tablillas (secuencia de números con comas)
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
    
    def _extract_tablets_from_parts(self, parts: List[str], start_pos: int) -> Dict:
        """Extraer tablillas desde una lista de partes"""
        
        tablets = []
        open_tablets = []
        
        # Buscar números de tablillas hasta encontrar los totales
        i = start_pos
        while i < len(parts) - 4:  # Dejar espacio para los totales
            part = parts[i]
            
            # Números de tablillas
            if re.match(r'^\d{1,4},?$', part):
                clean_number = re.sub(r'[^\d]', '', part)
                if len(clean_number) >= 1:
                    tablets.append(clean_number)
            
            # Códigos de tablillas abiertas
            elif re.match(r'^\d{1,4}[A-Z]+,?$', part):
                clean_code = part.replace(',', '')
                open_tablets.append(clean_code)
            
            i += 1
        
        # Extraer totales (últimos 4 números)
        totals = []
        for part in parts[-4:]:
            if re.match(r'^\d+$', part):
                totals.append(int(part))
        
        return {
            'tablets': ', '.join(tablets),
            'total_tablets': totals[0] if len(totals) >= 1 else 0,
            'open_tablets': ', '.join(open_tablets),
            'total_open': totals[1] if len(totals) >= 2 else 0,
            'counting_delay': totals[2] if len(totals) >= 3 else 0,
            'validation_delay': totals[3] if len(totals) >= 4 else 0
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

# Función de prueba
def test_ultra_precise_parser():
    """Probar el parser ultra-preciso"""
    parser = UltraPreciseAlsinaParser()
    
    # Datos de ejemplo del formato real
    sample_data = """FL 61D 729000018669 9/2/2025 40037739 FL053 8/31/2025 9/30/2025 3c Construction Corp     Biscayne Bay Coastal Wetl No 81, 134, 1666, 1708 4 1666M, 1708M 2 15 0
FL 612d 729000018670 9/2/2025 40036511 FL013 8/31/2025 9/30/2025 Caribbean Building Corp  Modena 22                No 230, 259, 263, 278 4 230M, 278A 2 15 0
FL 612d 729000018671 9/2/2025 40030876 FL052 8/31/2025 9/30/2025 Thales Builders Corp     4580 North Bay Road Resid Ye
s
9/16/2025 280, 1486, 1487 3 0 14 1"""
    
    result = parser._parse_page_text(sample_data, 0)
    
    if result:
        print("✅ Parser ultra-preciso funcionando")
        print(f"Registros extraídos: {len(result)}")
        for i, record in enumerate(result):
            print(f"\n=== REGISTRO {i+1} ===")
            print(f"Cliente: {record['Customer_Name']}")
            print(f"Sitio: {record['Job_Site_Name']}")
            print(f"Tablillas: {record['Tablets']}")
            print(f"Tablillas Abiertas: {record['Open_Tablets']}")
            print(f"Definitivo: {record['Definitive_Dev']}")
            print(f"Fecha Conteo: {record['Counted_Date']}")
    else:
        print("❌ Error en el parser ultra-preciso")

if __name__ == "__main__":
    test_ultra_precise_parser()