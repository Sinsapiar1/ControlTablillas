# 🏭 Sistema Profesional de Control de Tablillas - Alsina Forms Co.

## 📋 Descripción

Sistema profesional desarrollado en **Streamlit** para el análisis y control de tablillas de Alsina Forms Co. Permite procesar archivos PDF, analizar datos de Excel y generar informes ejecutivos profesionales con visualizaciones avanzadas y análisis comparativo multi-días.

## 🚀 Características Principales

### 📊 **Procesamiento Inteligente de PDF**
- ✅ **Extracción automática** con múltiples métodos Camelot (Stream optimizado, Stream básico, Lattice optimizado)
- ✅ **Corrección automática** de columnas concatenadas (ej: "FL 612D 729000018764" → separación correcta)
- ✅ **Normalización inteligente** de códigos de almacén (612d → 612D)
- ✅ **Procesamiento robusto** con manejo de errores y fallbacks
- ✅ **Análisis visual** con gráficos interactivos y métricas de performance

### 📈 **Análisis Multi-Excel Avanzado**
- ✅ **Comparación entre múltiples archivos** Excel de diferentes fechas
- ✅ **Detección automática** de albaranes cerrados, nuevos y con cambios
- ✅ **Análisis de tendencias** temporales con evolución día a día
- ✅ **Dashboard ejecutivo** profesional con KPIs destacados
- ✅ **Carga directa** sin archivos temporales para mejor performance

### 📋 **Informes Profesionales**
- ✅ **Exportación a Excel** con formato ejecutivo y múltiples hojas
- ✅ **Métricas avanzadas** y análisis de performance detallado
- ✅ **Gráficos significativos** con colores corporativos y diseño profesional
- ✅ **Descarga directa** sin afectar el dashboard (sin recarga de página)
- ✅ **Indicadores de progreso** visual durante la generación

### 🎨 **Interfaz Visual Profesional**
- ✅ **Dashboard ejecutivo** con cards con gradientes y efectos visuales
- ✅ **Gráficos mejorados** con colores corporativos (#667eea, #4facfe, #fa709a)
- ✅ **Métricas de evolución** con tendencias automáticas (CRECIENTE/DECRECIENTE/ESTABLE)
- ✅ **CSS personalizado** para efectos visuales profesionales

## 🛠️ Tecnologías

- **Frontend:** Streamlit 1.28.1
- **Procesamiento:** Pandas 2.0.3, Camelot-Py 0.10.1
- **Visualización:** Plotly 5.17.0
- **Excel:** OpenPyXL 3.1.2, XlsxWriter 3.1.9
- **PDF:** PyPDF2 2.12.1
- **Imágenes:** OpenCV 4.8.1.78
- **Sistema:** Ghostscript 0.7
- **Python:** 3.11.9

## 🚀 Despliegue en Render

### 📋 Requisitos
- Python 3.11.9
- Dependencias en `requirements_railway.txt`
- Configuración en `render.yaml`

### ⚙️ Configuración
```yaml
# render.yaml
services:
  - type: web
    name: control-tablillas
    env: python
    buildCommand: pip install -r requirements_railway.txt
    startCommand: streamlit run app_original.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
```

### 🔧 Archivos de Configuración
- `app_original.py` - Aplicación principal con todas las funcionalidades
- `requirements_railway.txt` - Dependencias optimizadas para Render
- `render.yaml` - Configuración de despliegue
- `Procfile` - Comando de inicio
- `runtime.txt` - Versión de Python

## 📊 Funcionalidades Detalladas

### 1. **📄 Procesamiento de PDF Avanzado**

#### **Extracción Multi-Método:**
- **Stream Optimizado:** Configuraciones avanzadas para mejor detección
- **Stream Básico:** Fallback para casos complejos
- **Lattice Optimizado:** Para tablas con líneas definidas

#### **Corrección Inteligente de Columnas:**
- **Detección automática** de columnas concatenadas
- **Separación correcta** de códigos (FL, WH_Code, Return_Packing_Slip)
- **Manejo de patrones** específicos de Alsina Forms

#### **Normalización de Datos:**
- **Códigos de almacén** normalizados a mayúsculas
- **Fechas** convertidas automáticamente
- **Números** validados y limpiados
- **Strings** estandarizados

### 2. **📊 Análisis Multi-Excel Comparativo**

#### **Carga Directa de Archivos:**
- **Sin archivos temporales** para mejor performance
- **Múltiples engines** (openpyxl, xlrd) para compatibilidad
- **Extracción automática** de fechas desde nombres de archivo
- **Validación** de formato y columnas

#### **Comparación Robusta:**
- **Detección de albaranes nuevos** (aparecen en archivo actual)
- **Detección de albaranes cerrados** (desaparecen del archivo actual)
- **Análisis de cambios** en albaranes existentes
- **Cálculo de tablillas** cerradas y agregadas

#### **Análisis de Tendencias:**
- **Evolución temporal** de tablillas pendientes
- **Métricas de eficiencia** por día
- **Patrones de cierre** y actividad
- **Predicciones** basadas en tendencias

### 3. **🎯 Dashboard Ejecutivo Visual**

#### **KPIs Principales:**
- **Nuevos Albaranes:** Cantidad de albaranes nuevos en el período
- **Albaranes Cerrados:** Cantidad de albaranes completamente cerrados
- **Tablillas Cerradas:** Total de tablillas cerradas
- **Tablillas Agregadas:** Total de tablillas agregadas

#### **Métricas Avanzadas:**
- **Eficiencia de Cierre:** Porcentaje de tablillas cerradas vs agregadas
- **Score de Actividad:** Actividad promedio por archivo
- **Tasa de Cierre:** Porcentaje de albaranes cerrados vs nuevos
- **Neto de Tablillas:** Balance entre cerradas y agregadas

#### **Visualizaciones:**
- **Cards con gradientes** y colores corporativos
- **Gráficos de evolución** temporal con tendencias
- **Análisis por almacén** con métricas específicas
- **Gráficos de prioridad** y urgencia

### 4. **💾 Exportación Profesional**

#### **Informe Ejecutivo Multi-Días:**
- **Dashboard Ejecutivo:** KPIs principales con interpretaciones
- **Evolución Diaria:** Cambios día a día con tendencias
- **Cambios Diarios:** Comparaciones detalladas entre fechas
- **Detalles de Cambios:** Análisis específico por albarán
- **Análisis por Almacén:** Métricas por código de almacén

#### **Características de Exportación:**
- **Descarga directa** sin afectar el dashboard
- **Indicadores de progreso** visual durante generación
- **Múltiples hojas** con análisis detallado
- **Formato profesional** con emojis y colores
- **Métricas calculadas** automáticamente

## 🎯 Flujo de Uso

### 1. **📄 Procesamiento de PDF**
1. **Subir archivo PDF** en la pestaña "PROCESAR PDF"
2. **Extracción automática** con múltiples métodos Camelot
3. **Corrección de columnas** concatenadas automáticamente
4. **Normalización** de códigos de almacén
5. **Análisis visual** con gráficos y métricas
6. **Exportación** a Excel con formato profesional

### 2. **📊 Análisis Multi-Excel**
1. **Subir múltiples archivos** Excel en "ANÁLISIS MULTI-EXCEL"
2. **Carga automática** con normalización de códigos
3. **Comparación robusta** entre archivos
4. **Dashboard ejecutivo** con KPIs destacados
5. **Análisis de tendencias** temporales
6. **Exportación** de informes profesionales

### 3. **📈 Análisis Visual**
1. **Dashboard ejecutivo** con métricas principales
2. **Gráficos de evolución** temporal
3. **Análisis por almacén** con performance
4. **Métricas de tendencia** automáticas
5. **Visualizaciones interactivas** con Plotly

## 📈 Métricas y Análisis

### **📊 Métricas de Albaranes:**
- **Nuevos:** Albaranes que aparecen en archivos más recientes
- **Cerrados:** Albaranes que desaparecen de archivos más recientes
- **Con Cambios:** Albaranes existentes con modificaciones
- **Total:** Cantidad total de albaranes por período

### **🔢 Métricas de Tablillas:**
- **Cerradas:** Tablillas que se cerraron en el período
- **Agregadas:** Tablillas que se agregaron en el período
- **Pendientes:** Tablillas que permanecen abiertas
- **Neto:** Balance entre cerradas y agregadas

### **📈 Métricas de Performance:**
- **Eficiencia de Cierre:** % de tablillas cerradas vs agregadas
- **Score de Actividad:** Actividad promedio por archivo
- **Tasa de Cierre:** % de albaranes cerrados vs nuevos
- **Ratio Cierre/Nuevo:** Relación entre cierres y nuevos albaranes

### **🎯 Métricas de Tendencias:**
- **Evolución Temporal:** Cambios día a día
- **Patrones de Actividad:** Días con más/menos actividad
- **Predicciones:** Tendencias basadas en datos históricos
- **Alertas:** Casos que requieren atención

## 🔧 Características Técnicas

### **🛡️ Manejo Robusto de Errores:**
- **Try/catch** en todas las funciones críticas
- **Fallbacks** para métodos de extracción
- **Validación** de datos antes de procesar
- **Mensajes informativos** para el usuario

### **⚡ Optimización de Performance:**
- **Carga directa** sin archivos temporales
- **Procesamiento en memoria** para mejor velocidad
- **Indicadores de progreso** visual
- **Limpieza automática** de recursos

### **🎨 Interfaz Profesional:**
- **CSS personalizado** con gradientes y efectos
- **Colores corporativos** consistentes
- **Iconos significativos** para cada métrica
- **Diseño responsivo** y moderno

## 🔒 Seguridad y Privacidad

- **Procesamiento local** de archivos sin almacenamiento permanente
- **Análisis en tiempo real** sin persistencia de datos
- **Exportación segura** con datos binarios válidos
- **Sin tracking** ni recolección de datos personales

## 📞 Soporte y Mantenimiento

Sistema desarrollado específicamente para **Alsina Forms Co.** con:
- **Control profesional** de tablillas y albaranes
- **Análisis de performance** operativa
- **Informes ejecutivos** para toma de decisiones
- **Visualizaciones avanzadas** para insights

## 🚀 Acceso a la Aplicación

**🌐 Aplicación Desplegada:** [Render Deployment URL]
- **Disponibilidad:** 24/7
- **Performance:** Optimizada para Render
- **Actualizaciones:** Automáticas desde GitHub

## 📋 Versión y Actualizaciones

**Versión:** 1.0.0  
**Plataforma:** Render  
**Python:** 3.11.9  
**Última actualización:** Septiembre 2024  
**Estado:** Activo y funcional

---

**Desarrollado con ❤️ para Alsina Forms Co. - Sistema profesional de control de tablillas**