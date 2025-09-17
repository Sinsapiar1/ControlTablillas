"""
Parser simple y rápido usando solo pdfplumber (ya instalado)
"""

import pdfplumber
import pandas as pd
import streamlit as st
import re
from typing import List, Dict, Optional
from datetime import datetime

class SimpleAlsinaParser:
    """Parser simple usando solo pdfplumber"""
    
    def __init__(self):
        self.debug_mode = True
        
    def parse_pdf_file(self, pdf_file) -> Optional[pd.DataFrame]:
        """Parsear PDF usando pdfplumber de forma simple"""
        
        st.info("⚡ **Parser Simple Activo** - Extracción rápida y confiable")
        
        try:
            # Leer PDF con pdfplumber
            with pdfplumber.open(pdf_file) as pdf:
                all_text = ""
                
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        all_text += page_text + "\n"
                
                if self.debug_mode:
                    st.write(f"📄 PDF leído: {len(pdf.pages)} páginas, {len(all_text)} caracteres")
                
                # Procesar texto
                return self._parse_text(all_text)
                
        except Exception as e:
            st.error(f"Error procesando PDF: {str(e)}")
            return None
    
    def _parse_text(self, text: str) -> Optional[pd.DataFrame]:
        """Parsear texto del PDF"""
        
        lines = text.split('\n')
        data_lines = []
        
        # Buscar líneas que empiecen con 'FL'
        for line in lines:
            line = line.strip()
            if line.startswith('FL') and len(line.split()) >= 8:
                data_lines.append(line)
        
        if self.debug_mode:
            st.write(f"📋 Encontradas {len(data_lines)} líneas de datos")
        
        if not data_lines:
            st.warning("⚠️ No se encontraron líneas de datos que empiecen con 'FL'")
            return None
        
        # Procesar cada línea
        parsed_data = []
        for i, line in enumerate(data_lines):
            row_data = self._parse_line(line, i + 1)
            if row_data:
                parsed_data.append(row_data)
        
        if parsed_data:
            df = pd.DataFrame(parsed_data)
            st.success(f"✅ Datos extraídos: {len(df)} registros")
            return df
        else:
            st.error("❌ No se pudieron extraer datos válidos")
            return None
    
    def _parse_line(self, line: str, line_num: int) -> Optional[Dict]:
        """Parsear una línea de datos"""
        
        try:
            # Patrón simple para extraer datos básicos
            # FL WH_CODE PACKING_SLIP DATE1 NUM1 TEXT1 DATE2 DATE3 CUSTOMER_NAME YES/NO DATE4 TABLILLAS NUM2 NUM3 NUM4 NUM5
            
            parts = line.split()
            
            if len(parts) < 10:
                return None
            
            # Extraer campos básicos
            wh_code = parts[1] if len(parts) > 1 else ""
            packing_slip = parts[2] if len(parts) > 2 else ""
            
            # Buscar fechas (formato MM/DD/YYYY)
            dates = []
            for part in parts:
                if re.match(r'\d{1,2}/\d{1,2}/\d{4}', part):
                    dates.append(part)
            
            return_date = dates[0] if len(dates) > 0 else None
            invoice_date = dates[1] if len(dates) > 1 else None
            counted_date = dates[2] if len(dates) > 2 else None
            
            # Buscar nombre del cliente (después de las fechas)
            customer_start = -1
            for i, part in enumerate(parts):
                if re.match(r'\d{1,2}/\d{1,2}/\d{4}', part):
                    customer_start = i + 1
                    break
            
            if customer_start != -1 and customer_start < len(parts):
                # Buscar hasta encontrar Yes/No
                customer_parts = []
                for i in range(customer_start, len(parts)):
                    if parts[i] in ['Yes', 'No', 'Ye', 's']:
                        break
                    customer_parts.append(parts[i])
                
                customer_name = ' '.join(customer_parts) if customer_parts else ""
            else:
                customer_name = ""
            
            # Buscar Yes/No
            definitive_dev = "No"
            for part in parts:
                if part in ['Yes', 'Ye']:
                    definitive_dev = "Yes"
                    break
                elif part == 's' and 'Ye' in line:
                    definitive_dev = "Yes"
                    break
            
            # Buscar números al final (tablillas)
            numbers = []
            for part in parts:
                if part.isdigit():
                    numbers.append(int(part))
            
            total_tablets = numbers[-4] if len(numbers) >= 4 else 0
            open_tablets = numbers[-3] if len(numbers) >= 3 else 0
            counting_delay = numbers[-2] if len(numbers) >= 2 else 0
            validation_delay = numbers[-1] if len(numbers) >= 1 else 0
            
            return {
                'WH_Code': wh_code,
                'Return_Packing_Slip': packing_slip,
                'Return_Date': self._parse_date(return_date),
                'Invoice_Date': self._parse_date(invoice_date),
                'Customer_Name': customer_name,
                'Job_Site_Name': customer_name,  # Usar el mismo nombre por ahora
                'Definitive_Dev': definitive_dev,
                'Counted_Date': self._parse_date(counted_date),
                'Tablets': f"{total_tablets},{open_tablets}",
                'Total_Tablets': total_tablets,
                'Open_Tablets': open_tablets,
                'Total_Open': open_tablets,
                'Counting_Delay': counting_delay,
                'Validation_Delay': validation_delay
            }
            
        except Exception as e:
            if self.debug_mode:
                st.write(f"⚠️ Error en línea {line_num}: {str(e)}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[pd.Timestamp]:
        """Parsear fecha de forma segura"""
        if not date_str:
            return None
        
        try:
            return pd.to_datetime(date_str, format='%m/%d/%Y')
        except:
            return None

# Función de prueba
def test_simple_parser():
    """Probar el parser simple"""
    parser = SimpleAlsinaParser()
    print("✅ Parser Simple creado exitosamente")
    print("⚡ Listo para procesar PDFs de forma rápida")

if __name__ == "__main__":
    test_simple_parser()