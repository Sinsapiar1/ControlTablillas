import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime, timedelta
import re
import tempfile
import os
import subprocess
import sys
from typing import Optional, List, Dict

# Intentar importar Camelot con instalación automática
CAMELOT_AVAILABLE = False
CAMELOT_INSTALLING = False

def install_camelot():
    """Instalar Camelot automáticamente"""
    global CAMELOT_INSTALLING
    CAMELOT_INSTALLING = True
    
    try:
        st.info("🔄 Instalando Camelot-py... Esto puede tomar unos minutos.")
        
        # Instalar camelot-py
        subprocess.check_call([sys.executable, "-m", "pip", "install", "camelot-py[cv]"])
        
        # Instalar opencv-python
        subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python"])
        
        st.success("✅ Camelot instalado exitosamente!")
        return True
        
    except Exception as e:
        st.error(f"❌ Error instalando Camelot: {str(e)}")
        return False
    finally:
        CAMELOT_INSTALLING = False

# Intentar importar Camelot
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False

# Importar pdfplumber como respaldo
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# Configuración de página
st.set_page_config(
    page_title="Control de Tablillas - Alsina Forms",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
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
    .success-box { background: #d4edda; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
    .error-box { background: #f8d7da; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
    .warning-box { background: #fff3cd; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
    .info-box { background: #d1ecf1; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
    .install-box { background: #e2e3e5; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

class TablillasExtractor:
    """Extractor especializado para PDFs de Alsina Forms usando Camelot"""
    
    def __init__(self):
        self.expected_columns = [
            'WH', 'WH_Code', 'Return_Packing_Slip', 'Return_Date', 'Jobsite_ID',
            'Cost_Center', 'Invoice_Start_Date', 'Invoice_End_Date', 
            'Customer_Name', 'Job_Site_Name', 'Definitive_Dev', 'Counted_Date',
            'Tablets', 'Total_Tablets', 'Open_Tablets', 'Total_Open',
            'Counting_Delay', 'Validation_Delay'
        ]
    
    def extract_from_pdf(self, uploaded_file) -> Optional[pd.DataFrame]:
        """Extrae datos usando Camelot (preferido) o pdfplumber (respaldo)"""
        
        if CAMELOT_AVAILABLE:
            st.info("🐪 Usando Camelot-py para extracción de tablas...")
            return self._extract_with_camelot(uploaded_file)
        elif PDFPLUMBER_AVAILABLE:
            st.warning("📄 Camelot no disponible. Usando pdfplumber como respaldo...")
            return self._extract_with_pdfplumber(uploaded_file)
        else:
            st.error("❌ No hay bibliotecas de PDF disponibles")
            return None
    
    def _extract_with_camelot(self, uploaded_file) -> Optional[pd.DataFrame]:
        """Extrae datos usando Camelot (LA MEJOR OPCIÓN)"""
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name
            
            # Extraer tablas con Camelot
            st.info("🔄 Extrayendo tablas con Camelot...")
            
            # Probar diferentes configuraciones
            tables = None
            
            # Configuración 1: Stream (para tablas sin bordes)
            try:
                st.write("🔍 Probando método Stream...")
                tables = camelot.read_pdf(tmp_file_path, pages='all', flavor='stream')
                st.write(f"📊 Método Stream: {len(tables)} tablas encontradas")
            except Exception as e:
                st.write(f"⚠️ Stream falló: {str(e)}")
            
            # Configuración 2: Lattice (para tablas con bordes) si Stream falla
            if not tables or len(tables) == 0:
                try:
                    st.write("🔍 Probando método Lattice...")
                    tables = camelot.read_pdf(tmp_file_path, pages='all', flavor='lattice')
                    st.write(f"📊 Método Lattice: {len(tables)} tablas encontradas")
                except Exception as e:
                    st.write(f"⚠️ Lattice falló: {str(e)}")
            
            # Configuración 3: Lattice con parámetros específicos
            if not tables or len(tables) == 0:
                try:
                    st.write("🔍 Probando Lattice con parámetros específicos...")
                    tables = camelot.read_pdf(
                        tmp_file_path, 
                        pages='all', 
                        flavor='lattice',
                        line_scale=40,
                        copy_text=['v']
                    )
                    st.write(f"📊 Lattice específico: {len(tables)} tablas encontradas")
                except Exception as e:
                    st.write(f"⚠️ Lattice específico falló: {str(e)}")
            
            # Limpiar archivo temporal
            os.unlink(tmp_file_path)
            
            if not tables or len(tables) == 0:
                st.error("❌ No se encontraron tablas en el PDF")
                return None
            
            # Procesar tablas encontradas
            return self._process_tables(tables)
            
        except Exception as e:
            st.error(f"❌ Error procesando PDF con Camelot: {str(e)}")
            return None
    
    def _extract_with_pdfplumber(self, uploaded_file) -> Optional[pd.DataFrame]:
        """Extrae datos usando pdfplumber como respaldo"""
        try:
            st.info("📄 Extrayendo texto con pdfplumber...")
            
            # Leer PDF con pdfplumber
            with pdfplumber.open(uploaded_file) as pdf:
                all_text = ""
                
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        all_text += page_text + "\n"
                
                st.write(f"📄 PDF leído: {len(pdf.pages)} páginas, {len(all_text)} caracteres")
            
            # Procesar texto para encontrar líneas FL
            return self._process_text_lines(all_text)
            
        except Exception as e:
            st.error(f"❌ Error procesando PDF con pdfplumber: {str(e)}")
            return None
    
    def _process_text_lines(self, text: str) -> Optional[pd.DataFrame]:
        """Procesa líneas de texto para extraer datos FL"""
        lines = text.split('\n')
        fl_lines = []
        
        # Buscar líneas que empiecen con FL
        for line in lines:
            line = line.strip()
            if line.startswith('FL') and len(line.split()) >= 8:
                fl_lines.append(line)
        
        st.write(f"📋 Encontradas {len(fl_lines)} líneas FL")
        
        if not fl_lines:
            st.error("❌ No se encontraron líneas FL en el PDF")
            return None
        
        # Procesar cada línea FL
        processed_data = []
        for i, line in enumerate(fl_lines):
            row_data = self._parse_fl_line(line, i + 1)
            if row_data:
                processed_data.append(row_data)
        
        if processed_data:
            df = pd.DataFrame(processed_data)
            return self._clean_and_standardize(df)
        else:
            st.error("❌ No se pudieron procesar las líneas FL")
            return None
    
    def _parse_fl_line(self, line: str, line_num: int) -> Optional[Dict]:
        """Parsea una línea FL individual"""
        try:
            parts = line.split()
            
            if len(parts) < 8:
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
            
            # Buscar nombre del cliente
            customer_start = -1
            for i, part in enumerate(parts):
                if re.match(r'\d{1,2}/\d{1,2}/\d{4}', part):
                    customer_start = i + 1
                    break
            
            customer_name = ""
            if customer_start != -1 and customer_start < len(parts):
                customer_parts = []
                for i in range(customer_start, len(parts)):
                    if parts[i] in ['Yes', 'No', 'Ye', 's']:
                        break
                    customer_parts.append(parts[i])
                customer_name = ' '.join(customer_parts) if customer_parts else ""
            
            # Buscar Yes/No
            definitive_dev = "No"
            for part in parts:
                if part in ['Yes', 'Ye']:
                    definitive_dev = "Yes"
                    break
                elif part == 's' and 'Ye' in line:
                    definitive_dev = "Yes"
                    break
            
            # Buscar números al final
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
                'Invoice_Start_Date': self._parse_date(invoice_date),
                'Customer_Name': customer_name,
                'Job_Site_Name': customer_name,
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
            st.write(f"⚠️ Error en línea {line_num}: {str(e)}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[pd.Timestamp]:
        """Parsea fecha de forma segura"""
        if not date_str:
            return None
        try:
            return pd.to_datetime(date_str, format='%m/%d/%Y')
        except:
            return None
    
    def _process_tables(self, tables) -> pd.DataFrame:
        """Procesa las tablas extraídas con Camelot"""
        all_data = []
        
        for i, table in enumerate(tables):
            st.write(f"📋 Tabla {i+1}: {table.shape[0]} filas, {table.shape[1]} columnas")
            
            df = table.df
            
            # Mostrar muestra de la primera tabla
            if i == 0:
                st.write("**Muestra de datos extraídos:**")
                st.dataframe(df.head(3), use_container_width=True)
            
            # Filtrar solo filas que empiecen con FL
            fl_rows = df[df.iloc[:, 0].astype(str).str.contains('FL', na=False)]
            
            if len(fl_rows) > 0:
                st.write(f"✅ {len(fl_rows)} filas FL encontradas en tabla {i+1}")
                all_data.append(fl_rows)
        
        if not all_data:
            st.error("❌ No se encontraron filas con datos FL")
            return None
        
        # Combinar todas las tablas
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Limpiar y estandarizar
        return self._clean_and_standardize(combined_df)
    
    def _clean_and_standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y estandariza los datos"""
        try:
            # Eliminar filas completamente vacías
            df = df.dropna(how='all').reset_index(drop=True)
            
            # Asignar nombres de columna estándar
            num_cols = len(df.columns)
            if num_cols >= len(self.expected_columns):
                df.columns = self.expected_columns[:num_cols]
            else:
                column_names = self.expected_columns[:num_cols]
                df.columns = column_names
            
            # Limpiar datos
            df = self._clean_data_types(df)
            
            # Calcular métricas adicionales
            df = self._calculate_metrics(df)
            
            st.success(f"✅ Datos procesados: {len(df)} registros válidos")
            return df
            
        except Exception as e:
            st.error(f"❌ Error limpiando datos: {str(e)}")
            return df
    
    def _clean_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia tipos de datos"""
        # Fechas
        date_columns = ['Return_Date', 'Invoice_Start_Date', 'Invoice_End_Date', 'Counted_Date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Números
        numeric_columns = ['Total_Tablets', 'Total_Open', 'Counting_Delay', 'Validation_Delay']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Limpiar strings
        string_columns = ['Customer_Name', 'Job_Site_Name', 'WH_Code', 'Return_Packing_Slip']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        return df
    
    def _calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula métricas adicionales"""
        try:
            # Días desde retorno
            if 'Return_Date' in df.columns:
                current_date = pd.Timestamp.now()
                df['Days_Since_Return'] = (current_date - df['Return_Date']).dt.days
                df['Days_Since_Return'] = df['Days_Since_Return'].fillna(0)
            
            # Score de prioridad
            df['Priority_Score'] = (
                df.get('Days_Since_Return', 0) * 0.4 +
                df.get('Counting_Delay', 0) * 0.3 +
                df.get('Validation_Delay', 0) * 0.2 +
                df.get('Total_Open', 0) * 0.1
            )
            
            # Nivel de prioridad
            df['Priority_Level'] = pd.cut(
                df['Priority_Score'],
                bins=[0, 15, 25, float('inf')],
                labels=['Baja', 'Media', 'Alta'],
                right=False
            )
            
            return df
            
        except Exception as e:
            st.warning(f"⚠️ Error calculando métricas: {str(e)}")
            return df

def main():
    # Header
    st.markdown('<div class="main-header"><h1>🏗️ Control de Tablillas - Alsina Forms Co.</h1><p>Extracción especializada con Camelot-py (LA MEJOR OPCIÓN) - v2.0</p></div>', 
                unsafe_allow_html=True)
    
    # Mostrar estado de dependencias
    if CAMELOT_AVAILABLE:
        st.markdown("""
        <div class="success-box">
        <h3>🐪 ✅ Camelot-py Disponible</h3>
        <p><strong>¡Perfecto!</strong> Usando la mejor biblioteca para extracción de tablas de PDFs</p>
        </div>
        """, unsafe_allow_html=True)
    elif PDFPLUMBER_AVAILABLE:
        st.markdown("""
        <div class="warning-box">
        <h3>📄 ⚠️ Usando pdfplumber como respaldo</h3>
        <p>Camelot no está disponible. Usando pdfplumber para extracción básica.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Botón para instalar Camelot
        if st.button("🐪 Instalar Camelot-py (Recomendado)", type="primary"):
            if install_camelot():
                st.rerun()
    else:
        st.markdown("""
        <div class="error-box">
        <h3>❌ No hay bibliotecas de PDF disponibles</h3>
        <p>Instala las dependencias necesarias:</p>
        <code>pip install pdfplumber</code><br>
        <code>pip install camelot-py[cv]</code>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    
    # Sidebar
    st.sidebar.header("📂 Cargar PDF")
    
    uploaded_file = st.sidebar.file_uploader(
        "Seleccionar archivo PDF",
        type=['pdf'],
        help="Sube el reporte de Outstanding Count Returns"
    )
    
    if uploaded_file is not None:
        st.markdown('<div class="warning-box">🔄 <strong>Procesando PDF...</strong></div>', 
                    unsafe_allow_html=True)
        
        # Extraer datos
        extractor = TablillasExtractor()
        df = extractor.extract_from_pdf(uploaded_file)
        
        if df is not None and not df.empty:
            st.markdown('<div class="success-box">✅ <strong>Extracción exitosa!</strong></div>', 
                        unsafe_allow_html=True)
            
            # Mostrar dashboard
            show_dashboard(df)
        else:
            st.markdown("""
            <div class="error-box">
            <h3>❌ No se pudieron extraer datos</h3>
            <p>Posibles soluciones:</p>
            <ul>
                <li>Verificar que el PDF contenga tablas o líneas FL</li>
                <li>Asegurar que el archivo no esté protegido</li>
                <li>Comprobar que el formato sea el esperado</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Instrucciones
        st.markdown("""
        ## 📋 Instrucciones de Uso
        
        1. **Subir PDF**: Usar el panel lateral para cargar el archivo
        
        2. **Automático**: Camelot extraerá las tablas automáticamente
        
        3. **Verificar**: Revisar los datos extraídos en el dashboard
        
        4. **Descargar**: Exportar a Excel para análisis adicional
        
        ### 🐪 ¿Por qué Camelot es la Mejor Opción?
        - **Diseñada específicamente** para extraer tablas de PDFs
        - **Detecta automáticamente** la estructura tabular
        - **Maneja correctamente** espacios y separadores
        - **Preserva la alineación** de columnas
        - **Menos errores** que parsing manual
        - **Múltiples métodos** (Stream, Lattice) para diferentes tipos de PDFs
        
        ### 📊 Datos Extraídos
        - Código de almacén (WH_Code)
        - Número de packing slip
        - Fechas de devolución
        - Nombre del cliente
        - Estado definitivo (Yes/No)
        - Números de tablillas
        - Delays de conteo y validación
        """)

def show_dashboard(df: pd.DataFrame):
    """Dashboard principal"""
    st.header("📊 Dashboard - Datos Extraídos")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Albaranes", len(df))
    
    with col2:
        total_open = int(df.get('Total_Open', pd.Series([0])).sum())
        st.metric("Tablillas Pendientes", total_open)
    
    with col3:
        avg_delay = df.get('Counting_Delay', pd.Series([0])).mean()
        st.metric("Retraso Promedio", f"{avg_delay:.1f} días")
    
    with col4:
        warehouses = df.get('WH_Code', pd.Series([''])).nunique()
        st.metric("Almacenes", warehouses)
    
    # Tabla principal
    st.subheader("📋 Datos Detallados")
    
    # Mostrar columnas principales
    main_columns = [
        'Return_Packing_Slip', 'Return_Date', 'Customer_Name', 'Job_Site_Name',
        'Definitive_Dev', 'Counted_Date', 'Tablets', 'Total_Tablets', 
        'Open_Tablets', 'Total_Open', 'Days_Since_Return', 'Priority_Level'
    ]
    
    available_columns = [col for col in main_columns if col in df.columns]
    
    if available_columns:
        st.dataframe(df[available_columns], use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)
    
    # Gráficos si hay datos suficientes
    if len(df) > 0 and 'Priority_Level' in df.columns:
        show_charts(df)
    
    # Descarga
    st.subheader("💾 Exportar Datos")
    if st.button("📥 Descargar Excel", type="primary"):
        download_excel(df)

def show_charts(df: pd.DataFrame):
    """Mostrar gráficos"""
    st.subheader("📈 Visualizaciones")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'WH_Code' in df.columns and 'Priority_Level' in df.columns:
            priority_data = df.groupby(['WH_Code', 'Priority_Level']).size().reset_index(name='count')
            
            if not priority_data.empty:
                fig1 = px.bar(
                    priority_data,
                    x='WH_Code',
                    y='count',
                    color='Priority_Level',
                    color_discrete_map={'Alta': '#dc3545', 'Media': '#fd7e14', 'Baja': '#28a745'},
                    title="Prioridades por Almacén"
                )
                st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        if 'Return_Date' in df.columns:
            timeline = df.groupby('Return_Date').size().reset_index(name='count')
            
            if not timeline.empty:
                fig2 = px.line(
                    timeline,
                    x='Return_Date',
                    y='count',
                    title="Devoluciones por Fecha",
                    markers=True
                )
                st.plotly_chart(fig2, use_container_width=True)

def download_excel(df: pd.DataFrame):
    """Generar y descargar Excel"""
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja principal
            df.to_excel(writer, sheet_name='Datos_Extraidos', index=False)
            
            # Hoja de resumen por almacén
            if 'WH_Code' in df.columns:
                summary = df.groupby('WH_Code').agg({
                    'Total_Open': 'sum',
                    'Total_Tablets': 'sum',
                    'Counting_Delay': 'mean',
                    'Return_Packing_Slip': 'count'
                }).round(2)
                summary.columns = ['Tablillas_Abiertas', 'Total_Tablillas', 'Retraso_Promedio', 'Num_Albaranes']
                summary.to_excel(writer, sheet_name='Resumen_Almacenes')
            
            # Hoja de alta prioridad
            if 'Priority_Level' in df.columns:
                high_priority = df[df['Priority_Level'] == 'Alta']
                if not high_priority.empty:
                    high_priority.to_excel(writer, sheet_name='Alta_Prioridad', index=False)
        
        # Botón de descarga
        current_date = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"tablillas_camelot_{current_date}.xlsx"
        
        st.download_button(
            label="📥 Descargar Excel Completo",
            data=output.getvalue(),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success(f"✅ Excel generado: **{filename}**")
        
    except Exception as e:
        st.error(f"❌ Error generando Excel: {str(e)}")

if __name__ == "__main__":
    main()