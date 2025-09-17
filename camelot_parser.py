"""
Parser robusto usando Camelot-py para extraer tablas de PDFs de Alsina Forms
"""

import camelot
import pandas as pd
import streamlit as st
import numpy as np
from typing import List, Dict, Optional
import re
from datetime import datetime
import tempfile
import os

class CamelotAlsinaParser:
    """Parser usando Camelot-py para extraer tablas de PDFs complejos"""
    
    def __init__(self):
        self.debug_mode = True
        
    def parse_pdf_file(self, pdf_file) -> Optional[pd.DataFrame]:
        """Parsear PDF usando Camelot-py"""
        
        st.info("🐪 **Parser Camelot Activo** - Usando la biblioteca más robusta para extracción de tablas")
        
        try:
            # Guardar archivo temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                # Intentar extraer tablas con Camelot
                st.write("🔍 Extrayendo tablas con Camelot...")
                
                # Probar diferentes métodos de Camelot
                tables = self._extract_tables_camelot(tmp_path)
                
                if tables:
                    st.success(f"✅ Camelot encontró {len(tables)} tablas")
                    
                    # Procesar y combinar todas las tablas
                    combined_df = self._process_camelot_tables(tables)
                    
                    if combined_df is not None and not combined_df.empty:
                        st.success(f"✅ Datos procesados exitosamente: {len(combined_df)} registros")
                        return combined_df
                    else:
                        st.warning("⚠️ No se pudieron procesar las tablas extraídas")
                        return None
                else:
                    st.error("❌ Camelot no pudo extraer tablas del PDF")
                    return None
                    
            finally:
                # Limpiar archivo temporal
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            st.error(f"Error procesando PDF con Camelot: {str(e)}")
            return None
    
    def _extract_tables_camelot(self, pdf_path: str) -> List:
        """Extraer tablas usando diferentes métodos de Camelot"""
        
        tables = []
        
        # Método 1: Lattice (para tablas con bordes)
        try:
            st.write("🔍 Intentando método Lattice...")
            lattice_tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')
            if lattice_tables:
                st.write(f"📊 Lattice encontró {len(lattice_tables)} tablas")
                tables.extend(lattice_tables)
        except Exception as e:
            if self.debug_mode:
                st.write(f"⚠️ Lattice falló: {str(e)}")
        
        # Método 2: Stream (para tablas sin bordes claros)
        try:
            st.write("🔍 Intentando método Stream...")
            stream_tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
            if stream_tables:
                st.write(f"📊 Stream encontró {len(stream_tables)} tablas")
                # Solo agregar si no tenemos tablas de Lattice
                if not tables:
                    tables.extend(stream_tables)
        except Exception as e:
            if self.debug_mode:
                st.write(f"⚠️ Stream falló: {str(e)}")
        
        # Método 3: Lattice con parámetros específicos
        if not tables:
            try:
                st.write("🔍 Intentando Lattice con parámetros específicos...")
                lattice_tables = camelot.read_pdf(
                    pdf_path, 
                    pages='all', 
                    flavor='lattice',
                    line_scale=40,
                    copy_text=['v']
                )
                if lattice_tables:
                    st.write(f"📊 Lattice específico encontró {len(lattice_tables)} tablas")
                    tables.extend(lattice_tables)
            except Exception as e:
                if self.debug_mode:
                    st.write(f"⚠️ Lattice específico falló: {str(e)}")
        
        return tables
    
    def _process_camelot_tables(self, tables: List) -> Optional[pd.DataFrame]:
        """Procesar tablas extraídas por Camelot"""
        
        all_data = []
        
        for i, table in enumerate(tables):
            if self.debug_mode:
                st.write(f"📋 Procesando tabla {i+1}...")
            
            # Obtener DataFrame de la tabla
            df = table.df
            
            if self.debug_mode:
                st.write(f"📊 Tabla {i+1}: {len(df)} filas, {len(df.columns)} columnas")
                st.write("Primeras filas:")
                st.dataframe(df.head())
            
            # Procesar la tabla
            processed_data = self._process_table_dataframe(df, i+1)
            
            if processed_data:
                all_data.extend(processed_data)
        
        if all_data:
            return pd.DataFrame(all_data)
        else:
            return None
    
    def _process_table_dataframe(self, df: pd.DataFrame, table_num: int) -> List[Dict]:
        """Procesar un DataFrame de tabla específica"""
        
        processed_data = []
        
        # Buscar la fila de headers
        header_row_idx = self._find_header_row(df)
        
        if header_row_idx == -1:
            if self.debug_mode:
                st.write(f"⚠️ No se encontró header en tabla {table_num}")
            return []
        
        if self.debug_mode:
            st.write(f"📋 Header encontrado en fila {header_row_idx}")
        
        # Procesar headers
        headers = self._process_headers(df, header_row_idx)
        
        if self.debug_mode:
            st.write(f"📋 Headers procesados: {headers}")
        
        # Procesar filas de datos
        for i in range(header_row_idx + 1, len(df)):
            row_data = self._process_data_row(df.iloc[i], headers, i)
            if row_data:
                processed_data.append(row_data)
        
        return processed_data
    
    def _find_header_row(self, df: pd.DataFrame) -> int:
        """Encontrar la fila que contiene los headers"""
        
        for i, row in df.iterrows():
            row_text = ' '.join([str(cell) for cell in row if pd.notna(cell)]).lower()
            
            # Buscar indicadores de header
            header_indicators = [
                'wh', 'return', 'packing', 'slip', 'date', 'jobsite', 
                'cost', 'center', 'invoice', 'customer', 'name', 'definitive',
                'counted', 'tablets', 'total', 'delay', 'validation'
            ]
            
            matches = sum(1 for indicator in header_indicators if indicator in row_text)
            
            if matches >= 3:  # Al menos 3 indicadores
                return i
        
        return -1
    
    def _process_headers(self, df: pd.DataFrame, header_row_idx: int) -> List[str]:
        """Procesar headers de la tabla"""
        
        header_row = df.iloc[header_row_idx]
        headers = []
        
        for col_idx, cell in enumerate(header_row):
            if pd.notna(cell) and str(cell).strip():
                # Normalizar header
                clean_header = self._normalize_header(str(cell).strip())
                headers.append(clean_header)
            else:
                headers.append(f"Column_{col_idx}")
        
        return headers
    
    def _normalize_header(self, header: str) -> str:
        """Normalizar nombres de headers"""
        
        header = header.lower().strip()
        
        # Mapeo de headers
        header_mapping = {
            'wh': 'WH',
            'return packing slip': 'Return_Packing_Slip',
            'return p.slip date': 'Return_Date',
            'jobsite': 'Jobsite_ID',
            'cost center': 'Cost_Center',
            'next invoice date': 'Invoice_Date',
            'customer name': 'Customer_Name',
            'job site name': 'Job_Site_Name',
            'definitive': 'Definitive_Dev',
            'definiti ve de v': 'Definitive_Dev',
            'counted date': 'Counted_Date',
            'tablets': 'Tablets',
            'total open tablets': 'Open_Tablets_Info',
            'total countin g delay': 'Counting_Delay',
            'validatio n delay': 'Validation_Delay'
        }
        
        # Buscar coincidencia
        for key, value in header_mapping.items():
            if key in header:
                return value
        
        # Si no encuentra, limpiar y usar
        return header.replace(' ', '_').replace('.', '').replace(',', '')
    
    def _process_data_row(self, row: pd.Series, headers: List[str], row_idx: int) -> Optional[Dict]:
        """Procesar una fila de datos"""
        
        # Verificar si es una fila de datos válida
        if not self._is_valid_data_row(row):
            return None
        
        row_data = {}
        
        # Mapear datos a headers
        for col_idx, (header, value) in enumerate(zip(headers, row)):
            if pd.notna(value) and str(value).strip():
                processed_value = self._process_field_value(header, str(value).strip())
                row_data[header] = processed_value
        
        # Validar que tenga campos mínimos
        required_fields = ['WH', 'Return_Packing_Slip', 'Customer_Name']
        if not all(field in row_data for field in required_fields):
            return None
        
        return row_data
    
    def _is_valid_data_row(self, row: pd.Series) -> bool:
        """Verificar si una fila contiene datos válidos"""
        
        row_text = ' '.join([str(cell) for cell in row if pd.notna(cell)])
        
        # Debe empezar con 'FL'
        if not row_text.strip().startswith('FL'):
            return False
        
        # Debe tener al menos un número de packing slip
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
        
        # Tablillas
        if 'tablets' in header.lower() and ',' in value:
            return value
        
        # Valores de sí/no
        if 'definitive' in header.lower():
            return 'Yes' if value.lower() in ['yes', 'yes s', 's'] else 'No'
        
        return value
    
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
def test_camelot_parser():
    """Probar el parser Camelot"""
    parser = CamelotAlsinaParser()
    
    print("✅ Parser Camelot creado exitosamente")
    print("🐪 Listo para procesar PDFs con Camelot-py")

if __name__ == "__main__":
    test_camelot_parser()