import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime, timedelta
import re
import tempfile
import os
from typing import Optional, List, Dict

# Intentar importar Camelot (la mejor para tablas)
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    st.error("⚠️ Camelot no está instalado. Ejecuta: pip install camelot-py[cv]")

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
        """Extrae datos usando Camelot"""
        if not CAMELOT_AVAILABLE:
            st.error("Camelot no disponible. Instala con: pip install camelot-py[cv]")
            return None
        
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
                tables = camelot.read_pdf(tmp_file_path, pages='all', flavor='stream')
                st.write(f"📊 Método Stream: {len(tables)} tablas encontradas")
            except:
                pass
            
            # Configuración 2: Lattice (para tablas con bordes) si Stream falla
            if not tables or len(tables) == 0:
                try:
                    tables = camelot.read_pdf(tmp_file_path, pages='all', flavor='lattice')
                    st.write(f"📊 Método Lattice: {len(tables)} tablas encontradas")
                except:
                    pass
            
            # Limpiar archivo temporal
            os.unlink(tmp_file_path)
            
            if not tables or len(tables) == 0:
                st.error("❌ No se encontraron tablas en el PDF")
                return None
            
            # Procesar tablas encontradas
            return self._process_tables(tables)
            
        except Exception as e:
            st.error(f"❌ Error procesando PDF: {str(e)}")
            return None
    
    def _process_tables(self, tables) -> pd.DataFrame:
        """Procesa las tablas extraídas"""
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
                # Rellenar con nombres genéricos si faltan columnas
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
    st.markdown('<div class="main-header"><h1>🏗️ Control de Tablillas - Alsina Forms Co.</h1><p>Extracción especializada con Camelot-py</p></div>', 
                unsafe_allow_html=True)
    
    # Verificar dependencias
    if not CAMELOT_AVAILABLE:
        st.markdown("""
        <div class="error-box">
        <h3>❌ Camelot no está instalado</h3>
        <p>Para instalar las dependencias necesarias:</p>
        <code>pip install camelot-py[cv]</code><br>
        <code>pip install opencv-python</code>
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
        st.markdown('<div class="warning-box">🔄 <strong>Procesando PDF con Camelot-py...</strong></div>', 
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
                <li>Verificar que el PDF contenga tablas</li>
                <li>Asegurar que el archivo no esté protegido</li>
                <li>Comprobar que el formato sea el esperado</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Instrucciones
        st.markdown("""
        ## 📋 Instrucciones de Uso
        
        1. **Instalar dependencias** (si no están instaladas):
           ```bash
           pip install camelot-py[cv]
           pip install opencv-python
           ```
        
        2. **Subir PDF**: Usar el panel lateral para cargar el archivo
        
        3. **Automático**: Camelot extraerá las tablas automáticamente
        
        4. **Verificar**: Revisar los datos extraídos en el dashboard
        
        5. **Descargar**: Exportar a Excel para análisis adicional
        
        ### 🎯 Ventajas de Camelot-py
        - Diseñada específicamente para **extraer tablas** de PDFs
        - Detecta automáticamente la **estructura tabular**
        - Maneja correctamente **espacios y separadores**
        - **Preserva la alineación** de columnas
        - **Menos errores** que parsing manual
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