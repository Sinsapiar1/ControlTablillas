# 🏭 Sistema Profesional de Control de Tablillas - Alsina Forms Co.

## 📋 Descripción

Sistema profesional desarrollado en **Streamlit** para el análisis y control de tablillas de Alsina Forms Co. Permite procesar archivos PDF, analizar datos de Excel y generar informes ejecutivos profesionales.

## 🚀 Características Principales

### 📊 **Análisis de PDF**
- ✅ Extracción automática de datos con **Camelot**
- ✅ Procesamiento inteligente de tablillas
- ✅ Corrección automática de columnas concatenadas
- ✅ Análisis visual con gráficos interactivos

### 📈 **Análisis Multi-Excel**
- ✅ Comparación entre múltiples archivos Excel
- ✅ Detección de albaranes cerrados y nuevos
- ✅ Análisis de tendencias temporales
- ✅ Dashboard ejecutivo profesional

### 📋 **Informes Profesionales**
- ✅ Exportación a Excel con formato ejecutivo
- ✅ Métricas avanzadas y análisis de performance
- ✅ Gráficos significativos y visualizaciones
- ✅ Informes multi-días con tendencias

## 🛠️ Tecnologías

- **Frontend:** Streamlit 1.28.1
- **Procesamiento:** Pandas 2.0.3, Camelot-Py
- **Visualización:** Plotly 5.17.0
- **Excel:** OpenPyXL, XlsxWriter
- **PDF:** PyPDF2 2.12.1
- **Python:** 3.11.9

## 🚀 Despliegue en Render

### 📋 Requisitos
- Python 3.11.9
- Dependencias en `requirements_compatible.txt`
- Configuración en `render.yaml`

### ⚙️ Configuración
```yaml
# render.yaml
services:
  - type: web
    name: control-tablillas
    env: python
    buildCommand: pip install -r requirements_compatible.txt
    startCommand: streamlit run app_original.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
```

### 🔧 Archivos de Configuración
- `app_original.py` - Aplicación principal
- `requirements_compatible.txt` - Dependencias optimizadas
- `render.yaml` - Configuración de Render
- `Procfile` - Comando de inicio
- `runtime.txt` - Versión de Python

## 📊 Funcionalidades

### 1. **Procesamiento de PDF**
- Extracción automática con múltiples métodos Camelot
- Corrección inteligente de columnas concatenadas
- Análisis visual con métricas de performance

### 2. **Análisis Comparativo**
- Comparación entre archivos Excel de diferentes fechas
- Detección de cambios día a día
- Análisis de tendencias y evolución

### 3. **Dashboard Ejecutivo**
- KPIs principales con diseño profesional
- Gráficos interactivos con colores corporativos
- Métricas de eficiencia y performance

### 4. **Exportación Profesional**
- Informes Excel con formato ejecutivo
- Múltiples hojas con análisis detallado
- Descarga directa sin afectar el dashboard

## 🎯 Uso

1. **Subir PDF:** Carga archivos PDF para extracción automática
2. **Análisis Multi-Excel:** Sube múltiples archivos Excel para comparación
3. **Visualizar:** Explora gráficos y métricas en el dashboard
4. **Exportar:** Descarga informes profesionales en Excel

## 📈 Métricas Incluidas

- **Albaranes:** Nuevos, cerrados, con cambios
- **Tablillas:** Cerradas, agregadas, pendientes
- **Performance:** Eficiencia, tasa de cierre, score de actividad
- **Tendencias:** Evolución temporal, patrones, predicciones

## 🔒 Seguridad

- Procesamiento local de archivos
- Sin almacenamiento permanente de datos
- Análisis en tiempo real
- Exportación segura

## 📞 Soporte

Sistema desarrollado para **Alsina Forms Co.** - Control profesional de tablillas y análisis de performance operativa.

---

**Versión:** 1.0.0  
**Plataforma:** Render  
**Python:** 3.11.9  
**Última actualización:** 2024