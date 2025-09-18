import streamlit as st
import csv
import io
from datetime import datetime

# Configuración de página
st.set_page_config(
    page_title="Control de Tablillas - Alsina Forms",
    page_icon="🏗️",
    layout="wide"
)

# CSS básico
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .success-box { 
        background: #d4edda; 
        padding: 1rem; 
        border-radius: 8px; 
        margin: 1rem 0; 
        border-left: 4px solid #28a745;
    }
    
    .alert-info { 
        background: #d1ecf1; 
        color: #0c5460; 
        padding: 1rem; 
        border-radius: 8px; 
        margin: 1rem 0; 
        border-left: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Función principal de la aplicación"""
    # Header
    st.markdown('''
    <div class="main-header">
        <h1>🏗️ SISTEMA DE CONTROL DE TABLILLAS</h1>
        <h2>Alsina Forms Co.</h2>
        <p>📊 Análisis básico de datos</p>
        <div style="background: #000; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.8rem; display: inline-block; margin: 1rem 0;">🚀 Powered by Vercel</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Información
    st.markdown("""
    <div class="alert-info">
    <h3>📊 Versión Ultra-Ligera</h3>
    <p>Esta es una versión optimizada al máximo para Vercel con funcionalidades básicas.</p>
    <p><strong>Funcionalidades disponibles:</strong></p>
    <ul>
        <li>📄 Cargar archivos CSV</li>
        <li>📊 Visualizar datos básicos</li>
        <li>📈 Análisis simple</li>
        <li>💾 Exportar datos</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar archivo
    uploaded_file = st.file_uploader(
        "📂 Seleccionar archivo CSV",
        type=['csv'],
        help="Sube un archivo CSV con datos de tablillas"
    )
    
    if uploaded_file is not None:
        st.markdown('<div class="success-box">✅ <strong>Archivo cargado correctamente!</strong></div>', 
                    unsafe_allow_html=True)
        
        try:
            # Leer CSV
            csv_data = []
            csv_reader = csv.reader(io.StringIO(uploaded_file.read().decode('utf-8')))
            
            for row in csv_reader:
                csv_data.append(row)
            
            if not csv_data:
                st.error("❌ El archivo CSV está vacío")
                return
            
            # Mostrar información básica
            st.subheader("📊 Información del Archivo")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📋 Total Filas", len(csv_data))
            
            with col2:
                st.metric("📊 Total Columnas", len(csv_data[0]) if csv_data else 0)
            
            with col3:
                st.metric("📅 Fecha", datetime.now().strftime('%Y-%m-%d'))
            
            # Mostrar encabezados
            if csv_data:
                st.subheader("📋 Encabezados de Columnas")
                headers = csv_data[0]
                for i, header in enumerate(headers):
                    st.write(f"{i+1}. **{header}**")
            
            # Mostrar datos (primeras 10 filas)
            st.subheader("📋 Datos (Primeras 10 filas)")
            
            if len(csv_data) > 1:
                # Crear tabla simple
                data_to_show = csv_data[:11]  # Headers + 10 filas
                
                # Mostrar como tabla HTML
                html_table = "<table style='width:100%; border-collapse: collapse;'>"
                
                for i, row in enumerate(data_to_show):
                    if i == 0:
                        # Header
                        html_table += "<tr style='background-color: #f0f0f0; font-weight: bold;'>"
                        for cell in row:
                            html_table += f"<td style='border: 1px solid #ddd; padding: 8px;'>{cell}</td>"
                        html_table += "</tr>"
                    else:
                        # Data rows
                        html_table += "<tr>"
                        for cell in row:
                            html_table += f"<td style='border: 1px solid #ddd; padding: 8px;'>{cell}</td>"
                        html_table += "</tr>"
                
                html_table += "</table>"
                st.markdown(html_table, unsafe_allow_html=True)
            
            # Análisis básico
            st.subheader("📈 Análisis Básico")
            
            if len(csv_data) > 1:
                st.write(f"**Total de registros:** {len(csv_data) - 1}")  # -1 por el header
                st.write(f"**Total de columnas:** {len(csv_data[0])}")
                
                # Contar valores únicos en cada columna
                if len(csv_data) > 1:
                    st.write("**Valores únicos por columna:**")
                    for i, header in enumerate(csv_data[0]):
                        unique_values = set()
                        for row in csv_data[1:]:  # Skip header
                            if i < len(row):
                                unique_values.add(row[i])
                        st.write(f"- **{header}**: {len(unique_values)} valores únicos")
            
            # Botón de descarga
            if st.button("💾 Descargar Datos como CSV", type="primary"):
                # Recrear CSV
                output = io.StringIO()
                csv_writer = csv.writer(output)
                
                for row in csv_data:
                    csv_writer.writerow(row)
                
                csv_content = output.getvalue()
                filename = f"datos_tablillas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv_content,
                    file_name=filename,
                    mime="text/csv"
                )
                
                st.success(f"✅ Archivo listo para descargar: **{filename}**")
            
        except Exception as e:
            st.error(f"❌ Error procesando archivo: {str(e)}")
            st.write("**Posibles soluciones:**")
            st.write("- Verifica que el archivo sea un CSV válido")
            st.write("- Asegúrate de que use codificación UTF-8")
            st.write("- Intenta con un archivo más pequeño")
    
    else:
        # Mostrar ejemplo de formato CSV
        st.subheader("📋 Formato de Archivo CSV Esperado")
        st.write("Tu archivo CSV debería tener este formato:")
        
        example_data = [
            ["Return_Packing_Slip", "Customer_Name", "Total_Open", "Total_Tablets"],
            ["FL001", "Cliente A", "5", "10"],
            ["FL002", "Cliente B", "3", "8"],
            ["FL003", "Cliente C", "7", "12"]
        ]
        
        # Mostrar ejemplo como tabla
        html_table = "<table style='width:100%; border-collapse: collapse;'>"
        for i, row in enumerate(example_data):
            if i == 0:
                html_table += "<tr style='background-color: #f0f0f0; font-weight: bold;'>"
                for cell in row:
                    html_table += f"<td style='border: 1px solid #ddd; padding: 8px;'>{cell}</td>"
                html_table += "</tr>"
            else:
                html_table += "<tr>"
                for cell in row:
                    html_table += f"<td style='border: 1px solid #ddd; padding: 8px;'>{cell}</td>"
                html_table += "</tr>"
        html_table += "</table>"
        st.markdown(html_table, unsafe_allow_html=True)

if __name__ == "__main__":
    main()