import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import io
from datetime import datetime, timedelta
import re
import pdfplumber
import base64
from pdf_parser import AlsinaPDFParser, TablillasAnalyzer

# Configuración de la página
st.set_page_config(
    page_title="Control de Tablillas - Alsina Forms",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
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
    
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem;
    }
    
    .priority-high { color: #dc3545; font-weight: bold; }
    .priority-medium { color: #fd7e14; font-weight: bold; }
    .priority-low { color: #28a745; font-weight: bold; }
    
    .sidebar .sidebar-content {
        background: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

class TablillasController:
    def __init__(self):
        self.data_file = "tablillas_history.json"
        self.config_file = "config.json"
        self.pdf_parser = AlsinaPDFParser()
        self.analyzer = TablillasAnalyzer()
        self.load_history()
        self.load_config()
    
    def load_config(self):
        """Cargar configuración desde JSON"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # Crear configuración por defecto
            self.config = self._create_default_config()
            self.save_config()
    
    def _create_default_config(self):
        """Crear configuración por defecto"""
        return {
            "priority_weights": {
                "days_since_return": 0.4,
                "counting_delay": 0.3,
                "validation_delay": 0.2,
                "open_tablets": 0.1
            },
            "alert_thresholds": {
                "high_priority_days": 15,
                "critical_open_tablets": 50,
                "warning_delay_days": 10
            }
        }
    
    def save_config(self):
        """Guardar configuración en JSON"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def load_history(self):
        """Cargar historial desde JSON"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
        except FileNotFoundError:
            self.history = {"reports": [], "summary": {}}
    
    def save_history(self):
        """Guardar historial en JSON"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def extract_pdf_data(self, pdf_file):
        """Extraer datos del PDF usando el parser especializado"""
        try:
            return self.pdf_parser.extract_from_pdf(pdf_file)
        except Exception as e:
            st.error(f"Error al procesar PDF: {str(e)}")
            return None
    
    def parse_pdf_content(self, content):
        """Parsear contenido del PDF en DataFrame"""
        lines = content.split('\n')
        data = []
        
        # Buscar líneas con datos (que empiecen con FL)
        for line in lines:
            if line.strip().startswith('FL'):
                # Limpiar y dividir la línea
                parts = re.split(r'\s+', line.strip())
                if len(parts) >= 16:  # Verificar que tenga suficientes columnas
                    try:
                        row = {
                            'WH': parts[0],
                            'WH_Code': parts[1],
                            'Return_Packing_Slip': parts[2],
                            'Return_Date': pd.to_datetime(parts[3]),
                            'Jobsite_ID': parts[4],
                            'Cost_Center': parts[5],
                            'Invoice_Start_Date': pd.to_datetime(parts[6]),
                            'Invoice_End_Date': pd.to_datetime(parts[7]),
                            'Customer_Name': ' '.join(parts[8:11]),  # Nombre puede tener espacios
                            'Job_Site_Name': ' '.join(parts[11:14]),  # Nombre puede tener espacios
                            'Definitive_Dev': parts[14],
                            'Counted_Date': pd.to_datetime(parts[15]) if parts[15] != 'No' else None,
                            'Tablets': self.extract_tablets(parts[16:19]),
                            'Total_Tablets': int(parts[19]) if parts[19].isdigit() else 0,
                            'Open_Tablets': self.extract_open_tablets(parts[20:22]),
                            'Total_Open': int(parts[22]) if parts[22].isdigit() else 0,
                            'Counting_Delay': int(parts[23]) if parts[23].isdigit() else 0,
                            'Validation_Delay': int(parts[24]) if parts[24].isdigit() else 0
                        }
                        data.append(row)
                    except (ValueError, IndexError) as e:
                        continue  # Saltar líneas con formato incorrecto
        
        return pd.DataFrame(data) if data else None
    
    def extract_tablets(self, parts):
        """Extraer información de tablillas"""
        tablets_str = ' '.join(parts)
        return tablets_str.replace(',', ' ').strip()
    
    def extract_open_tablets(self, parts):
        """Extraer información de tablillas abiertas"""
        open_str = ' '.join(parts)
        return open_str.replace(',', ' ').strip()
    
    def calculate_priorities(self, df):
        """Calcular prioridades usando el analizador especializado"""
        if df is None or df.empty:
            return df
        
        return self.analyzer.calculate_priority_score(df)
    
    def generate_warehouse_summary(self, df):
        """Generar resumen por almacén usando el analizador especializado"""
        if df is None or df.empty:
            return {}
        
        return self.analyzer.generate_warehouse_insights(df)

def main():
    st.markdown('<div class="main-header"><h1>🏗️ Control de Tablillas - Alsina Forms Co.</h1></div>', 
                unsafe_allow_html=True)
    
    controller = TablillasController()
    
    # Sidebar
    st.sidebar.header("📂 Carga de Datos")
    
    # Upload PDF
    uploaded_file = st.sidebar.file_uploader(
        "Cargar Informe PDF",
        type=['pdf'],
        help="Sube el informe de devoluciones en formato PDF"
    )
    
    # Navigation
    st.sidebar.header("📊 Navegación")
    page = st.sidebar.selectbox(
        "Seleccionar Vista",
        ["Dashboard Principal", "Análisis Detallado", "Historial", "Configuración"]
    )
    
    if uploaded_file is not None:
        # Procesar PDF
        with st.spinner('Procesando archivo PDF...'):
            df = controller.extract_pdf_data(uploaded_file)
        
        if df is not None and not df.empty:
            # Calcular prioridades
            df_prioritized = controller.calculate_priorities(df)
            
            # Guardar en historial
            report_data = {
                'date': datetime.now().isoformat(),
                'total_records': len(df),
                'warehouses': list(df['WH_Code'].unique()),
                'data': df_prioritized.to_dict('records')
            }
            controller.history['reports'].append(report_data)
            controller.save_history()
            
            # Mostrar contenido según la página seleccionada
            if page == "Dashboard Principal":
                show_main_dashboard(df_prioritized, controller)
            elif page == "Análisis Detallado":
                show_detailed_analysis(df_prioritized)
            elif page == "Historial":
                show_history(controller)
            elif page == "Configuración":
                show_configuration()
        else:
            st.error("No se pudieron extraer datos del PDF. Verifica el formato del archivo.")
    else:
        st.info("👆 Sube un archivo PDF para comenzar el análisis")
        
        # Mostrar historial si existe
        if controller.history['reports']:
            st.header("📈 Últimos Reportes")
            for report in controller.history['reports'][-3:]:  # Mostrar últimos 3
                st.write(f"📅 {report['date'][:10]} - {report['total_records']} registros")

def show_main_dashboard(df, controller):
    """Mostrar dashboard principal"""
    st.header("🎯 Dashboard Principal")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Devoluciones",
            value=len(df),
            delta=f"+{len(df)} nuevas"
        )
    
    with col2:
        total_open = df['Total_Open'].sum()
        st.metric(
            label="Tablillas Pendientes",
            value=total_open,
            delta=f"⚠️ {len(df[df['Priority_Level'] == 'Alta'])} alta prioridad"
        )
    
    with col3:
        avg_delay = df['Counting_Delay'].mean()
        st.metric(
            label="Retraso Promedio (días)",
            value=f"{avg_delay:.1f}",
            delta=f"📊 Crítico si >15"
        )
    
    with col4:
        warehouses = df['WH_Code'].nunique()
        st.metric(
            label="Almacenes Activos",
            value=warehouses,
            delta=f"🏢 {warehouses} ubicaciones"
        )
    
    # Gráficos principales
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Prioridades por Almacén")
        priority_chart = px.bar(
            df.groupby(['WH_Code', 'Priority_Level']).size().reset_index(name='count'),
            x='WH_Code',
            y='count',
            color='Priority_Level',
            color_discrete_map={
                'Alta': '#dc3545',
                'Media': '#fd7e14',
                'Baja': '#28a745'
            },
            title="Distribución de Prioridades"
        )
        st.plotly_chart(priority_chart, use_container_width=True)
    
    with col_right:
        st.subheader("📅 Tendencia de Devoluciones")
        timeline_data = df.groupby('Return_Date').size().reset_index(name='count')
        timeline_chart = px.line(
            timeline_data,
            x='Return_Date',
            y='count',
            title="Devoluciones por Fecha",
            markers=True
        )
        st.plotly_chart(timeline_chart, use_container_width=True)
    
    # Tabla de alta prioridad
    st.subheader("🚨 Devoluciones de Alta Prioridad")
    high_priority = df[df['Priority_Level'] == 'Alta'].head(10)
    
    if not high_priority.empty:
        display_df = high_priority[[
            'WH_Code', 'Return_Date', 'Customer_Name', 'Job_Site_Name',
            'Total_Open', 'Days_Since_Return', 'Counting_Delay'
        ]].copy()
        
        # Aplicar formato condicional
        st.dataframe(
            display_df.style.apply(
                lambda x: ['background-color: #ffebee' if x.name in high_priority.index else '' 
                          for i in x], axis=1
            ),
            use_container_width=True
        )
    else:
        st.success("✅ No hay devoluciones de alta prioridad pendientes")
    
    # Botón de descarga
    if st.button("📥 Descargar Reporte Excel", type="primary"):
        download_excel(df)

def show_detailed_analysis(df):
    """Mostrar análisis detallado"""
    st.header("🔍 Análisis Detallado")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        warehouse_filter = st.multiselect(
            "Filtrar por Almacén",
            options=df['WH_Code'].unique(),
            default=df['WH_Code'].unique()
        )
    
    with col2:
        priority_filter = st.multiselect(
            "Filtrar por Prioridad",
            options=['Alta', 'Media', 'Baja'],
            default=['Alta', 'Media', 'Baja']
        )
    
    with col3:
        date_range = st.date_input(
            "Rango de Fechas",
            value=(df['Return_Date'].min(), df['Return_Date'].max()),
            min_value=df['Return_Date'].min(),
            max_value=df['Return_Date'].max()
        )
    
    # Aplicar filtros
    filtered_df = df[
        (df['WH_Code'].isin(warehouse_filter)) &
        (df['Priority_Level'].isin(priority_filter)) &
        (df['Return_Date'] >= pd.Timestamp(date_range[0])) &
        (df['Return_Date'] <= pd.Timestamp(date_range[1]))
    ]
    
    # Mostrar tabla filtrada
    st.subheader(f"📋 Resultados Filtrados ({len(filtered_df)} registros)")
    st.dataframe(filtered_df, use_container_width=True)
    
    # Análisis estadístico
    st.subheader("📈 Estadísticas")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Por Almacén:**")
        warehouse_stats = filtered_df.groupby('WH_Code').agg({
            'Total_Open': 'sum',
            'Counting_Delay': 'mean',
            'Days_Since_Return': 'max'
        }).round(2)
        st.dataframe(warehouse_stats)
    
    with col2:
        st.write("**Por Cliente:**")
        customer_stats = filtered_df.groupby('Customer_Name').agg({
            'Total_Open': 'sum',
            'Priority_Score': 'mean'
        }).round(2).head(10)
        st.dataframe(customer_stats)

def show_history(controller):
    """Mostrar historial"""
    st.header("📚 Historial de Reportes")
    
    if not controller.history['reports']:
        st.info("No hay reportes en el historial")
        return
    
    # Mostrar reportes por fecha
    for i, report in enumerate(reversed(controller.history['reports'])):
        with st.expander(f"📅 Reporte del {report['date'][:10]} - {report['total_records']} registros"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Fecha:** {report['date'][:19]}")
                st.write(f"**Total Registros:** {report['total_records']}")
                st.write(f"**Almacenes:** {', '.join(report['warehouses'])}")
            
            with col2:
                if st.button(f"Ver Detalles", key=f"detail_{i}"):
                    # Mostrar datos del reporte
                    report_df = pd.DataFrame(report['data'])
                    st.dataframe(report_df.head(20))

def show_configuration():
    """Mostrar configuración"""
    st.header("⚙️ Configuración")
    
    st.subheader("🎯 Parámetros de Prioridad")
    
    col1, col2 = st.columns(2)
    
    with col1:
        days_weight = st.slider("Peso - Días desde retorno", 0.0, 1.0, 0.4, 0.1)
        delay_weight = st.slider("Peso - Retraso de conteo", 0.0, 1.0, 0.3, 0.1)
    
    with col2:
        validation_weight = st.slider("Peso - Retraso de validación", 0.0, 1.0, 0.2, 0.1)
        open_weight = st.slider("Peso - Tablillas abiertas", 0.0, 1.0, 0.1, 0.1)
    
    st.info(f"Suma total de pesos: {days_weight + delay_weight + validation_weight + open_weight:.1f}")
    
    st.subheader("🔔 Alertas")
    
    high_priority_days = st.number_input("Días para alta prioridad", min_value=1, value=15, step=1)
    critical_open_tablets = st.number_input("Tablillas abiertas críticas", min_value=1, value=50, step=5)
    
    if st.button("💾 Guardar Configuración"):
        st.success("Configuración guardada correctamente")

def download_excel(df):
    """Generar y descargar archivo Excel"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Hoja principal con datos
        df.to_excel(writer, sheet_name='Devoluciones', index=False)
        
        # Hoja de resumen
        summary = df.groupby('WH_Code').agg({
            'Total_Open': 'sum',
            'Counting_Delay': 'mean',
            'Priority_Score': 'mean'
        }).round(2)
        summary.to_excel(writer, sheet_name='Resumen_Almacenes')
        
        # Hoja de alta prioridad
        high_priority = df[df['Priority_Level'] == 'Alta']
        high_priority.to_excel(writer, sheet_name='Alta_Prioridad', index=False)
    
    # Descargar archivo
    st.download_button(
        label="📥 Descargar Excel",
        data=output.getvalue(),
        file_name=f"control_tablillas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    main()